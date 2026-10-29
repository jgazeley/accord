#pragma once
#include <stdint.h>
#include <stdio.h>

/* The self-describing card header of CARD_FORMAT.md, as pure text formatting
 * so the exact bytes can be tested off the board.
 *
 * WHY THIS IS A HEADER AND NOT F() STRINGS IN THE SKETCH. The format is frozen
 * the moment a card exists that is not the owner's, and the board that writes
 * it is in the car -- so it cannot be flashed and read back cheaply, and
 * BOOTSEL cycles are cumulative on the car Pi's root port. A format that
 * expensive to correct has to be verifiable without hardware, which means
 * rendering into a buffer that a native test can compare byte for byte. The
 * cost is one ~1 KB transient stack buffer against 179 KB free; the gain is
 * that tests/card_header_test.cpp checks the real emitted bytes rather than a
 * model of them. Same reasoning, and same shape, as host_time_frame.h.
 *
 * The side effects live elsewhere: the sketch fills in the hardware facts and
 * logger_sd.cpp writes the result as the first bytes of every file it opens.
 *
 * ratio and full_scale_v are COMPUTED from the two divider resistors, never
 * stated, so the published calibration cannot drift from the hardware.
 */
namespace logger_card_header {

// The magic first line. Deliberately outside the `log.` namespace: it is meant
// to be recognisable by eye and by file(1)-style sniffing. Bump ONLY if an
// existing key changes meaning -- never for a new key, never for a new column.
constexpr char MAGIC[] = "# accord-log/1";

struct Facts {
    bool power_qualified = false;
    // identity
    const char *chip = "";          // RP2040 unique board id (= the USB serial)
    const char *vehicle = "";       // opaque local label, never a VIN
    const char *fw = "";
    // the row shape
    const char *columns = "";
    uint8_t stable = 0;             // leading columns that never move
    // the pin map, as GP numbers
    uint8_t pin_vss = 0, pin_tach = 0, pin_brake = 0;
    uint8_t pin_ign = 0, pin_fuel = 0, pin_supply = 0;
    uint32_t glitch_us = 0;
    // the pulse constant: provenance for a card-only reader, NOT authority
    const char *ppm_value = "", *ppm_band = "", *ppm_asof = "";
    // the analog chain
    uint16_t adc_bits = 0;
    float adc_vref_v = 0.0f;
    uint16_t adc_burst = 0;
    uint16_t supply_dark = 0;
    /* Which statistic `fuel_counts` / `supply_counts` carry: "median" from
     * v0.7.0, "mean" through v0.6.0. ADDITIVE: a reader that does not know the
     * key, or a v0.6.0 file that does not carry it, must assume "mean" --
     * CARD_FORMAT.md §8. The column NAMES never change, so this line is the
     * only place a file says what its numbers are. */
    const char *adc_stat = "";
    uint32_t fuel_r_top = 0, fuel_r_bot = 0;
    uint32_t supply_r_top = 0, supply_r_bot = 0;
    /* Per-FILE facts. Null file_name omits the `log.file` line, which is what
     * the boot-time copy over USB does: that line describes one card file, and
     * a reader tolerates a tag it does not get (CARD_FORMAT.md rule 4). */
    const char *file_name = nullptr;
    const char *upload_id = nullptr; // immutable random 128-bit lowercase hex
    uint32_t opened_ms = 0;
    bool clock_trusted = false;
};

inline float divider_ratio(uint32_t top, uint32_t bot) {
    return (float)bot / (float)(top + bot);
}

/* Render the whole block, magic line through `# log.end`, LF-terminated lines.
 * Returns the length written, or 0 if it would not fit -- a truncated header is
 * never emitted, because a half-written description is worse than none and
 * `log.end` is what makes truncation detectable. */
inline size_t render(char *out, size_t n, const Facts &f) {
    const float fuel_ratio = divider_ratio(f.fuel_r_top, f.fuel_r_bot);
    const float supply_ratio = divider_ratio(f.supply_r_top, f.supply_r_bot);
    int w = snprintf(
        out, n,
        "%s\n"
        "# log.unit chip=%s vehicle=%s fw=%s\n"
        "# log.columns %s\n"
        "# log.stable %u\n"
        "# log.power interface=%s ign_source=%s hold=%s\n"
        "# log.pins vss=GP%u tach=GP%u brake=GP%u ign=GP%u fuel=GP%u supply=GP%u\n"
        "# log.pulses vss_per_mile=%s band=%s asof=%s source=tripd-refit"
        " authority=downstream\n"
        "# log.adc bits=%u vref_v=%.1f burst=%u stat=%s die=rp2040-internal\n"
        "# log.adc.fuel div=%lu/%lu ratio=%.4f full_scale_v=%.2f\n"
        "# log.adc.supply div=%lu/%lu ratio=%.4f full_scale_v=%.2f dark_counts=%u\n"
        "# log.means brake=1:line-grounded ign=1:on ms_since_ign=0:key-out"
        " glitch_us=%lu\n",
        MAGIC,
        f.chip, f.vehicle, f.fw,
        f.columns,
        (unsigned)f.stable,
        f.power_qualified ? "lra01-v1" : "manual",
        f.power_qualified ? "hardware-qualified" : "legacy-gp5",
        f.power_qualified ? "GP6" : "none",
        (unsigned)f.pin_vss, (unsigned)f.pin_tach, (unsigned)f.pin_brake,
        (unsigned)f.pin_ign, (unsigned)f.pin_fuel, (unsigned)f.pin_supply,
        f.ppm_value, f.ppm_band, f.ppm_asof,
        (unsigned)f.adc_bits, (double)f.adc_vref_v, (unsigned)f.adc_burst,
        f.adc_stat,
        (unsigned long)f.fuel_r_top, (unsigned long)f.fuel_r_bot,
        (double)fuel_ratio, (double)(f.adc_vref_v / fuel_ratio),
        (unsigned long)f.supply_r_top, (unsigned long)f.supply_r_bot,
        (double)supply_ratio, (double)(f.adc_vref_v / supply_ratio),
        (unsigned)f.supply_dark,
        (unsigned long)f.glitch_us);
    if (w < 0 || (size_t)w >= n) return 0;
    size_t len = (size_t)w;

    if (f.file_name) {
        w = snprintf(out + len, n - len,
                     "# log.file name=%s opened_ms=%lu clock=%s\n",
                     f.file_name, (unsigned long)f.opened_ms,
                     f.clock_trusted ? "sntp" : "none");
        if (w < 0 || (size_t)w >= n - len) return 0;
        len += (size_t)w;
    }

    if (f.upload_id) {
        w = snprintf(out + len, n - len,
                     "# log.upload id=%s policy=create-only\n", f.upload_id);
        if (w < 0 || (size_t)w >= n - len) return 0;
        len += (size_t)w;
    }
    w = snprintf(out + len, n - len, "# log.end\n");
    if (w < 0 || (size_t)w >= n - len) return 0;
    return len + (size_t)w;
}

/* The rename record, CARD_FORMAT.md §9. Written to a file that was created
 * before the clock was trusted and has since been renamed, so a card-only
 * reader can tie the header's creation-time name to the name on disk.
 *
 * NOT part of the header block: it necessarily happens after rows have already
 * been written, so it is an ordinary note in the body and `# log.end` has long
 * since gone by. It is in the `log.` namespace because it is machine-readable
 * format metadata, which is what that namespace is for.
 *
 * Returns the length written, or 0 if it would not fit -- in which case the
 * caller writes nothing rather than a truncated line.
 */
inline size_t render_rename(char *out, size_t n, const char *from,
                            const char *to, uint32_t at_ms) {
    const int w = snprintf(out, n, "# log.rename from=%s to=%s at_ms=%lu\n",
                           from, to, (unsigned long)at_ms);
    if (w < 0 || (size_t)w >= n) return 0;
    return (size_t)w;
}

// Comfortably larger than the longest block this can produce. The test asserts
// the real one fits and that a buffer one byte short renders nothing.
constexpr size_t BUFFER = 1152;
// The rename note is one short line; 96 holds two 31-char names and the ms.
constexpr size_t RENAME_BUFFER = 96;

} // namespace logger_card_header
