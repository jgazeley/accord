# LRA-01 — logger power interface contract candidate

Prepared October 28, 2026 by Codex `logger-power`, electrical engineering lead.
Session: `01a18463-5ed7-7041-ad90-ec3a7480c4e6`.
Resume: `codex resume 01a18463-5ed7-7041-ad90-ec3a7480c4e6`.
Identity verified from matching `CODEX_SESSION_ID` and `CODEX_THREAD_ID`.

**Disposition: electrical candidate with blockers; firmware review pending.**
Owner assigned LRA-01 electrical scope to this session. This acknowledges the
claim for pcb-manager; it does not claim firmware review or manager ownership.
Only `logger/hardware/power/` is edited. The manager records the claim and
integration disposition in the single project tracker. No assembly, firmware
change, flash, service change or physical measurement accompanied this work.

## 1. Authority, decisions and preserved baseline

Continue `9527a14153c7b06f3d59b641a2e681b28dcd1735`, exported at public
`25cebe8afab20dc675ca70ef6f25fd396175ee6e`. Original authorship/hashes remain in
[SOURCE_MANIFEST.json](SOURCE_MANIFEST.json); all eleven imported files remain
unchanged. This contract governs the **new candidate interface** and the narrow
changes below. [CUTOFF_MARGIN_REVIEW.md](CUTOFF_MARGIN_REVIEW.md) continues to
govern the revised clock/IGN/reset/supply connections, followed by
[MAX_ON_CUTOFF.md](MAX_ON_CUTOFF.md) and [DESIGN.md](DESIGN.md). This is not a
merged procurement BOM or an accepted schematic.

| Decision | Electrical disposition |
|---|---|
| E01 — power architecture | Retain QP before LM2678, independent A5 latch/counters/clock and direct QI startup; no topology replacement |
| E02 — ignition | One hardware-qualified IGN_Q, reported active-low on GP5; no second software debounce/rearm rule |
| E03 — HOLD | Select GP6, physical pin 9, for the candidate; default released; revise GPIO source allocation to **4 mA**; no GP7 alternate in this contract |
| E04 — deadlines | 1800 s software hold, finalization from 1770 s, release by software elapsed 1801 s; independent nominal 2048 s cutoff |
| E05 — protection | Retain TPS70950QDBVRQ1; prohibit the old 1.5KE30A as its sole protection. Select a common protected-rail requirement, not a fictitious completed vehicle clamp |
| E06 — parked draw | Retain whole-system 100/500 µA targets. Explicitly propose replacing the obsolete 40 µA timer allocation; no worst-case closure claimed |
| E07 — isolation | Disconnect energized sensing branches ahead of their divider/clamp paths; keep ground continuous. Select a lower-leakage DOR candidate; prohibit shared Pi GP5 pullup |
| E08 — integration | Current v0.8.1-dev cannot implement this contract as-is. Reviewer must accept the interface before LRA-05 implementation |

The existing keyless U13 PC817 cell and U3 LM2678 block were inspected in
`keyless/hardware/hondaPico.kicad_sch`. They support the retained opto/buck
precedents. Their IGN resistor, power lifecycle and protection are not logger
qualification. No keyless files or fitted circuits change.

## 2. Domains, pins and electrical meanings

| Net / pin | Direction and domain | Required meaning/default |
|---|---|---|
| P12 | Protected unswitched input | QP source and A5 regulator feed; see section 6 |
| A5 | Always-on nominal 5 V | Cutoff logic, supervisor, opto output; never Pico 3V3 |
| VCLK | A5 through 1k and effective 22–60 µF | Oscillator/UOE rail; retain margin-review ramp/load conditions |
| VIN_SW / B5 | Switched buck input / nominal 5 V output | Battery supply removed by QP, subject to alternate-source isolation |
| VSYS | B5 through DOR; USB through Pico diode | USB may intentionally keep Pico powered; never tie B5 to VBUS |
| 3V3 | Pico switched regulated output | SD and GP5 pullup; target 3.20–3.40 V |
| GP5 / QUAL_N_REPORT | Input, 3V3, physical pin 7 | LOW <=0.4 V means IGN_Q=1; HIGH >=3.0 V means IGN_Q=0; 10k to switched 3V3 |
| GP6 / HOLD_RAW | Output, 3V3, physical pin 9 | HIGH >=2.6 V requests retention; LOW <=0.3 V releases; 47k external pulldown; qualification targets below |
| JH | Removable link in QH base-drive path | Open physically disables HOLD retention, regardless of software; does not inhibit QI |
| ARM / EXPIRED / PGOOD | A5 test points only | No direct GPIO connection; firmware has no ARM feedback in this revision |
| PGND / B16 reference | Continuous ground/reference | Never switch common ground; do not use B16 as substitute power return |

Retain QREPORT BSS138P: source to ground, drain to GP5, gate from IGN_Q via
1k with 100k to ground. Thus there is no intentional DC A5 pullup into GP5.
Retain QMON sensing HOLD_RAW **before JH**, with 47k base resistor and 100k
base/emitter and collector/A5 resistors. QH receives HOLD through JH and 1k,
with its 100k base/emitter pulldown. QS interrupts QH's collector path, not
its emitter; QI remains the independent direct sink.
QMON's collector is HOLD_N: LOW means HOLD_RAW asserted. Opening JH does
not change that monitor connection, but still removes QH base drive.

For the inherited timing calculations, valid A5 means 4.89–5.11 V with
IGN filter endpoints ON >=4.5 V / OFF <=0.3 V. Those conditions still need
the all-load/temperature proof identified below. Initial active bench work
is at 20–30 C; 85 C parked-current screening does not by itself establish an
85 C operating/startup rating for the complete Pico/SD assembly. Freeze the
active temperature envelope with component ratings and LRA-02/03 review.

A pin-map inspection finds no present GP6 use. GP2/3/4, GP16–19 and GP26/27
remain capture/SD/ADC; GP23/24/25/29 remain wireless-board resources. This
reserves no UART, CAN, DE or extra GPIO for LRA-04. Manager/hardware and
firmware owners must acknowledge GP6 before freeze.

**Why 4 mA:** with 3.40 V, -1% resistors and even zero transistor VBE, the
upper source-current calculation is `3.40/990 + 2*3.40/46530 = 3.581 mA`
(QH, QMON and RPD; ignoring shunts makes this conservative). The former
3 mA depended on an assumed VBE. Keep the resistors; request at least 4 mA
pad drive and account for the total GPIO budget. Also replace the old 3.0 V
HOLD HIGH criterion with a **2.6 V qualification target**: RP2040 specifies
VOH >=2.62 V at IOVDD=3.3 V and the selected drive current, not >=3.0 V.
The 3.2 V rail corner must still be qualified. Assuming VBE <=0.95 V,
RH(+1%) and RBH(-1%), 2.6 V supplies QH >=1.624 mA base current, just over
the 1.616 mA needed for forced beta 10 at the 16.162 mA initial gate-current
screen. QMON similarly gets >=25.16 µA against <=51.62 µA collector load.
These are conditional drive calculations, not hot saturation guarantees;
retain R03 qualification of both transistors and loaded pin levels.
[RP2040 datasheet](https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf),
sections 5.5.3.4–5.5.3.5;
[onsemi 2N3904](https://www.onsemi.com/pdf/datasheet/2n3904-d.pdf), p.2 test conditions.

## 3. IGN and startup timing

Definitions:

- **Raw IGN** drives QI and the single opto LED. QI can energize the buck
  before qualification, including during a rejected short pulse.
- **Q** is hardware IGN_Q. It is the sole rearm authority for hardware and
  firmware. GP5 is its inverted report, not raw IGN.
- **tQoff** is the physical falling Q edge. **tFoff** is the first firmware
  observation of the corresponding GP5 HIGH. Normal observation delay is
  required to be <=10 ms. Timestamps and durations are monotonic.
- A boot-time OFF is not an OFF edge after an eligible ON; it grants no hold.
  An unplugged report wire reads OFF. A short to ground is a false ON fault
  and is not detectable with this two-signal interface.

Firmware must observe GP5 and own HOLD before blocking SD/network/serial
initialization. Set the output latch LOW before enabling output. Once a
valid qualified ON is observed, assert HOLD; do not wait for SD or radio.
No hold credit is recovered from wall time, retained RAM, a previous file,
a Wi-Fi window, or the fact that USB is present.

**Startup requirement retained:** raw IGN continuously present for at least
1.000 s must establish retention. Adopt the following **proposed acceptance
budgets**, to make that statement testable; they are not datasheet guarantees:

| Path measured from raw IGN rise, simultaneous battery application allowed | Budget |
|---|---:|
| A5 reaches and remains in its valid envelope | <=100 ms |
| Supervisor release after valid A5 | <=350 ms (specified maximum) |
| IGN qualification after release, worst discharged capacitor | <=400 ms across the accepted rail/temperature range |
| Pico reaches early power supervisor, GP5 usable | <=750 ms from raw IGN rise |
| Observe ON and drive HOLD | <=10 ms after both paths ready |
| QMON/latch/QS establish retention | <=10 ms further |
| Complete path | <=870 ms from these budgets; require measured <=900 ms |

Composition: `max(100+350+400,750)+10+10 = 870 ms`; a one-second pulse
then leaves at least 100 ms measured margin. With A5 already on, the startup
path is shorter. Clock stabilization does not delay HOLD; its separate <=1 s
allowance is included in the cutoff calculation.

The inherited 5.0 V calculation gives ON 104–376 ms and OFF 119–590 ms
from settled endpoints. It is **not** an all-A5/temperature guarantee. The
new 400 ms ON budget needs opto endpoint/Schmitt threshold qualification;
a prior generic “recognize within 1 s” check cannot establish this combined
startup requirement. A5 ramp, Pico boot and opto/logic timings must be captured
together. If the budget fails, first resolve the failing block or bounded
RC change; do not assert HOLD on unqualified raw IGN or silently lengthen the
owner's one-second requirement.

Adopt OFF recognition <=650 ms from settled ON as a qualification target.
Single 50 ms pulses from settled OFF must not rearm; arbitrary repeated bursts
are not covered by that assertion. RC charge accumulates, so test pulse trains.
Once Q changes, firmware applies **no extra 100 ms debounce**. A missed short
Q-ON may let hardware reset its count while firmware keeps the earlier
shutdown deadline: this fails early, not late. Never synthesize an ON that
hardware did not accept. An uncertain/overflowed edge history while Q is OFF
must retain the earliest trustworthy deadline or release, never start a later
window. Document actual minimum accepted/rejected pulse behavior after tests.

## 4. State and shutdown contract

Firmware power control has one owner on core 1, independent of the lossy
network mailbox. A bounded interrupt/alarm may capture edges and enforce the
absolute release, but must not feed the watchdog blindly or touch SdFat.
The reviewer chooses the implementation that proves <=10 ms observation and
release despite serial/SD/network stalls. All requests/acks carry a generation
number; on IGN return, invalidate the prior shutdown generation.

| State/event | HOLD and hardware | Firmware/storage action |
|---|---|---|
| Reset or boot with Q OFF/unknown | LOW/high-Z; no new grant | Wait for real Q ON; USB operation may continue with HOLD LOW |
| First Q ON, healthy supply | Assert HOLD; ARM sets; hardware counters reset | Enter RUN; setup may proceed after power supervision |
| RUN, Q OFF observed | Keep HOLD HIGH; hardware counts from tQoff | Store tFoff once; enter HOLD_WINDOW |
| HOLD_WINDOW, activity/no network/SD missing | HIGH until bounded shutdown | Never extend deadline; retries constrained by it |
| Elapsed 1770 s | HIGH | Enter FINALIZING(g); inhibit new uploads, new file opens, renames and retries; quiesce producer at complete-line boundary |
| Producer quiesced(g) | HIGH | Core 0 finishes/cancels bounded network work; drains queued complete lines, settles file tail, syncs and closes; publishes closed(g)/failed(g) |
| Closed/failed before 1800 s, Q still OFF | HIGH until 1800 s | Stay quiescent; no reopen. No early power saving is required in this revision |
| Elapsed 1800 s, Q still OFF | Drive LOW; must be LOW by 1801 s regardless of ack | Park external interfaces; state RELEASED. Storage failure may lose tail/data; no wait beyond limit |
| Q ON before release, including during finalization/close | Keep/assert HOLD; hardware resets count | Cancel generation; RUN. Core 0 serializes old close completion before reopening a file with a new header |
| Q ON after release but while residual/USB power remains | Reassert only on this genuine Q ON; QI supports restart | New RUN generation; never allow a stale completion to close the new file |
| Q OFF again after accepted Q ON | HIGH if successfully retained | New tFoff; new full window. If prior close is unresolved, recording stays faulted but deadline remains bounded |
| RESET during Q OFF countdown | Default LOW disarms; no reassertion | Discard prior software permission even if capacitors/USB allow boot |
| RESET while Q ON | QI supplies power; rearm possible | Early supervisor reacquires current Q ON before asserting HOLD |
| A5 supervisor BAD | Hardware resets/disarms independent of Pico | May cut power immediately with IGN absent; no guaranteed graceful close |
| EXPIRED while HOLD stuck HIGH/QH C-E short | QS opens HOLD sink path | Backup may truncate SD. Firmware cannot clear expiry with HOLD |
| JH open | QH cannot retain power; QMON may still sense asserted HOLD_RAW | Maintenance, not an autonomous-power test; raw IGN still overrides |

At the release boundary, re-read/capture Q and resolve a simultaneous ON in
favor of RUN. There remains a physical edge/read race; QI and the startup
budget cover return, but a zero-interruption guarantee for arbitrary pulses or
a rail already below reset is not claimed. No interrupt may race a second
HOLD writer. If close is executing when ON returns, cancellation does not
magically abort a blocking SdFat call: core 0 completes/abandons that operation
before admitting a new file, and ignores obsolete generations. Never resume
writing through a stale handle. Full queues and failed finalization must
remain unable to prevent power release.

Timing allocation is software elapsed time: use a 64-bit monotonic hardware
clock (or proved wrap-safe equivalent), independent of SNTP/host corrections.
Require clock rate error <=1% as a conservative qualification envelope.
With <=10 ms observation delay, latest healthy release in real time is
`0.010 + 1801/0.99 = 1819.202 s` after tQoff. The inherited conditional
hardware earliest expiry is `2047.5/1.000220 = 2047.050 s`, leaving **227.847 s**
after release, or 222.847 s after the separate 5 s rail-decay target. Latest
hardware expiry is 2049.951 s under the ±220 ppm/one-edge/1 s startup
assumptions. Do not call software elapsed 1801 s an exact physical-time bound
without the clock allowance. These margins require the stated clocks to run.

Require B5, VSYS and 3V3 <0.3 V within 5 s of release when USB is absent and
all accepted isolation is fitted. Measure the assembled cascade: CIN may
continue feeding the buck before COUT decays, so separate RC calculations
cannot prove the combined five-second result. No requirement makes A5 decay.

Watchdog review proposal: 4 s timeout, fed only by power-control code after
fresh progress from both cores (<=2 s old), valid Q/deadline state and no
overdue release. Distinguish roughly 2+4 s fault-to-reset from a 4 s timeout
after the last feed; include scheduling, clock and rail decay. Firmware must
prove reset covers both cores and releases GPIO/SIO HOLD, including early
boot. Debug settings must not silently suspend production watchdog coverage.
A watchdog-fed stuck-HOLD fault is tested separately against the hardware
cutoff. A5 loss is a fail-off event, not a guaranteed SD transaction finish.

## 5. Agreement needed with current firmware

Source inspected at public `25cebe8` (firmware unchanged from public `8261314`,
version 0.8.1-dev), not the historical v0.7.1 observations:

| Source symbol | Existing behavior | Required review / LRA-05 change |
|---|---|---|
| `accord-logger.ino::setup/setup1` | Core 0 sets SD pins/network; core 1 configures GP5 then can wait 3000 ms for USB; no HOLD output | Early power supervisor must meet section 3 before USB wait; identify SDK/core startup ordering |
| `loop1`, `command('l')`, serial burst handling | Network IGN sampled every 20 ms when loop runs; level command blocks 200 ms; bursts/printing/ADC add delay | Prove independent <=10 ms observation and release; merely reducing 20 to 10 is insufficient |
| `logger_network.cpp::networkSetIgn` | `mutex_try_enter` may drop the update | Do not use this mailbox as power authority; network may consume a copy |
| `wifi_schedule.h::Schedule` | 5 s settle, maximum 900 s radio window; initial known OFF opens a window | Keep radio policy subordinate; it cannot grant power or renew 1800/2048 s timers |
| `logger_sd.h`, `logger_sd.cpp::sdLoop` | Core 1 queues complete lines; core 0 owns SdFat/SPI; 10 s/4096 byte sync; retries failed card every 5 s | Add generation-tagged producer-stop/drain/close result and shutdown gates; existing sync is not a finalization handshake |
| `latchIgn`, row/header facts | `ign` samples GP5 at 1 Hz; `ms_since_ign` tracks ON time | Keep column order, polarity and units; the physical meaning changes to hardware-qualified IGN. Identify circuit/firmware revision in agreed metadata; no raw-IGN column exists after rewiring |
| Watchdog | No shutdown/watchdog policy found in inspected sketch | Reviewer defines startup/runtime feeds and verifies physical GPIO reset |

Firmware reviewer is **unclaimed in the packet and has not accepted** this
contract. This electrical source inspection is not that review. Reserve
`FIRMWARE_REVIEW.md` for the acknowledged reviewer. Requested dispositions:
GP6/4 mA drive; early startup and <=10 ms supervision; clock bound; generation
and IGN-return races; forced-release/data-loss policy; watchdog; qualified-IGN
recording semantics and bridge/header compatibility. No firmware edits here.

## 6. Input protection: decision and remaining engineering

Keep the reverse-current-protected TPS70950QDBVRQ1 (DBV pinout in margin
review). P_AON is fed from the **same coordinated protected P12** for the
candidate, rather than qualifying A5 in isolation while leaving QI/QH/buck
exposed. For design coordination require P12/P_AON <=28 V including specified
surge overshoot, nonnegative at the IC; TPS709's 30 V is the recommended
operating maximum, **32 V is absolute maximum**, not extra usable headroom.
The 6–28 V AON envelope does not mean the complete buck/IGN circuit operates
continuously at 28 V. [TI TPS709-Q1](https://www.ti.com/lit/ds/symlink/tps709-q1.pdf), sections 5.1/5.3/5.5/6.3.3.

Retain **12–16 V controlled bench operation**, characterize 9 V without
promising crank ride-through. First tests use a current-limited regulated
source whose output remains in that range, separate regulated IGN simulation,
and disconnected vehicle harness. This makes the retained regulator compatible
with the actual test supply; it does not qualify a vehicle feed.

**Reject 1.5KE30A as sole protection for this circuit:** its listed 41.4 V clamp
exceeds A5 input limits, 40 V QI/QH VCEO and LM2678's 40 V operating ceiling.
A 1.5KE20A is a bounded lower-clamp candidate for LRA-02: 17.1 V standoff and
27.7 V clamp at 54.2 A/25 C, versus the old part's 25.6/41.4 V. It is **not
selected as completed protection**: 0.3 V to the 28 V target is insufficient
unverified allowance for temperature and wiring overshoot. Its VBR temperature
coefficient is not a guaranteed VC-versus-temperature curve. Neither the
1500 W headline nor nominal fuse current establishes energy survival.
[Vishay 1.5KE table and pulse derating](https://www.vishay.com/docs/88301/15ke.pdf).

LRA-02 must close clamp/limiter selection using an explicit pulse source,
impedance, duration/repetition, hot/cold limits, harness inductance and fuse
clearing curve. IGN needs its own compatible protection: RI/RLED cannot be
assumed to survive a prolonged 28 V input (RLED upper sizing is
28²/990 = 0.792 W, above its 0.5 W rating). P12 transient voltage compliance
alone does not prove pulse power, QP SOA, gate-zener current or buck stability.
Selecting a higher-voltage LDO alone would not fix those paths; therefore it
is not the chosen response to this demonstrated defect.

Owner-specific exposure (starter/aux feed, jump-start and crank expectations,
harness/source details) is needed for vehicle acceptance, not to draft or test
this bounded contract. No new owner decision is required to keep the existing
bench envelope. Exact A5/clock capacitors and their effective C, ESR/leakage,
all-load LDO regulation below 100 µA and hot transistor limits remain
**datasheet/component-selection work**, followed by measurements; do not mark
them “bench only” to avoid closing the engineering.

## 7. Parked-current disposition

Acceptance remains <=100 µA at 20–30 C and <=500 µA at 85 C, after settled
cutoff, IGN OFF, USB absent and normal harness attached. Record J1 and every
independently energized harness source separately, then sum drawn current;
do not hide signal-source draw or cancel it with returned current. USB-powered
maintenance is a different operating state. No powered 5 V measurement is a
battery-side off-current measurement. A5 is linear-regulated: its load current
is approximately carried from battery, not scaled by 5/12 as for a buck.

| Battery-side allocation, µA | Old 25 C proposal | New room proposal | New 85 C proposal |
|---|---:|---:|---:|
| A5 supply + complete timer/logic/filter leakage | 40 | 50 | 250 |
| QP drain/gate leakage into switched stage | 30 | 30 | 200 |
| Gate sink paths, entry protection, other PCB leakage | 10 | 10 | 25 |
| All other energized signal/interface paths | 20 | 10 | 25 |
| Total | 100 | 100 | 500 |

This explicitly reallocates 10 µA from interfaces to A5 at room temperature;
manager/electrical review must accept it. These are **acceptance allocations,
not achievable maxima already established**. In particular:

- Inherited A5 static screens 48.55/236.6 µA leave only 1.45/13.4 µA within
  the new timer allocations. They omit input leakage and intermediate-level
  CMOS current and use condition-specific LDO limits. The 10 µA ground-current
  maximum at 100 µA load is not an all-load bound. No permanent 100 µA preload
  may be added to obtain a regulation specification; it defeats the budget.
- QP IRF4905 has IDSS limits 25 µA at -55 V/25 C and 250 µA at -44 V/150 C,
  both VGS=0. Thus its published hot screening value alone exceeds the 200 µA
  allocation. Adding it to 236.6 gives **486.6 µA before gate/protection/signal
  paths**, leaving 13.4 µA against the whole target. This is a mixed-condition
  warning screen, not a guarantee or a prediction at 85 C/16 V/-0.2 V VGS.
  A measured low-current specimen is not production worst-case proof.
  [Infineon IRF4905, Rev. 2.1, p.2](https://www.infineon.com/assets/row/public/documents/24/49/infineon-irf4905-datasheet-en.pdf).
- Independently enforce total off gate-sink leakage <=19.8 µA for 10.1k RGS
  and |VGS(QP)|<=0.2 V. The prior 19 µA allocation uses QS 10, QI 5 and PCB 4;
  QI/PCB terms remain unproved hot allocations. Passing this gate-voltage
  limit does not prove QP drain leakage or the whole parked budget.
- QMON/QH leakage into HOLD and QREPORT leakage into GP5 must be accounted
  at the actual rail voltages. QMON's collector pullup is not ideal isolation.
  QI/QH/QMON/QRESET hot limits and QS at its actual gate-source drive require
  specified parts or documented qualification, not generic kit names.

Retain the existing parts for bounded characterization. **Guaranteed-budget
freeze is blocked** until these rows close. LRA-02 should first obtain actual
condition-specific limits/qualification; only then replace the offending
leakage part(s), preserving topology, if the limits cannot fit. No target is
relaxed and no unattended acceptance follows from the arithmetic tests.

## 8. Off-state isolation decisions

| Path | Required circuit disposition / evidence |
|---|---|
| GP5 from A5 | Retain QREPORT level translation and switched pullup; remove Pi shared collector/pullup. Measure powered-A5/unpowered-Pico and USB/A5-absent states |
| GP6 into QH/QMON | Retain resistors and base pulldowns; no A5 pullup on GPIO. Require released HOLD <=0.3 V, including hot collector leakage and unpowered Pico; test QH short separately |
| VSS B2, tach B1, brake C14 | Existing upper 1N5819 clamps inject into off 3V3. Require normally-open, power-off-safe branch isolation before divider top, or an independently reviewed equivalent covering both injection and parked loading |
| Fuel C11, supply B11 | Same upstream isolation requirement; preserve divider ratios/B16 reference when enabled; analog reviewer must accept added resistance/leakage and changed loading while off |
| SD | Entire SD interface remains on Pico 3V3; no externally powered SD module or pullups. Include SD capacitance/IO paths in decay tests |
| USB | DOR direction B5 anode → VSYS cathode; no B5/VBUS tie. Open JH for maintenance. USB intentionally powers Pico; do not require VSYS/3V3 decay in this mode |
| Future bus/debug/service | No externally powered UART/SWD/RO pullup into off GPIO; disconnect or use specified power-off-safe interfaces. DE defaults LOW; unselected bus options unpopulated |
| Grounds | Do not switch PGND/B16. Review missing PGND and USB earth paths; this board is not galvanically isolated |

The upstream position is deliberate. Even a perfect buffer **after** a divider
leaves its DC loading: at illustrative 12 V the 22k/33k branch draws 218 µA
and a 22k/6.8k branch 417 µA. These exceed the entire room target if energized
while parked. With the existing upper clamp held near 0.3 V and the rail at
zero, the same VSS branch can inject about **523 µA** into 3V3. Series limiting
and firmware high-Z do not make this isolation. These are conditional circuit
calculations, not claims that those wires are normally HIGH with key removed.

**LRA-03 interface selection gate:** establish each normal/fault input range,
source impedance and permissible cluster loading. LRA-02/03 then specify
power-off leakage across supply ramps, not merely an “Ioff” headline. An
ADG5412F-class source-protected switch was screened as a possible upstream
approach, not selected: its 8 V minimum supply excludes powering it from B5,
and its power-off source-leakage fault entry is typical, not a budget maximum.
This does not close five channels or justify a new BOM. [ADI ADG5412F Rev. C](https://www.analog.com/media/en/technical-documentation/data-sheets/ADG5412F_5413F.pdf), +12 V table and Power-Off Protection.
Until parts are reviewed, omit/disconnect these inputs on the power fixture;
a manual disconnect is a bench restriction, not autonomous vehicle acceptance.

**Bounded DOR change:** select **Vishay 1N4004-E3/54** as the candidate replacing
DOR's 1N5819, same polarity and DO-41 class. The old part's rated reverse
current maxima are 1 mA/25 C and 10 mA/100 C, insufficient to prove a quiet
B5 behind its 1k bleeder. The replacement specifies 5 µA/25 C and
50 µA/125 C at rated reverse voltage; the corresponding RB5(+1%) screening
voltages are 5.05/50.5 mV. The 1.1 V forward limit at 1 A/25 C yields a
3.65 V screening VSYS minimum from B5=4.75 V; Pico W's allowed VSYS range
is 1.8–5.5 V. Characterize cold forward drop, heating (0.55 W sizing at 0.5 A),
load steps, USB insertion/reverse recovery and total Pico/SD input current.
Do not replace the buck catch diode with this slow rectifier. This resolves
a specific leakage-specification weakness, not all USB paths or a whole-board
leakage guarantee. [Vishay 1N5819](https://www.vishay.com/docs/88525/1n5817.pdf),
[Vishay 1N4004](https://www.vishay.com/docs/88503/1n4001.pdf),
[Raspberry Pi Pico W datasheet, powering section](https://datasheets.raspberrypi.com/picow/pico-w-datasheet.pdf).

## 9. Fault coverage, follow-ups and acceptance evidence

The independent cutoff bounds the **HOLD-retained battery path after the last
qualified OFF**, given valid A5/clock/logic and no raw QI override. It does not
bound an ignition line stuck HIGH, repeated raw pulses that energize QI, a
shorted QP/QS, stopped clock, timer logic fault or external backfeed. A5 faults
can remove power before 30 minutes. No promise of SD integrity after a forced
cutoff, reset or brownout is made. Single-clock operation is retained with
this named exclusion; adding redundant fault protection would be new scope.

| ID | Needed evidence / proposed test | Resolution class / owner |
|---|---|---|
| R01 | GP6, supervision, timing, handshake, log semantics and watchdog written disposition | Firmware review; reviewer-owned `FIRMWARE_REVIEW.md`, before integration |
| R02 | P12 and IGN envelope, exact limiter/clamp/fuse calculations; compare all affected part ratings and pulse energy | Engineering LRA-02; owner supplies vehicle exposure requirements |
| R03 | Exact CCLK/A5/CIN/COUT series, effective C/ESR/leakage; loaded logic levels, hot QI/QS/QMON/QRESET and regulator limits | Datasheets/engineering LRA-02; then corner measurements |
| R04 | Close current allocations, including actual QP leakage conditions and energized sources | Engineering LRA-02 plus assembled room/hot current tests |
| R05 | Five input isolation channels, DOR delta, bus/service paths and B16/PGND behavior | LRA-02/03/04 schematic/analog review, then powered-off harness tests |
| B01 | 20 cold starts with 1 s raw IGN, battery already on and simultaneous battery/IGN; scope Q/HOLD/A5/rails; <=900 ms retention | Bench LRA-07 plus LRA-05 candidate; repeat supply/temperature corners |
| B02 | Single 50 ms and burst IGN tests; <=400 ms settled ON / <=650 ms OFF; reset with IGN_RC previously charged; slow/fast/partial A5 ramps | Bench LRA-07; no false OFF-state rearm |
| B03 | Full 1800 s run with unavailable network, SD faults/full queue, serial flood; IGN return at producer-stop, drain, close, release and residual-power stages | Firmware tests plus bench; bound release, reject stale generations |
| B04 | RUN/watchdog/core stalls while Q OFF/ON; USB-only boot; rapid resets with residual charge | Firmware fault tests plus bench; no new OFF-state hold |
| B05 | Healthy full 2048 s run, stuck-high HOLD and QH C-E short on current-limited fixture; clock startup/load and gate/rail traces | Bench; separate Boolean evidence from physical cutoff |
| B06 | Each energized input alone and combined, Pico off; USB/A5 absent/present; JH open/closed; missing PGND safely simulated | Bench after isolation review; rail/current limits, no unintended rearm |
| B07 | DOR load/thermal/recovery, buck regulation/inrush, complete rail decay, hot parked currents | Bench; <=5 s decay and unchanged 100/500 µA targets |

All B tests remain pending. Original prototype steps P05/P09/P12 are
superseded where they use 100 ms raw qualification, promise 200 ms rearm or
say the independent cutoff does not exist. Use the revised behavior above,
retaining the old plan's safe fixture/instrument procedures. No test requires
changing live firmware, wiring the vehicle or modifying the keyless board.

Run the two historical scripts plus `check_interface_contract.py` from the
repository root. The new executable specification exercises candidate state
transitions/races and the new arithmetic using the historical hardware model;
it is not firmware, SPICE, a component guarantee or measured evidence.
See [LRA01_HANDOFF.md](LRA01_HANDOFF.md) for validation and return protocol.
