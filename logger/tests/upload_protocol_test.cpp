#include "../firmware/accord-logger/upload_protocol.h"
#include "../firmware/accord-logger/upload_identity.h"
#include <cassert>
#include <string>
#include <vector>
#include <iostream>
using namespace logger_upload;
static int parse(const std::string &wire, Reply &r) {
    char buffer[RESPONSE];
    assert(wire.size() < sizeof(buffer));
    strcpy(buffer, wire.c_str());
    return response(buffer, wire.size(), "U_test.CSV", r);
}
static std::string http(const std::string &body, const std::string &extra = "") {
    return "HTTP/1.1 200 OK\r\nContent-Length: " + std::to_string(body.size()) + "\r\n" + extra + "\r\n" + body;
}
struct IO {
    bool up = true, ready = true, validFile = true, waiting = false;
    unsigned starts = 0, stops = 0, reads = 0, scans = 0;
    std::vector<uint64_t> requestTimes;
    uint64_t now = 0;
    int pollResult = 0;
    Reply reply;
    File current;
    IO() { strcpy(current.name, "U_test.CSV"); current.bytes = 1024; current.closed = true; }
    bool networkUp() { return up; }
    bool storageReady() { return ready; }
    bool valid(const File &) { return validFile; }
    int next(File &f) { ++scans; f = current; return 1; }
    void rewind() {}
    int read(const File &, uint32_t, char *out, size_t n) { ++reads; memset(out, 'x', n); return n; }
    const char *unit() { return "E6614C311B3A3231"; }
    const char *host() { return "127.0.0.1"; }
    unsigned port() { return 8086; }
    const char *token() { return "dummy"; }
    bool start(const char *, size_t) { ++starts; requestTimes.push_back(now); waiting = true; return true; }
    void stop() { ++stops; waiting = false; }
    int poll(const char *, Reply &r) { r = reply; return pollResult; }
};
int main() {
    const std::string body = "{\"file\":\"U_test.CSV\",\"bytes\":4294967295,\"complete\":true}";
    const auto good = http(body);
    for (size_t i = 0; i < good.size(); ++i) { Reply r; assert(parse(good.substr(0, i), r) == 0); }
    Reply r;
    assert(parse(good, r) == 1 && r.bytes == UINT32_MAX && r.complete);
    for (const auto &bad : {
        "{\"file\":\"other.CSV\",\"bytes\":0}",
        "{\"file\":\"U_test.CSV\",\"bytes\":4294967296}",
        "{\"file\":\"U_test.CSV\",\"bytes\":-1}",
        "{\"file\":\"U_test.CSV\",\"bytes\":1.5}",
        "{\"file\":\"U_test.CSV\",\"bytes\":0,\"bytes\":0}",
        "{\"file\":\"U_test.CSV\",\"bytes\":0}garbage",
        "{\"file\":\"U_test.CSV\",\"bytes\":0,\"complete\":tru}",
        "{\"file\":\"U_test.CSV\",\"bytes\":0,}",
        "{\"file\":\"U_test.CSV\",\"bytes\":0"}) {
        Reply badReply; assert(parse(http(bad), badReply) == -1);
    }
    for (const auto &extra : {"Transfer-Encoding: chunked\r\n", "Content-Length: 0\r\n"}) {
        Reply badReply; assert(parse(http(body, extra), badReply) == -1);
    }
    assert(parse("HTTP/1.0 401 No\r\nContent-Length: 0\r\n\r\n", r) == -1);
    assert(parse(good + "x", r) == -1);
    const std::string header = "# accord-log/1\n# log.unit chip=E6614C311B3A3231 vehicle=trial\n"
        "# log.upload id=0123456789abcdef0123456789abcdef policy=create-only\n# log.end\n";
    char name[65]; bool seal;
    assert(identity(header.c_str(), "BOOT_540.CSV", "E6614C311B3A3231", name, seal) && seal);
    assert(std::string(name) == "U_0123456789abcdef0123456789abcdef.CSV");
    char renamed[65];
    assert(identity(header.c_str(), "20261025_000000.CSV", "E6614C311B3A3231", renamed, seal));
    assert(!strcmp(name, renamed));
    assert(!identity(header.c_str(), "BOOT_540.CSV", "0000000000000000", name, seal));
    for (size_t i = 0; i < header.size(); ++i)
        assert(!identity(header.substr(0, i).c_str(), "BOOT_540.CSV", "E6614C311B3A3231", name, seal));
    const char *legacy = "# accord-log/1\n# log.unit chip=E6614C311B3A3231 vehicle=trial\n# log.end\n";
    assert(!identity(legacy, "BOOT_540.CSV", "E6614C311B3A3231", name, seal));
    assert(identity(legacy, "20261025_000000.CSV", "E6614C311B3A3231", name, seal) && !seal);

    IO io; Client<IO> c(io);
    // No Wi-Fi: no socket or SD read. Busy card: no scan/read/request.
    io.up = false;
    for (unsigned i = 0; i < 1000; ++i) c.step(i);
    io.up = true; io.ready = false;
    for (unsigned i = 1000; i < 2000; ++i) c.step(i);
    assert(!io.starts && !io.reads && !io.scans);
    io.ready = true; io.now = 2000; c.step(io.now);
    assert(io.starts == 1);
    // A stalled peer is cancelled even while SD is busy; backoff prevents storms.
    io.ready = false; c.step(2000 + DEADLINE_MS);
    assert(!io.waiting && io.stops == 1);
    io.ready = true;
    for (io.now = 10001; io.now < 40000; ++io.now) c.step(io.now);
    assert(io.starts == 1);
    c.step(40000); assert(io.starts == 2);
    io.pollResult = 1; io.reply = Reply{200, 2048, false}; // server beyond local file
    c.step(40001); assert(io.reads == 0);
    c.step(40002); assert(io.starts == 2);
    // Offset accepted; storage pressure prevents the next payload read.
    IO io2; Client<IO> c2(io2); c2.step(0);
    io2.pollResult = 1; io2.reply = Reply{200, 0, false}; c2.step(1);
    io2.ready = false; c2.step(2); assert(io2.reads == 0);
    io2.ready = true; c2.step(3); assert(io2.reads == 1);
    io2.validFile = false; c2.step(4); assert(!io2.waiting);
    IO io3; Client<IO> c3(io3); c3.step(0);
    io3.pollResult = 1; io3.reply = Reply{200, 512, true}; c3.step(1);
    c3.step(2); assert(io3.starts == 1 && io3.reads == 0); // sealed prefix conflict
    IO io4; Client<IO> c4(io4); c4.step(0);
    io4.pollResult = 1; io4.reply = Reply{200, 0, false}; c4.step(1); c4.step(2);
    io4.reply = Reply{409, 0, false}; c4.step(3); c4.step(4);
    assert(io4.starts == 2 && io4.reads == 1); // nonadvancing 409 backs off
    std::cout << "PASS: fragmented/malformed HTTP, immutable identity, unknown legacy boot, scheduling, deadlines/backoff, invalidation\n";
}
