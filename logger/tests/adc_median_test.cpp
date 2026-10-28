#include "../firmware/accord-logger/adc_median.h"
#include <assert.h>
#include <algorithm>
#include <stdio.h>
#include <stdlib.h>
#include <vector>

/* The median convention and the properties the fuel thread depends on.
 *
 * Every case checks the histogram median against a straight sort of the same
 * samples, so the oracle is the definition rather than another copy of the
 * implementation. The impulse cases are the point of the whole change: they
 * are what a mean gets wrong.
 */
using logger_adc::Burst;
using logger_adc::BINS;

static Burst burst;      // 8 KiB; static rather than on the stack

static uint16_t lower_median_by_sort(std::vector<uint16_t> v) {
    std::sort(v.begin(), v.end());
    return v[(v.size() + 1) / 2 - 1];        // the (n+1)/2-th smallest
}

static double averaged_median_by_sort(std::vector<uint16_t> v) {
    std::sort(v.begin(), v.end());
    const size_t n = v.size();
    return n % 2 ? double(v[n / 2])
                 : (double(v[n / 2 - 1]) + double(v[n / 2])) / 2.0;
}

static double mean_of(const std::vector<uint16_t> &v) {
    double s = 0;
    for (uint16_t x : v) s += x;
    return s / double(v.size());
}

static void feed(const std::vector<uint16_t> &v) {
    burst.reset();
    for (uint16_t x : v) burst.add(x);
}

static int failures = 0;

static void expect(const char *label, bool ok, const char *detail = "") {
    if (ok) {
        printf("  ok  %s\n", label);
    } else {
        printf("FAIL  %s  %s\n", label, detail);
        ++failures;
    }
}

/* Agreement with the sorted oracle, plus the invariants that must hold for
 * every input: the extremes are the real extremes and the count is exact. */
static void check(const char *label, const std::vector<uint16_t> &v) {
    feed(v);
    const uint16_t want = lower_median_by_sort(v);
    const uint16_t got = burst.median();
    char detail[160];
    snprintf(detail, sizeof(detail), "median %u, want %u", got, want);
    expect(label, got == want, detail);
    expect("    extremes preserved",
           burst.lo == *std::min_element(v.begin(), v.end())
               && burst.hi == *std::max_element(v.begin(), v.end()));
    expect("    sample count exact", burst.n == v.size());
    expect("    no overflow", burst.overflow == 0);
}

int main(void) {
    // ---- the convention, on inputs small enough to check by eye ----------
    check("even count takes the LOWER median (1,2,3,4 -> 2)", {1, 2, 3, 4});
    check("odd count takes the middle (1,2,3 -> 2)", {1, 2, 3});
    check("two samples take the lower (7,9 -> 7)", {7, 9});
    check("one sample is itself", {1234});
    check("all values equal", std::vector<uint16_t>(2000, 2048));

    // ---- boundaries of the ADC range -------------------------------------
    check("the whole burst at 0", std::vector<uint16_t>(2000, 0));
    check("the whole burst at full scale", std::vector<uint16_t>(2000, 4095));
    check("both rails, even split", []{
        std::vector<uint16_t> v(1000, 0);
        v.insert(v.end(), 1000, 4095);
        return v;
    }());
    check("both rails, odd split", []{
        std::vector<uint16_t> v(1000, 0);
        v.insert(v.end(), 1001, 4095);
        return v;
    }());

    // ---- the reason this change exists: impulsive noise -------------------
    // 2000 samples at 1850 counts, plus a handful of 20-50x spikes. A mean is
    // dragged off; a median is not.
    {
        std::vector<uint16_t> v(1980, 1850);
        v.insert(v.end(), 20, 4095);            // 1 % of samples, at the rail
        feed(v);
        const double mean = mean_of(v);
        char detail[200];
        snprintf(detail, sizeof(detail),
                 "median %u, mean %.1f (%.1f counts of bias rejected)",
                 burst.median(), mean, mean - 1850.0);
        expect("20 rail-high impulses do not move the median", burst.median() == 1850, detail);
        printf("      %s\n", detail);
        expect("    and the impulses are still visible in hi", burst.hi == 4095);
    }
    {
        std::vector<uint16_t> v(1980, 1850);
        v.insert(v.end(), 20, 0);               // impulses on the LOW side
        feed(v);
        expect("20 rail-low impulses do not move the median", burst.median() == 1850);
        expect("    and are still visible in lo", burst.lo == 0);
    }
    {
        // Sparse impulses on BOTH sides, which a one-sided guard would miss.
        std::vector<uint16_t> v(1900, 1850);
        v.insert(v.end(), 50, 0);
        v.insert(v.end(), 50, 4095);
        check("impulses on both sides at once", v);
        feed(v);
        expect("    median still the quiet level", burst.median() == 1850);
    }
    {
        // A single outlier at each extreme, the sparsest case that exists.
        std::vector<uint16_t> v(1998, 2000);
        v.push_back(0);
        v.push_back(4095);
        check("one outlier at each rail", v);
    }

    // ---- an off-centre median, so an implicit "middle bin" bug shows ------
    {
        std::vector<uint16_t> v(1500, 300);     // 75 % low
        v.insert(v.end(), 500, 3800);
        check("median far from mid-scale (low)", v);
        feed(v);
        expect("    median is the dense low level", burst.median() == 300);
    }
    {
        std::vector<uint16_t> v(1500, 3800);
        v.insert(v.end(), 500, 300);
        check("median far from mid-scale (high)", v);
    }

    // ---- realistic noise, against a sort, many times ----------------------
    // Also measures how far the lower median sits from the textbook averaged
    // median on this signal, rather than asserting a number for it.
    {
        srand(20261024);
        double worst = 0, total = 0;
        int rounds = 0, mismatches = 0;
        for (int round = 0; round < 200; ++round) {
            std::vector<uint16_t> v;
            v.reserve(2000);
            for (int i = 0; i < 2000; ++i) {
                // ~Gaussian by summing uniforms; sigma ~5.3 counts as measured.
                double g = 0;
                for (int k = 0; k < 12; ++k) g += double(rand()) / RAND_MAX;
                v.push_back(uint16_t(1850 + (g - 6.0) * 5.3));
            }
            if (round % 3 == 0) {               // a spiky third of the bursts
                for (int i = 0; i < 15; ++i) v[i * 101] = 4000 + (i % 90);
            }
            feed(v);
            if (burst.median() != lower_median_by_sort(v)) ++mismatches;
            const double gap = averaged_median_by_sort(v) - double(burst.median());
            total += gap;
            if (gap > worst) worst = gap;
            ++rounds;
        }
        expect("200 realistic bursts match a sort exactly", mismatches == 0);
        printf("      lower vs averaged median over %d bursts:"
               " mean %+.4f counts, worst %+.4f\n", rounds, total / rounds, worst);
        expect("    and the convention costs well under one count",
               total / rounds < 0.5);
    }

    // ---- the channels are independent ------------------------------------
    {
        static Burst a, b;
        a.reset();
        b.reset();
        for (int i = 0; i < 2000; ++i) {
            a.add(1000);
            b.add(3000);
        }
        expect("two bursts do not share state",
               a.median() == 1000 && b.median() == 3000 && a.hi == 1000
                   && b.lo == 3000);
    }

    // ---- reset really clears ---------------------------------------------
    {
        feed(std::vector<uint16_t>(2000, 4095));
        burst.reset();
        expect("reset clears the histogram, count and extremes",
               burst.median() == 0 && burst.n == 0 && burst.lo == 0xFFFF
                   && burst.hi == 0);
        feed(std::vector<uint16_t>(2000, 100));
        expect("    and a reused burst reads only the new samples",
               burst.median() == 100 && burst.hi == 100);
    }

    // ---- an out-of-range sample is counted, not silently clipped ----------
    {
        burst.reset();
        for (int i = 0; i < 100; ++i) burst.add(500);
        burst.add(9999);                        // impossible from a 12-bit read
        expect("an out-of-range sample is counted in overflow",
               burst.overflow == 1);
        expect("    and is still visible in hi", burst.hi == 9999);
        expect("    and still counts toward n", burst.n == 101);
    }

    if (failures) {
        printf("\n%d failure(s)\n", failures);
        return 1;
    }
    printf("\nPASS: lower median matches a sort on every case, rejects impulses"
           " on both rails, preserves extrema, channels independent\n");
    printf("      %zu bytes of histogram per channel\n", sizeof(burst.bins));
    return 0;
}
