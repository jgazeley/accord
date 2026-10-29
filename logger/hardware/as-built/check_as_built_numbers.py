#!/usr/bin/env python3
# Independent recomputation of every derived number asserted in AS_BUILT.md and
# REV_A_INTERFACES.md, so a reviewer does not have to trust the prose.
#
# Run from the repository root:
#     python3 -B logger/hardware/as-built/check_as_built_numbers.py
#
# WHAT THIS IS: conditional circuit arithmetic from the fitted resistor values
# and the dated measurements recorded in AS_BUILT.md. The Schottky drop VF is an
# ASSUMPTION (see AS_BUILT.md U-07), not a specification, and every clamp-onset
# and injection figure moves with it.
#
# WHAT THIS IS NOT: a component guarantee, a measurement, a SPICE result, a
# calibration, or evidence that any of this hardware behaves as computed. It
# checks that the documents are arithmetically self-consistent. Nothing more.
import sys

fails = []
def chk(label, got, want, tol, unit=""):
    ok = abs(got - want) <= tol
    print(f"{'PASS' if ok else 'FAIL'}  {label}: {got:.6g}{unit} (asserted {want:g}{unit})")
    if not ok:
        fails.append(label)

VF = 0.3          # assumed Schottky drop at microamp currents
V33 = 3.3
VCLAMP = V33 + VF

def div(vin, rtop, rbot):
    return vin * rbot / (rtop + rbot)

def draw(vin, rtop, rbot):
    return vin / (rtop + rbot)

def onset(rtop, rbot):
    return VCLAMP * (rtop + rbot) / rbot

def inject(vtap, rtop, rbot):
    "rail held at 0 V, clamp at VF above it"
    return (vtap - VF) / rtop - VF / rbot

def clamp_powered(vtap, rtop, rbot):
    "3V3 alive, so the clamped node sits at 3.3 + VF"
    return (vtap - VCLAMP) / rtop - VCLAMP / rbot

def inject_thev(vtap, rtop, rbot, rseries):
    rth = rtop * rbot / (rtop + rbot)
    vth = vtap * rbot / (rtop + rbot)
    return (vth - VF) / (rth + rseries)

print("-- ratios and full scale")
fuel_ratio = 4700 / (7500 + 4700)
sup_ratio = 4700 / (22000 + 4700)
chk("fuel ratio", fuel_ratio, 0.3852, 5e-5)
chk("fuel full scale", V33 / fuel_ratio, 8.57, 0.005, " V")
chk("supply ratio", sup_ratio, 0.1760, 5e-5)
chk("supply full scale", V33 / sup_ratio, 18.75, 0.005, " V")
chk("fuel divider load", (7500 + 4700) / 1000, 12.2, 0.01, " k")
chk("supply divider load", (22000 + 4700) / 1000, 26.7, 0.01, " k")
chk("fuel thevenin", 7500 * 4700 / 12200, 2889, 1, " ohm")
chk("supply thevenin", 22000 * 4700 / 26700, 3873, 1, " ohm")

print("-- digital cell levels")
chk("VSS pin at 5 V", div(5.0, 22000, 33000), 3.00, 0.005, " V")
chk("tach pin at 14.8 V", div(14.8, 22000, 6800), 3.49, 0.005, " V")
chk("brake pin at 11.3 V", div(11.3, 22000, 6800), 2.67, 0.005, " V")
chk("brake pin at 14.1 V", div(14.1, 22000, 6800), 3.33, 0.005, " V")
chk("tach pin at 15 V (sketch claim)", div(15.0, 22000, 6800), 3.5, 0.05, " V")

print("-- divider draw")
chk("VSS draw at 5 V", draw(5.0, 22000, 33000) * 1e6, 90.9, 0.2, " uA")
chk("tach draw at 14.8 V", draw(14.8, 22000, 6800) * 1e6, 514, 1, " uA")
chk("brake draw at 11.3 V", draw(11.3, 22000, 6800) * 1e6, 392, 1, " uA")
chk("brake draw at 14.1 V", draw(14.1, 22000, 6800) * 1e6, 490, 1, " uA")
chk("brake divider share of 375 mA", draw(11.3, 22000, 6800) / 0.375 * 100,
    0.105, 0.001, " %")

print("-- clamp onset at the tap")
chk("VSS onset", onset(22000, 33000), 6.0, 0.01, " V")
chk("tach/brake onset", onset(22000, 6800), 15.25, 0.01, " V")
chk("tach idle margin to onset", onset(22000, 6800) - 14.8, 0.45, 0.01, " V")
chk("tach clamp current at 16 V, rail alive", clamp_powered(16.0, 22000, 6800) * 1e6, 34.2, 0.3, " uA")

print("-- off-state injection, rail at 0 V (DESIGN.md section 6)")
i_vss = inject(5.0, 22000, 33000)
i_tach = inject(16.0, 22000, 6800)
i_b11 = inject_thev(16.0, 22000, 4700, 1000)
i_c11 = inject_thev(8.0, 7500, 4700, 1000)
chk("VSS at 5 V", i_vss * 1e3, 0.205, 0.001, " mA")
chk("tach/brake at 16 V each", i_tach * 1e3, 0.670, 0.001, " mA")
chk("B11 at 16 V", i_b11 * 1e3, 0.516, 0.001, " mA")
chk("C11 at 8 V", i_c11 * 1e3, 0.715, 0.001, " mA")
chk("total five branches", (i_vss + 2 * i_tach + i_b11 + i_c11) * 1e3, 2.78, 0.01, " mA")
chk("VSS injection at 12 V", inject(12.0, 22000, 33000) * 1e6, 523, 1, " uA")
chk("22k/33k load at 12 V", draw(12.0, 22000, 33000) * 1e6, 218, 1, " uA")
chk("22k/6.8k load at 12 V", draw(12.0, 22000, 6800) * 1e6, 417, 1, " uA")

print("-- logged counts against the owner DMM, 2026-10-24 14:57")
def counts_to_tap(counts, ratio):
    return counts * V33 / 4095 / ratio
sup_tap = counts_to_tap(2596.4167, sup_ratio)
fuel_tap = counts_to_tap(893.0833, fuel_ratio)
chk("supply pin volts", 2596.4167 * V33 / 4095, 2.0924, 0.0005, " V")
chk("supply inferred tap", sup_tap, 11.886, 0.002, " V")
chk("supply difference", (sup_tap - 11.93) * 1000, -43.7, 0.2, " mV")
chk("supply difference pct", (sup_tap / 11.93 - 1) * 100, -0.37, 0.01, " %")
chk("fuel pin volts", 893.0833 * V33 / 4095, 0.7196, 0.0005, " V")
chk("fuel inferred tap", fuel_tap, 1.868, 0.002, " V")
chk("fuel difference", (fuel_tap - 1.847) * 1000, 21.2, 0.2, " mV")
chk("fuel difference pct", (fuel_tap / 1.847 - 1) * 100, 1.15, 0.01, " %")

print("-- isolation switch Ron in the fuel top leg")
RON = 25.0
r2 = 4700 / (7500 + RON + 4700)
err = (r2 / fuel_ratio - 1) * 100
chk("fuel ratio shift at Ron=25 ohm", err, -0.205, 0.002, " %")
chk("referred to a 2.4 V wire signal", 2.4 * err / 100 * 1000, -4.9, 0.05, " mV")
chk("as Rs, at 14 ohm/V", abs(2.4 * err / 100) * 14, 0.069, 0.001, " ohm")
r2s = 4700 / (22000 + RON + 4700)
chk("supply ratio shift at Ron=25 ohm", (r2s / sup_ratio - 1) * 100, -0.094, 0.002, " %")
chk("supply, at 12 V", abs(12 * (r2s / sup_ratio - 1)) * 1000, 11, 0.5, " mV")

print("-- rates")
chk("tach at 6500 rpm, 2 pulses/rev", 6500 / 60 * 2, 217, 1, " Hz")
chk("VSS at 80 mph, 4104.3 pulses/mile", 4104.3 * 80 / 3600, 91, 0.5, " Hz")
chk("buck branch power at 51 mA, 5 V", 5.0 * 0.051, 0.255, 0.001, " W")

print("-- GP5 node RC, fitted 100 nF across the opto output (section 3.2a)")
import math
C_OPTO = 100e-9
def t_rise(r, c, thr, vdd=3.3):
    return -r * c * math.log(1 - thr / vdd)
chk("tau at internal 60k", 60e3 * C_OPTO * 1e3, 6.00, 0.01, " ms")
chk("to 3.0 V at internal 50k", t_rise(50e3, C_OPTO, 3.0) * 1e3, 11.99, 0.02, " ms")
chk("to 3.0 V at internal 60k", t_rise(60e3, C_OPTO, 3.0) * 1e3, 14.39, 0.02, " ms")
chk("to 3.0 V at internal 80k", t_rise(80e3, C_OPTO, 3.0) * 1e3, 19.18, 0.02, " ms")
chk("to 3.0 V at Rev A 10k", t_rise(10e3, C_OPTO, 3.0) * 1e3, 2.40, 0.01, " ms")
# RP2040 VIH at IOVDD = 3.3 V is 2.0 V (datasheet 5.5.3.4, table 625). The
# 0.65*IOVDD formula belongs to the 1.8 V row and was used in error here before.
chk("to VIH 2.0 V at internal 50k", t_rise(50e3, C_OPTO, 2.0) * 1e3, 4.658, 0.01, " ms")
chk("to VIH 2.0 V at internal 60k", t_rise(60e3, C_OPTO, 2.0) * 1e3, 5.589, 0.01, " ms")
chk("to VIH 2.0 V at internal 80k", t_rise(80e3, C_OPTO, 2.0) * 1e3, 7.452, 0.01, " ms")
chk("node corner at internal 60k", 1 / (2 * math.pi * 60e3 * C_OPTO), 26.5, 0.1, " Hz")
chk("node corner at Rev A 10k", 1 / (2 * math.pi * 10e3 * C_OPTO), 159.2, 0.2, " Hz")
chk("largest cap holding 10 ms to 3.0 V at 80k",
    10e-3 / (80e3 * math.log(1 / (1 - 3.0 / 3.3))) * 1e9, 52.1, 0.2, " nF")

print("-- ADC filter poles with the fitted 1 uF (section 3.2a)")
# The specification's section 4 diagram puts the capacitor on the GPIO side of
# the 1k, so the resistance charging it is the divider Thevenin PLUS that 1k.
# An earlier revision used the Thevenin alone and reported 55.1/41.1 Hz.
def pole(rtop, rbot, rseries, c=1e-6):
    return 1 / (2 * math.pi * (rtop * rbot / (rtop + rbot) + rseries) * c)
chk("fuel R seen by the cap", 7500 * 4700 / 12200 + 1000, 3889.34, 0.01, " ohm")
chk("supply R seen by the cap", 22000 * 4700 / 26700 + 1000, 4872.66, 0.01, " ohm")
chk("fuel pole", pole(7500, 4700, 1000), 40.92, 0.01, " Hz")
chk("supply pole", pole(22000, 4700, 1000), 32.66, 0.01, " Hz")

print("-- edge-rejection headroom, corrected (section 3.1)")
chk("tach period at 6500 rpm", 1 / (6500 / 60 * 2) * 1e3, 4.62, 0.01, " ms")
chk("GLITCH_US margin against that period", 1 / (6500 / 60 * 2) / 100e-6, 46.2, 0.1, "x")

print("-- opto cell, assumed 2.2k versus 1k (section 3.4a)")
VLED, VD = 1.2, 0.35
chk("LED current, 2.2k at 14.4 V", (14.4 - VD - VLED) / 2200 * 1e3, 5.84, 0.01, " mA")
chk("LED current, 1k at 11.93 V", (11.93 - VD - VLED) / 1000 * 1e3, 10.38, 0.01, " mA")
chk("Ic needed, internal 60k", 3.3 / 60e3 * 1e6, 55.0, 0.1, " uA")
chk("Ic needed, Rev A 10k", 3.3 / 10e3 * 1e6, 330.0, 0.1, " uA")
# Conditional screen only: Sharp's 50% CTR minimum is specified at IF = 5 mA,
# VCE = 5 V, Ta = 25 C, and the fitted part is PC817-class from a kit. The Rev A
# ratio is deliberately NOT computed here: there the opto drives IGN_A/IGN_RC,
# not a 10k GP5 pull-up, so a ratio against that pull-up would be meaningless.
chk("CTR 50% screen ratio, as-built node", 4.72e-3 * 0.5 / (3.3 / 60e3), 42.9, 0.1, "x")
chk("RLED dissipation at 28 V, as-built 2.2k", 28 ** 2 / 2200, 0.356, 0.001, " W")
chk("RLED dissipation at 28 V, candidate 990", 28 ** 2 / 990, 0.792, 0.001, " W")

print()
if fails:
    print(f"{len(fails)} FAILED: {fails}")
    sys.exit(1)
print("All asserted derived numbers reproduce.")
