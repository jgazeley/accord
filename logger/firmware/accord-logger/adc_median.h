#pragma once
#include <stdint.h>
#include <string.h>

/* Per-burst MEDIAN for the analog channels, as pure arithmetic so it can be
 * tested off the board. `fuel/ADC_INTERFACE_SPEC.md` §7.
 *
 * WHY MEDIAN AND NOT MEAN. Decided 2026-10-23 on measurement, not preference:
 * the noise on this node is *impulsive*, crest factor 20-50x, and that is the
 * one distribution where the choice matters. A mean dilutes one spike across
 * the whole burst and biases the logged value; a median of 2000 samples
 * rejects it outright. v0.5.0/v0.6.0 shipped the mean because §6 said
 * "averaged" when the sampler was written and the median decision came after.
 *
 * ---- the algorithm, and what it costs -------------------------------------
 *
 * A 4096-bin histogram over the FULL 12-bit range, accumulated during
 * acquisition, then one prefix scan for the median.
 *
 *   RAM    4096 bins x uint16 = 8 KiB per channel, 16 KiB for both. Static,
 *          never heap; nothing here allocates.
 *   time   one array increment per sample, inside the sampling loop that
 *          already exists; then a memset of 8 KiB and a scan of at most 4096
 *          bins per channel per report. Tens of microseconds against a burst
 *          that already takes ~0.2 s, so it does not move the report budget.
 *   bounds every step has a fixed upper bound (the prefix scan touches at
 *          most 4096 bins, returning early at the median bin). No recursion,
 *          no pivot, no sort-order pathology.
 *
 * The alternative was keeping the 2000 samples (4 KiB per channel, half the
 * RAM) and running nth_element. Rejected: it needs a second pass over the
 * samples and drags in <algorithm> template code. 8 KiB more RAM, out of
 * 179 KiB free, buys a tighter, easily audited bound of at most 4096 bin
 * checks on the 1 Hz report path.
 *
 * BINS COVERS THE WHOLE RANGE ON PURPOSE. A narrower histogram centred on
 * where the signal is expected to sit would be smaller and would silently
 * discard exactly the impulsive outliers the median exists to reject -- and
 * would also quietly corrupt `lo`/`hi`, which are the noise estimate. There is
 * no clipping here: every value a 12-bit read can return has its own bin.
 *
 * ---- the even-sized median convention -------------------------------------
 *
 * N = 2000 is even, so "the median" needs defining. This takes the LOWER
 * median: the smallest value v for which at least N/2 samples are <= v, i.e.
 * the 1000th smallest of 2000.
 *
 * Chosen over averaging the two central order statistics because it involves
 * **no division and therefore no rounding rule at all**, and because the
 * logged number is always a value the ADC actually returned rather than a
 * synthetic half-count.
 *
 * What that costs, MEASURED rather than argued: over 200 simulated bursts at
 * the observed sigma of ~5.3 counts, a third of them carrying impulses, the
 * lower median sat below the averaged median by a mean of **0.0175 counts**,
 * worst case 0.5. The two are the same integer in most bursts, because 2000
 * quantised samples pile up on a handful of adjacent integers.
 * tests/adc_median_test.cpp reports those numbers on every run.
 *
 * As a synthetic illustration of why the statistic matters: 20 deliberately
 * rail-high samples (4095) among 2000 samples at 1850 pull the MEAN up by
 * **+22.5 counts** (~18 mV at the ADC pin, ~47 mV at the sender through the
 * 0.3852 divider), while the median stays at 1850. That 1 % rail-impulse
 * fixture is an illustrative test case, not a measurement of vehicle bias:
 * crest factor alone does not establish impulse duty cycle or amplitude in the
 * archived driving logs.
 */
namespace logger_adc {

// The full 12-bit range. Changing this changes what cannot be clipped, so it
// is not a tuning knob.
constexpr uint16_t BINS = 4096;

struct Burst {
    uint16_t bins[BINS];
    uint32_t n;          // samples accepted into the histogram
    uint32_t overflow;   // samples outside 0..BINS-1; see add()
    uint16_t lo, hi;     // TRUE burst extremes, the float-noise estimate

    void reset() {
        memset(bins, 0, sizeof(bins));
        n = 0;
        overflow = 0;
        lo = 0xFFFF;
        hi = 0;
    }

    /* One sample. `lo`/`hi` take the RAW value so they keep meaning the real
     * extremes of what was measured.
     *
     * A value at or above BINS cannot come from a 12-bit read and would mean
     * analogReadResolution() is not what this code assumes. It is counted in
     * `overflow` and binned at the top rather than dropped, so it still
     * participates in the median and the anomaly is visible instead of silent.
     * `overflow` is expected to be 0 forever; if it is not, `lo`/`hi` and the
     * histogram disagree and the histogram is the one that is wrong. */
    void add(uint16_t sample) {
        if (sample < lo) lo = sample;
        if (sample > hi) hi = sample;
        uint16_t bin = sample;
        if (bin >= BINS) {
            ++overflow;
            bin = BINS - 1;
        }
        ++bins[bin];
        ++n;
    }

    /* The lower median, as defined above. Returns 0 for an empty burst, which
     * is not a measurement and cannot occur with a fixed sample count -- the
     * caller logs `n` alongside, so an empty burst is distinguishable from a
     * real reading of zero. */
    uint16_t median() const {
        if (!n) return 0;
        const uint32_t need = (n + 1) / 2;   // ceil(n/2): n/2 for even n... see below
        uint32_t seen = 0;
        for (uint16_t bin = 0; bin < BINS; ++bin) {
            seen += bins[bin];
            if (seen >= need) return bin;
        }
        return BINS - 1;                     // unreachable while n > 0
    }
};

/* NOTE ON `need`. For even n, (n+1)/2 in integer arithmetic is n/2 -- 2001/2
 * is 1000 for n=2000 -- so this is the 1000th smallest, the lower median, as
 * documented. For odd n it is the true middle element, (n+1)/2. One expression
 * is correct for both, which is why there is no branch here.
 */

} // namespace logger_adc
