# Rev A communications — the bounded provision, so it cannot hold the PCB

Prepared October 29, 2026 by Claude Code `logger-electrical`, session
`b690946d-3a88-4626-8e7b-b321126a3d16` (LRA-12).
Resume: `claude --resume b690946d-3a88-4626-8e7b-b321126a3d16`.
Session ID read from this session's harness-assigned working paths; this tool
exposes no second identifier to cross-check it against.

**Scope.** This is the one thing LRA-12 was asked to do about communications:
select a bounded, power-off-safe provision so the board can be laid out. It is
**not** the LRA-04 deliverable. LRA-04 remains *returned, revisions required*:
its `REV_A_OPTIONS.md` and `INTERFACE_PROPOSAL.md` do not exist, no bus is
selected, and `D-RA-04` is unchanged. Nothing here claims bus
interoperability or completes that task.

**Decision: a passive DNP expansion header. No transceiver, bias or
termination on this board.** The packet allows it in as many words — *"a DNP
daughterboard/expansion header is an allowed Rev A solution if onboard bus
circuitry would keep this task open"* — and onboard bus circuitry would
certainly keep it open, because the two contradictions below are about a
transceiver this board now does not have.

---

## 1. The two actual contradictions, resolved

These are the only two things LRA-12 had to settle. The general bus comparison
is not redone; the
[LRA-04 review](../../../coordination/reviews/LRA04_REVIEW_2026-10-29.md)
stands.

### R04-REV-1 — tied DE//RE cannot reach shutdown

Both halves of the return cannot stand: a single GPIO driving DE and /RE
together means low enables the receiver and high enables the driver, so the
MAX3485 low-power shutdown state — DE low **and** /RE high — is unreachable,
and the 2 nA figure that depended on it is unobtainable.

**Resolved by keeping the tied line and dropping every claim that rested on
shutdown.** Not by spending a second GPIO. Two reasons:

1. The tied arrangement is the one the keyless board carries, with both pins
   labelled `RS485_DE`, and it was physically exercised: the owner confirms
   the MAX3485 is fitted in a socket and the link was tested extensively from
   the Pi 4 (`./hp out lock pulse`, `./hp io`, `./hp status`). `link.h:221`
   raises GP10, waits 10 µs for driver enable, sends, flushes, then holds one
   character time before dropping DE. That is operational evidence, and
   `D-KEYLESS-485-01` records it.
2. With no transceiver fitted there is no quiescent current to minimise, so
   the state the claim needed does not matter in Rev A. If a daughterboard
   later wants it, that board can drive /RE separately from its own pin — a
   decision for whoever designs it, with the GPIO cost falling on them.

**What is dropped:** the 2 nA shutdown typical, the 1 µA shutdown maximum, and
any statement that this interface reaches a low-power state.

### R04-REV-2 — the off-state recommendation contradicted its own finding

The return recorded that with V<sub>CC</sub> = 0 the MAX3485's bus pins draw up
to 1 mA at 12 V and −0.8 mA at −7 V, then called RS-485 the "best fit to the
2/5 µA provisional allocation". Both cannot stand, and the review was right
that a switched rail does not by itself answer it: the allocation governs the
parked board with the bus possibly still energized, and the transceiver's own
supply current is not the quantity in question.

**Resolved by removing the transceiver from Rev A.** With nothing populated
there is no bus pin, so there is no off-state bus current to allocate — not a
smaller number, no number. The 2/5 µA reserved for bus and service paths in
`COMPONENT_MARGIN_CLOSURE.md` §5 is returned unspent, and
`check_layout_closure.py` carries the interface row at 0 µA for this header.

The honest statement, in place of the one that was withdrawn: **the off-state
allocation is met by not having the interface. It is unmet for any populated
RS-485 transceiver on this header until the daughterboard's own
disconnection measure is designed and reviewed.**

---

## 2. The provision as drawn

**J3, `Connector_Generic:Conn_01x08` on
`Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical`.** Fitted —
a passive header has no quiescent current and no bus pins, so there is nothing
to gain by leaving it off, and an unpopulated pad row would be harder to use
later.

| Pin | Net | Direction / domain | Note |
|---:|---|---|---|
| 1 | B5 | switched 5 V | daughterboard supply; dies with the board |
| 2 | PGND | — | |
| 3 | P3V3_SW | switched 3V3 from the Pico regulator | logic-level supply |
| 4 | UART1_TX, GP8 | output, 3V3 | offered, not reserved |
| 5 | UART1_RX, GP9 | input, 3V3 | offered, not reserved |
| 6 | BUS_DE, GP10 | output, 3V3 | tied DE//RE, keyless style; **R_DE 10 k to PGND on this board** |
| 7 | SPARE_GP13 | — | offered as an expansion spare or interrupt |
| 8 | PGND | — | second return, for a clean pair with pin 7 |

**Population policy, which is the load-bearing part:**

- **No transceiver, no bias network, no termination resistor is fitted on this
  board.** The keyless R14/R15 bias mismatch its own validation flagged is
  therefore not inherited, and not resolved either — it stays a keyless item.
- **A daughterboard may take power only from pin 1 or pin 3, both switched.**
  There is no always-on rail on this header, by design. Connecting an
  externally powered adapter to J3 breaks the off-state contract of
  `INTERFACE_CONTRACT.md` §8 — *"no externally powered UART/SWD/RO pullup into
  off GPIO"* — and the board cannot prevent that, so it is written here and in
  the schematic note.
- **R_DE is a pulldown, not a pullup**, so the line is defined while the GPIO
  still floats at boot, and nothing feeds an off GPIO. This follows keyless
  practice exactly: default listen.
- GP8, GP9, GP10 and GP13 are **offers**. `REV_A_INTERFACES.md` §1 marks the
  first three as "not reserved until LRA-04 agrees", and LRA-12 does not agree
  on LRA-04's behalf — it routes them to a header so that agreeing later costs
  nothing. A later LRA-04 may reject the pinout; changing it costs one symbol
  and no other part of the board.

**CAN is not provisioned, and `check_layout_closure.py` does not pretend
otherwise.** Full CAN hardware and software is explicitly not required. The
review's R04-REV-5 point stands unanswered because this provision does not
need an answer: there is no controller, no interrupt line and no oscillator to
allocate. If CAN is ever wanted, the pin trade it needs — SPI1 overlapping
GP8/GP9/GP10 and GP28 kept free as the last ADC channel — is named in that
review and is a daughterboard-and-pin-map decision, not a layout one.

---

## 3. Service access

**There is no service UART header.** Capture question Q5 was that J4 could
not be both a "service UART on GP0/GP1" and have those pins stay free.
Resolved by dropping the UART: firmware already builds with
`pico_enable_stdio_usb`, so the **USB CDC console is the service path**, the
same connector `pico-flash` already needs. GP0/GP1 stay free, and the board
gains no externally powered pullup aimed at an off GPIO.

**J4 is the RUN-to-GND reset pair**, shorted with a link for a reset without
cutting power, following keyless J7. Two pins, both connected, nothing left
over.

---

## 4. What this does and does not establish

Establishes:

- A selected, power-off-safe provision with an exact footprint and pinout, so
  layout is not blocked on a bus decision.
- The 2/5 µA bus/service allocation is unspent in Rev A.
- The two LRA-04 contradictions are resolved rather than carried forward.

Does not establish:

- Any bus selection. `D-RA-04` is unchanged: minimal provisioning, no
  implementation chosen.
- Any interoperability with the keyless link, or any protocol.
- That R04-REV-4 (unversioned citations) or R04-REV-6 (reconciling against
  the integrated LRA-03 pin table) are answered. They are LRA-04's, and the
  pin table this header follows is `REV_A_INTERFACES.md` §1 as integrated.
- Anything about the keyless board, which is unchanged and read-only here.

**Disconnected interfaces, listed as the packet asks:** with Rev A populated as
drawn, there is no RS-485, no CAN and no external UART. The data path is Wi-Fi
plus the SD card, exactly as it is today.

> **Required agent attribution:** Follow `logger/coordination/AGENT_ATTRIBUTION.md`
> relative to this project root. Use your own tool, role and verified current
> session ID for Git author and committer identity (`<Tool> <role> [<short-id>]`),
> with per-command settings. End each new commit message with `Agent-Session: <role>`
> and your full tool-specific session-ID trailer. Identify yourself and your
> resume command in new coordination documents and dated updates. If your ID is
> unavailable, say so rather than inventing one.
