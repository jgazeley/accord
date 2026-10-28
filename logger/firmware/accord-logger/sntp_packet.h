#pragma once
#include <stddef.h>
#include <stdint.h>
#include <string.h>

namespace logger_sntp {
constexpr uint64_t NTP_UNIX_OFFSET = 2208988800ULL;
constexpr uint64_t MIN_UNIX_SECONDS = 1704067200ULL; // 2024-01-01
constexpr uint64_t MAX_UNIX_SECONDS = 4102444800ULL; // 2100-01-01
constexpr uint64_t MAX_ROUNDTRIP_US = 1500000ULL;

inline uint32_t read32(const uint8_t *p) {
    return (uint32_t(p[0]) << 24) | (uint32_t(p[1]) << 16) |
           (uint32_t(p[2]) << 8) | uint32_t(p[3]);
}

// Source IP and UDP port are checked by the caller. Echoed transmit bytes
// bind this response to our one outstanding request, including after retries.
inline bool decode(const uint8_t *p, size_t len, const uint8_t nonce[8],
                   uint64_t roundtripUs, uint64_t &unixUs) {
    if (len != 48 || (p[0] >> 6) == 3 || (p[0] & 7) != 4 ||
        ((p[0] >> 3) & 7) < 3 || ((p[0] >> 3) & 7) > 4 ||
        p[1] == 0 || p[1] > 15 || memcmp(p + 24, nonce, 8) != 0 ||
        roundtripUs > MAX_ROUNDTRIP_US) return false;
    if (read32(p + 40) == 0 && read32(p + 44) == 0) return false;
    uint64_t seconds = read32(p + 40);
    // Unfold NTP era 1 after the February 2036 rollover.
    if (seconds < NTP_UNIX_OFFSET) seconds += 1ULL << 32;
    seconds -= NTP_UNIX_OFFSET;
    if (seconds < MIN_UNIX_SECONDS || seconds >= MAX_UNIX_SECONDS) return false;
    unixUs = seconds * 1000000ULL +
             ((uint64_t(read32(p + 44)) * 1000000ULL) >> 32);
    // LAN/internet SNTP approximation; refuse slow replies rather than set a
    // clock more than the spec's two-second tolerance behind the server.
    unixUs += roundtripUs / 2;
    return true;
}
} // namespace logger_sntp
