#include "../firmware/accord-logger/sntp_packet.h"
#include <assert.h>
#include <initializer_list>
#include <stdio.h>

static void write32(uint8_t *p, uint32_t value) {
    for (int i = 3; i >= 0; --i) { p[i] = value; value >>= 8; }
}

int main() {
    uint8_t packet[48] = {};
    const uint8_t nonce[8] = {1, 3, 5, 7, 9, 11, 13, 15};
    packet[0] = 0x24;
    packet[1] = 2;
    memcpy(packet + 24, nonce, 8);
    const uint64_t epoch = 1792346400ULL;
    write32(packet + 40, epoch + logger_sntp::NTP_UNIX_OFFSET);
    write32(packet + 44, 0x80000000);
    uint64_t result = 0;
    assert(logger_sntp::decode(packet, 48, nonce, 100000, result));
    assert(result == epoch * 1000000ULL + 550000);
    assert(!logger_sntp::decode(packet, 47, nonce, 0, result));
    assert(!logger_sntp::decode(packet, 49, nonce, 0, result));
    assert(!logger_sntp::decode(packet, 48, nonce, 1500001, result));
    packet[24] ^= 1;
    assert(!logger_sntp::decode(packet, 48, nonce, 0, result));
    packet[24] ^= 1;
    for (uint8_t bad : {uint8_t(0), uint8_t(16), uint8_t(255)}) {
        packet[1] = bad;
        assert(!logger_sntp::decode(packet, 48, nonce, 0, result));
    }
    packet[1] = 2;
    for (uint8_t bad : {uint8_t(0xe4), uint8_t(0x23), uint8_t(0x25),
                        uint8_t(0x14), uint8_t(0x2c)}) {
        packet[0] = bad;
        assert(!logger_sntp::decode(packet, 48, nonce, 0, result));
    }
    packet[0] = 0x1c; // NTPv3 server is valid too.
    assert(logger_sntp::decode(packet, 48, nonce, 0, result));
    packet[0] = 0x24;
    for (uint64_t seconds : {2085978495ULL, 2085978496ULL, 2208988800ULL}) {
        write32(packet + 40, uint32_t(seconds + logger_sntp::NTP_UNIX_OFFSET));
        write32(packet + 44, 0x80000000);
        assert(logger_sntp::decode(packet, 48, nonce, 0, result));
        assert(result == seconds * 1000000ULL + 500000);
    }
    write32(packet + 40, logger_sntp::MIN_UNIX_SECONDS - 1 + logger_sntp::NTP_UNIX_OFFSET);
    assert(!logger_sntp::decode(packet, 48, nonce, 0, result));
    write32(packet + 40, uint32_t(logger_sntp::MAX_UNIX_SECONDS + logger_sntp::NTP_UNIX_OFFSET));
    assert(!logger_sntp::decode(packet, 48, nonce, 0, result));
    write32(packet + 40, 0);
    write32(packet + 44, 0);
    assert(!logger_sntp::decode(packet, 48, nonce, 0, result));
    puts("PASS: SNTP timestamps, fractions, era rollover, malformed/untrusted/replayed/slow replies");
}
