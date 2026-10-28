#pragma once
#include <Arduino.h>
#include "card_header.h"

/* Stage 3 -- the raw stream onto the card, without ever making core 1 wait.
 *
 * WHERE THE WORK RUNS. Core 1 owns the counters, the 1 Hz report and the
 * serial port; core 0 owns the radio, and now every SdFat and SPI call as
 * well. The two are joined by a single-producer/single-consumer ring: core 1
 * pushes finished lines into it and returns in a few hundred cycles, core 0
 * drains it to the card and is the only core allowed to block on one. Rule 4.2
 * is therefore satisfied by construction -- a slow card cannot stall a report,
 * the same way a failed Wi-Fi join cannot (see snapshot() in
 * logger_network.cpp).
 *
 * A full ring drops lines and counts them. A dropped line is a hole in the
 * card's copy, which the Pi's copy still has; a stalled report corrupts the
 * Pi's trip metrics. Losing the recording is always the better trade -- the
 * Pico's job as a counter outranks its job as a recorder.
 */

// Core 1 prints through Out instead of Serial: every byte goes to the host
// over USB CDC exactly as before, and each completed line is also pushed into
// the ring for core 0. CR is dropped on the way to the card so the file is
// LF-only and the stage-3 diff against the host CSV is byte-clean.
//
// CORE 1 ONLY. The line assembly buffer is not shared or locked.
class OutTee : public Print {
public:
    size_t write(uint8_t b) override;
    size_t write(const uint8_t *data, size_t n) override;
};
extern OutTee Out;

void sdSetup();          // core 0: pin assignment only, no card traffic
void sdLoop();           // core 0: card init, ring drain, flush, rename
void sdPrintStatus();    // core 1: the one-line '# SD' note
bool sdStatusChanged();  // core 1: true once after a state or filename change

/* The self-describing header block, CARD_FORMAT.md. Provided by the sketch and
 * called by this module, which is the opposite of the usual direction and is
 * deliberate: the per-file facts (name, open instant, whether the clock was
 * trusted) belong to the card module, while the pin map, the divider ratios and
 * the calibration belong to the sketch. Each fills in what it owns and
 * card_header.h renders the one agreed text.
 *
 * CORE SAFETY: compile-time constants and rp2040.getChipID() only. No pin
 * reads, no counter state, nothing core 1 owns -- so core 0 may call it. */
void cardHeaderFacts(logger_card_header::Facts &facts);

constexpr uint32_t SD_SYNC_INTERVAL_MS = 10000;  // flush at least this often
constexpr uint32_t SD_SYNC_BYTES = 4096;         // ...or this many bytes

#include "upload_protocol.h"
// Core 0 upload adapter. One directory entry or one <=512-byte read per call.
bool sdUploadReady();
void sdUploadRewind();
bool sdUploadValid(const logger_upload::File &item);
int sdUploadNext(logger_upload::File &item);
int sdUploadRead(const logger_upload::File &item, uint32_t offset, char *out, size_t n);
