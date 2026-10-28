#include <Arduino.h>
#include <SPI.h>
#include <SdFat.h>
#include <hardware/sync.h>
#include <pico/mutex.h>
#include <pico/rand.h>
#include <sys/time.h>
#include "logger_sd.h"
#include "logger_network.h"
#include "card_tail.h"
#include "upload_identity.h"

namespace {
// SPI0, wired as built 2026-10-18 (SPEC 5.2). The module's own 3V3 pin is fed
// from the Pico's 3V3(OUT), so the shifter's rail cannot exceed 3.3 V whatever
// a card does -- that is what makes MISO on GP16 safe here.
constexpr uint8_t PIN_SD_MISO = 16, PIN_SD_CS = 17, PIN_SD_SCK = 18,
                  PIN_SD_MOSI = 19;
// 12 MHz, not the 25 MHz these cards will take: the signals cross a level
// shifter and jumper wires. Bandwidth is irrelevant here -- 1 Hz of 40-byte
// lines is 40 B/s against a 512-byte sector.
constexpr uint32_t SD_CLOCK_MHZ = 12;

constexpr size_t RING_SIZE = 8192;   // power of two; ~200 lines of 1 Hz report
constexpr size_t RING_MASK = RING_SIZE - 1;
constexpr size_t CHUNK = 512;        // one sector per write call
constexpr size_t MAX_DRAIN = 8;      // chunks per core-0 pass
constexpr uint32_t RETRY_MS = 5000;  // card re-init backoff

char ring[RING_SIZE];
// SPSC: core 1 writes head, core 0 writes tail. 32-bit aligned loads and
// stores are single instructions on this core, so neither index can be seen
// half-updated; the barriers order the data against the index.
volatile uint32_t ringHead = 0, ringTail = 0;
uint32_t droppedLines = 0;           // core 1 only (producer side)

enum class SdState : uint8_t { Init, Ok, Fail };

struct Status {
    SdState state = SdState::Init;
    const char *err = "init";
    char file[32] = "";
    uint32_t bytes = 0;
    uint32_t wmaxMs = 0;
    uint32_t revision = 0;
    bool renameNoteLost = false;
    bool headerLost = false;
    uint8_t code = 0, data = 0;      // SdFat's own card error, see sdPrintStatus
};
auto_init_mutex(sdStatusMutex);
Status published;                    // core 0 writes, core 1 reads

SdFs sd;
FsFile file, uploadDir;
bool uploadActiveDone = false;
uint32_t cardGeneration = 0, syncedBytes = 0;
char uploadId[33] = "";
SdState state = SdState::Init;
const char *err = "init";
char filePath[32] = "";
bool nameIsBoot = false;             // /BOOT_<ms>.CSV, awaiting a trusted clock
uint32_t fileOpenMs = 0;             // millis() when the current file was opened
uint32_t fileBytes = 0, sinceSync = 0, wmaxMs = 0;
uint32_t retryAt = 0, syncAt = 0;
/* Where the file's last line stands. REQUIRED, because drain() writes raw ring
 * chunks capped at CHUNK and at the ring wrap and respects no line boundary at
 * all -- so after an arbitrary pass the file can end mid-row -- and because a
 * short METADATA write leaves a fragment that no ring byte will ever complete.
 * Every byte this module writes goes through `tail`; see card_tail.h for the
 * rules and tests/card_tail_test.cpp for the failure paths exercised natively.
 * (v0.7.0 had a bare `atLineStart` flag here, which tracked the first problem
 * and not the second: review R1, 2026-10-25.) */
logger_card_tail::Tail<FsFile> tail;
/* The header block could not be persisted whole. Reported like rnote=lost. */
bool headerLost = false;
/* A rename that happened but whose note could not be persisted. Reported in
 * the '# SD' note, which goes through the ring to the HOST as well -- the
 * right channel for a failure to write to the card. */
bool renameNoteLost = false;
uint32_t statusRevision = 0;
uint8_t errCode = 0, errData = 0;    // SdFat's card error, carried to the note

// Every call that can block on the card is wrapped in this, so wmax_ms in the
// '# SD' note is the real worst case over the whole run, not a sample.
void trackWorst(uint32_t startMs) {
    const uint32_t spent = millis() - startMs;
    if (spent > wmaxMs) wmaxMs = spent;
}

void publish() {
    mutex_enter_blocking(&sdStatusMutex);   // core 0 may block; core 1 never does
    published.state = state;
    published.err = err;
    memcpy(published.file, filePath, sizeof(published.file));
    published.bytes = fileBytes;
    published.wmaxMs = wmaxMs;
    published.renameNoteLost = renameNoteLost;
    published.headerLost = headerLost;
    published.revision = statusRevision;
    published.code = errCode;
    published.data = errData;
    mutex_exit(&sdStatusMutex);
}

void fail(const char *reason, uint8_t code = 0, uint8_t data = 0) {
    ++cardGeneration;
    if (uploadDir) uploadDir.close();
    if (file) file.close();
    state = SdState::Fail;
    err = reason;
    errCode = code;
    errData = data;
    ++statusRevision;
    retryAt = millis() + RETRY_MS;
    publish();
}

/* Name the file for the instant it was opened, in UTC, once that instant is
 * knowable. Before the first SNTP reply the clock is not trusted, so the file
 * opens as /BOOT_<ms>.CSV and is renamed the moment a trusted clock arrives --
 * one file per boot either way, and no file ever carries a wrong date. */
void nameFor(char *out, size_t n, uint32_t openedMs) {
    if (networkClockTrusted()) {
        struct timeval tv;
        gettimeofday(&tv, nullptr);
        const time_t when = tv.tv_sec - (millis() - openedMs) / 1000;
        struct tm utc;
        gmtime_r(&when, &utc);
        strftime(out, n, "/%Y%m%d_%H%M%S.CSV", &utc);
        return;
    }
    snprintf(out, n, "/BOOT_%lu.CSV", (unsigned long)openedMs);
}

void dateTimeCallback(uint16_t *date, uint16_t *time) {
    // Directory timestamps, so the card is readable without cross-referencing
    // the file name. Zero when the clock is not trusted -- an invented date on
    // disk is worse than none.
    *date = *time = 0;
    if (!networkClockTrusted()) return;
    struct timeval tv;
    gettimeofday(&tv, nullptr);
    struct tm utc;
    const time_t when = tv.tv_sec;
    gmtime_r(&when, &utc);
    *date = FS_DATE(utc.tm_year + 1900, utc.tm_mon + 1, utc.tm_mday);
    *time = FS_TIME(utc.tm_hour, utc.tm_min, utc.tm_sec);
}

bool openCard() {
    const uint32_t t0 = millis();
    ++cardGeneration;
    syncedBytes = 0;
    if (uploadDir) uploadDir.close();
    if (!sd.begin(SdSpiConfig(PIN_SD_CS, SHARED_SPI, SD_SCK_MHZ(SD_CLOCK_MHZ),
                              &SPI))) {
        trackWorst(t0);
        /* The label alone cannot tell an empty slot from a dead bus: both set a
         * card error code. So carry SdFat's own code out to the note. 0x01 is
         * SD_CARD_ERROR_CMD0 -- no response at all, meaning wiring, power or no
         * card. Any later code means the card did answer and got further. */
        const uint8_t code = sd.sdErrorCode(), data = sd.sdErrorData();
        fail(code ? "no-card" : "mount", code, data);
        return false;
    }
    const uint32_t openedMs = millis();
    nameFor(filePath, sizeof(filePath), openedMs);
    // Never reopen an old recording. This invariant makes completion a fact:
    // after this handle is abandoned no subsequent boot/open appends to it.
    snprintf(uploadId, sizeof(uploadId), "%016llx%016llx",
             (unsigned long long)get_rand_64(), (unsigned long long)get_rand_64());
    if (sd.exists(filePath))
        snprintf(filePath, sizeof(filePath), "/BOOT_%.16s.CSV", uploadId);
    file = sd.open(filePath, O_RDWR | O_CREAT | O_EXCL | O_APPEND);
    trackWorst(t0);
    if (!file) {
        fail("open");
        return false;
    }
    nameIsBoot = !strncmp(filePath, "/BOOT_", 6);
    fileOpenMs = openedMs;
    fileBytes = file.size();
    sinceSync = 0;
    // Every newly created file describes itself before sample draining.
    headerLost = false;
    if (fileBytes == 0) {
        const uint32_t h0 = millis();
        logger_card_header::Facts facts;
        cardHeaderFacts(facts);
        facts.file_name = filePath;
        facts.upload_id = uploadId;
        facts.opened_ms = openedMs;
        facts.clock_trusted = !nameIsBoot;
        char block[logger_card_header::BUFFER];
        const size_t len = logger_card_header::render(block, sizeof(block), facts);
        tail.created();
        /* render() returns 0 rather than truncating. Logging without a header
         * beats losing the stream over a description that would not fit.
         * appendMetadata() also syncs immediately rather than letting the
         * header wait up to SD_SYNC_INTERVAL_MS: a power cut in that window
         * would otherwise produce rows with no description of what they are --
         * the one piece of the file that cannot be reconstructed from the rest
         * of it. Until v0.7.1 the write and sync results were both ignored, so
         * a short header write left a '#' fragment that the first sample row
         * was appended to. Now a short or unsynced header marks the file for
         * settling before any sample is drained into it. */
        headerLost = tail.appendMetadata(file, block, len)
                     != logger_card_tail::Note::Written;
        fileBytes = file.size();
        trackWorst(h0);
    }
    if (!headerLost) syncedBytes = fileBytes;
    renameNoteLost = false;
    state = SdState::Ok;
    err = "";
    errCode = errData = 0;
    ++statusRevision;
    syncAt = millis() + SD_SYNC_INTERVAL_MS;
    publish();
    return true;
}

/* Rename a boot-named file once the clock is trusted, and RECORD that it
 * happened (CARD_FORMAT.md §9).
 *
 * Why the note exists: the header is written when the file is created, so for a
 * file opened before SNTP it says `name=/BOOT_<ms>.CSV clock=none` -- truthfully
 * -- and then the file on disk gets a different, dated name. A card-only reader
 * was left holding a header that disagreed with the filename and no record of
 * which was later. The note closes that without rewriting anything.
 *
 * Only reached when nameIsBoot is set, so a file opened with a trusted clock
 * can never gain a fictitious rename event.
 */
void renameWhenClockArrives() {
    if (!nameIsBoot || !networkClockTrusted()) return;
    /* WAIT FOR A LINE BOUNDARY. The note is written directly to the file, and
     * drain() writes raw ring chunks that respect no line boundary, so doing
     * this mid-row would cut a sample in half. Deferring costs at most one
     * report: the next drain that empties the ring ends on a newline, because
     * core 1 only ever pushes complete lines. This is a bounded wait on a
     * condition that arrives on its own, not a retry loop. noteAllowed() also
     * requires the ring to be at a row start and the file not to be awaiting
     * settle(). */
    if (!tail.noteAllowed()) return;

    char wanted[32];
    nameFor(wanted, sizeof(wanted), fileOpenMs);
    char from[32];
    memcpy(from, filePath, sizeof(from));

    const uint32_t t0 = millis();
    const bool ok = !sd.exists(wanted) && file.sync() && file.rename(wanted);
    trackWorst(t0);
    if (!ok) {
        // Keep logging under the boot name rather than lose the stream over a
        // cosmetic rename; the '# SD' note keeps showing which file is live.
        // NO note is written here: nothing happened, so nothing is claimed.
        nameIsBoot = false;
        return;
    }
    memcpy(filePath, wanted, sizeof(filePath));
    nameIsBoot = false;

    /* The rename is now a fact on disk. Record it, and treat failure to record
     * it as a metadata loss: the stream keeps running under the new name, the
     * note is not retried, and the loss is reported through the ring in the
     * '# SD' note -- which reaches the HOST even when the card is the thing
     * that is failing. Where `# SD state=ok file=<new name>` is then the only
     * record of the name, as in v0.6.0.
     *
     * A failed note CAN cost samples unless it is handled, which v0.7.0 got
     * wrong (review R1): a fragment with no newline would have the next row
     * appended to it and the whole line read as a note. appendMetadata() marks
     * that case, and sdLoop() settles the boundary -- or abandons the file --
     * before drain() may write another byte. */
    const uint32_t t1 = millis();
    char note[logger_card_header::RENAME_BUFFER];
    const size_t w = logger_card_header::render_rename(
        note, sizeof(note), from, wanted, millis());
    const bool noted =
        tail.appendMetadata(file, note, w) == logger_card_tail::Note::Written;
    trackWorst(t1);
    fileBytes = file.size();
    if (noted) {
        syncedBytes = fileBytes;
        sinceSync = 0;   // appendMetadata synced everything before it too
    } else {
        renameNoteLost = true;
    }
    ++statusRevision;
    publish();
}

/* Before any drain into a file that may end in an orphaned fragment. Bounded
 * (card_tail.h), never retried here: a failure hands the file to fail(), which
 * closes it and leaves the ring tail exactly where it was, so the queued rows
 * go to the next file after the RETRY_MS backoff. */
bool settleTail() {
    if (!tail.orphaned()) return true;
    const uint32_t t0 = millis();
    const bool ok = tail.settle(file);
    trackWorst(t0);
    if (!ok) {
        fail("boundary");
        return false;
    }
    fileBytes = file.size();
    syncedBytes = fileBytes;
    sinceSync = 0;       // settle() ends on a successful sync
    ++statusRevision;
    publish();
    return true;
}

bool drain() {
    // Never append to a file whose tail is an orphaned fragment; sdLoop()
    // settles first, so this is a guard, not a path.
    if (!tail.mayDrain()) return true;
    for (size_t pass = 0; pass < MAX_DRAIN; ++pass) {
        const uint32_t head = ringHead;
        __dmb();
        const uint32_t rtail = ringTail;
        uint32_t avail = head - rtail;
        if (!avail) return true;
        const size_t index = rtail & RING_MASK;
        size_t n = avail;
        if (n > CHUNK) n = CHUNK;
        if (n > RING_SIZE - index) n = RING_SIZE - index;  // no wrap in one write
        const uint32_t t0 = millis();
        const bool whole = tail.appendChunk(file, ring + index, n);
        trackWorst(t0);
        if (!whole) {
            fail("write");   // ring tail NOT advanced: these bytes are retried
            return false;
        }
        __dmb();
        ringTail = rtail + n;
        fileBytes += n;
        sinceSync += n;
    }
    return true;
}
} // namespace

OutTee Out;

size_t OutTee::write(uint8_t b) {
    return write(&b, 1);
}

size_t OutTee::write(const uint8_t *data, size_t n) {
    // One line of the report is ~40 bytes and the longest note is under 100,
    // so a line that does not fit is a bug, not a long line: push what we have
    // and keep the stream aligned rather than silently splice two lines.
    static char line[160];
    static size_t len = 0;
    for (size_t i = 0; i < n; ++i) {
        const char c = char(data[i]);
        if (c == '\r') continue;                 // CDC prints CRLF; the card gets LF
        if (len < sizeof(line)) line[len++] = c;
        if (c == '\n' || len == sizeof(line)) {
            // Push the whole line or none of it: a partial line on the card is
            // a bare row to whatever reads it later (rule 4.1).
            const uint32_t head = ringHead;
            __dmb();
            const uint32_t used = head - ringTail;
            if (len <= RING_SIZE - 1 - used) {
                for (size_t k = 0; k < len; ++k)
                    ring[(head + k) & RING_MASK] = line[k];
                __dmb();
                ringHead = head + len;
            } else {
                ++droppedLines;
            }
            len = 0;
        }
    }
    return Serial.write(data, n);
}

void sdSetup() {
    SPI.setRX(PIN_SD_MISO);
    SPI.setCS(PIN_SD_CS);
    SPI.setSCK(PIN_SD_SCK);
    SPI.setTX(PIN_SD_MOSI);
    FsDateTime::setCallback(dateTimeCallback);
}

void sdLoop() {
    if (state != SdState::Ok) {
        // Not fatal and not urgent: a missing card retries every 5 s forever
        // while the counter keeps counting and printing.
        if (state == SdState::Fail && int32_t(millis() - retryAt) < 0) return;
        openCard();
        return;
    }
    renameWhenClockArrives();
    if (!settleTail()) return;
    if (!drain()) return;
    const bool due = int32_t(millis() - syncAt) >= 0;
    if (sinceSync && (due || sinceSync >= SD_SYNC_BYTES)) {
        const uint32_t t0 = millis();
        const bool ok = file.sync();
        trackWorst(t0);
        if (!ok) {
            fail("sync");
            return;
        }
        syncedBytes = fileBytes;
        sinceSync = 0;
        syncAt = millis() + SD_SYNC_INTERVAL_MS;
        publish();
    } else if (due) {
        syncAt = millis() + SD_SYNC_INTERVAL_MS;
        publish();                               // keep bytes/wmax_ms fresh
    }
}

namespace {
Status readStatus() {
    // Same discipline as the network mailbox: core 1 takes the lock only if it
    // is free, and otherwise reports what it last saw.
    static Status cached;
    if (mutex_try_enter(&sdStatusMutex, nullptr)) {
        cached = published;
        mutex_exit(&sdStatusMutex);
    }
    return cached;
}
} // namespace

void sdPrintStatus() {
    const Status s = readStatus();
    char line[128];
    if (s.state == SdState::Ok) {
        snprintf(line, sizeof(line),
                 "# SD state=ok file=%s bytes=%lu wmax_ms=%lu drop=%lu%s%s",
                 s.file, (unsigned long)s.bytes, (unsigned long)s.wmaxMs,
                 (unsigned long)droppedLines,
                 // Appended only when they happened, so the usual line is
                 // byte-for-byte what v0.6.0 printed.
                 s.headerLost ? " hdr=lost" : "",
                 s.renameNoteLost ? " rnote=lost" : "");
    } else {
        snprintf(line, sizeof(line),
                 "# SD state=%s err=%s code=0x%02X data=0x%02X drop=%lu",
                 s.state == SdState::Init ? "init" : "fail", s.err,
                 s.code, s.data, (unsigned long)droppedLines);
    }
    Out.println(line);
}

bool sdStatusChanged() {
    static uint32_t seen = 0;
    const Status s = readStatus();
    if (s.revision == seen) return false;
    seen = s.revision;
    return true;
}

// CORE 0 ONLY. Upload reads share the logging handle for the active file;
// opening a second reader could observe stale size/cache state. Old files are
// opened read-only. Every operation is measured in the existing wmax_ms.
bool sdUploadReady() {
    __dmb();
    return state == SdState::Ok && ringHead == ringTail && tail.mayDrain();
}
void sdUploadRewind() {
    const uint32_t t0 = millis();
    if (uploadDir) uploadDir.close();
    trackWorst(t0);
}
bool sdUploadValid(const logger_upload::File &item) {
    return state == SdState::Ok && item.generation == cardGeneration;
}
int sdUploadNext(logger_upload::File &item) {
    if (!sdUploadReady()) return 0;
    const uint32_t t0 = millis();
    if (!uploadDir) {
        uploadActiveDone = false;
        uploadDir = sd.open("/", O_RDONLY);
        trackWorst(t0);
        return uploadDir ? 0 : -1;
    }
    FsFile entry;
    item = logger_upload::File();
    if (!entry.openNext(&uploadDir, O_RDONLY)) {
        if (uploadActiveDone) { trackWorst(t0); return 2; }
        // Old files get a bounded visit before the active file each sweep.
        uploadActiveDone = true;
        memcpy(item.path, filePath, sizeof(filePath));
        item.active = true;
    } else {
        char name[65] = {};
        const bool regular = !entry.isDir() && entry.getName(name, sizeof(name));
        const size_t n = strlen(name);
        if (!regular || n < 4 || n >= sizeof(item.path) - 1 || strcmp(name + n - 4, ".CSV")) {
            entry.close(); trackWorst(t0); return 0;
        }
        item.path[0] = '/';
        memcpy(item.path + 1, name, n + 1);
        if (!strcmp(item.path, filePath)) {
            entry.close(); trackWorst(t0); return 0;
        }
    }
    item.generation = cardGeneration;
    char header[logger_card_header::BUFFER + 1];
    int got;
    bool restored = true;
    if (item.active) {
        const uint32_t pos = file.curPosition();
        item.bytes = syncedBytes;
        const size_t want = item.bytes < sizeof(header) - 1 ? item.bytes : sizeof(header) - 1;
        got = file.seekSet(0) ? file.read(header, want) : -1;
        restored = file.seekSet(pos);
    } else {
        const uint64_t size = entry.size();
        item.bytes = size <= UINT32_MAX ? uint32_t(size) : 0;
        got = item.bytes ? entry.read(header, sizeof(header) - 1) : -1;
    }
    if (entry) entry.close();
    trackWorst(t0);
    if (!restored) { fail("upload-seek"); return -1; }
    if (got <= 0) return 0;
    header[got] = 0;
    bool sealable = false;
    if (!logger_upload::identity(header, item.path, rp2040.getChipID(), item.name, sealable)) return 0;
    item.closed = sealable && !item.active;
    return 1;
}
int sdUploadRead(const logger_upload::File &item, uint32_t offset, char *out, size_t n) {
    if (!sdUploadReady() || !sdUploadValid(item) || offset > item.bytes || n > item.bytes - offset) return -1;
    const uint32_t t0 = millis();
    int got = -1;
    if (item.active) {
        const uint32_t pos = file.curPosition();
        if (file.seekSet(offset)) got = file.read(out, n);
        if (!file.seekSet(pos)) { fail("upload-seek"); got = -1; }
    } else {
        FsFile input = sd.open(item.path, O_RDONLY);
        if (input && input.seekSet(offset)) got = input.read(out, n);
        if (input) input.close();
    }
    trackWorst(t0);
    return got;
}
