#pragma once
#include <stdint.h>
#include <stddef.h>
#include <string.h>
namespace logger_power {
// SPSC queue: core 1 publishes complete records, core 0 consumes chunks.
// 32-bit unsigned differences intentionally tolerate index rollover; capacity
// remains below 2^31. No compare/exchange or SDK lock is needed.
template<size_t N> class Queue {
    static_assert(N > 1 && (N & (N - 1)) == 0 && N < (1u << 31), "power-of-two queue");
    char bytes_[N] = {};
    uint32_t head_ = 0, tail_ = 0;
public:
    explicit Queue(uint32_t initialIndex = 0) : head_(initialIndex), tail_(initialIndex) {}
    uint32_t head() const { return __atomic_load_n(&head_, __ATOMIC_ACQUIRE); }
    uint32_t tail() const { return __atomic_load_n(&tail_, __ATOMIC_ACQUIRE); }
    bool push(const char *p, size_t n) {
        const uint32_t h = head();
        if (n > N - 1 - (h - tail())) return false;
        for (size_t i = 0; i < n; ++i) bytes_[(h + i) & (N - 1)] = p[i];
        __atomic_store_n(&head_, h + uint32_t(n), __ATOMIC_RELEASE);
        return true;
    }
    const char *peek(size_t &n, uint32_t limit) const {
        const uint32_t t = tail();
        size_t available = limit - t;
        if (available > N - 1) { n = 0; return nullptr; }
        if (n > available) n = available;
        const size_t contiguous = N - (t & (N - 1));
        if (n > contiguous) n = contiguous;
        return bytes_ + (t & (N - 1));
    }
    void consume(size_t n) { __atomic_store_n(&tail_, tail() + uint32_t(n), __ATOMIC_RELEASE); }
    // Only after the producer has acknowledged a stop and its stable watermark.
    void discard(uint32_t watermark) { __atomic_store_n(&tail_, watermark, __ATOMIC_RELEASE); }
};
}
