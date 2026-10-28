#include "../firmware/accord-logger/wifi_schedule.h"
#include <cassert>
#include <iostream>
using namespace logger_wifi;
int main() {
    Schedule s; Input in;
    s.step(0, in); s.step(1000000, in); assert(!s.enabled());
    in.known = true; in.ignOn = true; s.step(1000001, in);
    assert(s.phase() == Phase::Driving);
    in.ignOn = false; s.step(1000002, in); s.step(1005001, in);
    assert(s.phase() == Phase::Settling);
    in.ignOn = true; s.step(1005002, in); // off bounce cancels settling
    in.ignOn = false; s.step(1005003, in); s.step(1010003, in);
    assert(s.enabled());
    in.ignOn = true; s.step(1010004, in); assert(!s.enabled());

    Schedule away; in = Input{true, false, 0, false, 0};
    away.step(0, in); away.step(SETTLE_MS, in); assert(away.enabled());
    away.step(SETTLE_MS + CONNECT_MS - 1, in); assert(away.enabled());
    away.step(SETTLE_MS + CONNECT_MS, in);
    assert(!away.enabled() && away.reason() == Reason::NoProgress);
    away.step(7ULL * 86400000, in); assert(!away.enabled()); // days parked: no retries
    in.ignOn = true; away.step(7ULL * 86400000 + 1, in);
    in.ignOn = false; away.step(7ULL * 86400000 + 2, in);
    away.step(7ULL * 86400000 + 2 + SETTLE_MS, in); assert(away.enabled());

    Schedule home; in = Input{true, false, 8, true, 4};
    home.step(0, in); home.step(SETTLE_MS, in); assert(home.enabled());
    home.step(SETTLE_MS + 1, in); assert(home.enabled()); // old clock not fresh
    in.syncRevision++; home.step(SETTLE_MS + 2, in);
    assert(home.reason() == Reason::CaughtUp && !home.enabled());
    Schedule noNtp; in.syncRevision = 0;
    noNtp.step(0, in); noNtp.step(SETTLE_MS, in);
    noNtp.step(SETTLE_MS + CONNECT_MS, in);
    assert(noNtp.reason() == Reason::CaughtUp && !noNtp.enabled());

    Schedule backlog; in = Input{true, false, 0, false, 0};
    backlog.step(0, in); backlog.step(SETTLE_MS, in);
    ++in.progress; backlog.step(SETTLE_MS + 50000, in);
    backlog.step(SETTLE_MS + CONNECT_MS, in); assert(backlog.enabled());
    backlog.step(SETTLE_MS + 50000 + STALL_MS - 1, in); assert(backlog.enabled());
    backlog.step(SETTLE_MS + 50000 + STALL_MS, in);
    assert(backlog.reason() == Reason::NoProgress);

    Schedule growing; in = Input{true, false, 0, false, 0};
    const uint64_t base = (1ULL << 32) - 2000; // beyond millis() rollover
    growing.step(base, in); growing.step(base + SETTLE_MS, in);
    for (uint64_t t = 1000; t < MAX_WINDOW_MS; t += 1000) {
        ++in.progress; growing.step(base + SETTLE_MS + t, in); assert(growing.enabled());
    }
    growing.step(base + SETTLE_MS + MAX_WINDOW_MS, in);
    assert(growing.reason() == Reason::Limit);
    in.ignOn = true; growing.step(base + SETTLE_MS + MAX_WINDOW_MS + 1, in);
    assert(growing.reason() == Reason::IgnOn);
    in.known = false; growing.step(base + SETTLE_MS + MAX_WINDOW_MS + 2, in);
    assert(growing.reason() == Reason::UnknownIgn);
    std::cout << "PASS: IGN gating/bounce, boot states, deadlines, progress, fresh sync, days parked, rollover\n";
}
