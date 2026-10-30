# Owner decisions and statements

Add an entry **as soon as the owner says something that matters**, before
carrying on: date, what was said (quoted where possible), and what it
changes. Newest first. Don't re-ask anything recorded here. Entries before
October 29 evening were carried over from the retired tracker
(`PROJECT_MILESTONES.md`), which has the fuller original text.

## October 30, 2026

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
