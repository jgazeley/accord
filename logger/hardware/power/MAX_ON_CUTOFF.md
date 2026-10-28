# Independent maximum-on cutoff — candidate, 2026-10-25

**Design and local-agent handoff, not a validated circuit or fabrication release.**
This extends revision A in `DESIGN.md`; its existing connection list and BOM
do not yet include this circuit. No assembly, oscillator measurement, power
ramp test or vehicle test has been performed remotely. Start with the logic
on a current-limited regulated 5 V supply and a dummy load. The later
[CUTOFF_MARGIN_REVIEW.md](CUTOFF_MARGIN_REVIEW.md) supplies the revised clock,
reset/IGN and always-on supply blocks, calculations and remaining gates.

## Owner decisions and intended behavior

The owner confirmed auxiliary-battery testing, with eventual starter-battery
power preferred because the integrated logger PCB will probably be near the
gauge cluster. Through-hole is preferred; surface-mount parts are acceptable.
The connector, fuse/harness, IGN tap and ground point remain unspecified.
Starter power is therefore the eventual protection design case; an isolated
auxiliary supply is a test arrangement, not evidence of charging-system immunity.

Keep the firmware's proposed 30-minute shutdown. Add a separate hardware
deadline at nominal **2048 s (34 min 8 s)** after qualified IGN goes away.
This fits the earlier proposed 32–40 minute backup window. The timer has its
own always-on supply and clock; the Pico cannot refresh it with HOLD, resets,
network traffic or watchdog servicing. Releasing HOLD terminates permission
early. Only qualified IGN can grant it again.

| Event | Required settled behavior |
|---|---|
| Cold boot, IGN absent, HOLD high or low | HOLD path inhibited |
| Qualified IGN present, supply healthy, HOLD high | Arm; hold both counters reset; QI already supplies startup override |
| IGN becomes absent while armed | Run the hardware countdown |
| HOLD releases | Disarm immediately; do not rearm from subsequent HOLD assertion alone |
| Deadline reached with HOLD stuck high or QH shorted | Open the separate series sink switch; remain disarmed |
| Qualified IGN returns | Clear elapsed count; permit arming while HOLD is asserted |
| Timer supply brownout/loss, IGN absent | Disarm; recovery must not grant a new window |
| IGN electrically stuck high | QI keeps power on; not covered |

This is independent of logger firmware, **not protection against every
single component failure**. A stopped timer clock, failed timer logic,
shorted inhibit switch, shorted main QP, or stuck-high IGN can defeat the
claimed bound. USB or signal backfeed can keep the Pico alive after battery
cutoff; those paths still require the separate isolation work.

## Timing and latch connections

Use 5 V CMOS throughout this block. `A5` means the independent always-on
5 V rail, not switched B5 or Pico 3V3. Every IC gets local 100 nF bypassing;
all grounds join PGND. Unused CMOS inputs must be tied to a rail.

| Ref | Candidate | Connections |
|---|---|---|
| UCLK | TI CD74HC4060E, PDIP-16 | 16=A5, 8=GND, 12=COUNT1_RESET, 3=Q14 output to UCOUNT clock; pins 9/10 open; 11=CLK32 from the external clock block |
| UCOUNT | TI CD74HC4020E, PDIP-16 | 16=A5, 8=GND, 10=UCLK Q14, 11=BASE_RESET; pin 2 Q13=EXPIRED |
| ULATCH | TI CD4011BE, PDIP-14 | NAND A: 1=SET_N, 2=NARM, 3=ARM; NAND B: 5=RESET_N, 6=ARM, 4=NARM; NAND C: 8=QUAL_N, 9=QUAL_N, 10=IGN_Q; tie unused inputs 12,13 to GND; pin11 open |
| UOR | TI CD4071BE, PDIP-14 | A: 1=BAD, 2=IGN_Q, 3=BASE_RESET; B: 5=BASE_RESET, 6=NARM, 4=COUNT1_RESET; C: 8=BAD, 9=EXPIRED, 10=FAULT_RESET; D: 12=FAULT_RESET, 13=HOLD_N, 11=ARM_RESET |
| USCH | TI CD4093BE, PDIP-14 | A: 1=IGN_RC, 2=A5, 3=QUAL_N; B: 5=PGOOD, 6=PGOOD, 4=BAD; C: 8=ARM_RESET, 9=ARM_RESET, 10=RESET_N; D: 12=IGN_Q, 13=RESET_N, 11=SET_N |

All three 14-pin packages: pin 14=A5, pin 7=GND. The equations are:

```text
BASE_RESET   = BAD OR IGN_Q
COUNT1_RESET = BASE_RESET OR NARM
ARM_RESET    = BAD OR EXPIRED OR HOLD_N
RESET_N      = NOT ARM_RESET
SET_N        = NOT (IGN_Q AND RESET_N)
ARM          = NAND(SET_N, NARM)
NARM         = NAND(RESET_N, ARM)
```

Reset dominates set in the settled Boolean model. Propagation hazards and
power ramps still need scope checks. **Do not reset UCOUNT with NARM.**
That would erase EXPIRED as soon as it disarms the latch. Instead stop UCLK
when disarmed and leave UCOUNT's count until IGN or supply reset clears it.
Resetting UCLK can generate one final falling Q14 edge; at expiry that moves
4096 to at most 4097, leaving Q13 high. Early HOLD release also stops the
oscillator, avoiding continued clock power after ordinary shutdown.

For a 32768 Hz oscillator, UCLK Q14 supplies 2 falling edges/s. UCOUNT Q13
first rises on edge 4096: `4096 / 2 = 2048 s`. A clearly labelled bench
selection of UCOUNT Q8 (pin 13) gives `128 / 2 = 64 s`. Production uses Q13;
the accelerated test does not substitute for a full-duration test.
The [TI HC4060](https://www.ti.com/lit/ds/symlink/cd74hc4060.pdf) and
[HC4020](https://www.ti.com/lit/ds/symlink/cd74hc4020.pdf) specify the
negative-edge counters and active-high resets used here.

Clock qualification target: frequency within ±1%, startup at most 1 s,
with no pauses while counting. Conservatively allowing one 2 Hz edge of
phase uncertainty gives 2027.2–2070.2 s from qualified IGN loss. This is
conditional arithmetic, **not a measured or guaranteed oscillator bound**.
The physical IGN qualification delay must be added when timing from the wire.

### Selected external clock block

The revised proposal uses OV-7604-C7 (TA, ±20 ppm) with a filtered supply
and two compatible interface gates. See section 1 of
[CUTOFF_MARGIN_REVIEW.md](CUTOFF_MARGIN_REVIEW.md) for all connections,
ramp calculations and timing conditions. Remove the former AB38T bare
crystal and its four oscillator passives; that experiment is superseded.
The 2048 s/64 s counter selections above are unchanged.

## Separate interruption of the HOLD path

Replace only the direct SINK-to-QH-collector connection in revision A:

```text
SINK ---- QS drain
          QS source ---- QH collector
                         QH emitter ---- PGND
ARM ---- 1k ---- QS gate
QS gate ---- 100k ---- PGND
QI collector remains connected directly to SINK.
QP gate-to-source RGS: change 100k to 10k for this experiment.
```

QS candidate is **Nexperia BSS138P**, SOT-23 on an adapter: gate=1,
source=2, drain=3. Body diode points from QH collector toward SINK, so it
blocks the sink direction when QS is off. Keep QH's emitter grounded;
interrupting its emitter instead can couple fault voltage into the HOLD
interface. The switch grants permission only: it cannot sink without QH.

The [BSS138P datasheet](https://assets.nexperia.com/documents/data-sheet/BSS138P.pdf)
gives 60 V VDS, 2 Ω maximum at VGS=5 V/50 mA/25 C, and drain leakage limits
of 1 µA at 25 C and 10 µA at 150 C, both at 60 V. This favors it over the
through-hole 2N7000 for this leakage-sensitive position. A 2N7000's hot
leakage limit reaches 1 mA at 125 C/48 V in the
[onsemi family datasheet](https://www.onsemi.com/pdf/datasheet/nds7002a-d.pdf).
Neither name alone establishes assembled hot leakage or operation at the
actual minimum gate voltage; measure both.

With RGS=10k, 10 µA sink leakage would produce about 0.10 V of unwanted
QP gate bias. Include QI, PCB contamination and all other leakage in that
sum; retain revision A's off-state |VGS(QP)| limit of 0.2 V and require rail
decay/current to pass. Including +1% resistance, that allows at most 19.8 µA
total sink leakage. RGS draws about 1.2 mA with 12 V gate bias while on. Recheck
revision A's drive and clamp currents with this change. The candidate
transistor's rating does not qualify the remaining 40 V drivers for vehicle use.

Pre-commit review corrected an earlier 22k proposal and 0.5 V criterion:
10 µA through 22k already exceeds revision A's 0.2 V acceptance limit.
The 10k proposal preserves that criterion with some leakage margin; it does
not establish a complete worst-case leakage budget or measured cutoff.

Sense HOLD without a 5 V pullup on the Pico:

```text
HOLD_RAW (before JH) -- 47k -- QMON base
QMON base -- 100k -- PGND
QMON emitter -- PGND
QMON collector = HOLD_N; HOLD_N -- 100k -- A5
```

QMON is a third 2N3904, beyond revision A's QI/QH. Verify spare quantity
and pinout; do not assume the two listed inventory parts cover all three.
Opening maintenance link JH still physically releases QH. HOLD monitoring
adds roughly 50 µA GPIO base drive while asserted, not a timer refresh path.

## Revised supply, reset and ignition qualification

Use the replacement blocks in `CUTOFF_MARGIN_REVIEW.md`, sections 2–3:
TPS70950QDBVRQ1 from protected P_AON (controlled P12 for the bench), the
existing TPS3839K50 supervisor, an IGN filter whose empty capacitor means
OFF, QRESET discharge, and QREPORT translation to GP5. The old TPS7A16,
diode-precharge circuit and second series opto LED are superseded.

GP5 is proposed to report the **same hardware-qualified IGN_Q** used by the
cutoff. This changes the earlier firmware debounce/startup contract and
requires firmware-owner acceptance before integration. Exact 100 ms raw
IGN debounce is not claimed. The direct QI startup override remains.

## Inventory and current budget

`MAX_ON_BOM.csv` lists the updated incremental candidates; use it together
with revision A's BOM and the replacement notes. Inventory is not a fresh
spare count. The oscillator, regulator, supervisor, clock interface gates
and signal MOSFETs need SMD adapters. Counters and main latch logic remain
through-hole. No purchase was made.

The revised static screening sum is **48.55 µA at room temperature and
236.6 µA at 85 C**, before other leakage/current terms. It exceeds the former
40 µA timer allocation. The complete 100/500 µA logger targets are not yet
proven. See the current ledger and explicit conditions in
`CUTOFF_MARGIN_REVIEW.md`; do not treat this subtotal as an assembled maximum.

## Local execution and evidence to return

1. Review the revised blocks and remaining engineering gaps in
   `CUTOFF_MARGIN_REVIEW.md`; verify actual packages, effective capacitance
   and stock. Capture the final circuit and check its nets before wiring.
2. With regulated A5 and manual clean logic inputs, test the latch, 64 s
   output, early HOLD release, repeated HOLD toggles, and IGN recovery. Scope
   ARM, EXPIRED, Q14 and resets for feedback/ripple hazards. Then use Q13 and
   measure a complete 2048 s run, recording clock frequency and temperature.
3. Integrate the reset/IGN front end. Test cold boot, slow ramps, rapid
   interruptions and partial brownouts with IGN absent/HOLD high, then IGN
   present. Log A5, PGOOD, IGN_RC/IGN_Q and ARM; no false grant is acceptable.
4. On a current-limited dummy-load fixture, test stuck-high HOLD and short
   QH collector-to-emitter. Verify QS still interrupts, QP gate returns toward
   its source, and the rails decay. Repeat the leakage tests hot with suitable
   rated timing parts; include current from every connected source.
5. Coordinate IGN qualification and power-domain interfaces with the firmware
   owner before attaching a real Pico/SD. Perform normal shutdown and ignition
   return race tests. A forced cutoff can lose the current file; the backup
   is a battery bound, not a substitute for storage shutdown.

Return fitted part numbers, an as-wired diagram, instrument setup, timestamps,
rail/gate waveforms, currents and temperatures, including failures. The remote
logic check below does not establish any of these physical results.

## Remote logic check

Run `python3 logger-power/check_max_on_logic.py` and
`python3 logger-power/check_cutoff_margins.py` from the repository root.
It checks the proposed settled state behavior against no-rearm, deadline,
brownout and reset-priority invariants, plus accelerated/production arithmetic.
It does not simulate analog inputs, gate propagation, oscillator startup,
leakage, power rails or transistor failures. Physical tests above are pending.

Remote result, October 25: **11 tests passed** with Python 3.13.5, including
an exhaustive reachable-state check using a reduced terminal count and a
brownout check at every active production count. `git diff --check` passed.
The review base is `e7415c9`. See `NEXT_SESSION.md` for the commit scope,
remaining remote work and the evidence boundary for a returning engineer.
