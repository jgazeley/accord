#include "../firmware/accord-logger/card_header.h"
#include "../firmware/accord-logger/upload_identity.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

/* CARD_FORMAT.md, checked byte for byte off the board.
 *
 * WHY A GOLDEN STRING. This format is frozen the moment a card exists that is
 * not the owner's, and the board that writes it lives in the car -- flashing to
 * read it back costs a BOOTSEL cycle on a root port that has been disabled by
 * cumulative cycles before. So the expected bytes are written out in full here
 * rather than being derived, and any change to the format has to be made
 * deliberately in two places. That friction is the feature.
 *
 * The values below are the sketch's constants. If they change, this test fails
 * and should be updated with the reason recorded.
 */

static logger_card_header::Facts sketch_facts() {
    logger_card_header::Facts f;
    f.chip = "E6614C311B3A3231";       // the in-car board
    f.vehicle = "accord-1";
    f.fw = "0.7.1";
    f.columns = "ms,vss_total,vss_hz,tach_total,tach_hz,rpm,brake,"
                "fuel_counts,fuel_lo,fuel_hi,supply_counts,die_counts,"
                "ms_since_ign,ign";
    f.stable = 7;
    f.pin_vss = 2; f.pin_tach = 3; f.pin_brake = 4;
    f.pin_ign = 5; f.pin_fuel = 26; f.pin_supply = 27;
    f.glitch_us = 100;
    f.ppm_value = "4104.3";
    f.ppm_band = "4103.19..4105.42";
    f.ppm_asof = "2026-10-18";
    f.adc_bits = 12;
    f.adc_vref_v = 3.3f;
    f.adc_burst = 2000;
    f.supply_dark = 155;
    f.adc_stat = "median";
    f.fuel_r_top = 7500;    f.fuel_r_bot = 4700;
    f.supply_r_top = 22000; f.supply_r_bot = 4700;
    return f;
}

static const char EXPECTED_CARD[] =
    "# accord-log/1\n"
    "# log.unit chip=E6614C311B3A3231 vehicle=accord-1 fw=0.7.1\n"
    "# log.columns ms,vss_total,vss_hz,tach_total,tach_hz,rpm,brake,fuel_counts,"
    "fuel_lo,fuel_hi,supply_counts,die_counts,ms_since_ign,ign\n"
    "# log.stable 7\n"
    "# log.power interface=manual ign_source=legacy-gp5 hold=none\n"
    "# log.pins vss=GP2 tach=GP3 brake=GP4 ign=GP5 fuel=GP26 supply=GP27\n"
    "# log.pulses vss_per_mile=4104.3 band=4103.19..4105.42 asof=2026-10-18"
    " source=tripd-refit authority=downstream\n"
    "# log.adc bits=12 vref_v=3.3 burst=2000 stat=median die=rp2040-internal\n"
    "# log.adc.fuel div=7500/4700 ratio=0.3852 full_scale_v=8.57\n"
    "# log.adc.supply div=22000/4700 ratio=0.1760 full_scale_v=18.75"
    " dark_counts=155\n"
    "# log.means brake=1:line-grounded ign=1:on ms_since_ign=0:key-out"
    " glitch_us=100\n"
    "# log.file name=/20261024_101530.CSV opened_ms=540 clock=sntp\n"
    "# log.end\n";

static void for_each_line(const char *block, void (*fn)(const char *, size_t)) {
    const char *p = block;
    while (*p) {
        const char *nl = strchr(p, '\n');
        assert(nl && "every header line is LF-terminated");
        fn(p, (size_t)(nl - p));
        p = nl + 1;
    }
}

static void line_starts_with_hash(const char *line, size_t n) {
    // The load-bearing invariant: vssrec classifies a line as a note purely on
    // this first byte, and a bare continuation line once became a phantom
    // sample gap. The header gets no exception.
    assert(n > 0 && line[0] == '#');
}

static void line_is_namespaced_or_magic(const char *line, size_t n) {
    if (strncmp(line, logger_card_header::MAGIC, n) == 0) return;
    assert(n > 7 && strncmp(line, "# log.", 6) == 0);
}

static void line_cannot_be_read_as_an_ign_note(const char *line, size_t n) {
    /* tripd dispatches notes with `note.lstrip("# ").startswith("IGN")`, so a
     * header line that survived that strip as "IGN..." would be counted as a
     * malformed ignition note. Nothing in the block may. */
    size_t i = 0;
    while (i < n && (line[i] == '#' || line[i] == ' ')) ++i;
    assert(strncmp(line + i, "IGN", 3) != 0);
    assert(strncmp(line + i, "RESET", 5) != 0);
}

/* `--emit [file-name]` prints the block instead of testing it, so the Python
 * side (tests/check_card_v060.py) builds its fixtures from the REAL renderer
 * rather than from a hand-copied transcription that could drift from it. */
int main(int argc, char **argv) {
    if (argc > 1 && strcmp(argv[1], "--emit") == 0) {
        char out[logger_card_header::BUFFER];
        logger_card_header::Facts e = sketch_facts();
        e.file_name = argc > 2 ? argv[2] : "/20261024_101530.CSV";
        e.opened_ms = 540;
        e.clock_trusted = strncmp(e.file_name, "/BOOT_", 6) != 0;
        e.power_qualified = argc > 3 && strcmp(argv[3], "qualified") == 0;
        e.fw = "0.8.1-lra05-dev";
        e.upload_id = "0123456789abcdef0123456789abcdef";
        if (!logger_card_header::render(out, sizeof(out), e)) return 1;
        fputs(out, stdout);
        return 0;
    }

    char block[logger_card_header::BUFFER];
    logger_card_header::Facts f = sketch_facts();
    f.file_name = "/20261024_101530.CSV";
    f.opened_ms = 540;
    f.clock_trusted = true;

    size_t len = logger_card_header::render(block, sizeof(block), f);
    assert(len > 0);
    if (strcmp(block, EXPECTED_CARD) != 0) {
        printf("FAIL: rendered block differs from the golden text\n"
               "--- got ---\n%s--- want ---\n%s", block, EXPECTED_CARD);
        return 1;
    }
    assert(len == strlen(EXPECTED_CARD));

    // The derived calibration must come out as the documented numbers. These
    // are the two values ARCHITECTURE.md names as missing from the card.
    assert(strstr(block, "ratio=0.3852 full_scale_v=8.57"));
    assert(strstr(block, "ratio=0.1760 full_scale_v=18.75"));

    for_each_line(block, line_starts_with_hash);
    for_each_line(block, line_is_namespaced_or_magic);
    for_each_line(block, line_cannot_be_read_as_an_ign_note);

    // Magic first, terminator last, exactly one of each.
    assert(strncmp(block, logger_card_header::MAGIC,
                   strlen(logger_card_header::MAGIC)) == 0);
    assert(strcmp(block + len - strlen("# log.end\n"), "# log.end\n") == 0);
    {
        int ends = 0;
        for (const char *p = block; (p = strstr(p, "# log.end\n")); p += 2) ++ends;
        assert(ends == 1);
    }

    // The USB copy omits log.file; everything else is identical.
    {
        logger_card_header::Facts usb = sketch_facts();
        char ub[logger_card_header::BUFFER];
        const size_t ulen = logger_card_header::render(ub, sizeof(ub), usb);
        assert(ulen > 0);
        assert(!strstr(ub, "# log.file"));
        assert(strstr(ub, "# log.unit chip=E6614C311B3A3231"));
        for_each_line(ub, line_starts_with_hash);
        for_each_line(ub, line_is_namespaced_or_magic);
        // Dropping one line is the ONLY difference.
        assert(ulen == len - strlen("# log.file name=/20261024_101530.CSV"
                                    " opened_ms=540 clock=sntp\n"));
    }

    // clock=none when the clock is not trusted, which is what makes a BOOT_
    // name interpretable rather than just odd.
    {
        logger_card_header::Facts boot = sketch_facts();
        boot.file_name = "/BOOT_540.CSV";
        boot.opened_ms = 540;
        boot.clock_trusted = false;
        char bb[logger_card_header::BUFFER];
        assert(logger_card_header::render(bb, sizeof(bb), boot) > 0);
        assert(strstr(bb, "# log.file name=/BOOT_540.CSV opened_ms=540 clock=none\n"));
    }

    /* A buffer one byte short renders NOTHING rather than a truncated header.
     * A half-written description is worse than none, because `log.end` is what
     * makes truncation detectable and a truncated block loses it. */
    {
        char tight[logger_card_header::BUFFER];
        for (size_t n = 1; n <= len; ++n) {
            memset(tight, 'x', sizeof(tight));
            assert(logger_card_header::render(tight, n, f) == 0);
        }
        assert(logger_card_header::render(tight, len + 1, f) == len);
    }

    // The new optional identity is emitted by the real renderer and decoded
    // identically before and after a physical rename. Existing golden remains
    // the compatibility fixture for files that predate uploads.
    {
        auto upload = sketch_facts();
        upload.file_name = "/BOOT_0123456789abcdef.CSV";
        upload.opened_ms = 540;
        upload.power_qualified = true;
        upload.fw = "0.8.1-lra05-dev";
        upload.opened_ms = UINT32_MAX;
        upload.upload_id = "0123456789abcdef0123456789abcdef";
        char header[logger_card_header::BUFFER], name[65]; bool sealable;
        assert(logger_card_header::render(header, sizeof(header), upload));
        assert(logger_upload::identity(header, upload.file_name, upload.chip, name, sealable));
        assert(strstr(header, "# log.power interface=lra01-v1 ign_source=hardware-qualified hold=GP6\n"));
        assert(sealable && !strcmp(name, "U_0123456789abcdef0123456789abcdef.CSV"));
        assert(logger_upload::identity(header, "/20261025_120000.CSV", upload.chip, name, sealable));
        printf("  ok  immutable upload identity fits full header and survives rename\n");
    }

    /* ---- the rename record, CARD_FORMAT.md §9 ------------------------- */
    {
        char note[logger_card_header::RENAME_BUFFER];
        const size_t n = logger_card_header::render_rename(
            note, sizeof(note), "/BOOT_540.CSV", "/20261024_120000.CSV", 6042);
        assert(n > 0);
        assert(strcmp(note, "# log.rename from=/BOOT_540.CSV"
                            " to=/20261024_120000.CSV at_ms=6042\n") == 0);
        assert(n == strlen(note));
        // It is a note, so it obeys every rule the header block does.
        for_each_line(note, line_starts_with_hash);
        for_each_line(note, line_cannot_be_read_as_an_ign_note);
        // In the reserved namespace -- it is format metadata, not a status note.
        assert(strncmp(note, "# log.", 6) == 0);
        // ...but NOT inside the header block: it cannot precede log.end.
        assert(!strstr(block, "# log.rename"));

        // A buffer one byte short writes nothing, for the same reason the
        // header does: half a record is worse than none.
        for (size_t k = 1; k <= n; ++k) {
            char tight[logger_card_header::RENAME_BUFFER];
            memset(tight, 'x', sizeof(tight));
            // Through a volatile so the size is not a compile-time constant:
            // otherwise gcc folds the call and warns about the truncation this
            // loop exists to provoke.
            volatile size_t room = k;
            assert(logger_card_header::render_rename(
                       tight, room, "/BOOT_540.CSV",
                       "/20261024_120000.CSV", 6042) == 0);
        }
        printf("  ok  rename record: %zu bytes, truncation refused\n", n);
    }

    printf("PASS: card header renders the frozen bytes of CARD_FORMAT.md\n");
    printf("      %zu bytes per file, %zu of %zu buffer\n",
           len, len + 1, (size_t)logger_card_header::BUFFER);
    return 0;
}
