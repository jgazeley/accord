# Rev A build log: board 1 (in the car) and board 2 (new build)

Claude pcb-manager, November 24, 2026 (D-BUILD-39). Five boards from JLCPCB:
board 1 is in the car, board 2 is this build, three are spare. Nets, pads and
pin numbers were read from `kicad/accord-logger.kicad_pcb`. Expected values
marked (est.) are estimates, not datasheet limits. Nothing in the Result
columns has been measured yet.

## Board 1: the baseline

Sources: D-BUILD-25, D-BUILD-27, D-FW-26 and the owner's November 9 messages
("ok soldered everything"). Reported, not inspected.

| Function | Fitted |
|---|---|
| Fuel and supply ADC | R7-R12, D104-D107, C1, C2 (the 1 uF caps were specified; fitting not separately confirmed) |
| Ignition opto | D109, R13, U2, 100 nF in C18 (specified; not separately confirmed) |
| Tach, brake | R3-R6, D102, D103 |
| VSS | R1, R2, D101 |
| Pico W | soldered to U1, powered by its own USB socket (VBUS is not connected on Rev A) |

| Jumper | From | To | Stands in for |
|---|---|---|---|
| 1 | J1 pin 3 | R1 pin 1 | U3 (VSS isolation) |
| 2 | R14 pin 1 | R14 pin 2 | opto emitter to ground |
| 3 | TP9 | R21 pin 2 (R21 empty) | opto collector to GP5, in place of the qualifier |
| 4, only if needed | J1 pin 10 | J1 pin 2 | not recorded whether it was needed |

SD module, module order 3V3 CS MOSI CLK MISO GND (not J5's order): CS GP17 and
MISO GP16 through J5, MOSI by wire to GP7 (Pico pin 10), SCK by wire to GP6
(pin 9). GP19 on that Pico is damaged.

Do not carry over to board 2:
- **SD on GP6/GP7.** On Rev A, GP6 is HOLD and GP7 is ISO_EN. Use GP18 (SCK)
  and GP19 (MOSI), wired signal-for-signal to J5. The firmware build must match.
- **Jumpers 2 and 3 with A5 parts.** TP9 is the A5 rail; with the A5 regulator
  fitted they put 5 V on GP5. Remove them before that layer.

## Board 2: stage 1, 12 V in to 5 V rail

**Polarity rule, checked by net on every diode below: the band goes in pad 1,
the square-cornered pad. Electrolytic + also goes in pad 1. Ignore silkscreen
letters.** A backwards TVS burned a trace on the keyless board.

Connections: **J1 pin 6 = +12 V (BATT_IN)**, **J1 pin 14 = ground**. Check by
continuity before applying power: pin 6 to D112's round pad, pin 14 to TP21.
Check housing cavity numbers the same way before crimping.

Leave out for all of stage 1: **U1 (Pico), R22 (keeps the A5 supply off), D113
until step 5, Q6 until step 6, D116 until step 7.**
Source: current-limited, fused, or both. Do not use a bare battery or the car.

**Progress, November 25 (owner):** everything for stage 1 is soldered except C9,
C11, C12 and C13, so the parts were not added step by step. Skip the Q6 wire
link; use 12 V on J1 pin 5 wherever a step says "link". Check D113 (step 5)
unpowered first. Do not turn the buck on without C12. Later the same day the owner
fitted C11, C12 and C13; C9 is still off. No readings yet.

| Step | Fit | Do | Expect | Result |
|---|---|---|---|---|
| 1 | J1, D112, C9 (back) | 12 V, limit 0.1 A | TP1 about 11.5-11.9 V; no current to speak of | Nov 25, M12 battery via fuse: 12.0 V after the fuse, TP1 11.92 V. Pass |
| 2 | Q5, D114, R31 10k, R32 1k 1/2 W, R36 10k | 12 V, no link | TP2 (gate) = TP1; TP3 about 0 V | Nov 25, pin 5 open: TP2 11.91 V, TP3 0, TP5 0. Pass |
| 2b | wire link across Q6's two OUTER holes (pads 1 and 3, Q6 empty) | 12 V | TP2 about 1-2.5 V (est.); TP3 within 0.1 V of TP1; link off, TP3 falls to 0 | |
| 3 | U6, C10, C11 (back), C12 (back), D115, L1, C13 (back), C14, R37 1k | unpowered: ohms TP5 to TP21 | about 1k or somewhat lower, never near 0 | |
| 3b | link fitted | 12 V, limit 0.25 A, raise toward 1 A only if it trips at startup | TP5 4.90-5.10 V (limits 4.75-5.25 V); tens of mA input (est.) | |
| 4 | - | load TP5 with 100 ohm 1/2 W: one (50 mA), four in parallel (200 mA), ten (500 mA) | TP5 stays 4.75-5.25 V; ripple 100 mVpp or less; U6, L1, D115 not too hot to touch | |
| 5 | D113, band in pad 1 | unpowered: TP1 to TP21, then repeat 3b | diode drop one way only; input current unchanged | |
| 6 | remove link; Q6, R33 2.2k, R34 100k, D109 | 12 V on J1 pin 6; then also on J1 pin 5 | off with pin 5 open, on with 12 V on pin 5, off again when removed | |
| 7 | D116 | 12 V, on | TP6 about 0.3-0.8 V below TP5, meter load only (est.) | |

Stop at any step that misses. After step 7: Pico, then the baseline inputs with
jumpers 1-3, then one logic layer at a time. Remove jumpers 2 and 3 before A5.

Ground the scope only at PGND (TP21/TP22). Read gate-source voltage as TP2
minus TP1 on the meter.

Every stage 1 part is on the November 17 order or in stock; nothing on the
supplemental order is needed for it.
