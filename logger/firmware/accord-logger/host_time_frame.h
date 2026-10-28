#pragma once
#include <stdint.h>

/* Rule 4.10's frame, as pure arithmetic so it can be tested off the board.
 *
 *     @<13 digits>        epoch milliseconds, e.g. @1792345678901
 *
 * The side effect lives in the sketch; only the judgement lives here. Three
 * conditions have to hold at once, and the reason there are three rather than
 * one is that each alone is weak:
 *
 *  - LEADING '@'. This firmware prints no '@' anywhere, by standing invariant,
 *    so no echo of its own output can open a frame. That is the strong
 *    condition, and the other two are what keep it from being the only one.
 *  - EXACT LENGTH, 13 digits and nothing else. A split echo of a report row is
 *    all digits and commas; the comma fails, and so does any length but 14.
 *  - RANGE. 2026 to 2040. Catches a truncated or doubled frame that happens to
 *    land on the right length.
 */
namespace logger_host_time {

constexpr char     FRAME  = '@';
constexpr uint8_t  LENGTH = 14;                  // '@' + 13 digits
constexpr uint64_t MIN_MS = 1767225600000ULL;    // 2026-01-01T00:00:00Z
constexpr uint64_t MAX_MS = 2208988800000ULL;    // 2040-01-01T00:00:00Z

inline bool decode(const char *burst, uint8_t len, uint64_t &ms) {
    if (len != LENGTH || burst[0] != FRAME) return false;
    uint64_t value = 0;
    for (uint8_t i = 1; i < len; ++i) {
        if (burst[i] < '0' || burst[i] > '9') return false;
        value = value * 10 + uint64_t(burst[i] - '0');
    }
    if (value < MIN_MS || value > MAX_MS) return false;
    ms = value;
    return true;
}

} // namespace logger_host_time
