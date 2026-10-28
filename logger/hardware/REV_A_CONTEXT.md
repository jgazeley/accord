# Logger Rev A — current hardware and open interfaces

Prepared October 28, 2026 by Codex `pcb-manager`, session `01a17045-1855-7af2-b76a-32c2b778cd64`. Historical bookmark: `codex resume 01a17045-1855-7af2-b76a-32c2b778cd64`. Successors use their own identities.

This is active task context, **not a complete verified schematic**. It replaces
transcript reconstruction for onboarding. Task state belongs only in
[the project tracker](../../coordination/PROJECT_MILESTONES.md).

## Current circuit: confirmed records versus missing detail

| Block | Recorded baseline | Confirmation needed for LRA-03 |
|---|---|---|
| VSS | Cluster B2 → 22k series / 33k shunt → GP2, single upper clamp to 3V3 | Actual routing, fitted parts and off-state injection |
| Tach | B1 → 22k / 6.8k → GP3, upper clamp | Same checks |
| Brake warning | C14 → 22k / 6.8k → GP4, upper clamp; warning line shared with fluid warning | Input loading/off-state behavior and tap integrity; not proof of lever position |
| Clamp correction | Owner confirmed 1N5819 on these three cells, **not BAT54** | Do not copy older firmware comments/spec part names into the BOM |
| Fuel/supply ADC | C11 → GP26, specified 7.5k/4.7k; B11 → GP27, specified 22k/4.7k; dual-rail 1N5819 clamps and filtering specified | Actual fitted ADC protection/filter components and tolerances are not fully reconciled |
| Ground | Owner reports B16 to Pico AGND; opto output return to ordinary Pico GND; buck has its own return | Verify routing/reference/error and current paths; the overall installation is not galvanically isolated |
| IGN | Latest owner report: B11 → diode/resistor → opto LED; B16 input return; output collector → GP5, capacitor across collector/emitter, emitter → Pico GND; LOW means ON | Latest report does not confirm resistor/capacitor values or diode type. Old clock-harness drawing is not current |
| SD | SPI0 GP16 MISO, GP17 CS, GP18 SCK, GP19 MOSI; module powered from Pico 3V3 | Preserve tested rail arrangement; review full load and layout |
| Power | External auxiliary-battery buck feeds 5 V; Pi optional bench | No accepted autonomous power circuit installed |

Present fuel/supply data and road IGN behavior are useful functional evidence,
not electrical qualification. Upper-rail clamps need analysis when Pico power
is off and vehicle inputs remain energized. Do not copy statements that normal
signals never go negative into a vehicle-transient guarantee.

Power measurements reported at the 5 V feed: about 51 mA settled, 72–80 mA after
a longer drive, highest meter maximum 101 mA. They exclude buck draw and do not
bound inrush/fast transients. No measured battery-side off-current is established.

## Power candidate and contract conflicts (LRA-01/02)

Historical engineering candidate `9527a14` proposed a switched-input onboard
buck with IGN startup, active-high 3.3 V HOLD and independent maximum-on logic.
Normal firmware hold is proposed as 1800 s; independent cutoff nominally 2048 s.
Both are candidates requiring a coherent tolerance/startup/fault budget, not
measured shutdown guarantees. Supply/latch belongs on the eventual logger PCB.

Old interface text requested HOLD within 100 ms of valid 3V3, raw opto GP5 plus
100 ms software qualification, and a proposed GP6 (alternate GP7) HOLD pin.
Later design instead shares hardware-qualified IGN with firmware on GP5;
qualification can arrive after the old startup deadline. It proposes polling
within 10 ms and timing from the first observed qualified OFF edge. Do not
combine the incompatible rules or independently rearm on a pulse hardware rejected.
HOLD and optional future GP8/9 bus allocations are not finalized reservations.

Required outcomes: IGN return cancels shutdown safely; SD producer stops at a
record boundary and core 0 drains/syncs/closes; network progress never extends the
absolute cutoff; IGN-absent reset/USB boot must not invent a fresh hold window;
watchdog/core-stall and stuck-HOLD coverage are separate; a service connector
must not backfeed disabled rails. The public firmware has no accepted shutdown
API/implementation yet. These interfaces need source review against current
v0.8.1, not only the power document's v0.7.1 observations.

Candidate-specific gaps preserved for electrical review:

- Shared-qualified-IGN firmware agreement and cold-start/reset timing.
- TPS70950-Q1 candidate protected input: stated 28 V design ceiling / 30 V IC
  limit; previously discussed 41.4 V clamp is incompatible. Choose coordinated
  protection or deliberately replace the affected part.
- Oscillator supply slew/startup/load assumptions, exact effective capacitances,
  hot optocoupler/switch leakage and gate-clamp operating point.
- Partial parked-current screening sums 48.55 µA at room temperature and
  236.6 µA at 85 C exceed the former 40 µA timer allocation. These are not
  measured totals or guaranteed assembled maxima. Existing whole-system
  100/500 µA targets must not be silently relaxed.
- VSS/tach/brake/ADC/IGN/USB/future-bus paths when logger is unpowered; thermal,
  fuse/input protection and buck BOM boundaries.

Eleven Boolean and eight margin checks were recorded passing. They establish
conditional consistency, not assembled analog behavior. The original detailed
connection tables/BOM/test scripts are **not yet copied** into public source.
Retrieve only needed artifacts from historical `logger-power/` at `9527a14`
(or its unchanged descendants), preserve provenance, review for public suitability,
and make the selected version the single active design in `logger/hardware/power/`.
A public-only remote agent can start interface review here; it must request a
reviewed export for missing exact tables rather than inventing them or requiring
private transcripts. Manager handles that bounded dependency.

## LRA-04 communications review boundary

Compare onboard RS-485, a CAN controller/transceiver approach, and a host-side
daughterboard connector with neither bus populated. Existing keyless uses
RS-485; CAN does not make it compatible automatically. No usable factory CAN
connection is assumed. The owner's tested 5 V RS-485 module/dividers remain
an accepted interim option; do not reopen that feasibility investigation.

Use current primary documentation to verify controller versus transceiver
requirements, UART/SPI/PIO/DMA/interrupt resources, Arduino-Pico support and
interactions with SD/capture/Wi-Fi. Provide actual pin allocation, voltage and
power domains, active/off consumption assumptions, enable/reset defaults,
termination/bias/protection, unpowered behavior and connector/mechanical budget.
A daughterboard must specify these interfaces; a vague spare header is not a
resolved design. Consider RTC/test expansion only as a bounded pin requirement.

Deliver a short recommendation, fallback and unknowns sufficient for schematic
freeze. No full CAN stack/network is required before prototype fabrication.

## Provenance and optional deeper records

Historical `accord-logger` `1e99449`: `circuits.md` corrections Oct 24/26;
`fuel/ADC_INTERFACE_SPEC.md` and installation entries in `fuel/READINGS.md`;
`benchlink/picow-logger/SPEC.md` SD wiring; `logger-power/` and
`coordination/reviews/POWER_CUTOFF_9527A14_REVIEW_2026-10-25.md`.
Those records mix specified and fitted parts; newer as-built owner statements
supersede older claims. Public firmware and [pin map](README.md) provide the
current software interface, not complete circuit verification.

Power prior session: `01a17407-4357-7031-b3ac-a51c97864fbe`; predecessor
`01a173c4-d2fd-7f71-a396-8996d502387b`. Firmware delivery session:
`01a17526-034c-78f1-9d09-24c3b88c3dc7`. Bookmarks are optional history, not task ownership.
