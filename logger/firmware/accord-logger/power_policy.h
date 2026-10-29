#pragma once
#include <stdint.h>
#include <stddef.h>

// Production policy, also compiled by the deterministic native tests. Time is
// elapsed monotonic milliseconds, never epoch time or Arduino millis().
namespace logger_power {
constexpr uint64_t FINALIZE_MS = 1770000, RELEASE_MS = 1800000;
constexpr uint32_t FRESH_MS = 2000, STARTUP_MS = 8000;
enum class Input : uint8_t { Unknown, Off, On };
enum class Phase : uint8_t { Released, Run, Hold, Finalize };
struct Snapshot {
    uint32_t generation = 0;
    Phase phase = Phase::Released;
    bool recording() const { return phase == Phase::Run || phase == Phase::Hold; }
    bool hold() const { return phase != Phase::Released; }
};
class Policy {
    Snapshot state_;
    uint64_t off_ = 0, lastAt_ = 0;
    Input previous_ = Input::Unknown;
public:
    Snapshot step(uint64_t now, Input input) {
        if (now < lastAt_) { // outside the monotonic contract: fail closed
            state_.phase = Phase::Released;
            previous_ = input;
            lastAt_ = now;
            return state_;
        }
        if (input == Input::On) {
            if (previous_ != Input::On) {
                // Fail closed on generation exhaustion, rather than accepting
                // a stale token after wrap (over 4 billion ON transitions).
                if (state_.generation != UINT32_MAX) {
                    ++state_.generation;
                    state_.phase = Phase::Run;
                } else state_.phase = Phase::Released;
            }
        } else {
            if (state_.phase == Phase::Run) {
                // A missed supervision interval leaves uncertain edge history.
                // Charge the gap to OFF, never grant a later deadline on recovery.
                off_ = now - lastAt_ > 10 ? lastAt_ : now;
                state_.phase = Phase::Hold;
            }
            if (state_.phase == Phase::Hold || state_.phase == Phase::Finalize) {
                if (now - off_ >= RELEASE_MS) state_.phase = Phase::Released;
                else if (now - off_ >= FINALIZE_MS) state_.phase = Phase::Finalize;
            }
        }
        previous_ = input;
        lastAt_ = now;
        return state_;
    }
};

// Startup has a fixed deadline. Each core must explicitly finish setup and
// then report foreground progress; timer callbacks cannot refresh these stamps.
class Health {
    uint64_t start_;
    bool failed_ = false;
public:
    explicit Health(uint64_t now = 0) : start_(now) {}
    bool feed(uint64_t now, uint32_t ready, uint32_t beat0, uint32_t beat1) {
        if (failed_) return false;
        const uint32_t low = uint32_t(now);
        for (unsigned core = 0; core < 2; ++core) {
            if (ready & (1u << core)) {
                // Core 0 can publish just AFTER this ISR captured now. A
                // slightly future stamp is fresh, not unsigned age ~2^32.
                // Signed modular age is valid within half-wrap; the hardware
                // watchdog resets long before a missed 2^31 ms interval.
                if (int32_t(low - (core ? beat1 : beat0)) > int32_t(FRESH_MS)) failed_ = true;
            } else if (now - start_ >= STARTUP_MS) failed_ = true;
        }
        return !failed_; // Once unhealthy, reset is required; no late recovery feed.
    }
};

// All Out producers pass through this assembler. Stop commands are even, run
// commands odd; only core 0 issues commands. ACK is published only at an empty
// line buffer. Overlong/full-queue records are dropped WHOLE, never fragmented.
// The caller publishes ack with release ordering and reads it with acquire.
template<size_t N> class Producer {
    char line_[N];
    size_t length_ = 0;
    bool overflow_ = false, skipping_ = false;
    uint32_t ack_ = 0;
public:
    uint32_t poll(uint32_t command) {
        if (!length_ && !overflow_ && !(command & 1)) ack_ = command;
        return ack_;
    }
    template<class Emit> bool put(char c, uint32_t command, bool allowed, Emit emit) {
        if (c == '\r') return false;
        poll(command);
        // A denied prefix stays denied until LF, even if a new file becomes
        // ready halfway through a report or USB help line.
        if (skipping_) { if (c == '\n') skipping_ = false; return false; }
        if (!length_ && !overflow_ && (!(command & 1) || !allowed)) {
            skipping_ = c != '\n';
            return false;
        }
        if (length_ < N) line_[length_++] = c;
        else overflow_ = true;
        bool dropped = false;
        if (c == '\n') {
            dropped = overflow_ || !emit(line_, length_);
            length_ = 0; overflow_ = false;
            poll(command);
        }
        return dropped;
    }
};

// Single core-0 owner serializes all storage effects. A new ON never jumps over
// an old close. Each step does at most one potentially blocking stage. The next
// step gets a fresh snapshot, including after a slow open or close. IO is the
// real SdFat adapter in production and deterministic fault-injection in tests.
enum class Stage : uint8_t { Idle, Open, CheckOpen, Active, Wait, Drain, Settle, Sync, Close };
template<class IO> class Session {
    Stage stage_ = Stage::Idle;
    uint32_t epoch_ = 0, command_ = 0, watermark_ = 0;
    bool clean_ = true;
    bool exhausted_ = false;
    void stop(IO &io) {
        if (command_ == UINT32_MAX) { exhausted_ = true; command_ = 0; }
        else ++command_; // odd -> even
        io.command(command_);
        io.invalidate();
        stage_ = Stage::Wait;
    }
public:
    Stage stage() const { return stage_; }
    uint32_t generation() const { return epoch_; }
    bool active(Snapshot s) const {
        return stage_ == Stage::Active && s.recording() && s.generation == epoch_;
    }
    void step(Snapshot s, IO &io) {
        switch (stage_) {
        case Stage::Idle:
            if (!exhausted_ && s.recording() && io.retryReady()) {
                epoch_ = s.generation; clean_ = true; stage_ = Stage::Open;
            }
            break;
        case Stage::Open:
            if (!s.recording() || s.generation != epoch_) { stage_ = Stage::Idle; break; }
            clean_ = io.open(); stage_ = Stage::CheckOpen; break;
        case Stage::CheckOpen:
            if (!clean_ || !s.recording() || s.generation != epoch_) {
                stage_ = Stage::Close; break;
            }
            if (command_ >= UINT32_MAX - 1) { exhausted_ = true; stage_ = Stage::Close; break; }
            io.generation(epoch_);
            io.command(++command_); // even -> odd, only after file header persisted
            stage_ = Stage::Active;
            break;
        case Stage::Active:
            if (!s.recording() || s.generation != epoch_ || !io.good()) stop(io);
            break;
        case Stage::Wait:
            if (io.ack() == command_) { watermark_ = io.head(); stage_ = Stage::Drain; }
            break;
        case Stage::Drain: {
            const int result = io.drain(watermark_); // 0 pending, 1 done, -1 lost
            if (result) { clean_ = clean_ && result > 0; stage_ = Stage::Settle; }
            break;
        }
        case Stage::Settle: clean_ = io.settle() && clean_; stage_ = Stage::Sync; break;
        case Stage::Sync: clean_ = io.sync() && clean_; stage_ = Stage::Close; break;
        case Stage::Close:
            clean_ = io.close() && clean_;
            io.result(epoch_, clean_); // diagnostic only; cannot grant HOLD or reopen
            stage_ = Stage::Idle;
            break;
        }
    }
};
} // namespace logger_power
