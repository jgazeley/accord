#pragma once
#include <stdint.h>

// Pure policy: no GPIO, radio, SD, wall clock or sleeping. All times are
// monotonic 64-bit milliseconds. The adapter owns each window's upload reset.
namespace logger_wifi {
constexpr uint64_t SETTLE_MS = 5000;
constexpr uint64_t CONNECT_MS = 60000;
constexpr uint64_t STALL_MS = 120000;
constexpr uint64_t MAX_WINDOW_MS = 900000;
enum class Phase { Unknown, Driving, Settling, Window, Parked };
enum class Reason { UnknownIgn, IgnOn, Settling, Attempt, CaughtUp, NoProgress, Limit };
inline const char *name(Phase p) {
    switch (p) {
    case Phase::Unknown: return "unknown-ign";
    case Phase::Driving: return "driving";
    case Phase::Settling: return "settling";
    case Phase::Window: return "window";
    case Phase::Parked: return "parked";
    }
    return "unknown";
}
inline const char *name(Reason r) {
    switch (r) {
    case Reason::UnknownIgn: return "unknown-ign";
    case Reason::IgnOn: return "ign-on";
    case Reason::Settling: return "ign-off-settle";
    case Reason::Attempt: return "attempt";
    case Reason::CaughtUp: return "caught-up";
    case Reason::NoProgress: return "no-progress";
    case Reason::Limit: return "window-limit";
    }
    return "unknown";
}
struct Input {
    bool known = false, ignOn = false;
    uint64_t progress = 0; // monotonic count of validated append/completion progress
    bool caughtUp = false; // complete successful sweep, never a sealed-file claim
    uint32_t syncRevision = 0; // changes only on adopting a fresh trusted time
};
class Schedule {
public:
    Phase phase() const { return phase_; }
    Reason reason() const { return reason_; }
    bool enabled() const { return phase_ == Phase::Window; }
    uint64_t deadline() const {
        const uint64_t idle = progressed_ ? progressAt_ + STALL_MS : opened_ + CONNECT_MS;
        const uint64_t limit = opened_ + MAX_WINDOW_MS;
        return idle < limit ? idle : limit;
    }
    void step(uint64_t now, const Input &in) {
        if (!in.known) { set(Phase::Unknown, Reason::UnknownIgn); return; }
        // On wins immediately over completion, deadlines and settling.
        if (in.ignOn) { set(Phase::Driving, Reason::IgnOn); return; }
        if (phase_ == Phase::Unknown || phase_ == Phase::Driving) {
            offAt_ = now;
            set(Phase::Settling, Reason::Settling);
        }
        if (phase_ == Phase::Settling && now - offAt_ >= SETTLE_MS) {
            opened_ = now;
            progress_ = in.progress;
            sync_ = in.syncRevision;
            progressed_ = false;
            set(Phase::Window, Reason::Attempt);
            return; // feedback here belongs to the previous upload window
        }
        if (!enabled()) return;
        if (now - opened_ >= MAX_WINDOW_MS) { stop(Reason::Limit); return; }
        // A late observation cannot revive an already expired window.
        if (now >= deadline()) {
            if (in.caughtUp && now - opened_ >= CONNECT_MS) stop(Reason::CaughtUp);
            else stop(Reason::NoProgress);
            return;
        }
        if (in.progress != progress_) {
            progress_ = in.progress;
            progressAt_ = now;
            progressed_ = true;
        }
        if (in.caughtUp && (in.syncRevision != sync_ || now - opened_ >= CONNECT_MS))
            stop(Reason::CaughtUp);
    }
private:
    Phase phase_ = Phase::Unknown;
    Reason reason_ = Reason::UnknownIgn;
    uint64_t offAt_ = 0, opened_ = 0, progressAt_ = 0, progress_ = 0;
    uint32_t sync_ = 0;
    bool progressed_ = false;
    void set(Phase p, Reason r) { phase_ = p; reason_ = r; }
    void stop(Reason r) { set(Phase::Parked, r); }
};
} // namespace logger_wifi
