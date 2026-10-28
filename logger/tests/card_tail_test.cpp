#include "../firmware/accord-logger/card_tail.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <algorithm>
#include <functional>
#include <memory>
#include <string>
#include <vector>

/* Behavioural regression for review R1 (2026-10-25): a short METADATA write
 * must never cost a sample row.
 *
 * What is real and what is modelled, stated so nobody over-reads a PASS:
 *
 *   REAL      card_tail.h -- the exact Tail<File> logger_sd.cpp instantiates,
 *             every decision about when bytes may be written and when a file
 *             must be settled or abandoned.
 *   MODELLED  the file (FakeFile: O_APPEND semantics, with writes, syncs and
 *             reads that fail on command), and the order sdLoop() calls things
 *             in (Device::step mirrors it: open-or-retry, rename note, settle,
 *             drain). The ring is a byte string the producer appends whole
 *             lines to, drained in chunks that deliberately split rows.
 *   NOT HERE  SdFat itself and the card. FakeFile is the worst case the
 *             contract allows -- including a write that reports 0 after landing
 *             bytes, which SdFat's FatFile::write really does -- not an
 *             emulation of the library.
 *
 * Every scenario asserts ROW IDENTITY: the data rows across all files the run
 * produced, in order, are exactly the rows core 1 pushed -- not totals, which a
 * later cumulative counter can carry over a lost row.
 *
 * `--emit DIR HEADER` writes each scenario's card files plus the expected `ms`
 * list into DIR, so tests/check_rename_note.py can push them through the real
 * cardconv.py as well. HEADER is the real renderer's block
 * (card_header_test --emit).
 */

namespace {

// ---- the file --------------------------------------------------------------

enum class Fx { Full, Zero, Short, LyingZero, Vanish };
struct WriteFx {
    Fx kind = Fx::Full;
    size_t keep = 0;   // bytes that land, for Short and LyingZero
};

struct FakeFile {
    std::string name;
    std::string data;   // the file as its logical end sees it
    uint64_t pos = 0;
    std::function<WriteFx(const char *, size_t)> onWrite;
    std::function<bool()> onSync;
    std::function<bool()> onRead;

    size_t write(const void *buf, size_t n) {
        const char *b = static_cast<const char *>(buf);
        const WriteFx fx = onWrite ? onWrite(b, n) : WriteFx{};
        switch (fx.kind) {
        case Fx::Full: data.append(b, n); return n;
        case Fx::Zero: return 0;
        case Fx::Short: data.append(b, fx.keep); return fx.keep;
        case Fx::LyingZero: data.append(b, fx.keep); return 0;
        case Fx::Vanish: return n;   // claims success, lands nothing
        }
        return 0;
    }
    bool sync() { return onSync ? onSync() : true; }
    uint64_t size() { return data.size(); }
    bool seekSet(uint64_t p) {
        if (p > data.size()) return false;
        pos = p;
        return true;
    }
    int read() {
        if (onRead && !onRead()) return -1;
        if (pos >= data.size()) return -1;
        return static_cast<unsigned char>(data[pos++]);
    }
};

using Tail = logger_card_tail::Tail<FakeFile>;

bool starts(const char *b, size_t n, const char *prefix) {
    const size_t p = strlen(prefix);
    return n >= p && memcmp(b, prefix, p) == 0;
}

// ---- the device, in sdLoop() order ----------------------------------------

const char *const NOTE =
    "# log.rename from=/BOOT_540.CSV to=/20261024_115959.CSV at_ms=6540\n";

struct Device {
    std::string header;                 // written to every created file
    std::vector<FakeFile *> card;       // every file, in creation order
    FakeFile *file = nullptr;
    bool open = false;
    Tail tail;
    std::string ring;                   // bytes core 1 pushed
    size_t ringTail = 0;                // bytes consumed
    size_t chunk = 512;
    bool renamePending = false;         // a BOOT_ file awaiting its note
    bool legacy = false;                // drain like v0.7.0, as the control
    bool headerLost = false, noteLost = false;
    int fails = 0;
    // How the next open after a failure names its file.
    bool resumeSameName = false;
    std::function<void(FakeFile &)> arm;   // fault injection for new files

    ~Device() {
        for (FakeFile *f : card) delete f;
    }

    void openCard() {
        if (resumeSameName && file) {
            open = true;               // same name again: O_APPEND onto it
            tail.resumed();
            return;
        }
        file = new FakeFile;
        file->name = "/F" + std::to_string(card.size()) + ".CSV";
        if (arm) arm(*file);
        card.push_back(file);
        open = true;
        tail.created();
        headerLost = tail.appendMetadata(*file, header.data(), header.size())
                     != logger_card_tail::Note::Written;
    }

    void fail() {
        open = false;
        ++fails;
    }

    void rename() {
        if (!renamePending || !tail.noteAllowed()) return;
        renamePending = false;
        noteLost = tail.appendMetadata(*file, NOTE, strlen(NOTE))
                   != logger_card_tail::Note::Written;
    }

    bool drain() {
        if (legacy) {
            // v0.7.0: wrote straight through, whatever the file ended in.
            while (ringTail < ring.size()) {
                size_t n = ring.size() - ringTail;
                if (n > chunk) n = chunk;
                if (file->write(ring.data() + ringTail, n) != n) return false;
                ringTail += n;
            }
            return true;
        }
        if (!tail.mayDrain()) return true;
        while (ringTail < ring.size()) {
            size_t n = ring.size() - ringTail;
            if (n > chunk) n = chunk;
            if (!tail.appendChunk(*file, ring.data() + ringTail, n))
                return false;          // ring tail NOT advanced
            ringTail += n;
        }
        return true;
    }

    void step() {
        if (!open) {
            openCard();
            return;
        }
        rename();
        if (!legacy && tail.orphaned() && !tail.settle(*file)) {
            fail();
            return;
        }
        if (!drain()) fail();
    }
};

// ---- the producer ----------------------------------------------------------

std::string row(unsigned i) {
    const unsigned ms = 1540 + i * 1000;
    const bool moving = i < 155;
    const unsigned steps = moving ? i : 155;
    char out[128];
    snprintf(out, sizeof(out),
             "%u,%u,%s,%u,%s,%s,0,%u,1844,1861,2900,2714,%u,%u\n",
             ms, steps * 46, moving ? "46.00" : "0.00",
             steps * 30, moving ? "30.00" : "0.00",
             moving ? "900" : "0",
             1840 + (i % 19),
             moving ? ms : 0u, moving ? 1u : 0u);
    return out;
}

struct Run {
    std::vector<std::string> pushed;   // data rows, without '\n'
};

/* Push `rows` rows, one per pass, with a note line every 7 so the ring holds
 * mixed lines; the BOOT_ rename becomes due at row `renameAt`. Odd chunk
 * sizes make the drain end mid-row on most passes, which is the state that
 * makes metadata dangerous. A few idle passes at the end let retries finish. */
Run drive(Device &d, unsigned rows, unsigned renameAt) {
    Run r;
    for (unsigned i = 0; i < rows + 12; ++i) {
        if (i < rows) {
            if (i % 7 == 3) d.ring += "# TIME 2026-10-24T12:00:06Z src=sntp synced=1 age=0s\n";
            const std::string line = row(i);
            d.ring += line;
            r.pushed.push_back(line.substr(0, line.size() - 1));
            if (i == renameAt) d.renamePending = true;
        }
        d.step();
    }
    return r;
}

// ---- what a reader sees ----------------------------------------------------

std::vector<std::string> lines(const std::string &s) {
    std::vector<std::string> out;
    size_t at = 0;
    while (at < s.size()) {
        size_t nl = s.find('\n', at);
        if (nl == std::string::npos) nl = s.size();
        out.push_back(s.substr(at, nl - at));
        at = nl + 1;
    }
    return out;
}

struct Seen {
    std::vector<std::string> rows;
    int blank = 0, torn = 0, notes = 0;
};

Seen read(const Device &d) {
    Seen s;
    for (const FakeFile *f : d.card)
        for (const std::string &l : lines(f->data)) {
            if (l.empty()) ++s.blank;
            else if (l[0] == '#') ++s.notes;
            else if (std::count(l.begin(), l.end(), ',') != 13) ++s.torn;
            else s.rows.push_back(l);
        }
    return s;
}

int failures = 0, passes = 0;
// Quiet on success -- 160-odd assertions -- and loud on failure.
void check(const char *scenario, const char *what, bool ok,
           const std::string &detail = "") {
    if (ok) {
        ++passes;
        return;
    }
    printf("  FAIL %-28s %s%s%s\n", scenario, what,
           detail.empty() ? "" : " -- ", detail.c_str());
    ++failures;
}

struct Scenario {
    const char *name;
    const char *what;
    std::function<void(Device &)> setup;
    int wantFails;      // file abandonments expected
    bool wantNoteLost;
    bool wantHeaderLost;
};

const char *emitDir = nullptr;

void emit(const Scenario &sc, const Device &d, const Run &r) {
    if (!emitDir) return;
    const std::string base = std::string(emitDir) + "/" + sc.name;
    for (size_t i = 0; i < d.card.size(); ++i) {
        FILE *f = fopen((base + "." + std::to_string(i) + ".CSV").c_str(), "wb");
        assert(f);
        fwrite(d.card[i]->data.data(), 1, d.card[i]->data.size(), f);
        fclose(f);
    }
    FILE *f = fopen((base + ".expected").c_str(), "w");
    assert(f);
    for (const std::string &p : r.pushed) fprintf(f, "%s\n", p.substr(0, p.find(',')).c_str());
    fclose(f);
}

void run(const Scenario &sc, const std::string &header) {
    const int before = failures;
    std::string summary;
    for (size_t chunk : {size_t(512), size_t(37), size_t(61)}) {
        Device d;
        d.header = header;
        d.chunk = chunk;
        sc.setup(d);
        const Run r = drive(d, 180, 5);
        const Seen s = read(d);
        std::string label = std::string(sc.name) + "/" + std::to_string(chunk);
        check(label.c_str(), "every pushed row, intact, once, in order",
              s.rows == std::vector<std::string>(r.pushed),
              std::to_string(s.rows.size()) + " of " +
                  std::to_string(r.pushed.size()) + " rows");
        check(label.c_str(), "no torn row, no blank line",
              s.torn == 0 && s.blank == 0,
              "torn=" + std::to_string(s.torn) + " blank=" + std::to_string(s.blank));
        check(label.c_str(), "ring fully drained", d.ringTail == d.ring.size());
        check(label.c_str(), "file abandonments as expected",
              d.fails == sc.wantFails, std::to_string(d.fails));
        check(label.c_str(), "loss reported exactly when it happened",
              d.noteLost == sc.wantNoteLost && d.headerLost == sc.wantHeaderLost);
        if (chunk == 37) {
            emit(sc, d, r);
            summary = std::to_string(s.rows.size()) + " rows, " +
                      std::to_string(d.card.size()) + " file(s), " +
                      std::to_string(s.notes) + " notes";
        }
    }
    printf("  %-4s %-24s %-46s %s\n", failures == before ? "ok" : "FAIL",
           sc.name, sc.what, summary.c_str());
}

} // namespace

int main(int argc, char **argv) {
    std::string header = "# accord-log/1\n# log.file name=/BOOT_540.CSV opened_ms=540 clock=none\n# log.end\n";
    if (argc > 1 && strcmp(argv[1], "--emit") == 0) {
        if (argc < 4) {
            fprintf(stderr, "usage: %s --emit DIR HEADER\n", argv[0]);
            return 2;
        }
        emitDir = argv[2];
        FILE *h = fopen(argv[3], "rb");
        if (!h) return 2;
        header.clear();
        char buf[256];
        size_t n;
        while ((n = fread(buf, 1, sizeof(buf), h)) > 0) header.append(buf, n);
        fclose(h);
    }

    auto isNote = [](const char *b, size_t n) { return starts(b, n, "# log.rename"); };
    auto isNewline = [](const char *b, size_t n) { return n == 1 && b[0] == '\n'; };
    auto isHeader = [](const char *b, size_t n) { return starts(b, n, "# accord-log/1"); };
    // Fault only the first file; files opened after an abandonment are healthy.
    auto firstFile = [](Device &d, std::function<void(FakeFile &)> f) {
        d.arm = [f, done = false](FakeFile &file) mutable {
            if (!done) f(file);
            done = true;
        };
    };

    const std::vector<Scenario> scenarios = {
        {"baseline", "no fault", [](Device &) {}, 0, false, false},
        {"note-zero", "note write lands nothing, returns 0",
         [&](Device &d) { firstFile(d, [&](FakeFile &f) {
             f.onWrite = [&](const char *b, size_t n) {
                 return isNote(b, n) ? WriteFx{Fx::Zero} : WriteFx{}; }; }); },
         0, true, false},
        {"note-short", "note write lands 34 bytes, returns 34",
         [&](Device &d) { firstFile(d, [&](FakeFile &f) {
             f.onWrite = [&](const char *b, size_t n) {
                 return isNote(b, n) ? WriteFx{Fx::Short, 34} : WriteFx{}; }; }); },
         0, true, false},
        {"note-lying", "note write lands 20 bytes, returns 0",
         [&](Device &d) { firstFile(d, [&](FakeFile &f) {
             f.onWrite = [&](const char *b, size_t n) {
                 return isNote(b, n) ? WriteFx{Fx::LyingZero, 20} : WriteFx{}; }; }); },
         0, true, false},
        {"note-unsynced", "note written whole, its sync fails once",
         [&](Device &d) { firstFile(d, [&](FakeFile &f) {
             auto armed = std::make_shared<bool>(false);
             f.onWrite = [&, armed](const char *b, size_t n) {
                 if (isNote(b, n)) *armed = true;
                 return WriteFx{}; };
             f.onSync = [armed] {
                 if (!*armed) return true;
                 *armed = false;
                 return false; }; }); },
         0, true, false},
        {"note-unsynced-dead", "note sync fails, and settle's sync too",
         [&](Device &d) { firstFile(d, [&](FakeFile &f) {
             auto armed = std::make_shared<bool>(false);
             f.onWrite = [&, armed](const char *b, size_t n) {
                 if (isNote(b, n)) *armed = true;
                 return WriteFx{}; };
             f.onSync = [armed] { return !*armed; }; }); },
         1, true, false},
        {"short-newline-fails", "short note, settle's newline write fails",
         [&](Device &d) { firstFile(d, [&](FakeFile &f) {
             f.onWrite = [&](const char *b, size_t n) {
                 if (isNote(b, n)) return WriteFx{Fx::Short, 34};
                 if (isNewline(b, n)) return WriteFx{Fx::Zero};
                 return WriteFx{}; }; }); },
         1, true, false},
        {"short-newline-vanishes", "settle's newline claims success, lands nothing",
         [&](Device &d) { firstFile(d, [&](FakeFile &f) {
             f.onWrite = [&](const char *b, size_t n) {
                 if (isNote(b, n)) return WriteFx{Fx::Short, 34};
                 if (isNewline(b, n)) return WriteFx{Fx::Vanish};
                 return WriteFx{}; }; }); },
         1, true, false},
        {"short-read-fails", "short note, settle cannot read back",
         [&](Device &d) { firstFile(d, [&](FakeFile &f) {
             f.onWrite = [&](const char *b, size_t n) {
                 return isNote(b, n) ? WriteFx{Fx::Short, 34} : WriteFx{}; };
             f.onRead = [] { return false; }; }); },
         1, true, false},
        {"short-then-resume", "short note, abandon, reopen SAME name",
         [&](Device &d) {
             d.resumeSameName = true;
             firstFile(d, [&](FakeFile &f) {
                 auto once = std::make_shared<int>(0);
                 f.onWrite = [&, once](const char *b, size_t n) {
                     if (isNote(b, n)) return WriteFx{Fx::Short, 34};
                     // the first settle attempt fails; the resumed one works
                     if (isNewline(b, n) && (*once)++ == 0) return WriteFx{Fx::Zero};
                     return WriteFx{}; }; }); },
         1, true, false},
        {"header-short", "header lands 40 bytes, returns 40",
         [&](Device &d) { firstFile(d, [&](FakeFile &f) {
             f.onWrite = [&](const char *b, size_t n) {
                 return isHeader(b, n) ? WriteFx{Fx::Short, 40} : WriteFx{}; }; }); },
         0, false, true},
    };

    printf("card_tail_test: %zu scenarios x 3 chunk sizes\n", scenarios.size());
    for (const Scenario &sc : scenarios) run(sc, header);

    // ---- a resumed file whose previous boot ended mid-row ------------------
    {
        Device d;
        d.header = header;
        d.resumeSameName = true;
        d.file = new FakeFile;
        d.card.push_back(d.file);
        d.file->data = header + "99540,4554,46.00,2970,30.";   // power cut mid-row
        const Run r = drive(d, 40, 1000);
        const Seen s = read(d);
        check("resume-torn-boot", "every pushed row, intact, in order",
              s.rows == r.pushed, std::to_string(s.rows.size()));
        check("resume-torn-boot", "the old fragment stands alone as one torn line",
              s.torn == 1 && s.blank == 0, "torn=" + std::to_string(s.torn));
    }

    // ---- the control: the same fault through v0.7.0's drain ----------------
    // Proves the scenarios above can fail: the short note swallows a row.
    {
        Device d;
        d.header = header;
        d.legacy = true;
        d.chunk = 37;
        firstFile(d, [&](FakeFile &f) {
            f.onWrite = [&](const char *b, size_t n) {
                return isNote(b, n) ? WriteFx{Fx::Short, 34} : WriteFx{}; }; });
        const Run r = drive(d, 180, 5);
        const Seen s = read(d);
        check("control-v070", "v0.7.0 drain LOSES exactly one row here",
              s.rows.size() + 1 == r.pushed.size(),
              std::to_string(s.rows.size()) + " of " + std::to_string(r.pushed.size()));
    }

    // ---- unit edges of Tail itself -----------------------------------------
    {
        FakeFile f;
        Tail t;
        t.created();
        check("unit", "unrenderable note writes nothing and orphans nothing",
              t.appendMetadata(f, NOTE, 0) == logger_card_tail::Note::Lost
                  && f.data.empty() && t.mayDrain());
        check("unit", "a note without its newline is refused",
              t.appendMetadata(f, "# x", 3) == logger_card_tail::Note::Lost
                  && f.data.empty() && t.mayDrain());
        check("unit", "a mid-row chunk forbids notes",
              t.appendChunk(f, "1,2,", 4) && !t.noteAllowed());
        check("unit", "settle on a non-orphan touches nothing",
              t.settle(f) && f.data == "1,2,");
        f.onWrite = [](const char *, size_t) { return WriteFx{Fx::Short, 2}; };
        check("unit", "while orphaned, chunks are refused",
              t.appendChunk(f, "3\n", 2) && t.noteAllowed()
                  && t.appendMetadata(f, "# n\n", 4) == logger_card_tail::Note::Lost
                  && !t.appendChunk(f, "4\n", 2) && f.data == "1,2,3\n# ");
        f.onWrite = nullptr;
        check("unit", "settle terminates the fragment exactly once",
              t.settle(f) && f.data == "1,2,3\n# \n" && t.noteAllowed());
        FakeFile empty;
        Tail e;
        e.resumed();   // ring at line start: orphaned
        check("unit", "an empty resumed file settles with no write",
              e.orphaned() && e.settle(empty) && empty.data.empty());
    }

    printf("  %-4s %-24s %s\n", failures ? "" : "ok", "edges",
           "resumed torn boot, v0.7.0 control, Tail unit edges");
    if (failures) {
        printf("\n%d failure(s), %d passed\n", failures, passes);
        return 1;
    }
    printf("\nPASS (%d assertions): no metadata fault costs a sample row; every "
           "abandonment carries the queued rows to the next file\n", passes);
    return 0;
}
