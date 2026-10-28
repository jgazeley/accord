#include "../firmware/accord-logger/host_time_frame.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

/* Rule 4.10. The interesting half of this test is the NEGATIVE half, and the
 * negatives are not invented: they are real lines this firmware printed onto
 * the card on 2026-10-19, plus every split of them that begins at a '@'-less
 * byte. The whole point of the frame is that the board cannot talk itself into
 * setting its own clock, and the only honest way to check that is to feed it
 * its own output.
 */

static bool accepted(const char *s) {
    uint64_t ms = 0;
    const size_t n = strlen(s);
    return n <= 255 && logger_host_time::decode(s, (uint8_t)n, ms);
}

// Real output, copied from evidence/card_drive_20261019_150841.csv.
static const char *const REAL_OUTPUT[] = {
    "# picow-logger stages=1,2,3 version=0.3.0",
    "# w=wifi status  t=UTC clock  d=sd status (also every 60s)",
    "# vsslog -- r=reset totals  m=mark  l=levels  ?=help",
    "# columns: ms,vss_total,vss_hz,tach_total,tach_hz,rpm,brake",
    "# brake: 1 = parking brake ENGAGED (pin pulled low)",
    "# WIFI state=down ssid=MG_Wifi reason=starting retry_in=0s",
    "# WIFI state=up ssid=MG_Wifi ip=192.168.60.90 rssi=-60 since=0s",
    "# TIME unset src=none synced=0",
    "# TIME 2026-10-19T17:01:40Z src=sntp synced=1 age=91s",
    "# TIME 2026-10-19T17:01:40Z src=host synced=1 age=0s",
    "# SD state=ok file=/BOOT_564.CSV bytes=0 wmax_ms=32 drop=0",
    "# SD state=ok file=/20261019_150841.CSV bytes=276415 wmax_ms=32 drop=0",
    "# SD state=fail err=sync code=0x00 data=0x00 drop=0",
    "# LEVELS vss=LOW (0% high)  tach=HIGH (100% high)",
    "# MARK 1 at ms=6922003 vss=85893 tach=131976",
    "# RESET",
    "6919003,85893,0.00,131976,0.00,0,1",
    "47003,0,0.00,0,0.00,0,1",
    "24519752,0,0.00,0,0.00,0,1",
};

int main() {
    uint64_t ms = 0;

    // A well-formed frame, and the value arrives intact.
    assert(logger_host_time::decode("@1792345678901", 14, ms));
    assert(ms == 1792345678901ULL);
    assert(accepted("@1767225600000"));                 // exactly the floor
    assert(accepted("@2208988800000"));                 // exactly the ceiling

    // Range. One millisecond outside either end is not a clock.
    assert(!accepted("@1767225599999"));
    assert(!accepted("@2208988800001"));
    assert(!accepted("@0000000000000"));

    // Length. 13 digits, no more and no fewer.
    assert(!accepted("@179234567890"));                 // 12
    assert(!accepted("@17923456789012"));               // 14
    assert(!accepted("@"));
    assert(!accepted(""));

    // Shape. The lead byte and the payload are both mandatory.
    assert(!accepted("1792345678901"));                 // no '@'
    assert(!accepted(" @1792345678901"));               // '@' not first
    assert(!accepted("@179234567890a"));
    assert(!accepted("@17923456789 1"));
    assert(!accepted("@1792345,78901"));                // a split report row
    assert(!accepted("@@792345678901"));
    assert(!accepted("@-792345678901"));
    assert(!accepted("@+792345678901"));

    // THE REAL TEST: no line this firmware prints, and no tail of one, may be
    // accepted. Every suffix is checked, because a 256-byte read can split an
    // echoed line anywhere and leave the remainder looking like a burst.
    int suffixes = 0;
    for (const char *line : REAL_OUTPUT) {
        const size_t n = strlen(line);
        for (size_t at = 0; at <= n; ++at) {
            ++suffixes;
            if (accepted(line + at)) {
                printf("FAIL accepted a suffix of real output: %s\n", line + at);
                return 1;
            }
        }
        // And the standing invariant that makes the above hold at all.
        if (strchr(line, logger_host_time::FRAME)) {
            printf("FAIL firmware output contains '%c': %s\n",
                   logger_host_time::FRAME, line);
            return 1;
        }
    }

    printf("PASS: frame decodes, bounds enforced, and %d suffixes of real "
           "firmware output rejected with no '@' among them\n", suffixes);
    return 0;
}
