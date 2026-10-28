#pragma once
#include <stddef.h>
#include <stdint.h>

/* Where the card file's last line stands, and the rule for writing to it.
 * Pure state over a file-like object, so the failure paths can be exercised
 * off the board with a file that short-writes on demand
 * (tests/card_tail_test.cpp). logger_sd.cpp instantiates it with SdFat's FsFile.
 *
 * ---- why this exists (v0.7.1, review R1 of 2026-10-25) --------------------
 *
 * Two kinds of bytes reach the file, and they have different continuations:
 *
 *   ring chunks  drain() copies raw ring bytes capped at 512 and at the ring
 *                wrap. A chunk can end mid-row, and that is FINE: the rest of
 *                the row is the next thing in the ring, so the next chunk
 *                finishes it.
 *   metadata     the header block and the `# log.rename` note are written
 *                directly. If such a write stops short, the fragment has NO
 *                continuation anywhere -- and the next ring chunk, which begins
 *                a fresh row, would be appended to it. A reader then sees one
 *                line starting `#` and drops it as a note: the sample is gone.
 *                v0.7.0's comment claimed a partial note "costs no sample";
 *                that was wrong, and the review reproduced the loss with the
 *                real cardconv.py. The header had the same hole since v0.6.0,
 *                with its write result and sync result both ignored.
 *
 * So the state is not just "does the file end in '\n'" but also "if it does
 * not, is the rest of that line still coming from the ring". The second is
 * `orphan_`: the file may end in a fragment nothing will complete. While it is
 * set, NOTHING may be drained into the file; settle() must first make the file
 * provably end at a line boundary, or the caller abandons the file.
 *
 * ---- what is trusted, and what is not ---------------------------------------
 *
 * A write's return value is NOT trusted to say how many bytes landed. SdFat's
 * FatFile::write returns 0 on any failure even after copying part of the data
 * into the sector cache, and other implementations may return a positive short
 * count. settle() therefore asks the FILE: it reads back the last byte at the
 * file's logical end -- which is also exactly where the next O_APPEND write
 * lands -- and only declares a boundary when that byte is '\n' after a
 * successful sync. That covers every case without modelling the library:
 *
 *   zero-byte write        file still ends in the '\n' before the note: nothing
 *                          is added, no blank line is created
 *   positive short write   file ends in the fragment: one '\n' terminates it, so
 *                          it stays a '#' line and swallows nothing
 *   reports 0, wrote some  whichever of the two the file actually shows
 *   full write, sync fails file ends in the note's own '\n': only a successful
 *                          sync is still required before samples resume
 *   any step of settle()   returns false; the caller fails the file (it closes,
 *   failing                and the ring is untouched, so no sample is lost --
 *                          it lands in the next file after the 5 s retry)
 *
 * Bounded: settle() is at most sync, seek, read, write, sync, seek, read. It is
 * never retried within a pass; a failure hands over to the existing fail() and
 * its backoff.
 *
 * A file RESUMED by O_APPEND (same name opened again -- in practice
 * `BOOT_<ms>.CSV` colliding across boots) is treated the same way when the ring
 * is at a line start: whatever ends that file was written by an earlier open,
 * and nothing in this ring completes it. When the ring is mid-row on resume the
 * v0.6.0 assumption -- the file holds the head of that row -- is kept unchanged.
 *
 * NOT addressed here, recorded in NOTES-FOR-REVIEW.md as pre-existing (v0.6.0)
 * and outside this fix: a NEW file created while the ring is mid-row (a drain
 * failure part-way through a row, then card reinsertion) begins with the tail
 * of a row whose head went to the old file.
 */
namespace logger_card_tail {

enum class Note : uint8_t {
    Written,   // the whole note, newline included, is in the file and synced
    Lost,      // not persisted; the file must be settled before samples resume
};

template <class File>
class Tail {
public:
    /* A file this module just created. Its header block ends in '\n', and an
     * empty file (header refused by render()) is a boundary too. */
    void created() {
        fileAtLineStart_ = true;
        orphan_ = false;
    }

    /* A file reopened with bytes already in it. */
    void resumed() {
        fileAtLineStart_ = false;
        orphan_ = ringAtLineStart_;
    }

    /* True when a directly-written line (metadata) may go in now: the file
     * ends at a boundary AND the ring's next byte starts a row, so the note
     * lands between two whole lines and cannot meet a fragment from either
     * side. */
    bool noteAllowed() const {
        return fileAtLineStart_ && ringAtLineStart_ && !orphan_;
    }

    /* False while the file may end in a fragment nothing will complete. */
    bool mayDrain() const { return !orphan_; }
    bool orphaned() const { return orphan_; }

    /* One ring chunk. Returns false if it did not all land; the caller must
     * then fail the file WITHOUT advancing the ring tail, exactly as v0.6.0
     * did. Refuses outright while orphaned. */
    bool appendChunk(File &f, const char *bytes, size_t n) {
        if (orphan_) return false;
        if (!n) return true;
        if (f.write(bytes, n) != n) return false;
        // The ring and the file move together here: same last byte.
        fileAtLineStart_ = ringAtLineStart_ = bytes[n - 1] == '\n';
        return true;
    }

    /* Metadata written directly to the file: one or more complete lines, the
     * last ending in '\n'. Used for the header block (straight after
     * created()) and the rename note (only once noteAllowed()). Anything short
     * of the whole block, synced, marks the file orphaned so settle() runs
     * before the next drain. A block that could not be rendered (n == 0) is
     * reported Lost and nothing is written, so nothing needs settling. */
    Note appendMetadata(File &f, const char *line, size_t n) {
        if (!fileAtLineStart_ || orphan_ || !n || line[n - 1] != '\n')
            return Note::Lost;
        const bool whole = f.write(line, n) == n;
        if (whole && f.sync()) return Note::Written;   // still at a boundary
        fileAtLineStart_ = false;
        orphan_ = true;
        return Note::Lost;
    }

    /* Make the file provably end at a line boundary. true: samples may
     * resume. false: the caller must fail the file. Only does work when
     * orphaned. */
    bool settle(File &f) {
        if (!orphan_) return true;
        // The fragment, or the note's own newline, must reach the card before
        // anything is appended after it; a card that cannot sync now is
        // failing and the file is abandoned.
        if (!f.sync()) return false;
        int last = lastByte(f);
        if (last < 0) return false;
        if (last != '\n' && last != EMPTY) {
            if (f.write("\n", 1) != 1) return false;
            if (!f.sync()) return false;
            // Verify rather than infer: the newline must be the file's last
            // byte, at the place the next append will land.
            last = lastByte(f);
            if (last != '\n') return false;
        }
        orphan_ = false;
        fileAtLineStart_ = true;
        return true;
    }

private:
    static constexpr int EMPTY = 256;   // not a byte value

    // The byte at the file's logical end, EMPTY for an empty file, -1 if it
    // cannot be read.
    static int lastByte(File &f) {
        const uint64_t size = f.size();
        if (size == 0) return EMPTY;
        if (!f.seekSet(size - 1)) return -1;
        return f.read();
    }

    bool fileAtLineStart_ = false;
    // Survives across files: whether the NEXT ring byte begins a line. True at
    // boot, because core 1 only ever pushes whole lines into an empty ring.
    bool ringAtLineStart_ = true;
    bool orphan_ = false;
};

} // namespace logger_card_tail
