#!/usr/bin/env python3
"""LRA-01 candidate executable specification, not deployed firmware.

Models already-qualified input observations, generation-tagged close results,
and settled hardware logic. Excludes GPIO/IRQ timing, analog propagation,
actual file operations, clock/part qualification and physical measurements.
New arithmetic checks expose open budgets rather than declaring them closed.
"""
from dataclasses import dataclass
from itertools import product
import unittest

from check_max_on_logic import State as Hardware, step as hardware_step
from check_cutoff_margins import calculate


@dataclass
class PowerPolicy:
    phase: str = "BOOT"
    hold: bool = False
    off_ms: int | None = None
    generation: int = 0
    closed: bool = False
    last_ms: int = -1

    def observe(self, now_ms, qualified_on):
        if now_ms < self.last_ms:
            raise ValueError("power time must be monotonic within a boot")
        self.last_ms = now_ms
        # ON takes priority, including at the software release boundary.
        if qualified_on:
            if self.phase != "RUN":
                self.generation += 1
            self.phase, self.hold, self.off_ms = "RUN", True, None
            self.closed = False
            return
        if self.phase == "RUN":
            self.off_ms = now_ms
            self.phase = "WINDOW"
        if not self.hold:
            return  # boot/released OFF cannot grant a window
        elapsed = now_ms - self.off_ms
        if elapsed >= 1_800_000:
            self.phase, self.hold = "RELEASED", False
        elif elapsed >= 1_770_000 and self.phase == "WINDOW":
            self.generation += 1
            self.phase = "FINALIZING"

    def close_result(self, generation, success):
        if self.phase == "FINALIZING" and generation == self.generation:
            self.closed = success
            return True
        return False


class InterfaceChecks(unittest.TestCase):
    def running_off(self, off_ms=10):
        fw = PowerPolicy()
        fw.observe(0, True)
        fw.observe(off_ms, False)
        return fw

    def test_boot_off_and_usb_time_grant_nothing(self):
        fw = PowerPolicy()
        for now in (0, 3000, 900000, 1800000, 10**12):
            fw.observe(now, False)
            self.assertFalse(fw.hold)
            self.assertIsNone(fw.off_ms)
            self.assertFalse(hardware_step(Hardware(), hold=True).armed)

    def test_deadline_independent_of_repeated_off_observations(self):
        fw = self.running_off()
        for now in range(20, 1_800_010, 997):
            fw.observe(now, False)
            self.assertEqual(fw.off_ms, 10)
        fw.observe(1_800_010, False)
        self.assertFalse(fw.hold)

    def test_failed_or_missing_close_never_delays_release(self):
        for result in (None, False, True):
            fw = self.running_off()
            fw.observe(1_770_010, False)
            self.assertEqual(fw.phase, "FINALIZING")
            if result is not None:
                self.assertTrue(fw.close_result(fw.generation, result))
            fw.observe(1_799_010, False)
            self.assertTrue(fw.hold)  # no early power release in this candidate
            fw.observe(1_800_010, False)
            self.assertFalse(fw.hold)

    def test_return_at_each_shutdown_phase_invalidates_old_ack(self):
        for returned in (1_769_999, 1_770_010, 1_785_010, 1_800_010, 1_801_010):
            fw = self.running_off()
            fw.observe(returned, False)
            old_generation = fw.generation
            fw.observe(returned, True)
            self.assertTrue(fw.hold)
            self.assertEqual(fw.phase, "RUN")
            self.assertFalse(fw.close_result(old_generation, True))
            fw.observe(returned + 100, False)
            self.assertEqual(fw.off_ms, returned + 100)
            fw.observe(returned + 100 + 1_770_000, False)
            self.assertFalse(fw.close_result(old_generation, True))
            self.assertTrue(fw.close_result(fw.generation, True))

    def test_on_wins_at_deadline(self):
        fw = self.running_off()
        fw.observe(1_800_010, True)
        self.assertTrue(fw.hold)
        self.assertIsNone(fw.off_ms)

    def test_reset_during_off_releases_even_with_residual_power(self):
        hw = hardware_step(Hardware(), ignition=True, hold=True)
        hw = hardware_step(hw, ignition=False, hold=True, edge=True)
        self.assertTrue(hw.armed)
        hw = hardware_step(hw, hold=False)
        fw = PowerPolicy()  # new boot; no permission restored from the old one
        fw.observe(0, False)
        for now in (10, 3000, 1800000):
            fw.observe(now, False)
            hw = hardware_step(hw, hold=fw.hold, edge=True)
            self.assertFalse(fw.hold or hw.armed)

    def test_missed_qualified_return_can_only_keep_earlier_deadline(self):
        fw = self.running_off()
        hw = hardware_step(Hardware(), ignition=True)
        hw = hardware_step(hw, edge=True)
        hw = hardware_step(hw, ignition=True)  # hardware sees return; FW misses
        self.assertEqual(hw.count, 0)
        fw.observe(1_800_010, False)
        hw = hardware_step(hw, hold=fw.hold)
        self.assertFalse(fw.hold or hw.armed)
        self.assertEqual(fw.off_ms, 10)

    def test_release_and_hold_toggle_do_not_rearm_without_qualified_on(self):
        hw = hardware_step(Hardware(), ignition=True)
        hw = hardware_step(hw, hold=False)
        for levels in product((False, True), repeat=6):
            state = hw
            for hold in levels:
                state = hardware_step(state, hold=hold, edge=True)
                self.assertFalse(state.armed)

    def test_bad_supply_dominates_and_recovery_off_cannot_grant(self):
        hw = hardware_step(Hardware(), ignition=True)
        hw = hardware_step(hw, good=False, ignition=True)
        self.assertFalse(hw.armed)
        hw = hardware_step(hw, good=True, ignition=False, hold=True)
        self.assertFalse(hw.armed)

    def test_monotonic_epoch_and_long_uptime(self):
        fw = PowerPolicy()
        origin = 2**32 - 100
        fw.observe(origin, True)
        fw.observe(origin + 10, False)
        fw.observe(origin + 10 + 1_800_000, False)
        self.assertFalse(fw.hold)
        with self.assertRaises(ValueError):
            fw.observe(0, False)

    def test_startup_budget_composes_with_one_second_pulse(self):
        # New acceptance allocations, not measured boot or filter maxima.
        retained_ms = max(100 + 350 + 400, 750) + 10 + 10
        self.assertEqual(retained_ms, 870)
        self.assertLessEqual(retained_ms, 900)
        self.assertGreaterEqual(1000 - 900, 100)
        # The former 3000 ms USB wait cannot fit, nor a 1 s qualifier.
        self.assertGreater(max(850, 3000) + 20, 1000)
        self.assertGreater(max(100 + 350 + 1000, 750) + 20, 1000)

    def test_clock_drift_and_observation_delay_leave_cutoff_reserve(self):
        earliest, latest = calculate()['cutoff_seconds_at_220ppm_and_1s_start']
        for error in (-.01, 0, .01):
            for observation in (0, .010):
                latest_release = observation + 1801 / (1 + error)
                self.assertGreater(earliest - latest_release, 227)
                self.assertGreater(earliest - latest_release - 5, 222)
        self.assertGreater(earliest, 32 * 60)
        self.assertLess(latest, 40 * 60)

    def test_hold_current_allocation_and_dor_screening(self):
        upper_mA = (3.4 / 990 + 2 * 3.4 / 46530) * 1000
        self.assertGreater(upper_mA, 3)
        self.assertLess(upper_mA, 4)
        # Conditional 2.6 V HOLD drive with a 0.95 V VBE assumption.
        qh_base = (2.6 - .95) / 1010 - .95 / 99000
        self.assertGreater(qh_base, (16 / 990) / 10)
        qmon_base = (2.6 - .95) / 47470 - .95 / 99000
        self.assertGreater(qmon_base, (5.11 / 99000) / 10)
        self.assertLess(50e-6 * 1010, .3)  # new DOR hot rated-voltage screen
        self.assertGreater(1e-3 * 1010, .3)  # old DOR max cannot prove it
        self.assertGreater(4.75 - 1.1, 1.8)  # 25 C VF screen, not cold proof

    def test_budget_protection_and_backfeed_gaps_stay_visible(self):
        room, hot = calculate()['parked_screening_subtotals_uA']
        self.assertGreater(room, 40)
        self.assertAlmostEqual(50 - room, 1.45)
        self.assertAlmostEqual(hot + 250, 486.6)
        self.assertGreater(250, 200)  # QP hot screen exceeds proposed allocation
        self.assertGreater(41.4, 32)  # old clamp even exceeds LDO abs max
        self.assertGreater(28**2 / 990, .5)  # IGN resistor isn't 28 V continuous
        self.assertGreater(12 / (22000 + 33000), 100e-6)
        injection = (12 - .3) / 22000 - .3 / 33000
        self.assertAlmostEqual(injection * 1e6, 522.7272727272727)


if __name__ == '__main__':
    unittest.main(verbosity=2)
