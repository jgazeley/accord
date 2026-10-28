#!/usr/bin/env python3
"""LRA-02 arithmetic/coverage checks; no component or hardware certification.

All condition-dependent inputs are explicit. The tests intentionally preserve
open budget failures instead of asserting that mixed-condition sums are limits.
Run from any directory with Python's standard library only.
"""
# SPDX-License-Identifier: Apache-2.0
import csv
import hashlib
import json
import math
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def capacitor_stack(nominal_uf, tolerance, temperature, endurance):
    """Independent engineering factors, not a combined manufacturer guarantee."""
    factors = (tolerance, temperature, endurance)
    return (nominal_uf * math.prod(1 - x for x in factors),
            nominal_uf * math.prod(1 + x for x in factors))


class ComponentMargins(unittest.TestCase):
    def test_clock_capacitance_window_and_rejected_47uf(self):
        low, high = capacitor_stack(33, .1, .1, .1)
        self.assertAlmostEqual(low, 24.057)
        self.assertAlmostEqual(high, 43.923)
        self.assertGreater(low, 22)
        self.assertLess(high, 60)
        self.assertGreater(capacitor_stack(47, .1, .1, .1)[1], 60)

    def test_clock_slew_including_load(self):
        low_f = capacitor_stack(33, .1, .1, .1)[0] * 1e-6
        fall_v_per_ms = (5.11 / 990 + 100e-6) / low_f / 1000
        self.assertLess(fall_v_per_ms, .5)
        self.assertAlmostEqual(fall_v_per_ms, .21871456, places=7)
        self.assertAlmostEqual(4.89 - 100e-6 * 1010, 4.789)
        self.assertLess(5.11 / 990, .005163)

    def test_clock_load_reserve_is_not_startup_proof(self):
        cap_hot_ua = 5.3 * 10 * 1.25
        remaining_ua = 100 - cap_hot_ua - 10 - 1.1
        self.assertAlmostEqual(cap_hot_ua, 66.25)
        self.assertAlmostEqual(remaining_ua, 22.65)
        enabled_load_ua = 10e-12 * 5.11 * 32768 * 1e6
        self.assertAlmostEqual(enabled_load_ua, 1.6744448)
        self.assertGreater(remaining_ua, enabled_load_ua)
        # No claim about the unknown oscillator startup/internal dynamic term.

    def test_a5_retention_thresholds(self):
        unit_min_uf = 4.7 * .9 * .85
        self.assertAlmostEqual(unit_min_uf, 3.5955)
        self.assertGreaterEqual(unit_min_uf * .278126, 1)
        self.assertGreaterEqual(2 * unit_min_uf * .305938, 2.2)
        # Negative case: a plausible but unverified retention cannot be assumed.
        self.assertLess(unit_min_uf * .25, 1)
        self.assertLess(2 * unit_min_uf * .25, 2.2)

    def test_buck_capacitor_sizing_only(self):
        ripple_pp = 5.25 * (1 - 5.25 / 16) / (22e-6 * .9 * 225000)
        self.assertLess(ripple_pp, .792)
        self.assertLess(ripple_pp / math.sqrt(12), .229)
        self.assertGreater(.870, .75 / 2)
        self.assertGreater(1.790, ripple_pp / math.sqrt(12))
        self.assertAlmostEqual(capacitor_stack(100, .2, 0, .25)[0], 60)
        self.assertAlmostEqual(capacitor_stack(100, .2, 0, .25)[1], 150)
        self.assertAlmostEqual(capacitor_stack(1000, .2, 0, .25)[0], 600)
        self.assertAlmostEqual(capacitor_stack(1000, .2, 0, .25)[1], 1500)
        b5_decay = 1500e-6 * 1010 * math.log(5.25 / .3)
        vin_decay = 150e-6 * 10100 * math.log(16 / 8)
        self.assertLess(b5_decay, 5)
        self.assertGreater(b5_decay + vin_decay, 5)  # Full-circuit decay remains open.
        # Neither an ESR interval nor phase margin is inferred from impedance.

    def test_correct_cd_package_distribution(self):
        self.assertEqual(sum((.25, .25, 1)), 1.5)
        self.assertEqual(sum((7.5, 7.5, 30)), 45)
        self.assertEqual(sum((.5, .5, 2)), 3)  # 10 V sensitivity, not 5.11 V guarantee
        self.assertEqual(sum((15, 15, 60)), 90)

    def test_parked_subtotals_and_unclosed_allocations(self):
        # HC pair, CD packages, new UOE, UGCLK, UXO, supervisor, LDO reserve, CCLK.
        room = sum((16, 1.5, 1, 10, .55, .5, 10, 6.625))
        hot = sum((160, 45, 10, 10, 1.1, .5, 10, 66.25))
        self.assertAlmostEqual(room, 46.175)
        self.assertAlmostEqual(hot, 302.85)
        self.assertEqual(22 + 4 + 2 + 1, 29)  # 32 total minus three hard-grounded inputs
        pin_room = 26 * .1 + 2 * 5 + .1
        pin_hot = 26 * 1 + 2 * 5 + 1
        self.assertAlmostEqual(room + pin_room + 1, 59.875)
        self.assertAlmostEqual(hot + pin_hot + 5, 344.85)
        self.assertGreater(room + pin_room + 1, 50)  # Parent room allocation open
        self.assertGreater(hot, 250)  # Parent hot allocation open even before pins
        self.assertAlmostEqual(65 - (room + pin_room + 1), 5.125)  # Unproved reserve for discretes
        self.assertGreater(hot + 45 + pin_hot + 5, 375)
        self.assertEqual(sum((65, 5, 20, 10)), 100)
        self.assertEqual(sum((375, 75, 25, 25)), 500)

    def test_gate_sink_and_asymmetric_qp_rating(self):
        self.assertAlmostEqual(19e-6 * 10100, .1919)
        self.assertLess(19e-6, .2 / 10100)
        self.assertGreater(20e-6 * 10100, .2)
        # New option cannot inherit the old 18 V-magnitude criterion.
        self.assertGreater(-14, -16)
        self.assertLess(1, 5)
        self.assertLess(-18, -16)
        self.assertGreater(28, 16)  # Protected-input target is not the bench envelope.

    def test_drive_and_filter_endpoint_screens(self):
        self.assertLess(5.11 / 21780, .000420)
        self.assertLess(5.11 / (990 + 99000), .000052)
        self.assertAlmostEqual(.3 / 47470 * 1e6, 6.3197809, places=6)
        ib = (2.6 - .95) / 1010 - .95 / 99000
        demand = (16 / 990) / 10
        self.assertGreater(ib, demand)
        self.assertLess(ib - demand, 9e-6)  # Deliberately flag narrow conditional margin.
        self.assertGreater(28**2 / 990, .5)

    def test_bom_structure_and_paired_proposal(self):
        with (HERE / 'BOM_DELTA.csv').open(newline='') as f:
            raw = list(csv.reader(f))
        self.assertEqual(len(raw), 15)
        self.assertTrue(all(len(row) == 8 for row in raw))
        data = {r[0]: dict(zip(raw[0], r)) for r in raw[1:]}
        self.assertEqual(len(data), 14)
        self.assertEqual(data['QP']['disposition'], 'PAIRED_PROPOSAL')
        self.assertEqual(data['DZ']['disposition'], 'PAIRED_PROPOSAL')
        self.assertEqual(data['CCLK']['new_candidate'], 'KEMET T491D336K016AT')
        self.assertEqual(data['A5_COUT']['qty'], '2')
        self.assertEqual(data['TVS']['qty'], '0')
        self.assertTrue(all(r['conditions'] and r['evidence'] for r in data.values()))

    def test_historical_artifacts_remain_identical(self):
        manifest = json.loads((HERE / 'SOURCE_MANIFEST.json').read_text())
        self.assertEqual(len(manifest['files']), 11)
        for entry in manifest['files']:
            with self.subTest(path=entry['destination']):
                digest = hashlib.sha256((ROOT / entry['destination']).read_bytes()).hexdigest()
                self.assertEqual(digest, entry['destination_sha256'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
