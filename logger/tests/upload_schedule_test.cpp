#include "../firmware/accord-logger/upload_protocol.h"
#include "../firmware/accord-logger/wifi_schedule.h"
#include <cassert>
#include <string>
#include <iostream>
using namespace logger_upload;
struct IO {
    bool up = true, ready = true, validFile = true, pending = false, failReply = false;
    bool closed = true, sealed = false, empty = false;
    uint32_t bytes = VISIT_BYTES + 512, remote = 0;
    unsigned index = 0, sweeps = 0, starts = 0, stops = 0;
    Reply reply;
    bool networkUp() { return up; }
    bool storageReady() { return ready; }
    bool valid(const File &) { return validFile; }
    int next(File &f) {
        if (empty || index++) { ++sweeps; return 2; }
        f = File(); strcpy(f.name, "U_test.CSV"); f.bytes = bytes; f.closed = closed;
        return 1;
    }
    void rewind() { index = 0; }
    int read(const File &, uint32_t, char *p, size_t n) { memset(p, 'a', n); return n; }
    const char *unit() { return "test"; }
    const char *host() { return "127.0.0.1"; }
    unsigned port() { return 1; }
    const char *token() { return "dummy"; }
    bool start(const char *p, size_t n) {
        ++starts; pending = true;
        std::string request(p, n);
        if (request.find("/append?") != std::string::npos) {
            remote += n - request.find("\r\n\r\n") - 4;
        } else if (request.find("/complete?") != std::string::npos) sealed = true;
        reply = Reply{200, remote, sealed};
        return true;
    }
    void stop() { ++stops; pending = false; }
    int poll(const char *, Reply &r) { r = reply; return failReply ? -1 : 1; }
};
int main() {
    IO io; Client<IO> c(io); uint64_t t = 0;
    while (!io.sweeps) c.step(t++);
    assert(io.remote == VISIT_BYTES && !c.caughtUp() && !io.sealed);
    while (io.sweeps < 2) c.step(t++);
    assert(io.remote == io.bytes && io.sealed && c.caughtUp());
    auto progress = c.progress();
    while (io.sweeps < 3) c.step(t++);
    assert(c.caughtUp() && c.progress() == progress); // offset/old seal isn't progress

    // Restart interrupts an acknowledged-but-unconsumed append response.
    IO cut; cut.bytes = 2048; cut.closed = false; Client<IO> interrupted(cut);
    interrupted.step(0); interrupted.step(1); interrupted.step(2);
    assert(cut.remote == 512 && cut.pending);
    interrupted.restart(); assert(!cut.pending && !interrupted.caughtUp());
    cut.ready = false; auto starts = cut.starts;
    interrupted.step(3); assert(cut.starts == starts); // no rewind/scan during SD pressure
    cut.ready = true;
    for (uint64_t n = 4; !interrupted.caughtUp() && n < 1000; ++n) interrupted.step(n);
    assert(interrupted.caughtUp() && cut.remote == cut.bytes && !cut.sealed);

    // Failed sweep must not report caught up, including when error skips a file.
    IO bad; Client<IO> failed(bad); bad.failReply = true;
    for (uint64_t n = 0; n < 40000; ++n) failed.step(n);
    assert(!failed.caughtUp());
    bad.failReply = false; bad.remote = 0; failed.restart();
    for (uint64_t n = 40000; !failed.caughtUp() && n < 150000; ++n) failed.step(n);
    assert(failed.caughtUp());
    IO none; none.empty = true; Client<IO> empty(none);
    empty.step(0); assert(!empty.caughtUp() && empty.progress() == 0);

    // Shared policy + client: old backlog exceeds a visit; only complete sweep
    // may end the window. IGN immediately cancels and the next window resumes.
    IO car; car.bytes = 180000; Client<IO> upload(car);
    logger_wifi::Schedule schedule;
    bool wasEnabled = false;
    unsigned windows = 0;
    uint32_t sync = 0;
    for (uint64_t n = 0; n < 300000; n += 10) {
        const bool ign = n < 1000 || (n >= 7000 && n < 10000);
        schedule.step(n, {true, ign, upload.progress(), upload.caughtUp(), sync});
        if (schedule.enabled() && !wasEnabled) { upload.restart(); ++windows; }
        if (!schedule.enabled() && wasEnabled) upload.restart();
        car.up = schedule.enabled();
        wasEnabled = schedule.enabled();
        if (schedule.enabled()) { sync = windows; upload.step(n); }
        if (schedule.reason() == logger_wifi::Reason::CaughtUp) break;
    }
    assert(windows == 2 && car.remote == car.bytes && car.sealed);
    assert(schedule.reason() == logger_wifi::Reason::CaughtUp);
    std::cout << "PASS: partial sweep, progress/old seals, cancellation/resume, storage priority, failed/empty sweeps, policy+client\n";
}
