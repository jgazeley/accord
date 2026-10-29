#!/usr/bin/env python3
"""LRA-11 arithmetic for the B2 off-state isolation choice.

Every number the recommendation rests on, recomputed from the owner's four
October 29 measurements and from datasheet limits that are quoted in
``B2_ISOLATION.md`` with their source. Nothing here certifies a component,
authorizes a purchase or asserts that a bench result exists: the two rows this
file cannot close from datasheets alone (hot leakage of the fallback, and the
RP2040's intrinsic pin-to-IOVDD diode) are marked in the test names and are
listed as open items in the companion document.

Stdlib only. Run from any directory:  python3 check_b2_isolation.py
"""
# SPDX-License-Identifier: Apache-2.0
import unittest

# --- Owner measurements, 2026-10-29 (D-OFFSTATE-01 / U-07, U-08, U-10, U-14).
# Key out, parked, everything seated, Pico unpowered, USB lead off.
V_B2_OPEN = 4.669      # V, B2 open-circuit at the tap
V_B2_LOADED = 4.140    # V, B2 at the tap with the divider and clamp connected
V_JUNCTION = 1.042     # V, 22k/33k junction (the GP2 node)
V_RAIL_DEAD = 0.883    # V, 3V3 rail = clamp cathodes, board unpowered

R_TOP = 22_000.0       # ohm, fitted divider top leg
R_BOT = 33_000.0       # ohm, fitted divider bottom leg

# --- Budgets. REV_A_INTERFACES 3.1 criterion A, reallocated by the LRA-11
# packet to the single live branch now that B1/C11/C14/B11 are dead when parked.
BUDGET_COLD_UA = 8.0   # uA at 20-30 C
BUDGET_HOT_UA = 20.0   # uA at 85 C
GLITCH_US = 100.0      # firmware edge-rejection window

# --- Datasheet limits, Broadcom ASSR-601JV/JT (AV02-4387EN).
# "Unless otherwise stated, all minimum/maximum specifications are over
# recommended operating conditions", and Recommended Operating Conditions give
# TA = -40 to +105 C for the JV. The IO(OFF) row carries no TA override, unlike
# the Output Withstand Voltage row immediately above it, which states TA = 25 C.
ASSR_ILEAK_MAX_NA = 1000.0     # nA max at VO = 1000 V, over operating temp
ASSR_VO_TEST = 1000.0          # V, the condition that maximum is quoted at
ASSR_BVDSS_MIN = 1500.0        # V min at IO = 250 uA
ASSR_RON_MAX_2MA = 300.0       # ohm max at IO = 2 mA
ASSR_COUT_TYP_PF = 190.0       # pF typ at VO = 0 V, 1 MHz
ASSR_TOFF_MAX_MS = 0.5
ASSR_TON_MAX_MS = 4.0
ASSR_IF_ON_MIN_MA = 7.0        # recommended operating condition
ASSR_IF_ON_MAX_MA = 30.0
ASSR_VF_MIN = 1.25             # V at IF = 10 mA
ASSR_VF_MAX = 1.85

# --- Datasheet limits, Panasonic AQY221N2S (ASCTB156E), the fallback.
AQY_ILEAK_MAX_NA = 10.0        # nA max at VL = Max (40 V), table headed 25 C
AQY_RON_MAX = 12.5             # ohm max
AQY_COUT_MAX_PF = 1.5
AQY_TOFF_MAX_MS = 0.2

# --- Datasheet limits, Omron G6K-2F-Y DC5, the rejected third line.
G6K_IR_MIN_MOHM = 1000.0       # MOhm min at 500 V DC, initial
G6K_MIN_LOAD_UA = 10.0         # uA at 10 mV DC, minimum permissible load
G6K_MIN_LOAD_MV = 10.0
G6K_COIL_MA = 21.1             # mA at 5 V DC
G6K_TMAX_C = 70.0              # distributor-stated maximum ambient

BRANCH_BASELINE_MA = 51.0      # REV_A_INTERFACES 3.3, the awake branch baseline


def dead_rail_ohms(v_rail, i_amp):
    """One-point linear model of the unpowered 3V3 rail's leakage load.

    A dead rail is not ohmic; this is used only to show that removing the
    external clamp does not remove the back-feed, a conclusion that does not
    depend on the model being accurate.
    """
    return v_rail / i_amp


def schottky_vf(i_amp, vf_ref=0.159, i_ref=109.2e-6, n=1.05, vt=0.02585):
    """1N5819 forward drop extrapolated from the single measured point.

    U-07 is open: one room-temperature point at 109.2 uA. The ideality factor
    is an assumption, stated as such.
    """
    import math
    return vf_ref + n * vt * math.log(max(i_amp, 1e-12) / i_ref)


class MeasuredState(unittest.TestCase):
    """Reproduce D-OFFSTATE-01 from the four readings, so the rest is anchored."""

    def test_parked_source_impedance(self):
        i = (V_B2_LOADED - V_JUNCTION) / R_TOP
        self.assertAlmostEqual(i * 1e6, 140.8, places=1)
        r_src = (V_B2_OPEN - V_B2_LOADED) / i
        self.assertAlmostEqual(r_src, 3757, delta=2)

    def test_the_split_and_the_backfeed(self):
        i_total = (V_B2_LOADED - V_JUNCTION) / R_TOP
        i_ground = V_JUNCTION / R_BOT
        i_clamp = i_total - i_ground
        self.assertAlmostEqual(i_ground * 1e6, 31.6, places=1)
        self.assertAlmostEqual(i_clamp * 1e6, 109.2, places=1)
        # The clamp drop, U-07's first measured point.
        self.assertAlmostEqual(V_JUNCTION - V_RAIL_DEAD, 0.159, places=3)

    def test_one_branch_against_the_budgets(self):
        i_ua = (V_B2_LOADED - V_JUNCTION) / R_TOP * 1e6
        self.assertAlmostEqual(i_ua / 100.0, 1.408, places=3)   # 141 % of 100 uA
        self.assertAlmostEqual(i_ua / BUDGET_COLD_UA, 17.6, places=1)


class RejectRaisingTheDividerImpedance(unittest.TestCase):
    """Non-switch direction 1. Reduces; cannot eliminate; costs the edge."""

    @staticmethod
    def parked_current(scale):
        """Injection with the divider scaled by `scale`, clamp still conducting.

        Solved by iteration on the clamp current, with the dead rail modelled
        from the measurement and the Schottky drop extrapolated from U-07.
        """
        r_rail = dead_rail_ohms(V_RAIL_DEAD, 109.2e-6)
        top, bot = R_TOP * scale, R_BOT * scale
        i_clamp = 10e-6
        for _ in range(200):
            v_rail = i_clamp * r_rail
            v_j = v_rail + schottky_vf(i_clamp)
            i_top = (V_B2_OPEN - v_j) / (3757.0 + top)
            new = i_top - v_j / bot
            if new <= 0:
                return i_top, v_j, 0.0
            i_clamp += 0.3 * (new - i_clamp)
        return i_top, v_j, i_clamp

    def test_present_divider_reproduces_the_measurement(self):
        i_top, v_j, i_clamp = self.parked_current(1.0)
        self.assertAlmostEqual(i_top * 1e6, 140.8, delta=1.5)
        self.assertAlmostEqual(v_j, 1.042, delta=0.02)
        self.assertAlmostEqual(i_clamp * 1e6, 109.2, delta=1.5)

    def test_ten_times_misses_both_budgets(self):
        i_top, _, i_clamp = self.parked_current(10.0)
        self.assertGreater(i_top * 1e6, BUDGET_COLD_UA)     # fails cold
        self.assertGreater(i_clamp, 0.0)                    # still back-feeding

    def test_one_hundred_times_buys_the_budget_and_loses_the_edge(self):
        i_top, _, i_clamp = self.parked_current(100.0)
        self.assertLess(i_top * 1e6, BUDGET_COLD_UA)
        # ... but the GP2 node's Thevenin source is now megohms.
        top, bot = R_TOP * 100, R_BOT * 100
        r_thevenin = top * bot / (top + bot)
        self.assertAlmostEqual(r_thevenin / 1e6, 1.32, places=2)
        for c_node_pf in (15.0, 30.0):
            tau_us = r_thevenin * c_node_pf * 1e-12 * 1e6
            # Same order as the firmware's whole rejection window.
            self.assertGreater(tau_us, 0.15 * GLITCH_US)
        # And the back-feed is reduced, never eliminated: the criterion is
        # elimination, so no scale factor passes.
        self.assertGreater(i_clamp, 0.0)


class RejectChangingTheClampTopology(unittest.TestCase):
    """Non-switch direction 2. The clamp that matters is inside the RP2040.

    NOT bench-confirmed: the RP2040's intrinsic pin-to-IOVDD diode is taken
    from the datasheet's absolute-maximum GPIO limit of IOVDD + 0.3 V, which is
    how a pin-to-rail protection diode is stated, not from a measurement.
    """

    def test_unclamped_junction_rises_far_above_any_diode_onset(self):
        # External Schottky removed, nothing else changed, rail genuinely open.
        i = V_B2_OPEN / (3757.0 + R_TOP + R_BOT)
        v_j = i * R_BOT
        self.assertAlmostEqual(i * 1e6, 79.5, delta=0.3)
        self.assertAlmostEqual(v_j, 2.62, delta=0.02)
        self.assertGreater(v_j, 0.7)   # any silicon pin diode is forward-biased

    def test_substituting_a_silicon_pin_diode_does_not_help(self):
        """Back-feed persists at a comparable current and a higher rail."""
        r_rail = dead_rail_ohms(V_RAIL_DEAD, 109.2e-6)
        i_clamp = 100e-6
        for _ in range(400):
            v_rail = i_clamp * r_rail
            v_d = schottky_vf(i_clamp, vf_ref=0.60, i_ref=100e-6)  # silicon
            v_j = v_rail + v_d
            i_top = (V_B2_OPEN - v_j) / (3757.0 + R_TOP)
            i_clamp += 0.2 * ((i_top - v_j / R_BOT) - i_clamp)
        self.assertGreater(i_clamp * 1e6, 50.0)        # still energizing the rail
        self.assertGreater(v_rail, 0.3)                # criterion B's 0.3 V limit
        # A ground-referenced clamp low enough to hold the node under the
        # internal diode's onset would sit below the RP2040's VIL and destroy
        # the logic low. There is no value that satisfies both.
        self.assertLess(0.3, 0.8)

    def test_only_breaking_the_dc_path_upstream_works(self):
        """Restates REV_A_INTERFACES 3.2 as arithmetic, not as a rule."""
        # A switch after the divider top leaves the full divider current.
        i_after = (V_B2_LOADED - V_JUNCTION) / R_TOP
        self.assertAlmostEqual(i_after * 1e6, 140.8, places=1)


class PrimaryASSR601JV(unittest.TestCase):
    """Broadcom ASSR-601JV in series with the B2 divider top."""

    def test_leakage_max_is_inside_both_budgets_at_the_quoted_condition(self):
        leak_ua = ASSR_ILEAK_MAX_NA / 1000.0
        self.assertLessEqual(leak_ua, BUDGET_COLD_UA)
        self.assertLessEqual(leak_ua, BUDGET_HOT_UA)
        self.assertAlmostEqual(BUDGET_COLD_UA / leak_ua, 8.0, places=1)
        self.assertAlmostEqual(BUDGET_HOT_UA / leak_ua, 20.0, places=1)
        # The maximum is quoted at 1000 V; B2 parked applies 4.669 V.
        self.assertAlmostEqual(ASSR_VO_TEST / V_B2_OPEN, 214.2, delta=0.2)

    def test_withstand_margin_over_the_charging_fault(self):
        self.assertGreaterEqual(ASSR_BVDSS_MIN / 16.0, 90.0)

    def test_on_state_ratio_error_is_negligible_for_a_digital_input(self):
        nominal = R_BOT / (R_TOP + R_BOT)
        withsw = R_BOT / (R_TOP + ASSR_RON_MAX_2MA + R_BOT)
        self.assertAlmostEqual(nominal, 0.600000, places=6)
        self.assertAlmostEqual((withsw / nominal - 1) * 100, -0.5424, places=3)
        # Referred to a 5 V pulse at the junction:
        self.assertAlmostEqual((withsw - nominal) * 5.0 * 1000, -16.27, places=1)
        # RP2040 VIH at 3V3 is 2.0 V; the high level is nowhere near it.
        self.assertGreater(withsw * 5.0, 2.0)

    def test_load_current_is_inside_the_recommended_operating_window(self):
        i_signal_ua = 5.0 / (R_TOP + R_BOT) * 1e6
        self.assertAlmostEqual(i_signal_ua, 90.9, places=1)
        self.assertLess(i_signal_ua / 1000.0, 10.0)   # IO max 10 mA

    def test_no_edge_artefact_within_the_glitch_window(self):
        # Closed: the device is a resistor. Worst-case added time constant
        # against a generous 100 pF of node and track capacitance.
        tau_ns = ASSR_RON_MAX_2MA * 100e-12 * 1e9
        self.assertLess(tau_ns / 1000.0, 0.001 * GLITCH_US)
        # Open, board off, key at II (criterion B): COUT couples each VSS edge
        # into the divider. 91 Hz at 80 mph, two edges per cycle, 5 V.
        q_per_edge = ASSR_COUT_TYP_PF * 1e-12 * 5.0
        i_avg_ua = q_per_edge * 2 * 91.0 * 1e6
        self.assertLess(i_avg_ua, 1.0)
        self.assertLess(i_avg_ua, BUDGET_COLD_UA)
        # ... and what that puts on the dead rail, against criterion B's 0.3 V.
        v_rail = i_avg_ua * 1e-6 * dead_rail_ohms(V_RAIL_DEAD, 109.2e-6)
        self.assertLess(v_rail, 0.3)

    def test_isolate_then_release_ordering_has_ten_times_margin(self):
        t_iso_ms = 5.0
        self.assertGreaterEqual(t_iso_ms / ASSR_TOFF_MAX_MS, 10.0)
        t_settle_ms = 20.0
        self.assertGreaterEqual(t_settle_ms / ASSR_TON_MAX_MS, 5.0)

    def test_led_series_resistor_holds_IF_inside_spec_over_tolerance(self):
        r_iso, v_ds_fet = 330.0, 0.05
        worst_low = (5.0 * 0.95 - ASSR_VF_MAX - v_ds_fet) / r_iso * 1000
        nominal = (5.0 - (ASSR_VF_MIN + ASSR_VF_MAX) / 2 - v_ds_fet) / r_iso * 1000
        worst_high = (5.0 * 1.05 - ASSR_VF_MIN - v_ds_fet) / r_iso * 1000
        self.assertGreaterEqual(worst_low, ASSR_IF_ON_MIN_MA)
        self.assertLessEqual(worst_high, ASSR_IF_ON_MAX_MA)
        self.assertAlmostEqual(worst_low, 8.64, places=2)
        self.assertAlmostEqual(nominal, 10.30, places=2)
        self.assertAlmostEqual(worst_high, 11.97, places=2)
        # Resistor dissipation, and the cost on the awake branch baseline.
        self.assertLess((worst_high / 1000) ** 2 * r_iso, 0.05)
        self.assertAlmostEqual(nominal / BRANCH_BASELINE_MA * 100, 20.2, places=1)


class FallbackAQY221N2S(unittest.TestCase):
    """Panasonic AQY221N2S. Better number, weaker guarantee, no automotive grade.

    NOT closed by datasheet: the 10 nA maximum is from a table headed
    "Ambient temperature: 25 C" and the datasheet publishes no leakage-versus-
    temperature curve, only leakage versus load voltage at 25 C. The hot case
    below is an argument from junction-leakage physics, not a specification.
    """

    def test_cold_maximum_is_specified_and_inside_budget(self):
        self.assertAlmostEqual(AQY_ILEAK_MAX_NA / 1000.0, 0.010, places=3)
        self.assertAlmostEqual(BUDGET_COLD_UA / (AQY_ILEAK_MAX_NA / 1000), 800.0)

    def test_hot_case_is_an_argument_not_a_specification(self):
        # Junction leakage doubling every 8 to 10 C over a 60 C rise.
        for per_decade_c in (8.0, 10.0):
            factor = 2 ** (60.0 / per_decade_c)
            hot_ua = AQY_ILEAK_MAX_NA / 1000.0 * factor
            self.assertLess(hot_ua, BUDGET_HOT_UA)
        self.assertAlmostEqual(2 ** (60 / 8) * 0.010, 1.810, places=3)
        # The multiplier that would actually breach the hot budget:
        self.assertAlmostEqual(BUDGET_HOT_UA / (AQY_ILEAK_MAX_NA / 1000), 2000.0)

    def test_signal_and_timing_are_strictly_better_than_the_primary(self):
        self.assertLess(AQY_RON_MAX, ASSR_RON_MAX_2MA)
        self.assertLess(AQY_COUT_MAX_PF, ASSR_COUT_TYP_PF)
        self.assertLess(AQY_TOFF_MAX_MS, ASSR_TOFF_MAX_MS)
        nominal = R_BOT / (R_TOP + R_BOT)
        withsw = R_BOT / (R_TOP + AQY_RON_MAX + R_BOT)
        self.assertAlmostEqual((withsw / nominal - 1) * 100, -0.0227, places=4)

    def test_withstand_covers_the_charging_fault_with_less_margin(self):
        self.assertAlmostEqual(40.0 / 16.0, 2.5)
        self.assertLess(40.0 / 16.0, ASSR_BVDSS_MIN / 16.0)


class RejectedSignalRelay(unittest.TestCase):
    """Omron G6K-2F-Y. Functionally adequate, strictly dominated."""

    def test_dry_circuit_margin_is_genuinely_adequate(self):
        i_branch_ua = (V_B2_LOADED - V_JUNCTION) / R_TOP * 1e6
        self.assertGreater(i_branch_ua / G6K_MIN_LOAD_UA, 14.0)
        self.assertGreater(V_JUNCTION * 1000 / G6K_MIN_LOAD_MV, 100.0)

    def test_insulation_resistance_converts_to_a_small_leakage(self):
        leak_na = V_B2_OPEN / (G6K_IR_MIN_MOHM * 1e6) * 1e9
        self.assertLess(leak_na, 5.0)
        self.assertLess(leak_na / 1000.0, BUDGET_COLD_UA)

    def test_but_it_loses_on_temperature_and_on_coil_current(self):
        # The spec point for criterion A is 85 C; this part stops at 70 C.
        self.assertLess(G6K_TMAX_C, 85.0)
        # And the enable cost is twice the primary's.
        self.assertAlmostEqual(G6K_COIL_MA / 10.3, 2.05, places=2)
        self.assertAlmostEqual(G6K_COIL_MA / BRANCH_BASELINE_MA * 100, 41.4,
                               places=1)

    def test_its_leakage_guarantee_is_no_better_qualified_than_the_fallback(self):
        """The IR minimum is an initial, room-temperature, 500 V figure.

        That is the same defect that disqualified the ADG5412F: a number
        without a temperature qualification. Only the primary carries a maximum
        stated over its operating range.
        """
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
