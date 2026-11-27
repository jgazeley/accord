# Owner decisions and statements

Add an entry **as soon as the owner says something that matters**, before
carrying on: date, what was said (quoted where possible), and what it
changes. Newest first. Don't re-ask anything recorded here. Entries before
October 29 evening were carried over from the retired tracker
(`PROJECT_MILESTONES.md`), which has the fuller original text.

## November 27, 2026

**D-CASE-41: interrupt the lid's inner lip above the SD window.** Owner:
*"I would like the top to leave a "gap" in that same area, where the top
half does not extend below the very top edge of the bottom half. This means
the small thin inner pieces"*. Remove the downward-projecting alignment
skirt across the SD window's width, stopping the lid at the Z=16 mm seam
there. Preserve the already printed bottom, clips and raised roof.

**D-CASE-40: bottom printed; more component headroom needed before printing lid.**
Owner: *"I printed the bottom, now I am going to print the top, but first I
can field measure the tallest components on the PCB to make sure the top
has enough room without touching the components"*. After being told the
current ceiling is 18.225 mm above the PCB, owner estimated:
*"I think it will need 25 - 30 mm"*. This is an estimate, not a confirmed
component measurement. Preserve compatibility with the already printed
bottom. Asked to distinguish component height from desired clear space,
owner clarified: *"tallest component looks about 20 mm its hard to measure
directly"*. Use 25 mm PCB-to-ceiling clearance as the modelling choice,
providing about 5 mm over that estimate. Raise the lid roof and upper walls;
retain the original seam, alignment skirt, clip positions and JAE aperture.

## November 25, 2026

**D-BUILD-39 progress: stage 1 soldered except the small caps.** Owner: *"i have
everything from the table above soldered except the small caps, was wondering if
there is enough to test the 5V rail"*. The table is the stage 1 parts list, so
C9, C11, C12 and C13 are off. Nothing has been powered or measured yet.
- The Q6 wire-link steps no longer apply: Q6, R33, R34 and D109 are on, so 12 V
  on J1 pin 5 turns the buck on.
- Then: *"ok C11, 12 and 13 are soldered"*. C9 is still off.
- 12 V source: *"ill use an m12 milwaukee battery with a fuse"*. That's 3 Li-ion cells,
  about 12.0-12.6 V charged, with no current limit. Advised a 100 ohm series
  resistor until the unloaded 5 V check passes.
- First reading: *"battery reads 12.0 at fuse blade (after fuse filament), TP1 is
  11.92"*.
- Pin 5 open: *"TP2 11.91, TP3 0, TP5 0"*.
- J1 pins 5 and 6 jumpered (ignition on): *"4.974 at tp5"*. The buck runs.
- Then: *"TP3 11.68, TP6 4.673, 1.508 at tp2"*.
- Then: *"TP1 is 11.67 with the buck on"*.
- Jumper pulled: *"ign off, tp5 0.006 after a couple seconds"*.
- Owner: *"i didnt do the 100 ohm series resistor or any load testing yet."* So
  every reading above was straight from the battery through the fuse. The series
  resistor is no longer needed: the unloaded checks passed.
- Owner: *"i might just solder the pico and skip the in depth test."* The load
  steps are optional now. Not done: load regulation, ripple, heat under load.
- Stage 2, the board 1 baseline. Owner: *"before i do that, id like a list for
  R3-R9, D104,D105,D101,D102, D103, R13, R7, R8, R1, R2, C18, C2, D106, D107, C1,
  R10, R11. and note that this is a new board so the sd card connections should
  be the original design and not the version i needed to move some wires due to
  a damaged pico pin or two. im basically adding all the parts to get the basic
  circuit working, but with the battery 12V. i can manually disconnect and later
  add the logic chips for the automatic shutoff"*.
  - SD goes to J5 as designed: GP16 MISO, GP17 CS, GP18 SCK, GP19 MOSI. These are
    the defaults in `logger_sd.cpp`. Not GP6/GP7.
  - Also needed but not on the owner's list: R12 (the supply ADC series
    resistor), U2 PC817, and jumpers 1-3.
  - R2 (33k) is not in the Digi-Key order. Use the 1/4 W 33k from the CmpE 110 kit.
- Firmware for board 2. Owner: *"what about just for me to attach for you to
  flash the pico"*, *"pico is plugged in"*, and *"side note pico should be brand
  new so whatever data on it is either sketchy or worth double checking out of
  curiosity"*. The Pico held Raspberry Pi's factory production test. Built
  `0.8.1-dev+w43init.nocorew43.board2` (board 1's build with SD SCK/MOSI on
  GP18/GP19); not flashed yet. Private record:
  `/srv/agent_share/pcb/build-board2-20261125/README.md`.
- Owner: *"go ahead and flash new pico with accord firmware, but make sure its
  set for the original pinout without the damaged pins"*. Flashed with
  pico-flash (`OK: new firmware running`). The build has SD on GP16 MISO, GP17 CS,
  GP18 SCK and GP19 MOSI. Chip E6642815E3477A23. Wi-Fi is up at 192.168.60.74,
  SNTP is synced, and SD shows no-card. It is not yet in the VM intake's unit
  list.
- Owner: *"yes add it, and i want to add tge sd card and see if it can read
  it."* Then: *"Add the new pico to the database. In fact it can replace the old
  one unless something goes wrong and we need to revert back for some reason."*
  Added E6642815E3477A23 to the VM intake's `units`
  (`policy.json.bak-pre-unit3-20261125`). The older units stay listed so a revert
  needs no change.
- Owner's plan: *"Once it seems like everything that you can think of to test
  what the current configuration which is the Pico SD card, the inputs and stuff
  that I mentioned earlier for the prototype and Buck converter. And then before
  placing back in the car, I know I have to put the jumpers in a few spots. At
  that point I can test it in the car or solder u16 and associated circuitry so
  that you can test if the Pico can talk to the IC. I'm aware that the battery is
  not attached yet, so the time will not survive power loss."*
- SD card on board 2. Owner: *"i mean the old card not "new card", the existing
  card with exisitng trip data. i hust attached the 16 gb card witb existing trip
  data that was briefly attached to the new pico. please just prepare it for tge
  new pico. the sd module is already wired"*. Copied every file read-only to
  `/srv/agent_share/pcb/sdtools/cards/20261125_16gb_before_board2/` (with
  SHA-256 list). **The SD card works on board 2:** during the brief insert the new
  Pico wrote `20261126_025629.CSV`, with header chip E6642815E3477A23, fw `…board2`,
  `clock=sntp`, and 31 s of rows. Today's drive is in `20261125_194132.CSV` and
  `20261125_200411.CSV`.
- Power in the car. Owner: *"im going to just unplug J1 after awhile"*. So the
  buck has to stay on with pin 5 low: link Q6 collector to emitter (pads 3 and 1).
  Pin 5 is then only the ignition sense, and key-off opens the upload window.
- Harness grounds. Owner: *"I have the GND from the gauge cluster going there"*
  (cluster B16 to J1 pin 10, AGND), then: *"ok so I can use a ring terminal and
  bolt to chassis? (checked with DMM to make sure its a good ground)"*. J1 pin 14
  (PGND) goes by its own wire to a chassis bolt, so the buck's return current
  does not flow through the Pico's AGND. Pin 6 BATT_IN is still to be found
  (measure key-out), with a 1 A fuse at the tap.
- Owner: *"do we know if there is a constant 12V+ on the A B or C connector for
  the gauge cluster to tap for J1"*. From the 1998-2002 Accord service manual
  (`/srv/agent_share/obdii/`, gauges circuit diagram '00-02, p. 22-64/65): **gauge
  assembly B21, WHT/YEL**, comes from the passenger's under-dash fuse No. 13
  (7.5 A). The PCM terminal table gives that fuse's WHT/YEL as "Back-up power
  supply, Always battery voltage". The same fuse also feeds PCM memory, the heater
  panel, the security indicator and the multiplex unit, so the 1 A inline fuse at
  the tap matters. Not yet measured in the car: B21 to B16 with the key out should
  read battery voltage.

**Set aside for a quiet time: the Nov 25 drive.** Owner: *"today I spaced out
and unplugged the Pico after stopping. I noted the time that I started the car
which would have been only maybe a minute or so after turning the ignition on
... I'm hoping that it caught the time when I arrived back home for you to piece
together the trip. I also took a picture of the mileage and odometer at the stop
where I unplug the pico. Please don't worry about that right now ... next time
... when it is quiet. Freshen the odometer and fix that trip."* The owner has the
start time and a photo of the odometer at the stop. Not yet checked whether
any of the drive reached the receiver.

**Board 2 first road test.** Owner: *"ok I went for a test ride, noted the
odometer before and after, note from earlier: 12:36:03 pm I started the car, did
the ignition ~:30 - 1 minute earlier. PLease report once/if the Pico uploads over
the wifi, the fuel state, the brake state, the trip overview, the top speed seen,
etc. Only indication I have anything worked was the green light on the pico came
on when moving around. The car was at Trip 10.0 mi, 231617 when I noted the dash
after unplugging, it was 10.2 mi when odometer was 231628 before I left, new trip
I will leave to you to read if it uploaded, and current odometer"*. The 12:36:03
start and the 10.0 mi / 231617 reading belong to the earlier Nov 25 drive; the
10.2 mi / 231628 reading is the dash before this test ride.

Receiver check at 22:40 PST: no request from the new Pico (E6642815E3477A23)
has reached the receiver, and nothing from 192.168.60.74 at all. The forwarding
still admits only .89. The test ride is on the SD card only. The earlier Nov 25
drive did stream live from board 1's Pico (E66480454F4CA92D) until 13:27 PST.

Owner: *"ok sd card attached first"*. The ride is `20261126_061003.CSV`
(copied read-only to `pcb/sdtools/cards/20261125_board2_roadtest/`).
- Key on 22:18:20 PST, engine 22:18:49, key off 22:19:47. Key on again
  22:21:11, engine 22:21:15, moving 22:21:23 to 22:33:28, key off 22:33:30.
  Logged on battery power until J1 was unplugged at 22:42:13.
- VSS: 6.30 mi, so the dash should read about trip 16.5 / 231634. Top speed
  70.2 mph at 22:29:03. Max 3810 rpm. 7 brake presses.
- Brake: the column reads 0 while the speed is falling (mean -3.2 Hz per 2 s vs
  +0.3), the same as board 1. So 0 is pedal down, despite the
  "line-grounded" label.
- Supply: 11.92 V at key-on, 13.61 V running. Board 1's Nov 25 drive read a
  saturated 4095 for supply and fuel, so board 2 is the first with real analog.
- Fuel: 1.07 V at key-on, 1.32 V running (counts 539 to 737, p10 to p90). No
  calibration curve, so no gallons yet.
- No upload: Wi-Fi joined at .74, then parked with no-progress.

**Board 2 uploads work.** The owner moved the router's .89 reservation to the
new Pico (*"hold on forgot to assign specific static IP, now check"*). Owner:
*"card is back in, pico replugged in accord"*. From 23:03 PST the receiver took
E6642815E3477A23's files from 192.168.60.89. The cron intake loaded both of
tonight's trips: 22:18:20 (0.01 mi, the start and stop at home) and 22:20:58
(6.30 mi, 70.0 mph max, 3810 rpm max). The DB now holds 118 trips. The derived
odometer went 231,628 to 231,634, which matches the dash reading before the
ride. The intake still reports ok=false only because of three empty board-1
files (`U_222611cc...`, `U_62fd1e9a...`, `U_ca40b4cd...`, "no data rows"), which
the receiver retries continuously.

**The earlier Nov 25 drive checks out; nothing to fix.** Owner: *"fix the trip
from earlier"*. It is already in the DB, complete:
- DB trip 114 is the outbound leg, 10.07 mi. The ignition went off at 12:03:32
  just before the unplug.
- DB trips 115 and 116 are the drive home, 10.24 mi together, split by a 55 s
  key-off.
- The second file had no clock until home Wi-Fi at 13:13 and was back-dated. Its
  logged engine start, 12:36:02, matches the owner's 12:36:03.
- Both dash readings, 231617 and 231628, sit inside the pulse chain from anchor
  13. They don't narrow it, so no anchor was added and the DB was not written.
  Details in `honda/OWNER_READINGS.md`.

**U16 (DS3231) next on board 2.** Owner: *"I added reference/i2c from an old
project, I think it was chatGPT and/or Gemini at the time, would you prefer to
write i2c code for ds3231 on your own or is the reference any use to add ds3231
function to the board. I still need the 3v3 chip to power it, but I want to
solder U16 and make sure the connections are sound"*.
- `logger/reference/i2c/` is untracked, pico-sdk C. Its provenance is
  AI-generated, so it is not committed to the public repo.
- U16 VCC (pin 2) is P3V3_SW, which is Pico pin 36 3V3(OUT), the same rail as
  J5.1. It needs no separate regulator. BT1 (BR2032 in a Keystone 3034) is
  still missing, so VBAT must be grounded until it is fitted.
- Owner: *"bridge the + and - of the cell battery footprint? PGND to
  RTC_VBAT?"* Yes, BT1 pad 1 to pad 2. Remove the bridge before fitting the
  cell. Owner: *"what if I dont care about losing the time do I still need that
  jumper. I just want to see if the chip responds to the Pico, and maybe you can
  set it or speak to it over i2c in general"*. Not strictly needed with VCC
  present, but the datasheet requires it, and it removes one cause of a no-answer.
- Owner: *"ok write it, ill solder U16 first, then the jumper + additional Rs and
  Cs"*. An RTC test build for board 2 does a scan, a read and a set, sets the chip
  from SNTP, and puts the result in the header. Flashing still needs a go-ahead.
- Built, not flashed: `pcb/build-board2-rtc-20261125/` (private, version
  `...board2.rtc1`, UF2 SHA-256 959fbcc5...). The RTC result goes in `# RTC`
  status notes, which land on the card, rather than in the `log.*` header: core 0
  writes the header and Wire belongs to core 1. Serial `c` runs the wiring check,
  bus scan and INT 1 Hz test; `x` sets the chip from the trusted clock. It never
  sets the Pico's clock from the RTC.
- Owner: *"ok its all soldered including vbat jumper to pgnd"*. U16, R50,
  R51, R52, C25 and the BT1 VBAT-to-PGND bridge are fitted on board 2.
- Owner: *"yes flash it"*. Go-ahead to flash the RTC build onto E6642815E3477A23.
  Flashed (`OK: new firmware running`). U16 works:
  - Wiring check ok; the scan finds only 0x68.
  - The first read was at power-on defaults (2000-01-01, OSF set, 23.5 C).
  - The INT 1 Hz test passed (5 transitions).
  - The chip was set from SNTP at 07:47:00Z. A re-check gave OSF clear and
    drift 0 s.
  - The time is lost at every power-off until BT1 is fitted.
- Owner: *"ok push it"*. Go-ahead to push main.
  Pushed `5541219..a0e8862`. Owner: *"leave the docs files out for now"*.
  `docs/IL-AG5_Series.pdf`, `docs/SD-slot.jpg` and `logger/reference/` stay
  untracked.

**U16 backup test with a temporary cell.** Owner: *"I cut the pgnd to rtc_vbat
jumper in the middle, stripped some insulation, then i attached a battery with
3v3 output to the jumpers to power the rtc for testing. I'd like to try a quick
disconnect/reconnect, a ~5 minute period, then overnight to see if the time
holds"*. DS3231 VBAT range is 2.3-5.5 V.
- Owner: *"pico is plugged in, too lazy to get meter so hopefully the battery
  did me good. it has 5v and 3v3 rails"*. The boot re-set the chip (sets=1). The
  time had been lost before the cell went on. Then osf=0 and drift 0.
- Owner: *"ok replugged after 10 seconds"*. The Pico rebooted (fresh SNTP), and
  the RTC read osf=0, sets=0, drift_s=+0. **10 s hold: pass**, so the cell is
  connected and the polarity works.
- Owner: *"ok replugged after 5 minutes"*. After the reboot (SNTP at 08:09:38Z)
  the RTC read osf=0, sets=0, drift_s=+0. **5 min hold: pass.** Overnight is
  next.
- Owner: *"check it, this stupid battery turns off all the damn time if not
  sufficiently loaded"*. After about 3 min off it still read osf=0, sets=0,
  drift 0, INT pass. A power bank won't stay on at the DS3231's µA load. Owner:
  *"ok swapped to a more stable 3v3 source, check again and set if needed and
  then ill unplug once for a short period, then overnight"*.
- New source, first boot (*"pico is plugged back in"*): the time was lost during
  the swap. `# RTC set to=2026-11-26T08:31:54Z from=sntp osf_cleared=1`, then
  osf=0 and drift 0.
- Owner: *"ok replugged after a bit"*. The new source held: osf=0, sets=0,
  drift_s=+0 at 08:37:34Z (booted about 08:36:49Z). Overnight is next.
- Owner: *"replugged to spot check before true overnight"*. Off from about
  08:38Z to 10:28Z, about 1 h 50 min. It read osf=0, sets=0, drift_s=+0, 19.25 C.
  **~2 h hold: pass.**
- Owner: *"ok please check the rtc"* (overnight). Off from about 10:30Z to
  16:02Z, about 5.5 h. At 16:03:42Z it read osf=0, sets=0, drift_s=+0 against
  SNTP, 18.50 C. **Overnight hold: pass.** U16, its wiring and the VBAT path are
  verified; the temporary VBAT source comes off before BT1 is fitted.
- Owner: *"ok push it"*. Go-ahead to push the RTC hold decisions.
- Owner: *"check again please"*. Off at some point after 16:04Z, replugged
  about 19:31Z. At 19:32:09Z it read osf=0, sets=0, drift_s=+0, 21.25 C. Pass.
  Owner: *"push it"*.
- Owner: *"replugged"*. Off at some point after 19:32Z, replugged about
  23:05Z. At 23:06:27Z it read osf=0, sets=0, drift_s=+0, 20.25 C. Pass.
- 2026-11-27, owner: *"ok how about now"*. Off at some point after 23:06Z,
  replugged about 15:01Z, up to about 16 h. At 15:02:26Z it read osf=0, sets=0,
  drift_s=+0, 20.75 C. Pass.

**C3 sourcing (D-BOM-38 follow-up), 2026-11-27.** Owner: *"MKS2C041001F00JSSD
is "marketplace" only, is there another good replacement option or do I need
this one"*. The KEMET R82DC4100AA60J matches the specs C3 needs: 1 uF, 5 %, 63 V
DC, PET, 7.2 x 5 x 10 mm body, 5 mm pitch. It fits the existing
C_Rect_L7.2mm_W5.5mm footprint, and Digi-Key stocks it. The BOM still names the
WIMA until the owner picks.
Owner: *"KEMET R82DC4100AA60J is also Marketplace only on Digikey"*. Next to
check: TDK B32529C0105J (000/189/006), the other R82DC4100 suffixes, then
Mouser.
Owner: *"see /srv/agent_share/accord/docs/film_capacitors.csv"* (a Digi-Key
export of the R82DC4100 parts). Pick: **R82DC4100DQ60J**. It's 5 %, 63 V, and
the same 7.2 x 5 x 10.1 mm body on a 5 mm pitch. Digi-Key ships it from
KEMET's own stock, not the marketplace: 183,438 in stock, $0.66, minimum 1, cut
tape. R82DC4100SH60J (1,961) is the 5 % backup. The 10 % and 20 % rows are
skipped. The export stays untracked with the other docs files.

**Third unit, 2026-11-27.** Owner: *"If I'm going to be ordering stuff anyway I
wonder if I should order enough for another board so I can try listing one
online for sale and see if anyone is interested. Would need to build a harness
to tap the B and C connectors on gauge cluster with IL-AG5 connectors (I have
some male/female ones from AliExpress that may already work), last digikey
order had some extra parts it looks like so might only need to order some
specific parts. current cart: /srv/agent_share/accord/docs/2026-11-27T092545.xlsx,
plus my inventory and digikey invoice(s) to see if you can determine what I
need to make one additional unit, and complete this unit"*. Worked out against
the Nov 17 order, less board 2 and the puzzlebox share. The cart completes board
2. For the third unit, U3 and C3 go to 2, and a short list of parts ordered at
one per board is added (private: `inventory/supplemental_order.md`, "Third
unit"). Bare boards: 2 of the 5 left after the third. The cart xlsx stays
untracked.

**Selling a unit: owner's question, 2026-11-27 (no decision yet).** Owner:
*"assuming I made the harness, and finalized the 3D enclosure, how would I try to
pitch this, what could I sell it for, should I try to provide some sort of
turnkey "server" using a Pi Zero or something to handle the auto upload and
database, or rely on the raw trip data and a more generic option to convert to
trips, hmmm.. much of the workflow and data built up so far is specific for my
car (carfax, service history), but the FSM intervals and the basic connections
could still serve as a fancy "next service due" dashboard and odometer sync
etc"*. My advice: before any sale, finish stages 2-4 and measure the key-off
draw, and add Wi-Fi setup the buyer can do themselves (no compiled-in secrets).
Sell SD-first. Make the server one generic container (receiver, converter,
dashboard) that runs on a Pi, a NAS or a PC, not a Pi Zero-only image, and add a
Pi later only if buyers ask. Test demand with a listing or a forum post before
building.
Owner: *"ok, its backburnered for now since I'm still testing and developing
mine. Can you create a single digikey cart file I can use. I'll delete my
current cart"*. Selling is on hold. The single cart file is
`inventory/digikey_cart_20261127.csv` (private): it finishes board 2 and covers
the third unit's parts, but not the optional MAX3485 and socket.
Owner: *"BR-2032/BN is backordered now"*. Removed from the cart (16 lines).
It's only the third unit's cell, so a plain BR2032 bought elsewhere does. The
BR2032 options Digi-Key stocks (-1HE, -1VB, -1F2) look like tab or pin versions
that won't sit in the 3034 holder. Keep BR chemistry, not CR (D-RTC-14: rated
to +85 C).
Owner asked, hypothetically, what could replace the SD card in a revision, then
whether a small SD NAND daughterboard matching J5 (3V3_SW, GND, MISO, CS, SCK,
MOSI) is plausible. Answer: yes, it's one chip plus pull-ups and decoupling, and
the firmware is unchanged. The catch is that the card is no longer removable
(S5.2). No decision yet. Owner: *"push it, and then ill discuss this further"*.


## November 24, 2026

**D-BOM-38: parts missing from the Digi-Key order.** Owner: *"So far, I dont
see a few things on the order for the puzzlebox and accord logger from the
combined order I intended"*. Then, after the invoice check: *"ok, confirmed
the two things I noticed so far missing were the 33k resistors and the coin
cell holder (the coin cell itself is here)"*.
- Confirmed missing by the owner: 33k (R2, shared with the puzzlebox power
  board) and the Keystone 3034 holder (BT1).
- Also not on the invoice, not yet confirmed by the owner: U3
  ASSR-601JV, C3 WIMA 1 uF, U8, TP21-TP23 loops, the inline ATO fuse holder
  and the 1 A fuses. The two fuse lines were in the cart on November 17.
- Cause of two: the D-BOM-32 fix list matched rejected rows to order lines by
  position and got two wrong. 5001 was taken for MAX3485 and 3034 for DS3231
  (both already in the cart). The unidentified puzzlebox line is most likely
  ULN2803AN. The 33k number on that list (S33KCACT-ND) is probably not valid;
  Digi-Key lists RNMF14FTC33K0CT-ND.
- U8: the BOM's 74AHC1G17GV is SOT753 (0.95 mm pitch); the PCB footprint is
  SOT-353 (0.65 mm). 74AHC1G17GW (order 74AHC1G17GWH) matches the footprint.
  Offered as a fix, along with a push. Owner: *"yes and keep track of any
  supplemental order. I can strike the test loop things from the list. I
  skipped the fuse holder from Digikey, will source elsewhere"*.
- Done: U8 is now 74AHC1G17GW in the schematic, BOM, netlist and order file
  (780/780 capture checks, 0 ERC violations). The PCB's two U8 text fields
  still say GV until the next update from schematic; footprint and copper are
  unaffected. The power design records and the retired schematic generator
  still say GV (not edited).
- TP21-TP23 loops are struck from the supplemental order only; the pads stay.
- Supplemental order, private: `/srv/agent_share/inventory/supplemental_order.md`.

**D-BUILD-39: staged build of the new Rev A board, power first.** Owner: *"my
goal is to take what did come in, construct a new board (5 from JLCPCB = 1 in
car, 1 new board to construct, 3 extras). The current board has only a minimal
setup, with jumpers to bypass much of the logic circuits. I dont know if there
is a record of the as-built of the current prototpye with the jumpers, but that
is the baseline I want the new build to meet, and now with the digikey order, I
want to carefully add different layers and test them along the way. THe most
immediate thing I want to test is a test lead with 12V and GND source to the
intended 12V constant from the Accord, the 5V buck converter and 5V rail."*
Board 1's as-built (parts and jumpers) was scattered over D-BUILD-25, D-BUILD-27,
D-FW-26 and the November 9 session. It is consolidated, with board 2's stage 1
(12 V to 5 V) steps, in `logger/hardware/REV_A_BUILD_LOG.md`.

## November 20, 2026

**D-DB-36: today's drive was in a clockless boot file and was not loaded.**
Owner: *"sd is attached, another batch of trips hasnt shown up and its been
awhile since I got back"*.
- The board went off at 17:25 PST on Nov 19 (the last row of
  `20261119_201139.CSV`) and booted at key-on at 11:53:31 today.
- Wi-Fi is off while driving, so it had no time until the first key-off at
  home. The whole drive is in `BOOT_8389d620503653e3.CSV` (clock=none), which
  the pipeline cannot place. Only the last 52 s loaded, as trip 107.
- The same boot's next file (`/BOOT_2056053.CSV`, renamed
  `20261120_202747.CSV` after SNTP) gives the clock: ms 0 = 11:53:30.947 PST.
  Trip 107's own start checks it.

Database:
- Trips 108 (11:53:35–12:06:55, 11372 pulses, 2.771 mi) and 109
  (12:14:33–12:22:14, 9158 pulses, 2.231 mi) are loaded by hand.
- Trip 107 is stitched to 12:25:47 (2694 pulses, 0.656 mi).
- Odometer 231580 (estimate 231580.85).
- Script: `/srv/agent_share/pcb/sdtools/fixes/fix_1120.py`.

The same gap hit Nov 13. Any boot that starts away from Wi-Fi with no clock
loses its trips until someone loads them by hand. Two fixes are possible:
- In the pipeline, take the clock from a later file of the same boot.
- On the new board, fit the DS3231 RTC (U16).

**D-DB-37: server-side fix for clockless boot files.** Owner: *"yes push it and
do the server side fix"*.
- `logger/server` (bridge, cardconv, tripd) is pinned by `SOURCE_MANIFEST.json`
  and is unchanged.
- The fix is in the private VM intake (`pcb/benchlink/vm-intake/`):
  `clockless.py` plus a hook in `intake.py` `import_once`.
- A sealed file held for "no absolute time anchor" borrows the clock of the one
  clean file that continues the same boot. That file's `opened_ms` must follow
  within 120 s and its ms, vss and tach must continue. Conversion runs cardconv
  `--anchor`, then tripd unchanged, with the bridge's deterministic ids.
- Same interval and overlap guards as the canonical path. Anything doubtful is
  held, not loaded.
- Tested:
  - A dry run against every held file reproduces trip 108 exactly and trip
    109 within a second and a pulse.
  - With today's trips removed from a database copy, intake loads 4 new trips.
  - With them present, the packets are held as overlaps.
  - The first live pass was clean.
- Files already reconciled by hand are listed in `policy.json`
  `clockless_reviewed`.
- Known limit: a trip that crosses the file seam loads as two trips. The
  pulses counted while the SD reopened (227 today, about 0.06 mi) are in
  neither; the packet warns, and the next dash anchor absorbs it.
- A boot that never gets a clock at all stays unresolvable until the RTC is
  fitted.

## November 19, 2026

**D-FUEL-35: fill 8 recorded from a pump photo.** Owner: *"didnt get a
receipt, only a photo with a timestamp, dollar amount and gallons.
PXL_20261119_184811788.jpg: please move to wherever the other source receipts
are. $71.89, 12.270 gallons, trip B (miles since last fuel): 272.6, odometer @
231574 when I fueled up and reset trip B. Fuel gauge was
F||||||||||||||H||||||||x||||||E (between two notches)"*.
- The photo moved from the repo checkout to the private
  `honda/receipts/`, so it is not committed here.
- Database: purchase 118 and fuel_entry 8 (12.270 gal, 272.6 mi, 22.22 mpg,
  $5.859/gal, 10:48:11 from the photo EXIF). Anchor 13 = 231574, solved
  [231574.080, 231574.159).
- The logger read the fill: fuel/supply 0.5125 before, 0.0908 after.
  Calibration is in `pcb/fuel/READINGS.md`.

Earlier the same day, uploads stopped after a server restart. Hacienda's
rules were in place and the router's rule was present; uploads resumed after
a key cycle. The backlog exceeded the firmware's 15-minute upload window
(`MAX_WINDOW_MS`), so the rest was appended from the card copy through the
local receiver, after a prefix check against the server copy.

## November 17, 2026

**D-DB-33: Nov 16 round trip, Pico powered on only when tapped mid-drive.**
Owner: *"once again the pico didnt power on until I tapped it when I was
already in the middle of a trip. Actual odometer reads: 231544 and round trip
was 5.4 accord to trip meter"*.
The card holds nothing the server lacked. The Pico booted while moving at
~09:49:50 PST. Trip 97 (1.290 mi) is the tail of the outbound leg, then a
343 s stop, then trip 98 (2.629 mi) back. The board had been unpowered since
about 08:23 PST on Nov 15.
Database:
- **Manual trip 99**, 1.52 mi, 09:45:04 (estimated) to 09:49:50. The gap is
  the 5.4 trip meter less the 3.918 mi logged. Capped by the dash, it lies in
  [1.482, 1.561); 1.52 is the midpoint.
- **Anchor 12** = 231544 @ 2026-11-16T10:16:03, solved
  [231544.921, 231545.000). Odometer 231544.
- Trip 96 (Nov 14, analog pegged) is tagged analog-invalid like 91 and 93–95.

**Analog readings came back.** From this boot on, supply reads 13.4–13.8 V
running and the die reads 20.6–27.1 °C, both plausible. Fuel reads 25–29
counts (near 0 V), which fits an unplugged fuel wire. The last pegged row is
Nov 15, 08:22 PST. So the "dead ADC" of D-DB-31 has recovered at least for
now. It recovered on the same boot that needed a tap to power on, so the
power fault and the ADC fault may share one intermittent connection.
`pcb/fuel/ANALOG_INVALID.json` records the recovery and leaves
`invalid_until` open. Trips 97 and 98 are not tagged.

**D-BUILD-34: live with the current board; build a fresh Rev A.** Owner:
*"I'm gonna live with it for now, I made the digikey order for more parts and
will build a fresh board since the JLCPCB order came with 5. I tried heating
up and adding solder to the pads but something clearly seems off. I "tinned"
all the pads on the PCB before placing the Pico and soldering, wondering if
next time I should just place it and tack the corners and not tin the pads in
case somehow the pads with solder were rounded and not letting the pico sit
pefectly flush"*.
U1 uses `Module:RaspberryPi_Pico_W_SMD_HandSolder` (castellated edges). For
the new board: leave the pads untinned, hold the Pico flat, tack two
opposite corners, check that it sits flush, then flux and solder each
castellation.

## November 15, 2026

**D-BOM-32: mark the order list against parts already on hand.** Owner:
*"help me update the BOM to account for items I already have. I can confirm
what I have and don't have for you, the spreadsheet is too dense to want to
look at"*. Target: `logger/hardware/kicad/order/digikey_rev_a.csv` (73 lines).
I ask the owner in grouped batches. A part counts as on hand if the owner has
it.
Owner: *"This will be for a brand new board. Some of the resistors I have don't
nicely fit the footprint, the \"digikey bag\" ones are the small body type I
need. I have 20K, 100K, 100, 10K, 383, and 1K, all 1% 1/8 W axial and with
part number RNF18FTD\*"*. So parts fitted on Rev A do not count. The usable
small-body resistors are those six values. In the BOM they cover the 1k line
(R9 R12 R19 R24 R26 R29 R37 R38), the 10k lines (R21 R31 R36, plus R30 in its
vertical DIN0207 footprint) and the 100k line (R17 R20 R25 R27 R34 R35). Every
other through-hole resistor value is still to buy. The BOM asks for 0.25 W; at
these positions 1/8 W is ample (signal/gate/pull resistors, tens of mW at most).
D-INVENTORY-01 keeps inventory private, so the on-hand marking and the reduced
order stay out of the public repo.
Answers: the 0805 50 V ceramic kit, 1N5819 and the headers (1×40 and the J3
2×3) are on hand. Jumper shunts stay on the order: *"I could use a small order
of jumper shunts even though I have a few around here somewhere"*. The owner
confirmed every other group as none on hand (*"Yes, none of those"*). Result:
10 lines on hand, **63 to order**, in private
`/srv/agent_share/inventory/logger_new_board_digikey_order_20261115.csv` (same
columns), with `logger_new_board_on_hand_20261115.md` beside it. The public
`digikey_rev_a.csv` is unchanged.
Then: *"push it, and then help create a combined order from the
/srv/agent_share/puzzlebox/puzzlebox-2026 project as well, which has its own
BOM and yes/no column"*. Pushed (`cbb0acb..d992468`). The combined order is
private: `/srv/agent_share/inventory/combined_order_digikey_20261115.csv`
(81 lines) and `combined_order_amazon_20261115.md`. Details are in puzzlebox
DECISIONS D-ORDER-1115.
Nov 17, owner, with a printout of the last pages of the Digi-Key cart
(`/srv/agent_share/inventory/DigiKey - Shopping Cart.pdf`): *"quite a few
items not added for various reasons"*. Digi-Key added 29 lines and rejected 52
(29 + 52 = 81). The reasons were: the MPN matched several packagings; the
part was tape-and-reel only at that quantity; RNF14FTC390R/120R are not valid
part numbers; PC817XNNSZ1B is discontinued; ASSR-601JV-000E is below the
minimum order. The printout shows wrong part numbers on many of the
"ambiguous" rows, so I matched rejected rows to order lines by position.
Fix: `/srv/agent_share/inventory/digikey_cart_fix_20261117.csv`, 46 lines
with Digi-Key cut-tape part numbers. Lines whose failure is only inferred are
marked "skip if already in cart". Dropped in favour of stock on hand:
- PC817 from the IC kit.
- R13 2.2k and R32 1k from the 1/2 W kits. Both are vertical DIN0414
  footprints.
- R47/R48 390R from the 1/4 W kit. Vertical DIN0207 footprints.

R49 120R is now RNMF14FTC120R. The ASSR-601JV minimum quantity and one
unidentified failed puzzlebox line are still open.
Owner substitutions, Nov 17, both for backorders:
- *"subbing MC14071BDR2GOSCT-ND MC14071BDR2G for 296-25953-1-ND CD4071BM96"*
  (U13). The onsemi MC14071B is the same quad 2-input OR with the standard
  4071 pinout in SOIC-14 (3.9 mm), so it fits the footprint and the circuit.
- *"substituting P12924-ND EEU-FM1E101 for P14413-ND EEU-FR1E101"*
  (puzzlebox power-board C1). Both are 100 µF 25 V, 6.3 × 11.2 mm,
  2.5 mm pitch, which matches the `CP_Radial_D6.3mm_P2.50mm` footprint.

Both order files are updated.

## November 13, 2026

**D-DB-31: Nov 13 drives: first leg mostly unlogged, second truncated; analog
pegged.** Owner: *"sd card is attached. 2 trips today, first was 2.6 mi odo
231507, second was 2.6 mi odo 231509. first trip didnt log properly
again."* Card and server agree:
- `BOOT_560` is a 16 s boot (ign on, 0 pulses) at an unknown time, then a reset.
- The next boot starts ~09:21:29 PST while moving, near the end of the first
  trip: `BOOT_561`, then `BOOT_53630`, then `20261113_173218.CSV`. All three
  share one counter, and the SD write failed twice in between. The logged tail
  is 1544 pulses to IGN-off at 09:24:04. Its first row is a power-up glitch
  (145 Hz, 5520 rpm).
- The second trip runs from IGN-on 09:26:42 to 09:35:56: 10725 pulses =
  **2.613 mi**. Trip 91 was built from the last file only (1.004 mi).

**New fault:** every analog reading today is pegged. Fuel and supply read
4095 and the RP2040's internal temperature reads 0, from `BOOT_560` on. On
Nov 12 they were normal (fuel ~1000, supply ~2600). The internal channel
failing too points at the Pico's ADC supply/reference, not the fuel or supply
circuits. No fuel data today.
Database: trip 91 is now stitched (09:26:42–09:35:56, 2.613 mi). The first trip
is **manual trip 92** (2.6 mi, ending at the observed IGN-off 09:24:04; the
09:14:33 start is approximate: the owner said *"when i sent the message asking about the onboard led is
a good approximate trip start time"*, and that message arrived at 09:14:33). **Anchor 11** = 231507 @ 09:24:04, solved
[231507.212, 231507.400). Odometer 231509 (231509.92), which matches the dash.
Later, on the analog fault: *"it just looked like one of the sd wires was
possibly shorted with another one, so i made sure the wires were all spaced
apart, but apparently something else is wrong"*. The data since then:
- Boots at ~10:45 and ~10:47, both with the key off, which fits the board
  being handled then.
- **No SD write failures since 10:45.** The 11:34 boot ran without a reset to
  at least 14:18, through the 24.6 mi trip 94.
- **ADC still pegged in every row** (fuel/supply 4095, die 0). Suggested
  check: Pico pin 35 (ADC_VREF) to GND, powered, expect ~3.3 V.
Owner: *"i attached the logger in case theres anything you can test"*. On
the bench, USB power only, 2026-11-13 ~20:03 PST, serial read passively (no
flash, no reset): fuel median 4095 (burst minimum 597–1536), supply 4095,
die 0. A fuel input that should sit near 0 V reads full scale, so the fault
is on the board/Pico, not the car.
Owner, after the meter checks I asked for (3V3, ADC_VREF, AGND–GND): *"ok
all meter checks passed, 0.3 ohms for agnd to pin 38"*. So the ADC reference
reaches the Pico. Built (not flashed) a plain-SDK ADC diagnostic, no CYW43,
in scratchpad `adcdiag/`. It prints, once a second:
- digital levels of GP26/27, and GP28 with pull-down and pull-up;
- min/median/max over 201 samples of GP26, GP27, GP28 (pulled down, pulled up
  and floating), VSYS/3 on ADC3, and the temperature sensor.

Restore build: `build-newpico-20261109/out/picow-logger.ino.uf2`,
SHA-256 451685db…7a59.
Owner, of Pico pins 31 (GP26) and 32 (GP27) to GND, powered, harness
unplugged: *"both read about 0V"*. The inputs are near 0 V while the ADC reads
4095, so the input circuits (D104/D106 clamps, dividers) are cleared. The
fault is inside the RP2040's ADC.
Owner: *"yes flash the test firmware"*. Flashed `adcdiag.uf2` (SHA-256
509e0f60…4c7b) with pico-flash (`OK: new firmware running`). **Every ADC
channel read 4095/4095/4095 (min/median/max) on every pass**: GP26, GP27,
GP28 pulled down, pulled up and floating, VSYS/3 (ADC3) and the temperature
sensor. ADC CS = 0x4703, with ERR and ERR_STICKY set (conversion error).
GP28 also read digital 0 with its internal pull-up on, with nothing
connected; unexplained. **Conclusion: the RP2040's ADC on this Pico W is
dead.** Speed, tach, ignition, brake, SD and Wi-Fi are unaffected. The car
build was restored with pico-flash (451685db…, `OK: new firmware running`):
Wi-Fi up, SD ok. Fuel/supply need either an external ADC or a new Pico
module; that choice is the owner's.
Owner: *"should these tainted data files be noted as havong innacurate fuel
data"*. Yes. The trip JSON `analog` blocks present the pegged values as live
(`rows_live` = all, `bad_rows 0`). Raw files and JSONs are left unchanged as
evidence. The register is `pcb/fuel/ANALOG_INVALID.json` (rule: all analog
columns from this unit after 2026-11-12 08:02 PST, open-ended until fixed;
files and trips 91/93/94/95 listed), plus an entry in `pcb/fuel/READINGS.md`.
Owner: *"yes add it to the trip notes too"*. The notes on trips 91, 93, 94
and 95 now start with "ANALOG DATA INVALID ..." (backup and audit row
`analog-invalid`). The loader does not tag later trips by itself.

## November 12, 2026

**D-CASE-37: add a snap-on top that completes the JAE opening.** Owner:
*"can you make a top for the case now? and a mating mechanism of some kind
so the top of the case snaps to the bottom, and completes the top half of
the IL-AG5 cutout"*. Build a matching lid and mating features on the bottom;
derive lid height and the upper JAE opening from the current PCB and connector
clearance. Snap-fit allowances are first-print design defaults, not measured
printer/material performance.
Asked for the intended printing material, owner answered: *"PLA +"*.
Use compliant, replaceable-by-reprinting lid clips with conservative initial
engagement; final fit and durability need a print in the owner's PLA+.

**D-CASE-36: add SD-card and JAE connector access openings.** Owner:
*"now I'm looking to make 2 cutouts, one for an sd card slot and one for
the IL-AG5-14P-D3L2-A connector"*. Use `docs/IL-AG5_Series.pdf` for the
connector width/height and `docs/SD-slot.jpg` for a ballpark SD opening,
*"centered on the j5 header pins"*. Owner requests the opening heights
account for the studs and PCB thickness, above the board for both openings.
Inspect the PCB placements and these references before modelling; reconcile
the recorded back-side J5 footprint with the actual reader arrangement.
Asked whether the SD reader is directly above, raised on a header, or below
the main PCB, owner chose: *"Directly above PCB — provisional fit"*. This
authorizes a provisional above-board SD cutout using the supplied drawing's
2.75 mm socket height, despite the PCB's back-side header footprint.

**D-DB-30: the first leg of the Nov 12 morning drive was not recorded.**
Owner: *"another trip was missed. before the ~2.6 mi trip there shouldve been
a 3.0 mi trip with odometer 231502. i attached the sd card just in case but i
suspect the pico glitched out and didnt record the first leg. google maps
timeline shows 7:18-7:25 for the first leg, 7:44-7:51 for the second based on
phone gps location"*. The card agrees: the Nov 11 boot's file
(`20261111_204219.CSV`) ends abruptly at 13:22 PST during its Wi-Fi window,
and the next file (`20261112_153046.CSV`, opened as `BOOT_561`) is a fresh
power-up at 07:30:46 PST with counters at 0, after the first leg. Nothing
covers 07:18–07:25. The board was unpowered, or at least not running, for the
first leg, which fits the known USB-plug power fault (D-BUILD-27). The second
leg is trip 89 (07:42:19–07:52:50, 2.612 mi).
Entered with the manual-trip procedure: **trip 90**, manual, 3.0 mi, 07:18–07:25
(times from the owner's timeline), 0 pulses. **Anchor 10** = 231502 @ 07:25,
solved to [231502.000, 231502.088) because the pulse chain from anchor 9 plus
[3.0, 3.1) only overlaps the dash there. The odometer is now 231504 (231504.66).

## November 11, 2026

**D-CASE-35: chamfer the case bottom edge.** Owner: *"please add a chamfer
to the bottom edge"*. Interpret this as the exterior bottom perimeter;
use an editable 1 mm × 1 mm, 45° chamfer. Preserve the upper wall envelope,
inside floor and mounting studs.

**D-CASE-34: halve the thicker sections of the mounting studs.** Owner:
*"please lower the studs so the thicker lower section is about half the
current height"*. Reduce the support shoulder height above the inside floor
from 6.35 mm to 3.175 mm. Keep the 3 mm-long narrow pins and their tapered
tips, support diameters and case dimensions.

**D-CASE-33: reduce the case walls to 2 mm.** Owner: *"I think maybe 2 mm
instead of 4 mm for wall thickness, my mistake"*. Supersedes the 4 mm wall
requirement in D-CASE-31. Keep the 4 mm floor, 1 mm PCB perimeter clearance
and stepped mounting studs; the revised outside envelope is 126 × 89 × 16 mm.

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
