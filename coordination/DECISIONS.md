# Owner decisions and statements

Add an entry **as soon as the owner says something that matters**, before
carrying on: date, what was said (quoted where possible), and what it
changes. Newest first. Don't re-ask anything recorded here. Entries before
October 29 evening were carried over from the retired tracker
(`PROJECT_MILESTONES.md`), which has the fuller original text.

## November 11, 2026

**D-CASE-32: add locating studs on the four PCB mounting-hole centers.**
Owner: *"can you create mount points that line up with the pcb mounting
holes, that start wider, raise the board about 1/4 inch from the bottom of
the case, and then narrow to the hole inner diameter so the pcb fits over
the 'studs'"*. Interpret the quarter inch as 6.35 mm above the inside floor.
Use wider support shoulders and smaller locating pins through the Ø3.2 mm
PCB holes; pin fit clearance is an editable modelling allowance. Implemented
with Ø6 mm shoulders, Ø3.0 mm pins (0.2 mm diametral clearance), and 3 mm
pin height including a 0.5 mm lead-in taper to Ø2.4 mm. These diameters and
pin height are agent defaults, not owner measurements.

**D-CASE-31: make a simple case bottom from the extracted outline.** Owner:
*"can you create a simple case bottom from the footprint, with 4mm thick
walls, rounded corners, a little bit of room along the outside perimeter of
the PCB edge."* Agent starting dimensions: 1 mm PCB clearance per side,
4 mm floor, and 12 mm internal wall height, all editable. A plain open tray
is the first model; mounting supports and connector openings await the
physical assembly dimensions. The owner specified the 4 mm wall thickness;
the other dimensions are modelling defaults, not measured fit requirements.

**D-CASE-30: extract the logger PCB geometry for a case model.** Owner:
*"please see /srv/agent_share/accord/logger/hardware/kicad project PCB, see
if you can extract the board footprint to use as the base for making a 3D
case model"*. Use the current PCB outline and actual mounting-hole geometry
as the mechanical reference; this request is for extraction, not fabrication.

**D-DB-29: the outbound leg of the Nov 11 drive lost its first part when the
SD card was knocked out.** Owner: *"the last drive, the SD card was knocked
out in the middle of a trip ... accord_record.html says 231493, but actual is
231,498. I seem to remember a 10.0 mile trip meter before the first stop, and
then I reset it and got 13.0 trip meter for the return trip. The SD was
knocked out towards the end of the ~10.0 mile trip. I see 4.138 mi and 13.066
mi trips, my guess is the 4.138 mi trip was cut short"*. The card shows the
board ran one boot the whole time and its pulse counter never reset. The
first 487 s are in `BOOT_566.CSV` (U_e340f1e0…, clock none), which ends while
moving. The card was missing from ms ~490 s to 860 s, then
`BOOT_860499.CSV` (U_67dec0d5…, card name `20261111_204219.CSV`) kept rows
from 497 s on. Trip 87 was built from that second file alone (zero-based,
16985 pulses, 4.138 mi). The full leg from key-on (ms 4004, ~12:28:03) is
**40909 pulses = 9.967 mi**, which fits the owner's 10.0. Then anchor 9
(231475.904) + 9.967 + 13.066 (trip 88) = **231498.94**, which matches the dash.
Owner, asked whether to apply the fix: *"yes please"*. Trip 87 now starts at 12:28:03,
40909 pulses, 9.967 mi (audit row `trip-stitch`; backup
`accord_maintenance.before_stitch_trip87_20261111_…`). Running tripload by hand
(empty spool) moved the odometer 231493 → **231498** from the pulse chain, with no override.
No anchor was added.

## November 9, 2026

**D-FW-26: the Rev A board's Pico runs a tailored car build.** Owner: *"this
Pico, that USED to be the carport pico, NEEDS to work with the existing server
and firmware I had from the car, so make it happen ... adjust the firmware to
work with this exact pico if needed"*, then, of the three options (fix the
Wi-Fi start-up in the existing firmware, port to the plain SDK, or move the
car's Pico): *"#1 I guess"*. On this Pico W (E66480454F4CA92D) the
arduino-pico core never starts the CYW43, and the first Wi-Fi call freezes the
chip. The build `0.8.1-dev+w43init` is the exact 0.8.1-dev car source plus a
start-up in `networkSetup()`; it joined MG_Wifi at 192.168.60.89 with SNTP.
The VM intake now authorizes both chip IDs. Private build record:
`/srv/agent_share/pcb/build-newpico-20261109/README.md`.
Working at 22:09 (build `0.8.1-dev+w43init.mosi7.sck6.nocorew43`): SD ok,
SNTP, Wi-Fi, upload completed at the receiver. Final SD wiring: CS GP17 and MISO
GP16 via J5, **MOSI on GP7 (Pico pin 10) and SCK on GP6 (Pico pin 9) by wire**;
GP19 is damaged and nothing uses J5 pin 6. The core's own CYW43 start is linked
out (`-Wl,--wrap=init_cyw43_wifi`); its Pico/Pico W guess hung this Pico before
USB at some power-ups. **Rev B:** J5 to the module's real order (3V3, CS, MOSI,
CLK, MISO, GND), MOSI/SCK on GP7/GP6 or fixed.

**D-BUILD-25: Rev A bare boards arrived; the as-built circuit is moving
onto one.** Owner: *"they arrived, and I transferred certain components from
the breadboad to the PCB"*, then: *"never ordered any parts. Transferred
PC817, and the as-built circuit from the breadboard. D106, D107, D105, D104,
R9, R12, U2, R13, R8, R7, D109, R10, R11, then I plan to carry over the
1N5819s for the brake, VSS, and Tach circuits (plus the R3, R4, R5, R6, and
whichever 2 I can use for the VSS circuit)"*. The DigiKey order (D-ORDER-19)
was not placed. Power stays as today: *"I would power with the same USB
cable I use now, and the external buck, and would power off manually"*
(D-POWER-01 continues). Jumpers stand in for unfitted Rev A circuitry:
VSS past U3, and the opto output straight to GP5 in place of the
QUAL_N_REPORT stage. Then: *"yes pico and sd module are going on the board
too"*, so the breadboard logger is being retired in favour of this board.
The module's pin order, read by the owner: *"3V3 GND MISO CS SCK MOSI"*,
which matches J5 pins 1-6, so a straight header fits. **Corrected the same
evening:** after MOSI would not reach the card, the owner re-read the module:
*"The SD module is 1: 3v3 2: CS 3: MOSI 4: CLK 5: SCK 6: GND"*, then: *"the module is in order from 1-6: 3v3, CS, MOSI,
CLK, MISO, GND"*. That does not match J5 (3V3, GND, MISO, CS, SCK, MOSI): on a
straight header the module's GND lands on GP19 and its CS on ground. The
module is to be wired to J5 pin-for-signal instead.
Then: *"pleae backup athe attached picos firmware, and then flash the attached
pico with the accord-logger firmware"*. The attached board was the carport
Pico W (flash id E66480454F4CA92D), not the car's logger
(E6614C311B3A3231). Its flash was backed up (private, outside the repo) and
it now runs the deployed 0.8.1-dev logger build. It has a different Wi-Fi
MAC from the car's Pico, so it will not get the 192.168.60.89 reservation
the upload rules match.

**D-BUILD-27: Rev A board installed in the car; first drive.** Owner, late
November 9: *"i moved the board to the car, and did another test drive.
Feeling pretty pessimistic it actually worked. Never once saw the onboard led
come on or anything."* In this firmware the LED lights only while it counts
VSS pulses on GP2, and an upload window opens only after GP5 reports ignition
on and then off. Nothing reached the receiver after the 22:09 bench upload.
The card held no file from the car. Back on the bench (November 10, 00:14 to
00:36) the Pico booted cold and ran normally whenever powered, logged to the
card and uploaded two files, but dropped off repeatedly while the owner
flicked parts: *"no consistency except the actual usb plug"*. Pico VBUS
(pin 40) is unconnected on Rev A, so the micro-USB socket is the Pico's only
power input. The board's designed bypass is D116 (1N5819 fits) from J3 pin 1
(5 V) to VSYS, with J3 pin 2 ground.

**D-DB-28: last night's unlogged drive entered by hand; the board logged this
morning.** Owner, November 10: *"there is a procedure to manually add miles
not caught by the logger, which now needs to be done since the test drive last
night didnt catch the 0.5 miles and 231469 odometer. that manual trip was
followed by a short test drive this morning."* Done per honda/OWNER_READINGS.md
and the trip 26 precedent: manual trip 80 (0.5 mi, 0 pulses, window bounds
22:22-23:57 PST November 9) and dash anchor 8 (231469 at 23:57, default +0.5).
The anchor also absorbs the November 8-9 old-Pico drives (11.213 mi) that never
reached the database. The morning drive is trip 79 (0.925 mi, 3,796 pulses),
the Rev A board's first logged and uploaded car trip; VSS, tach, IGN, brake and
fuel all read. The database odometer is 231470. Then: *"so should you add the missing trips
and have the odo calculate itself from the data + manual entries"* (kept the
dash reading as the baseline, explained), and *"ok pleass make sure trips are
reconciled and everything is up to date"*: the rest of the old Pico's
`U_c81d3a06...` (card copy, SHA-256 verified, server prefix byte-identical) was
sent through the receiver from byte 5,853,006 and completed. Trips 81-84
(Nov 8-9, 11.212 mi) loaded; 84 trips. The logged chain from anchor 7 plus the
0.5 manual mile gives [231469.141, 231469.417), matching the dash. Owner, about 08:28: *"latest trip
calibration: after 2.9 on trip meter -> 231473 odo; trip meter reset, then at
0.7 miles, shortly rolled over to 0.8 on trip meter the odo was 231474, and
final reading is 231475 on dash with 2.6 on trip meter, accord database is
showing 231476"*. Trips 85/86 match both trip meters; the rollover solves the
car at 231475.85-231475.95 (honda/OWNER_READINGS.md). The DB's 231476 comes from
anchor 8's +0.5 midpoint default. Owner: *"yes apply it"*. Applied:
solved anchor 9 (231475, [231475.854, 231475.954)) and odo_correct to 231475;
the page shows 231475. Owner: *"did rebuilding database remove manual fuel
entry, i thought there was amother 7th entry"*. It was never entered: the
October 26 fill (8.414 gal, Trip B 179.7, about 231301) sat in
pcb/coordination/reviews/EVENING_TRIPS_2026-10-26.md, deferred to a fuel update
that never ran. Owner: *"i just added the receipt to
/srv/agent_share/honda/receipts/"* (Chevron, 2026-10-26 19:47:12, 8.414 gal at
$6.359, $53.50). Added as fuel_entry 7 with purchase 117; 21.36 mpg.

## October 31, 2026

**D-DRC-24: the 11 remaining DRC items are accepted and excluded.** Asked
which to ignore, the owner chose to exclude all of them: the Pico W
footprint's two paste-only pads in its RF keepout, J1's silkscreen at the
edge it overhangs (D-CONN-23), the U1/J5 library-metadata warnings, the
U7 and U3 silkscreen ticks on their own pads, and the single-spoke thermal
connections at U7 pin 2 and U13 pin 7 (connected).

**D-CONN-23: J1 overhangs the board edge on purpose.** At the silkscreen
review the owner said: *"J1 I want to hang off the board a little"*. Its
silkscreen outline beyond the edge is accepted.

**D-TP-22: TP11 and TP19 removed.** Owner, during the silkscreen pass:
*"I removed TP11 and TP19, please update the silscreen list based on the
revisions I just did"*. TP11 (QUAL_N_REPORT, GP5) and TP19 (HOLD_RAW,
GP6) leave the board; the schematic, BOM and checks follow.

**D-SD-21: J5 on the back is intentional.** Asked at the pre-order check
whether the SD header on the underside was meant (the module hangs below
the board), the owner said: *"J5 on back was intentional"*. Also: *"silkscreen
pass incoming before fab files and ordering"*.

**D-CQUAL-20: C3 is the WIMA MKS2 on a 5.5 mm-wide footprint.** Told the
chosen 1 uF 5 % 63 V film (WIMA MKS2C041001F00JSSD, 7.2 x 5 x 10 mm) does
not fit the 2.5 mm-wide C_Rect footprint, the owner said: *"yes change
C3's footprint"*. Footprint becomes C_Rect_L7.2mm_W5.5mm_P5.00mm; the
owner re-places it (it meets R14/R15 pin 2 and TP12 where it sits).

**D-ORDER-19: DigiKey order scope.** Owner: *"if no parts are likely to
change id like to come up with a digikey order file containing the BOM"*.
Answers: one board plus spares (cheap passives rounded up to DigiKey's
10-piece break, one spare of each cheap IC or transistor); order
everything fresh, nothing taken from inventory; include the JAE mating
housing and contacts, the 1 A inline fuse and holder, jumper shunts and a
BR2032 cell.

**D-ENVELOPE-02: board 120 x 83 mm.** Found at the final placement review:
the owner made the board 3 mm taller at the top (80 -> 83 mm) and moved
H1/H3 to y 60.96. Reported to the owner, who carried on without
objection; supersedes the 80 x 120 mm of D-ENVELOPE-01.

**D-CCLK-18: C15 may go through-hole.** Asked how far C15 can sit from U7,
then whether it could use a through-hole footprint, the owner said:
*"confirm and if it works, swap it in and I'll update from schematic"*.
Candidate: KYOCERA AVX TAP336K016SCS (33 uF +/-10 %, 16 V, dipped radial
tantalum, 6 x 10 mm, 2.5 mm pitch), subject to its datasheet meeting the
CCLK budget in COMPONENT_MARGIN_CLOSURE (22-60 uF effective; leakage
within the 66.25 uA hot reserve).

**D-SMD-17: no more test points; the remaining resistors are surface
mount.** Owner, during the cutoff-timer steps: *"at this point all
unplaced test points need to go. All remaining resistors should be surface
mount. please review before I carry on"*. Applies to the parts not yet
placed on the board; placed parts keep their footprints (no backtracking).

**D-HDR-16: GP11 and GP12 move from test pads to J3.** Owner, after
placing the qualifier steps: *"I removed GP12 and GP11 test points, would
prefer to change J3 to a 6 pin header, either 1x06 or 2x03, and include
them there instead"*. TP24 (SPARE_GP11) and TP25 (SPARE_GP12) are off the
board; J3 (now 1x04: B5, PGND, P3V3_SW, SPARE_GP13) becomes a 6-pin header
carrying SPARE_GP11 and SPARE_GP12 as well. Schematic, BOM, checks and
the `headers` step follow. Offered 1x06 or 2x03 (a 1x06 reaches H4 and
the antenna strip, or R21), the owner chose: *"2x03 please"*. Pins 1-4
keep B5, PGND, P3V3_SW, SPARE_GP13; 5 SPARE_GP12, 6 SPARE_GP11. After
routing it the owner had pins 3 and 4 the other way round: *"keep my
routing, I swapped the GP13 and 3v3 pins for ease of routing"*. Final
J3: 1 B5, 2 PGND, 3 SPARE_GP13, 4 P3V3_SW, 5 SPARE_GP12, 6 SPARE_GP11.

## October 30, 2026

**D-THT-15: through-hole resistors and 1N5819 from the vehicle inputs
on.** Owner, at the in_tach step: *"ok here I want to start using
Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal and 1N5819 not
1N5819HW, despite my earlier request to convert a bunch of things to surface
mount"*. Applied to every surface-mount resistor not yet placed (R1-R29,
R38-R46 less the through-hole ones already there: 37 parts) and every
1N5819HW (D101-D107, D109: 8 parts), including the in_tach parts already on
the board. The diodes go back to the pre-D-SMD-09 footprint,
DO-41 vertical P5.08 (as D116). Kept: the placed RTC pull-ups R50-R52
(0805), the D-THT-13 power resistors, R13/R32 (DIN0414, 0.5 W positions),
R30/R47-R49 (DIN0207, keyless). R22 R_AON needs >= 0.15 W at 85 C: a
0.25 W DIN0204 derates to about 0.2 W there, so it qualifies. Capacitors,
transistors, D110 (1N4148W) and the ICs stay surface mount.

**D-STAGE-11 revised: small ordered steps, not subsystem chunks.** After
importing the 39-part timer batch the owner removed it from the board:
*"I removed the timer and clock hardware for now. Too many pieces at once
all tangled together, I need a structured logical way to add small groups
of components at a time"*. `board_chunks.py` now holds an ordered list of
small steps (2-10 parts), each one a single function that connects to parts
already placed, each with its test points and a placement note;
`board_chunks.py next` switches on the next step. Flags reset to match the
board: power, pico, sd and connector on, everything else off.

**D-RTC-14: DS3231 chip on the board, not the module.** Offered a soldered
DS3231SN (SOIC-16W) with a coin-cell holder, or the stocked DS3231 +
AT24C32 module on a header, the owner said: *"go with the DS3231 chip"*.
The module was turned down for its LIR2032 charging circuit (unsafe with a
CR2032), power LED, size and header mounting. Recommended cell: BR2032
(rated to +85 °C) rather than CR2032. New schematic chunk `rtc`; needs
ordering and a firmware change.
Same message: *"yes push it"*, covering the 13 commits then on `main`.

**D-THT-13: power-block resistors back to through-hole.** Owner: *"R31, R32,
R33, R34, R35, R36, R37: I would like to use through hole after all. I have
small thorugh hole footprints, R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal,
let me know if any of these resistors need to be a specific rating"*. R31 and
R33-R37 move to that footprint. **R32 (RG) stays on its 0.5 W DIN0414**: a
shorted gate zener puts 0.26 W in it, beyond a 0204. R33 (RI) dissipates
0.11 W at a sustained 17.1 V, so it needs >= 0.25 W (0.4 W preferred). The
rest are under 30 mW; none is precision, and R37 stays exactly 1 k for the
B5 decay test.
Then: *"what about Q6 and Q7 do I have through hole equiv. in inventory"* and
*"switch to the 2N3904s"*. QI (Q6) and QH (Q7) go back to through-hole
2N3904 on TO-92_Inline, using the two in the CmpE 110 kit. The symbol was
changed, not just the footprint, because TO-92 numbers the pins E-B-C and
SOT-23 B-E-C. A 2N2222A (40 V) may substitute; a plain 2N2222 (30 V) or the
S9013H (25 V) may not, because the hot entry clamp reaches 29.2 V. QRESET and
QMON stay MMBT3904.

**D-FP-12: LM2678 footprint matches keyless.** Owner: *"trying to change
Package_TO_SOT_THT:TO-220-7_P2.54x3.7mm_StaggerEven_Lead3.8mm_Vertical to
...StaggerOdd... I think thats the one used for hondaPico/accord-keyless"*.
Confirmed: keyless U3 uses StaggerOdd. U6 switched in the schematic, BOM and
board (position, rotation, nets and schematic link kept); check_capture
now asserts UREG's footprint equals keyless U3's.

**D-STAGE-11: build the board up by subsystem.** Owner: *"I think I want to
remove everything except buck converter related components, and add chunks
of components by subsystem as I go"*, then *"leave only U1, J5, J1, the
mounting holes, and the buck / power block related components"*. The
schematic stays complete; every other symbol is marked "Exclude from board"
and its footprint removed, and chunks are switched back on as the owner asks
(chunk list in `logger/hardware/kicad/tools/board_chunks.py`).

**D-FUSE-10: no fuse on the board.** Owner: *"remove the fuse from the
circuit and the board, I will use an inline fuse in the harness"*. F1 and
its holder are removed; BATT_IN connects straight to the reverse-block
diode DREV. The harness inline fuse now does both jobs F1 and the
feed-source fuse shared: protecting the wire, and clearing a sustained
overvoltage before the entry clamp fails (D-OVERVOLT-04), so it should
stay at the 1 A rating the clamp analysis assumed and sit at the feed end.

## October 29, 2026

**D-SMD-09: convert to surface mount for space.** Owner: *"are we able to
look into surface mount components, resistor arrays, transistor arrays, or
other combined chips that could save boards space. it looks too tight to
me"*, then *"start with the conversion"*. Passives, logic ICs, small
transistors, small diodes and signal test points move to SMD (SOIC, not
TSSOP, for hand soldering). This supersedes the earlier through-hole
preference recorded in LAYOUT_CLOSURE §8. The TPL5111-class timer
replacing the cutoff oscillator and counters is **deferred**, to be
considered after the conversion.

**D-LAYOUT-08: commit the owner's layout as it goes.** Owner: *"yes commit
as I go"*. When the owner reports layout progress, commit
`accord-logger.kicad_pcb` / `.kicad_pro` with the owner as author
(`Jayson Gazeley <jayson@sjsu>`, the configured identity) and the agent as
committer, then push. Never run `kicad-cli pcb drc` in the shared checkout
(it rewrites the `.kicad_pro`); inspect read-only with `pcbnew.LoadBoard`.

**D-CONN-06 revised: JAE IL-AG5-14P-D3L2-A instead of the 10-pin Molex.**
Asked whether ten pins was "JUST enough", the owner said: *"in the hondaPico
kicad they added IL-AG5-22P I believe. Can you add IL-AG5-14P-D3L2-A?"* The
14-pin JAE (Honda's connector style, already on keyless as the 22P) becomes
the single board connector J1, giving four spare contacts over the ten
signals. Used as: 1 RS-485 A, 2 bus GND (PGND), 3 B2 VSS, 4 B1 tach, 5 B11, 6 BATT_IN / 7 RS-485 B, 8 spare, 9 C11 fuel, 10 AGND (B16), 11 spare, 12 spare, 13 C14 brake, 14 PGND. Pin numbering follows the keyless 22P
convention and must be checked against the housing cavity numbers before
crimping. The board end of the harness needs housing IL-AG5-14S-D3C1-A,
IL-AG5-C1-5000 crimps and the CT150-1-AG5 hand tool.

**D-CONN-06, first choice (superseded by the JAE 14P above): the 10-pin Molex.** Owner: *"/srv/agent_share/pcb/old_hondaPCB/footprints.pretty/CON_39301100.kicad_mod
is the 10 pin molex connector I have"*. That is **Molex 39-30-1100**
(Mini-Fit Jr 5569-10A2, 2×5, right-angle, pegs), the same family as keyless
J1. It becomes the **single board connector**, replacing J1 (power), J2
(signals) and the interim RS-485 connector. Footprint: KiCad standard
`Molex_Mini-Fit_Jr_5569-10A2_2x05_P4.20mm_Horizontal`. Geometry checked
identical to the owner's file (1.8 mm drills, 4.2 mm pitch, 5.5 mm rows,
3.0 mm pegs), just drawn rotated 180° with smaller pads. All ten pins used;
the RS-485 ground shares PGND.

**D-PROCESS-07: one agent, no multi-agent process.** Owner: *"I might as
well have just opened one agent, have them use git and just go. So many
little details and nuances keep getting missed."* The manager/specialist/
packet arrangement is retired; see `AGENTS.md`.

**D-CONN-06: single connector.** Owner, 19:11 UTC (told to the previous
manager, recorded late): *"ultimately I may want to feed the logger from a
constant 12V+ battery feed from the car like hondaPico/accord-keyless, the aux
battery feed is not permanent. In which case I would want a single connector.
For hondaPico I used a 16-pin molex connector, I also added a
JAE_IL-AG5-22P-D3L2 to hondapIco as an experiment, which appears to be the
same style of connector honda uses. I have a 10 pin molex style right angle
connector similar to hondaPicos 16 pin connector in stock. Digikey carries
IL-AG5-14P-D3L2-A which is 14 pins. I haven't determined if the molex versus
the JAE connectors have any particular benefit besides personal preference
and factory styling."* Ten signals are needed: BATT, PGND, B2, B1, C14,
C11, B11, AGND, RS-485 A, B. A separate bus ground makes 11.
**Pending:** owner choice (10-pin in stock, part number to confirm, or
JAE 14P).

**D-RS485-05: keyless RS-485 onboard.** Owner: *"yes, it should be like
keyless, same footprint, same circuit (should be flexible for unknown
topology with RS-485), the keyless/hondaPico was the template for the working
buck converter, car inputs, the RS-485 etc."* MAX3485 in a socketed DIP-8, GP8
TX, GP9 RX, GP10 tied DE//RE with a 10 k pulldown, bias pair and 120 Ω
termination each on jumpers (open by default). Replaces LRA-12's passive
header. The LRA-04 bus comparison is closed for Rev A. Bias value: keyless
schematic says 270 Ω, its PCB 390 Ω; 390 Ω used unless the owner says
otherwise.

**D-OVERVOLT-04: defer sustained overvoltage.** Owner chose "3": accept the
1.5KE20A entry clamp's limit for Rev A and carry it as a vehicle-test risk.
Any sustained P12 above 17.1 V (24 V jump start, alternator overcharge)
overheats the clamp before the 1 A fuse clears. Until resolved, jump start
only from a 12 V source. A series overvoltage cutoff is the option for a
later revision. LRA-12R kept the 1.5KE20A by stated choice (the 1.5KE30A
would need a new A5 protection stage and 60 V driver transistors, and would
leave the LM2678 1.19 V under its 45 V absolute limit).

**L07 parked-current re-allocation accepted** (manager, within the owner's
unchanged 100 µA at 20–30 °C and 500 µA at 85 °C whole-system targets).

**D-REUSE-02: reuse keyless circuitry by default.** The logger board largely
reuses the working keyless/hondaPico circuitry, adding IGN sense, power hold
and automatic shutoff. Change an inherited block only for a concrete reason
in the logger's loads, connections or power-off behaviour. This supersedes
the earlier "copy no circuit" instruction. Board files stay separate.

**D-POWER-03: the power front end is not new work.** Keyless already runs
it on a permanent 12 V body-harness feed in this car, through cranking:
LM2678T-5.0, 1.5KE30A (logger now uses 1.5KE20A, see D-OVERVOLT-04),
820 µF/16 V out, 100 µF/50 V in, 22 µH, Schottky catch and reverse diodes.
Keyless also has seven P6KE30A on its harness lines; the owner has four
P6KE30A on hand. Both connector families (Molex Mini-Fit Jr 16P, JAE IL-AG5
22P) are in service on keyless in this car.

**D-ENVELOPE-01: board size.** Generic rectangle, **80 × 120 mm**, no
enclosure, no mounting method chosen (behind-the-cluster mounting set
aside). Carries the Pico, the SD module (16 × 16 mm plus a 1×6 2.54 mm
header) and the rest. Corner mounting holes, generic.

**D-OFFSTATE-01: parked measurements, key out, to chassis.** Configuration:
dividers, clamps, Pico and SD all seated, Pico unpowered, USB off.
B2 (VSS) 4.140 V loaded, **4.669 V** open-circuit; B1 (tach) 0 V; C11 (fuel)
0 V; C14 and B11 dead with the key out. At the B2 22k/33k junction
1.042 V; clamp cathodes 0.883 V. So B2 is held up through about 3,757 Ω
and draws about 140.8 µA, of which about 109 µA back-feeds the unpowered
Pico 3V3 through a clamp. B2 is the only branch live while parked and needs
isolation (now the ASSR-601JV). **Don't re-ask these readings.**

**D-KEYLESS-485-01: keyless RS-485 is proven.** The keyless MAX3485 is
fitted in a socket, and the link was tested extensively from the Pi 4 with
`./hp out lock pulse`, `./hp io` and `./hp status` (tooling at
`/srv/agent_share/pcb/benchlink/`). Old firmware comments saying "no MAX3485
fitted" were stale and have been corrected.

**D-INVENTORY-01: inventory.** Primary list:
`/srv/agent_share/inventory/inventory_list.md`. Mostly accurate, incomplete,
may include consumed parts; plus four P6KE30A not on it. Reconcile during
parts discussion. Stock doesn't make a part suitable. Keep the list private.

## October 28, 2026 and earlier

**D-REUSE-01:** consult keyless before designing an equivalent logger
block. Use its KiCad conventions (project-relative library tables, one
project `Custom` symbol library, a project `.pretty`, test-point and reset
header patterns, `kicad-cli` validation). The logger is its own project at
`logger/hardware/kicad/accord-logger.*`.

**D-ASBUILT-01:** the logger already has a physical as-built circuit;
`logger/hardware/as-built/` is its record. Keep fitted wiring, keyless
examples and the new power design distinct.

**D-POWER-02:** continue the existing `9527a14` power circuit; new
investigation only for identified gaps.

**D-RA-01:** prioritize integrated-power Rev A. Fuel curve, dashboard and
future-network work do not gate it.

**D-RA-02:** prototype order, assembled-board bring-up and unattended
vehicle approval are separate gates.

**D-RA-03:** use the qualified-IGN/deadline contract
(`logger/hardware/power/INTERFACE_CONTRACT.md`, `FIRMWARE_REVIEW.md`); never
mix it with the old raw-GP5/100 ms rules.

**D-REPO-01:** `jgazeley/accord` is authoritative; `accord-logger` is
historical. Recover material selectively with provenance; private deployment
data stays private.

**D-DATA-01:** SD raw evidence → canonical converter/trip engine; the public
service stops at trip JSON. The guarded private DB intake is separate.

**D-POWER-01 (interim, still current until Rev A):** manual buck power and
time sync before departure. Automatic cutoff is the Rev A goal.
