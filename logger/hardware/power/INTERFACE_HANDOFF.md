# Interface handoff — proposed, 2026-10-25

Owner direction: supply and latch belong **on the logger board**, similar to
hondaPico's onboard supply. Circuit owner remains `logger-power/`. This file
requests owner review; no firmware changes, flashes, deployments or messages
to other sessions were performed.

**Latest cutoff integration proposal:** `CUTOFF_MARGIN_REVIEW.md`, section 2,
supersedes the raw GP5/debounce/startup portions of the revision A contract
below **if that cutoff circuit is adopted**. It proposes shared hardware-
qualified IGN on GP5 and assertion of HOLD after that decision. It requires
firmware-owner acceptance; do not mix the two contracts in an implementation.

## Logger firmware owner

Current source has GP2/3/4/5 for VSS/tach/brake/IGN, GP16–19 for SD,
GP26/27 for fuel/supply, and GP23/24/25/29 reserved for CYW43. Candidate
HOLD is **GP6, physical pin 9**, alternate GP7. Please accept/reserve one
before implementation; preserve future GP8/9 RS-485 and agree its DE pin.

Contract to implement in a separate batch from v0.7.1 acceptance:

1. **HOLD is active-high 3.3 V**, <=3 mA source allocation; no 5 V tolerance
   assumed. External GPIO pulldown 47k, driver base pulldown 100k. Default
   low/high-Z. Set output latch low before enabling output; only assert at
   boot if actual IGN is ON. Target assertion within 100 ms of valid 3V3,
   before any SD, Wi-Fi, USB wait or blocking setup. Initial raw ON may grant
   boot power retention; require 100 ms stable ON for normal state transitions.
2. Dedicated opto produces **GP5 LOW=IGN ON**, HIGH=OFF with 10k to switched
   3V3. The old Pi-shared collector must not remain attached. Firmware cannot
   distinguish an unplugged opto wire from IGN OFF. Treat either as IGN OFF:
   leave HOLD low at boot, or enter the normal bounded shutdown window if
   already running. Do not infer IGN ON from VSS or network activity.
3. Poll IGN <=10 ms; qualify both states for 100 ms. Timestamp the start of the
   eventually accepted stable OFF interval. Use a monotonic wrap-safe clock,
   preferably 64-bit uptime; wall-clock/SNTP/host changes cannot alter expiry.
   `ms_since_ign` currently tracks ON time and is zero in multiple states;
   do not reuse it as the hold deadline. The existing 1 Hz `ign` observation
   can remain a reporting field; coordinate any change in its semantics.
4. Set expiry=OFF edge+1800 s. A stable ON cancels it; next OFF establishes
   a new expiry. Activity never refreshes it. At every loop, check absolute
   expiry even if queues are full or a previous shutdown attempt failed.
5. Begin finalization at expiry-30 s: stop starting uploads, cancel bounded
   in-flight requests; take a final complete sample and stop the producer
   at a line boundary; core 0 drains queued bytes, settles metadata boundaries,
   syncs and closes the file. Complete gracefully by expiry when possible.
   Stop new SD reopen/rename work once finalization owns the file. No
   independent core may write a closing marker while core 0 owns SdFat.
6. **At expiry, release by +1 s regardless of network/card success.** Set
   RS-485 DE low, park interface pins to prevent injections, drive HOLD low
   and remain released. No logging/retry callback may reassert it. Failed
   sync/close may lose data; a bounded power policy must say so. There is
   currently no explicit public shutdown/drain/close API in `logger_sd.h`;
   this interface is work to add, not an existing function to call.
7. IGN returning during finalization cancels power release. If a file was
   already closed, reopen safely with a new header; never append blindly to
   a closed handle. Hardware QI keeps power on during this race. A subsequent
   qualified OFF starts a new window.
8. IGN-absent reset/brownout/USB-only boot must **not** assert HOLD or start a
   fresh window. IGN-present boot may start normally. Test rapid reset while
   reservoir capacitors still power the CPU, not just a fully dead power cycle.
9. Proposed watchdog: enable a 4 s hardware timeout early; **core 1 alone
   feeds**, from the power-supervision path after observing fresh progress
   counters from both cores (age <=2 s), valid power-state/deadline checks,
   and no overdue shutdown. Core 0 publishes progress after bounded work;
   neither timer ISR, network callback nor a blind busy flag feeds. Measure
   healthy longest SD/network call and adjust the validated policy if needed,
   without hiding indefinite blocking. A card stall may force a reset and
   lose its tail; record this tradeoff. Configure reset to include GPIO/SIO
   and both cores, then verify HOLD physically releases.
10. A watchdog-fed logic error or physical stuck-high HOLD is still uncovered
    by that policy. Independent 32–40 min inhibit is a hardware requirement
    before unattended installation. Test core hangs and live-but-stuck HOLD
    as different cases. Production watchdog must not silently pause because
    a debug probe is attached; explicit bench debug builds may differ.
11. USB maintenance: physical JH open guarantees no HOLD retention. USB can
    power the Pico through its existing diode; DOR isolates the buck output.
    Do not rely solely on software USB detection to make maintenance safe.
    IGN can still start the hardware supply; disconnect BATT/IGN if desired
    for a USB-only maintenance session.

Proposed diagnostics (outside the reserved `log.` namespace unless deliberately
versioned): power state, accepted IGN edge uptime, remaining deadline, shutdown
reason/outcome and watchdog reset reason. Preserve raw samples and existing
card/serial compatibility. Any `# log.closed` metadata needs agreement with
the bridge/card-format owner; it is not implemented by this power package.

### Source-review constraints for implementing this contract

Checked against v0.7.1 source in checkout `e7415c9` on October 25:

- `setup1()` waits up to 3000 ms for USB after configuring inputs. Assert
  eligible HOLD before that wait; application-entry uptime alone does not
  prove the 100 ms requirement measured from valid 3V3. Define watchdog
  startup eligibility explicitly so normal initialization is not mistaken
  for stalled runtime progress.
- `command('l')` samples inputs in a blocking 200 ms loop. `loop1()` can
  process multiple commands in one burst and also performs the ADC burst,
  status printing and USB writes. Adding an IGN poll only at the top of
  `loop1()` does not establish a maximum 10 ms service interval. Bound or
  restructure those paths, or provide independently scheduled IGN capture
  and supervision. An interrupt that captures time must not blindly feed
  the watchdog; application health must still govern feeding.
- Keep the existing instantaneous 1 Hz `ign` reporting meaning separate
  from the debounced power-control state. There is no need to change the
  recorded column merely to add power supervision.
- Finalization needs an explicit producer-stop acknowledgement and a
  core-0-owned drain/sync/close result. Include a generation or equivalent
  state check so a late completion from a cancelled shutdown cannot close
  a newly resumed recording after IGN returns. No such public API exists
  today; the exact implementation belongs to the firmware owner.
- Distinguish time since the injected fault, time since progress became
  stale, time since feeding stopped, reset, and rail collapse. A 2 s
  freshness allowance followed by a 4 s watchdog can permit roughly 6 s
  from a core-0 stall to reset, plus scheduling/tolerance; it is not a
  blanket 4 s fault-to-power-off guarantee. P11's bound is measured from
  lost feeding eligibility. Establish and test the full end-to-end bound.

These are integration requirements for the next firmware assignment, not
changes to the already reviewed v0.7.1 candidate or evidence of hardware tests.

## Logger PCB integration owner

Use the hondaPico **onboard LM2678 topology** as precedent. Do not copy its
whole pin map, assume its as-built 100 uH kit inductor is suitable, or reuse its
always-on battery ADC without accounting for parked draw. First logger design
allocation is 5 V/0.5 A continuous with 0.75 A/100 ms peak; freeze it after
measurement. The Pico 3V3 regulator's SD+radio current budget is separate from
the buck budget; an external switched 3.3 V regulator may be needed if measured
load exceeds that budget. Powering the SD module from 5 V requires rechecking
its level shifters and MISO, not just moving a wire.

Tentative logical power interface: BATT_IN, power GND, IGN; separate B16
reference and signal harness. Connector type/cavity assignments, wire gauge,
feed source, enclosure and thermal envelope remain to be frozen. Do not use
hondaPico J1/J2 numbers for a physically different logger connector.

Keep high di/dt loop CIN -> UREG internal switch -> DCATCH -> CIN compact;
keep SW copper small and away from radio, ADC and feedback. Return COUT and
feedback quietly; provide a continuous ground plane with controlled current
paths, not a cut ground moat. Put DREV/TVS at entry, the MOSFET ahead of buck
input bulk, and test loops at entry/logic ground. QP tab is switched input,
not ground. Separate its mechanical clearance from exposed grounded hardware.

Need physical access to JH, RUN, signal isolation and test points. Automatic
signal isolation, independent maximum-on hardware, protection coordination,
capacitor series/stability, fault testing and roadmap gates must close before
layout/fabrication. The current component-level schematic is textual and has
not passed KiCad ERC. Agree per-file ownership before schematic integration;
power engineer owns the power sheet or supplies a bounded reviewed patch.

## Fuel/reference integrity owner

Existing B16, both divider bottoms and Pico AGND share the installed common
rail. Preserve that while designing the new supply; do not route buck/SD/radio
return current through B16 or switch B16 with the power latch. A common chassis
and USB still create parallel paths; the 21 mV chassis reading does not isolate
B16 error. Test load-correlated C11/B11 and B16-to-local-ground changes when
the buck, radio and SD load change, including loss of the intended power ground.

Upper rail clamps on GP26/27 can energize an off 3V3 rail. Isolation must
precede those paths and remain safe with the full divider voltage while its
own supply is absent. Review analog-switch resistance, leakage, temperature
drift and charge injection against the existing 7.5k/4.7k and 22k/4.7k
dividers plus 1k ADC protection. No divider ratio or B16 wiring change has
been made here. Acceptance should compare gauge behavior and calibrated raw
readings before/after isolation; adding components does not silently preserve
the existing calibration.

## Bridge/upload timing owner

Window is 30 minutes from qualified IGN OFF, irrespective of reachability.
Stop starting uploads 30 s before expiry; cancellation/retry must be bounded
inside the remaining window. No HTTP response or server acknowledgment can
hold power indefinitely. Persist/recover upload offsets so unfinished work
resumes at a later IGN session; the SD card remains the durable source.

A synchronized and closed file is not automatically a server-side completion
message. Agree any closing metadata/protocol extension with the firmware
owner, including what an abrupt cut means. This package does not authorize
bridge deployment or resolve migration/replay-overlap issues; the recorded
owner deployment hold remains in force.

## Manager handoff and evidence status

Engineer bookmark is `codex resume 01a173c4-d2fd-7f71-a396-8996d502387b`.
Initial assignment package now exists under `logger-power/`; all physical
results remain pending. Owner clarified onboard integration, auxiliary-battery
testing and eventual starter-battery preference near the cluster. Actual
harness/fuse/connector and ground remain open; the old external buck model is
no longer a design blocker for this architecture.

Proposed coordination corrections, for manager-owned files: replace literal
zero-draw claims with a measured parked budget; distinguish high-Z/reset
failure coverage from driven-high HOLD; replace the unqualified claim that a
watchdog removes every need for a maximum-on timer. Roadmap may now say
component-level bench proposal delivered, not prototype validated. No
`circuits.md` as-built entry is proposed yet because nothing was assembled or
measured. Distribute this handoff as a file; do not start or message other
sessions implicitly.

## Independent cutoff candidate — October 25 continuation

`MAX_ON_CUTOFF.md` proposes a separate 2048 s hardware deadline and latched
HOLD permission. A HOLD release ends permission early; subsequent assertions
cannot restore it without qualified IGN. This is compatible with refusing
HOLD on an IGN-absent reboot. No firmware implementation is included here.

The candidate's analog IGN qualification is not yet equivalent to the proposed
100 ms firmware debounce. A pulse accepted by firmware but rejected by the
hardware could restart the software deadline while the earlier hardware
deadline persists. Resolve a common contract or an agreed qualified feedback
interface before integration; no new pin has been reserved. Supply/reset and
clock qualification remain open, so the nominal 34 min 8 s is not a validated
physical cutoff guarantee.

Subsequent margin review resolves the *proposed interface* by feeding the
same IGN_Q decision to GP5 through QREPORT, keeping the direct QI startup
override. Hardware and firmware then reference one qualified edge; the
firmware deadline begins at the first observed OFF edge (<=10 ms polling).
This replaces independent 100 ms raw-signal rearming. Review the change in
`ign` row semantics and the startup wait for qualified ON. The circuit and
firmware must be adopted together; no firmware changes are included here.
