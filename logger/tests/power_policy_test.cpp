#include "../firmware/accord-logger/power_policy.h"
#include "../firmware/accord-logger/power_queue.h"
#include <cassert>
#include <cstdio>
#include <string>
#include <vector>
#include <cstring>
#include "../firmware/accord-logger/card_tail.h"
using namespace logger_power;

static void deadlines() {
    Policy p;
    assert(!p.step(0, Input::Unknown).hold());
    assert(!p.step(5000000, Input::Off).hold()); // USB alone never grants
    auto s = p.step(5000001, Input::On);
    assert(s.phase == Phase::Run && s.generation == 1);
    assert(p.step(5000002, Input::On).generation == 1);
    const uint64_t off = 0xffffffffULL - 1000; // crosses Arduino millis wrap
    p.step(off - 1, Input::On);
    assert(p.step(off, Input::Unknown).phase == Phase::Hold);
    assert(p.step(off + 1, Input::Off).phase == Phase::Hold); // no renewal
    assert(p.step(off + FINALIZE_MS - 1, Input::Off).recording());
    assert(p.step(off + FINALIZE_MS, Input::Off).phase == Phase::Finalize);
    assert(p.step(off + RELEASE_MS - 1, Input::Off).hold());
    assert(!p.step(off + RELEASE_MS, Input::Off).hold());
    assert(!p.step(off + RELEASE_MS + 99999999, Input::Off).recording());
    s = p.step(off + RELEASE_MS + 100000000, Input::On);
    assert(s.generation == 2 && s.phase == Phase::Run);
    // Each genuine return supersedes old deadlines, including at finalization.
    for (uint64_t at : {FINALIZE_MS - 1, FINALIZE_MS, RELEASE_MS - 1, RELEASE_MS}) {
        Policy q;
        q.step(0, Input::On); q.step(1, Input::Off);
        s = q.step(at + 1, Input::On);
        assert(s.generation == 2 && s.phase == Phase::Run);
        assert(q.step(at + 2, Input::Off).phase == Phase::Hold);
    }
    Policy late;
    late.step(10, Input::On);
    assert(!late.step(10 + RELEASE_MS, Input::Off).hold());
    Policy backwards;
    backwards.step(10, Input::On);
    assert(!backwards.step(9, Input::On).hold());
    Policy reset;
    assert(!reset.step(1, Input::Off).hold()); // no surviving grant across reset
    // Epoch is intentionally not an input to Policy; forward/backward SNTP
    // corrections cannot affect this monotonic sequence or renew an OFF.
    Policy wallIndependent;
    wallIndependent.step(0, Input::On); wallIndependent.step(1, Input::Off);
    assert(!wallIndependent.step(RELEASE_MS + 1, Input::Off).hold());
}

static void health() {
    Health startup(100);
    assert(startup.feed(8099, 0, 0, 0));
    assert(!startup.feed(8100, 0, 0, 0));
    assert(!startup.feed(8101, 3, 8101, 8101)); // failure latches
    Health partial(0);
    assert(partial.feed(1000, 1, 1000, 0));
    assert(!partial.feed(3001, 1, 1000, 0)); // ready core loses startup exemption
    Health concurrent(0);
    assert(concurrent.feed(1000, 3, 1001, 1000)); // core 0 publishes during ISR
    assert(concurrent.feed(1001, 3, 1001, 1000));
    Health live(0);
    assert(live.feed(2000, 3, 0, 0));
    assert(!live.feed(2001, 3, 2001, 0)); // IRQ activity/core 0 alone is insufficient
    Health other(0);
    assert(!other.feed(2001, 3, 0, 2001));
    Health wrap(0xfffffff0ULL);
    assert(wrap.feed(0x100000010ULL, 3, 0xfffffff0u, 0xfffffff0u));
    assert(!wrap.feed(0x1000007c1ULL, 3, 0xfffffff0u, 0x7c1));
}

static void producer() {
    Producer<8> p;
    Queue<16> q;
    auto emit = [&](const char *s, size_t n) { return q.push(s, n); };
    // Enabling midway through a suppressed report must not create a suffix row.
    p.put('x', 0, false, emit); p.put('y', 1, true, emit);
    p.put('\n', 1, true, emit); assert(q.head() == 0);
    p.put('a', 1, true, emit);
    assert(p.poll(2) == 0); // unfinished ADC/report: no early stable watermark
    p.put('b', 2, false, emit); p.put('\n', 2, false, emit);
    assert(p.poll(2) == 2 && q.head() == 3);
    p.put('c', 2, true, emit); p.put('\n', 2, true, emit);
    assert(q.head() == 3); // commands/help/status cannot bypass stopped producer
    for (char c : std::string("123456789\n")) p.put(c, 3, true, emit);
    assert(q.head() == 3); // entire overlong record dropped
    for (char c : std::string("1234567\n")) p.put(c, 3, true, emit);
    assert(q.head() == 11);
    bool dropped = false;
    for (char c : std::string("abcd\n")) dropped |= p.put(c, 3, true, emit);
    assert(dropped && q.head() == 11); // full ring retains previous complete rows
    assert(p.poll(4) == 4);
    const uint32_t watermark = q.head();
    size_t n = 16; const char *bytes = q.peek(n, watermark);
    assert(n == 11 && std::string(bytes, n) == "ab\n1234567\n");
    q.consume(n); assert(q.tail() == watermark);
    Queue<16> rollover(0xfffffffcu);
    assert(rollover.push("1234567\n", 8));
    assert(rollover.head() == 4 && rollover.tail() == 0xfffffffcu);
    size_t rn = 16;
    assert(std::string(rollover.peek(rn, rollover.head()), 4) == "1234" && rn == 4);
    rollover.consume(4); rn = 16;
    assert(std::string(rollover.peek(rn, rollover.head()), 4) == "567\n" && rn == 4);
    rollover.consume(4); assert(rollover.tail() == rollover.head());
    // Ring wrap and chunks never change byte ordering.
    assert(q.push("ABCDEFG\n", 8));
    n = 16; bytes = q.peek(n, q.head()); assert(n == 5 && std::string(bytes,n) == "ABCDE");
    q.consume(n); n = 16; bytes = q.peek(n, q.head());
    assert(n == 3 && std::string(bytes,n) == "FG\n");
    q.consume(n);
}

// This IO mock injects completion/failure at the actual Session call boundary,
// including IGN changes while a blocking operation is in flight. Production
// instantiates precisely this same Session with PowerStorage (SdFat adapter).
struct IO {
    uint32_t cmd = 0, acknowledged = 0, epoch = 0, watermark = 0;
    uint32_t completed = 0;
    unsigned opens = 0, closes = 0, invalidations = 0;
    bool healthy = true, opening = true, settled = true, synced = true, closed = true;
    bool clean = false, retry = true;
    int drainResult = 1;
    std::vector<std::string> events;
    bool retryReady() { return retry; }
    bool good() { return healthy; }
    bool open() { ++opens; events.push_back("open"); return opening; }
    void command(uint32_t c) { cmd = c; }
    void generation(uint32_t g) { epoch = g; }
    uint32_t ack() { return acknowledged; }
    uint32_t head() { return watermark; }
    void invalidate() { ++invalidations; events.push_back("invalidate"); }
    int drain(uint32_t mark) { assert(mark == watermark); events.push_back("drain"); return drainResult; }
    bool settle() { events.push_back("settle"); return settled; }
    bool sync() { events.push_back("sync"); return synced; }
    bool close() { ++closes; events.push_back("close"); return closed; }
    void result(uint32_t g, bool ok) { completed = g; clean = ok; }
};
static constexpr Snapshot RUN{1, Phase::Run}, FINAL{1, Phase::Finalize}, NEW{2, Phase::Run};
static void activate(Session<IO> &s, IO &io, Snapshot snap = RUN) {
    for (unsigned i = 0; i < 3; ++i) s.step(snap, io);
    assert(s.active(snap) && (io.cmd & 1));
}
static void sessions() {
    // OFF/unknown boot: no retry, open or producer grant, indefinitely on USB.
    Session<IO> off; IO offIO;
    for (unsigned i=0; i<20; ++i) off.step({}, offIO);
    assert(!offIO.opens && !offIO.cmd);
    // Return ON in every finalization stage. Old close always precedes reopen;
    // stale ACK cannot authorize drain or affect a fresh file.
    for (Stage target : {Stage::Wait, Stage::Drain, Stage::Settle, Stage::Sync, Stage::Close, Stage::Idle}) {
        Session<IO> s; IO io; activate(s, io);
        s.step(FINAL, io); assert(s.stage() == Stage::Wait && io.cmd == 2);
        io.acknowledged = 0;
        s.step(NEW, io); assert(s.stage() == Stage::Wait && io.opens == 1);
        io.acknowledged = 2; io.watermark = 1700;
        while (s.stage() != target) s.step(FINAL, io);
        for (unsigned i=0; i<15 && !s.active(NEW); ++i) s.step(NEW, io);
        assert(s.active(NEW) && io.opens == 2 && io.closes == 1);
        assert(io.completed == 1 && io.clean && io.epoch == 2);
        assert(io.events.back() == "open");
        s.step(NEW, io); assert(io.closes == 1); // no stale second close
        s.step({2, Phase::Finalize}, io);
        assert(io.cmd == 4);
        s.step({2, Phase::Finalize}, io); assert(s.stage() == Stage::Wait); // old ACK=2 refused
    }
    // An open that was allowed when called can finish after OFF/return. It is
    // closed without publishing a producer grant; a fresh open gets fresh facts.
    for (Snapshot changed : {FINAL, NEW, Snapshot{}}) {
        Session<IO> s; IO io;
        s.step(RUN, io); s.step(RUN, io); // call finished, not yet granted
        s.step(changed, io); assert(s.stage() == Stage::Close && io.cmd == 0);
        s.step(changed, io); assert(io.closes == 1 && io.opens == 1);
    }
    // Every IO failure is observable and cannot turn into a clean ACK.
    for (unsigned fault=0; fault<5; ++fault) {
        Session<IO> s; IO io; activate(s, io);
        if (fault == 0) io.healthy = false;
        if (fault == 1) io.drainResult = -1;
        if (fault == 2) io.settled = false;
        if (fault == 3) io.synced = false;
        if (fault == 4) io.closed = false;
        if (fault == 0) io.drainResult = -1;
        s.step(FINAL, io); io.acknowledged = io.cmd;
        for (unsigned i=0; i<8; ++i) s.step(FINAL, io);
        assert(io.completed == 1 && !io.clean && io.closes == 1 && io.opens == 1);
    }
    Session<IO> failed; IO missing; missing.opening = false;
    for (unsigned i=0; i<4; ++i) failed.step(RUN, missing);
    assert(!missing.cmd && missing.closes == 1 && !missing.clean);
    missing.retry = false;
    for (unsigned i=0; i<20; ++i) failed.step(RUN, missing);
    assert(missing.opens == 1);
    // Policy release does not require any Session call, producer ACK, drain,
    // sync or close completion. Simulate core 0 stopped outright.
    for (Stage target : {Stage::Active, Stage::Wait, Stage::Drain, Stage::Sync, Stage::Close}) {
        Policy p; p.step(0, Input::On); p.step(1, Input::Off);
        Session<IO> s; IO io; activate(s, io);
        if (target != Stage::Active) {
            s.step(FINAL, io); io.acknowledged = io.cmd;
            while (s.stage() != target) s.step(FINAL, io);
        }
        auto released = p.step(RELEASE_MS+1, Input::Off);
        assert(!released.hold() && !released.recording());
        assert(!p.step(RELEASE_MS*2, Input::Off).hold());
    }
    Session<IO> stuck; IO io; activate(stuck, io);
    stuck.step(FINAL,io); io.acknowledged=io.cmd; stuck.step(FINAL,io);
    io.drainResult=0;
    for(unsigned i=0;i<20;++i) stuck.step(NEW,io);
    assert(stuck.stage()==Stage::Drain && io.opens==1); // no reopen past stalled drain
}
// End-to-end normal finalization uses the real Producer, Queue, Session and
// Tail together. The file mock exercises chunk splits and complete boundaries.
struct MemoryFile {
    std::string bytes;
    size_t position = 0;
    size_t write(const char *p, size_t n) { bytes.append(p,n); return n; }
    bool sync() { return true; }
    size_t size() { return bytes.size(); }
    bool seekSet(size_t p) { position=p; return p <= bytes.size(); }
    int read() { return position < bytes.size() ? static_cast<unsigned char>(bytes[position++]) : -1; }
};
struct FlowIO : IO {
    Producer<64> producer;
    Queue<128> queue;
    MemoryFile file;
    logger_card_tail::Tail<MemoryFile> tail;
    bool open() {
        IO::open(); file.bytes.clear(); tail.created();
        return tail.appendMetadata(file,"# header\n",9) == logger_card_tail::Note::Written;
    }
    uint32_t ack() { return producer.poll(cmd); }
    uint32_t head() { return queue.head(); }
    int drain(uint32_t mark) {
        size_t n=3; // force a report across multiple writes
        const char *p=queue.peek(n,mark);
        if(n) { assert(tail.appendChunk(file,p,n)); queue.consume(n); }
        return queue.tail()==mark ? 1 : 0;
    }
    bool settle() { return tail.noteAllowed() && tail.settle(file); }
    void put(const std::string &text, bool allowed) {
        for(char c:text) producer.put(c,cmd,allowed,
            [&](const char *p,size_t n){return queue.push(p,n);});
    }
};
static void flow() {
    Session<FlowIO> session; FlowIO io;
    for(unsigned i=0;i<3;++i) session.step(RUN,io);
    io.put("1000,0,",true); // report paused during ADC
    session.step(FINAL,io);
    for(unsigned i=0;i<3;++i) session.step(FINAL,io);
    assert(session.stage()==Stage::Wait && io.closes==0);
    io.put("1\n# ignored status\n",false); // finish old report, suppress new note
    for(unsigned i=0;i<30 && session.stage()!=Stage::Idle;++i) session.step(FINAL,io);
    assert(io.file.bytes=="# header\n1000,0,1\n" && io.clean && io.closes==1);
    for(unsigned i=0;i<3;++i) session.step(NEW,io);
    assert(session.active(NEW) && io.opens==2);
    io.put("2000,1,1\n",true);
    session.step({2,Phase::Finalize},io);
    for(unsigned i=0;i<30 && session.stage()!=Stage::Idle;++i) session.step({2,Phase::Finalize},io);
    assert(io.file.bytes=="# header\n2000,1,1\n" && io.completed==2 && io.clean);
}
int main() {
    deadlines(); health(); producer(); sessions(); flow();
    puts("PASS power: monotonic policy, both-core health, complete records, storage generations/faults");
}
