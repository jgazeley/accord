#!/usr/bin/env python3
"""Executable specification of settled cutoff logic, not an electrical simulator."""

from dataclasses import dataclass
from itertools import product
import unittest


@dataclass(frozen=True)
class State:
    armed: bool = False
    count: int = 0


def step(state, *, good=True, ignition=False, hold=True, edge=False,
         limit=4096, stop_edge=False):
    """Inputs are already qualified Boolean levels; edge is UCLK Q14 falling.

    stop_edge models the possible extra edge when UCLK is reset on disarm.
    Reset/set propagation, invalid supply levels and analog faults are excluded.
    """
    if limit <= 0 or limit & (limit - 1):
        raise ValueError("limit must select a binary counter bit")
    base_reset = not good or ignition
    count = 0 if base_reset else state.count
    expired = bool(count & limit)
    reset_n = not (not good or expired or not hold)
    set_n = not (ignition and reset_n)
    armed = False if not reset_n else (True if not set_n else state.armed)

    if edge and armed and not base_reset:
        count = (count + 1) % 16384
        if count & limit:
            armed = False
    if state.armed and not armed and not base_reset and stop_edge:
        count = (count + 1) % 16384
    return State(armed, count)


class CutoffChecks(unittest.TestCase):
    def arm(self):
        return step(State(), ignition=True)

    def test_no_cold_boot_grant_without_ignition(self):
        for hold in (False, True):
            state = step(State(True, 123), good=False, hold=hold)
            self.assertFalse(step(state, hold=hold).armed)

    def test_exact_production_edge_count(self):
        state = self.arm()
        for _ in range(4095):
            state = step(state, edge=True)
            self.assertTrue(state.armed)
        state = step(state, edge=True)
        self.assertEqual(state, State(False, 4096))
        for _ in range(10000):
            state = step(state, edge=True)
        self.assertEqual(state, State(False, 4096))

    def test_expiry_survives_possible_stop_edge(self):
        state = step(State(True, 4095), edge=True, stop_edge=True)
        self.assertEqual(state, State(False, 4097))
        self.assertFalse(step(state).armed)

    def test_hold_release_cannot_rearm_without_ignition(self):
        for elapsed in (0, 1, 100, 3599, 4095):
            state = step(State(True, elapsed), hold=False, stop_edge=True)
            for hold in (True, False, True, True):
                state = step(state, hold=hold, edge=True)
                self.assertFalse(state.armed)

    def test_ignition_can_start_new_window(self):
        for old in (State(True, 100), State(False, 4096), State(False, 20)):
            self.assertEqual(step(old, ignition=True), State(True, 0))

    def test_reset_dominates_ignition(self):
        for good, hold in ((False, True), (True, False), (False, False)):
            self.assertEqual(step(self.arm(), good=good, hold=hold,
                                  ignition=True), State(False, 0))

    def test_ignition_keeps_count_reset_until_loss(self):
        state = self.arm()
        for _ in range(5000):
            state = step(state, ignition=True, edge=True)
        self.assertEqual(state, State(True, 0))
        self.assertEqual(step(state, edge=True), State(True, 1))

    def test_all_reachable_small_counter_transitions(self):
        # Exhaust the state graph with a smaller terminal bit, including a
        # possible clock-reset edge. This checks all Boolean input combinations.
        seen = {State()}
        pending = [State()]
        while pending:
            old = pending.pop()
            for good, ignition, hold, edge, stop_edge in product((False, True), repeat=5):
                new = step(old, good=good, ignition=ignition, hold=hold,
                           edge=edge, stop_edge=stop_edge, limit=4)
                if new.armed and not old.armed:
                    self.assertTrue(good and ignition and hold)
                if not good or not hold:
                    self.assertFalse(new.armed)
                if good and not ignition:
                    self.assertGreaterEqual(new.count, old.count)
                if new.count & 4:
                    self.assertFalse(new.armed)
                if new not in seen:
                    seen.add(new)
                    pending.append(new)
        self.assertGreater(len(seen), 8)

    def test_deadline_for_all_hold_patterns(self):
        for holds in product((False, True), repeat=6):
            state = self.arm()
            for tick, hold in enumerate(holds, 1):
                state = step(state, hold=hold, edge=True, limit=4)
                if tick >= 4:
                    self.assertFalse(state.armed)

    def test_brownout_at_every_active_count(self):
        for count in range(4096):
            state = step(State(True, count), good=False)
            self.assertEqual(state, State())
            self.assertFalse(step(state, edge=True).armed)

    def test_timing_arithmetic_and_conditional_margin(self):
        divided_hz = 32768 / 2**14
        self.assertEqual(2**12 / divided_hz, 2048)
        self.assertEqual(2**7 / divided_hz, 64)
        earliest = (2048 - 0.5) / 1.01
        latest = (2048 + 0.5) / 0.99 + 1
        self.assertGreater(earliest, 32 * 60)
        self.assertLess(latest, 40 * 60)


if __name__ == "__main__":
    unittest.main(verbosity=2)
