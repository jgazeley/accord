#!/usr/bin/env python3
"""Conditional engineering arithmetic. Not SPICE, a part model, or bench evidence.

Endpoints, load and saturation assumptions are explicitly listed in
CUTOFF_MARGIN_REVIEW.md. Passing these checks does not validate those inputs.
"""
import json
import math
import unittest
from itertools import product


def crossing_time(initial, final, threshold, tau):
    if not min(initial, final) < threshold < max(initial, final):
        raise ValueError("Threshold must lie between initial and final values")
    return -tau * math.log((threshold - final) / (initial - final))


def calculate():
    rlo, rhi = 220e3 * .99, 220e3 * 1.01
    clo, chi = 1e-6 * .95, 1e-6 * 1.05
    # Endpoint envelopes include leakage; thresholds are the 5.0 V table.
    on = (crossing_time(.3, 5.11, 2.2, rlo * clo),
          crossing_time(0, 4.5, 3.6, rhi * chi))
    off = (crossing_time(4.5, 0, 2.8, (rlo + 47e3 * .99) * clo),
           crossing_time(5.11, .3, .9, (rhi + 47e3 * 1.01) * chi))
    rd = 4700 * 1.01
    reset_req = 1 / (1 / rd + 1 / rlo)
    reset_endpoint = (.2 / rd + 5.11 / rlo + 1e-6) * reset_req
    reset_time = crossing_time(5.11, reset_endpoint, .9, reset_req * chi)
    rclk_min, rclk_max, cclk_min = 990, 1010, 22e-6
    clock_load_allowance = 100e-6
    clock_slew = (5.11 / rclk_min + clock_load_allowance) / cclk_min / 1000
    drift_ppm = 20 + .035 * 1.1 * 70**2 + 1.5 * 2.5 + 3
    gate = {str(v): (v - .2) * 10000 / (10000 + 1000 + 10)
            for v in (9, 12, 16)}
    return {
        'ign_on_seconds_5V_conditional': on,
        'ign_off_seconds_5V_conditional': off,
        'reset_endpoint_volts_conditional': reset_endpoint,
        'reset_discharge_seconds_conditional': reset_time,
        'clock_slew_V_per_ms_at_allocated_load': clock_slew,
        'clock_min_voltage_at_allocated_load': 4.89 - rclk_max * clock_load_allowance,
        'clock_first_year_sum_ppm': drift_ppm,
        'cutoff_seconds_at_220ppm_and_1s_start': (2047.5 / 1.000220,
                                                 2048.5 / .999780 + 1),
        'unclamped_gate_bias_V_at_P12': gate,
        'gate_bias_12V_resistor_corner': (12 - .2) * 9900 / (9900 + 1010 + 10),
        'max_gate_sink_leakage_uA': .2 / 10100 * 1e6,
        'gate_bias_at_19uA_V': 19e-6 * 10100,
        'initial_RG_current_mA': 16 / 990 * 1000,
        'RG_short_fault_W': 16**2 / 990,
        'RGS_upper_power_W': 16**2 / 9900,
        'parked_screening_subtotals_uA': (16 + 1.5 + 20 + .55 + .5 + 10,
                                         160 + 45 + 20 + 1.1 + .5 + 10),
    }


class MarginChecks(unittest.TestCase):
    def test_conditional_pulse_separation(self):
        result = calculate()
        for name in ('ign_on_seconds_5V_conditional', 'ign_off_seconds_5V_conditional'):
            lo, hi = result[name]
            self.assertGreater(lo, .05)
            self.assertLess(hi, 1)

    def test_reset_has_margin_to_minimum_supervisor_delay(self):
        result = calculate()
        self.assertLess(result['reset_endpoint_volts_conditional'], .9)
        self.assertLess(result['reset_discharge_seconds_conditional'], .120 / 5)

    def test_charge_polarity_defaults_off(self):
        # Even a previously charged capacitor reaches the OFF region during
        # the minimum reset delay, under the stated discharge assumptions.
        rd, rq, cap = 4700 * 1.01, 220000 * .99, 1e-6 * 1.05
        req = 1 / (1 / rd + 1 / rq)
        endpoint = (.2 / rd + 5.11 / rq + 1e-6) * req
        for initial in (0, .3, .9, 2.2, 3.6, 4.5, 5.11):
            at_release = endpoint + (initial - endpoint) * math.exp(-.120 / (req * cap))
            self.assertLess(at_release, .9)
        with self.assertRaises(ValueError):
            crossing_time(0, 2, 2.2, .22)  # Inadequate ON endpoint cannot qualify.

    def test_clock_ramp_and_logic_margin_under_allocated_load(self):
        result = calculate()
        self.assertLess(result['clock_slew_V_per_ms_at_allocated_load'], .5)
        self.assertGreater(result['clock_min_voltage_at_allocated_load'] - .4, 3.33)
        # A 1 uF substitute fails the slew envelope even with no load.
        self.assertGreater(5.11 / (990 * 1e-6) / 1000, .5)

    def test_clock_and_gate_function(self):
        # Manufacturer truth table indexed by (In2, In1, In0).
        truth = (0, 0, 1, 1, 0, 1, 0, 1)
        for arm, clock in product((0, 1), repeat=2):
            self.assertEqual(truth[(arm << 2) | clock], arm & clock)

    def test_timing_window(self):
        result = calculate()
        self.assertLess(result['clock_first_year_sum_ppm'], 220)
        lo, hi = result['cutoff_seconds_at_220ppm_and_1s_start']
        self.assertGreater(lo, 1920)
        self.assertLess(hi, 2400)

    def test_gate_drive_and_old_resistor_regression(self):
        result = calculate()
        self.assertGreater(result['gate_bias_12V_resistor_corner'], 10)
        self.assertLess(result['unclamped_gate_bias_V_at_P12']['9'], 10)
        self.assertLess(result['gate_bias_at_19uA_V'], .2)
        self.assertGreater(10e-6 * 22000, .2)  # Why the old 22k choice failed.
        self.assertLess(result['RG_short_fault_W'], .5)

    def test_budget_shortfall_remains_visible(self):
        room, hot = calculate()['parked_screening_subtotals_uA']
        self.assertGreater(room, 40)
        # These are safeguard subtotals; neither assertion proves whole-board current.
        self.assertLess(room, 100)
        self.assertLess(hot, 500)


if __name__ == '__main__':
    print(json.dumps(calculate(), indent=2), flush=True)
    unittest.main(verbosity=2)
