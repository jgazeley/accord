#include "host_time_frame.h"
#include "logger_network.h"
#include "logger_sd.h"
#include "card_header.h"
#include "adc_median.h"
#include "logger_power.h"

// Keep both cores at 8 KB stack; Wi-Fi stays on core 0.
bool core1_separate_stack = true;

// Core 0: the radio and the card. Both can block for hundreds of milliseconds
// and neither is allowed anywhere near the 1 Hz report, which runs on core 1.
void setup() { sdSetup(); networkSetup(); powerReady(0); }
void loop() { sdLoop(); networkLoop(); powerProgress(0); }

/* vsslog -- count the VSS and tach pulse trains on a bare Pico, in the car.
 *
 * WHY A PICO AND NOT THE PI'S OWN GPIO. A Pi pin has no voltage tolerance
 * either, and a slip costs the whole Pi and its card; this board is a spare.
 * It also counts in an ISR with nothing else competing, so no edge is lost
 * while Linux is busy. The Pi only has to read text.
 *
 * WHY NOT THE SCOPE. Proven on 2026-10-15: `WF? DAT2` returns a zero-length
 * block at 100 ms/div and slower, so the scope cannot span a drive -- 0.7 s is
 * its longest downloadable window. It characterises a waveform; it cannot
 * count one. See SCOPE.md.
 *
 * WIRING -- the Pico is NOT 5 V tolerant and neither line is a logic level.
 *
 *   VSS  (22P conn B, terminal B2, BLU/WHT)  pulses 0 -> "about 5 V or more"
 *        22k series, 6k8 to GND, Schottky to 3V3    -> GP2     (SPEC wiring)
 *
 *   TACH (gauge cluster, found by probing)   idles 14.8 V, pulled to 0
 *        22k series, 6k8 to GND, Schottky to 3V3     -> GP3    15 V in = 3.5 V
 *
 *   BRAKE (cluster C14, GRN/RED -- the brake-system WARNING line; NOT the
 *        brake pedal, which is a different wire and the load-bearing one for
 *        interlocks)
 *
 *        TOPOLOGY, from the FSM via the obdii session 2026-10-23 -- C14 is the
 *        GROUND-SWITCHED side of the lamp, so it idles HIGH:
 *
 *          ign -> driver's fuse 9 (7.5 A) -> YEL -> cluster B11 -> BRAKE bulb
 *            -> cluster internal diode -> C14 GRN/RED -> any of:
 *                 parking-brake switch -> body ground
 *                 brake-fluid level switch -> G302
 *                 driver's multiplex control unit
 *                 ABS control unit (if equipped)
 *
 *        SO brake=1 IS NOT "PARKING BRAKE". It is "the brake warning line is
 *        grounded", which low brake fluid also does. Reading it as the
 *        handbrake would log a fluid fault as a raised lever. The lamp can
 *        also light WITHOUT C14 grounded (internal diode to the charging
 *        warning circuit, for the engine-off bulb check), so the dash lamp and
 *        this column are not the same signal in either direction.
 *
 *        Measured/derived idle: ~11.3 V at C14 (12 V less the internal diode),
 *        ~14.1 V with the engine charging.
 *        22k series, 6k8 to GND, Schottky to 3V3     -> GP4   same cell as TACH
 *
 *        ACTIVE LOW at the pin; the column is printed as the MEANING, so
 *        brake=1 is "engaged". Pin HIGH = brake off.
 *
 *        The divider puts ~0.42 mA through the warning lamp circuit forever.
 *        An instrument bulb needs 80-250 mA to glow, so it cannot light the
 *        lamp -- but meter it if the cluster uses an LED and a large resistor.
 *
 *   Colour warning: GRN/RED is ALSO the keyless connector's unlock output
 *   (circuits.md:203, :758), and YEL/BLU is both cluster-C11 fuel sender and
 *   stock-pin-11 IGN. Four same-colour-different-function pairs in this car.
 *   Meter every wire; colour alone will get you the wrong one.
 *
 * The dividers are deliberately high impedance. On the automatic the VSS
 * signal is synthesised by the PCM (32P connector, terminal 9) -- an opto cell
 * would pull 4-10 mA out of a PCM output pin, and this takes 0.09 mA.
 *
 * MEASUREMENT. On the A/T the odometer is the integral of this very signal, so
 * a measured trip is an exact ruler: reset the trip meter, drive, read `total`.
 * Make it 10 miles, not 1 -- the trip meter resolves 0.1 mile.
 *
 * Service manual, p.22-71 (Vehicle Speed Signal Circuit Troubleshooting (A/T)):
 * "Slowly rotate (over 3 mph (2 km/h)) 1 wheel" -- the PCM emits NOTHING below
 * about 2 km/h, which is why rocking the car by hand never produced a pulse.
 */

const uint8_t PIN_VSS   = 2;
const uint8_t PIN_TACH  = 3;
const uint8_t PIN_BRAKE = 4;   // level, not a pulse train: no ISR, no glitch filter

/* Ringing on a 12 V automotive edge can look like several edges. Nothing real
 * here goes near 5 kHz -- tach at redline is ~220 Hz, VSS at 80 mph a few
 * hundred -- so refusing anything inside 100 us costs nothing and rejects it. */
const uint32_t GLITCH_US = 100;

volatile uint32_t vssCount = 0, tachCount = 0;
volatile uint32_t vssLastUs = 0, tachLastUs = 0;

void vssIsr() {
  uint32_t now = micros();
  if (now - vssLastUs < GLITCH_US) return;
  vssLastUs = now;
  vssCount++;
}

void tachIsr() {
  uint32_t now = micros();
  if (now - tachLastUs < GLITCH_US) return;
  tachLastUs = now;
  tachCount++;
}

uint32_t lastReport = 0, lastVss = 0, lastTach = 0;
uint32_t markNo = 0;

// Logic-side optocoupler input only. LOW means ignition ON. A disconnected
// input reads OFF via the pull-up; this cannot prove that the wire is present.
const uint8_t PIN_IGN = 5;

/* ---- analog: fuel signal and cluster supply -----------------------------
 * Implements fuel/ADC_INTERFACE_SPEC.md. Dividers are the spec's §3:
 *   fuel   GP26/ADC0  7.5k / 4.7k  ratio 0.3852  full scale 8.57 V
 *   supply GP27/ADC1   22k / 4.7k  ratio 0.1760  full scale 18.75 V
 * RAW COUNTS ONLY, never volts: counts plus a stored calibration can be
 * re-derived when the calibration changes, and volts cannot be un-derived.
 * The divider ratio is deliberately NOT applied here for the same reason.
 *
 * One SAR behind a mux, so the two channels are ~2 us apart. For a signal
 * that moves in minutes that is simultaneous and needs no sync hardware.
 */
const uint8_t PIN_FUEL   = 26;        // ADC0
const uint8_t PIN_SUPPLY = 27;        // ADC1
const uint16_t ADC_BURST = 2000;      // samples per channel per report (spec §6)
/* Below this the supply channel is dark, i.e. B11 is not live, i.e. the key is
 * out. The columns are still emitted -- see the note at the CSV header -- but
 * a reader filters on this rather than guessing. 0.5 V at the pin. */
const uint16_t SUPPLY_DARK = 155;

uint32_t ignOnMs = 0;                 // millis() when GP5 last went ON, 0 = off

/* Results live at module scope and the sampler takes no arguments, DELIBERATELY.
 * The .ino preprocessor hoists a prototype for every function to the top of the
 * translation unit, above any struct declared in the sketch body, so a struct
 * in the signature fails to compile with "declared void" -- which is what the
 * first version of this did. Keeping the type out of the signature sidesteps
 * the generated prototype entirely.
 *
 * CORE OWNERSHIP, corrected 2026-10-24. An earlier version of this comment
 * said "the sketch is single-threaded", which is false -- there are two cores
 * here, setup()/loop() on core 0 and setup1()/loop1() on core 1. The
 * conclusion it drew is still right, but for a different reason: these two
 * objects are touched ONLY from the 1 Hz report in loop1(), so they are core-1
 * private and need no lock. Nothing in logger_sd.cpp or logger_network.cpp
 * reads them. If anything on core 0 ever needs a reading, it goes through a
 * mailbox like networkSetLed()/snapshot(), not by reading these directly.
 *
 * SIZE: two 4096-bin histograms, 8 KiB each. Static, so it is in the 31 %
 * figure the build reports and not on either core's stack. */
static logger_adc::Burst adcFuel, adcSupply;

/* Round-robin so the two channels see the same ~0.2 s window rather than two
 * adjacent ones -- a chopped excitation would otherwise alias differently into
 * each. Whether it IS chopped is spec §8, still unmeasured.
 *
 * v0.7.0: the per-report statistic is the MEDIAN of the burst, not the mean.
 * The histogram is accumulated here, in the loop that was already reading the
 * samples, so this costs one array increment per sample; the median itself is
 * one bounded scan, taken at print time. See adc_median.h for why, what it
 * costs, and the even-count convention. `lo`/`hi` are still the true burst
 * extremes and still mean the same thing. */
static void adcBurst() {
  adcFuel.reset();
  adcSupply.reset();
  for (uint16_t i = 0; i < ADC_BURST; i++) {
    adcFuel.add(analogRead(PIN_FUEL));
    adcSupply.add(analogRead(PIN_SUPPLY));
  }
}

/* ONE definition of the column list, used by the human `# columns:` line and by
 * the machine `# log.columns` header. They described the same thing in two
 * places before and could have drifted; now they cannot.
 *
 * APPEND ONLY. The first seven are indexed by position downstream (tripd's
 * N_CORE_COLS, which counts 8 because vssrec prepends `wall`) and must never be
 * reordered or removed. `ign` was appended 2026-10-24 when the `# IGN` note
 * became a column. */
#define CSV_COLUMNS "ms,vss_total,vss_hz,tach_total,tach_hz,rpm,brake," \
                    "fuel_counts,fuel_lo,fuel_hi,supply_counts,die_counts," \
                    "ms_since_ign,ign"

void firmwareInfo() {
  Out.println(F("# picow-logger stages=1,2,3 version=0.8.1-dev ign_source=gp5 analog=fuel+supply+die"));
}

/* ---- the self-describing card header: CARD_FORMAT.md --------------------
 * A stranger with the card, no server and no access to this repository has to
 * be able to turn the file into miles and volts. These are the facts that
 * makes that possible and that no amount of analysis of the rows recovers.
 *
 * Everything here is derived from the constants above rather than written out
 * as literal text, so the header cannot drift from the firmware that produced
 * it -- the pin map, the divider ratios and the full-scale voltages are
 * computed from the same symbols the code uses.
 */
const char VEHICLE_ID[] = "accord-1";
/* Deliberately an opaque local label and NOT the VIN. A card is handed around
 * and ARCHITECTURE.md records that spare boards sometimes get sold; a VIN
 * written onto a card cannot be un-written, and nothing downstream needs it to
 * tell two cars apart. Change the label, not the kind of thing it is. */
const char FW_VERSION[] = "0.8.1-lra05-dev";

const uint16_t ADC_BITS = 12;
/* The per-report statistic, published in the card header so a card-only reader
 * never has to map a firmware version onto a behaviour. v0.6.0 and earlier
 * logged the mean and carried no `stat=` key at all. */
const char ADC_STAT[] = "median";
const float ADC_VREF_V = 3.3f;
/* The physical dividers, fuel/ADC_INTERFACE_SPEC.md §3. The ratio and the full
 * scale are COMPUTED from these two resistors by card_header.h rather than
 * written out, so the published calibration cannot disagree with the hardware:
 * 4700/(7500+4700) = 0.3852 and 3.3/0.3852 = 8.57 V. */
const uint32_t FUEL_R_TOP = 7500,   FUEL_R_BOT = 4700;
const uint32_t SUPPLY_R_TOP = 22000, SUPPLY_R_BOT = 4700;

/* The pulse constant lives in tripd and is refit from real drives; this copy is
 * provenance for a card-only reader, never an authority. CARD_FORMAT.md §4 has
 * the reasoning, including why the band matters more than the point value. */
const char PPM_VALUE[] = "4104.3";
const char PPM_BAND[]  = "4103.19..4105.42";
const char PPM_ASOF[]  = "2026-10-18";

/* Fill in everything the board knows about itself. The per-file fields are left
 * unset here: logger_sd.cpp adds them on each open, and the boot-time copy over
 * USB deliberately has none. */
void cardHeaderFacts(logger_card_header::Facts &f) {
  f.power_qualified = LOGGER_POWER_QUALIFIED;
  f.chip = rp2040.getChipID();
  f.vehicle = VEHICLE_ID;
  f.fw = FW_VERSION;
  f.columns = CSV_COLUMNS;
  f.stable = 7;
  f.pin_vss = PIN_VSS;   f.pin_tach = PIN_TACH;     f.pin_brake = PIN_BRAKE;
  f.pin_ign = PIN_IGN;   f.pin_fuel = PIN_FUEL;     f.pin_supply = PIN_SUPPLY;
  f.glitch_us = GLITCH_US;
  f.ppm_value = PPM_VALUE; f.ppm_band = PPM_BAND;   f.ppm_asof = PPM_ASOF;
  f.adc_bits = ADC_BITS; f.adc_vref_v = ADC_VREF_V; f.adc_burst = ADC_BURST;
  f.adc_stat = ADC_STAT;
  f.supply_dark = SUPPLY_DARK;
  f.fuel_r_top = FUEL_R_TOP;     f.fuel_r_bot = FUEL_R_BOT;
  f.supply_r_top = SUPPLY_R_TOP; f.supply_r_bot = SUPPLY_R_BOT;
}

/* Latch the ignition ON edge for ms_since_ign. Called at the TOP of the report,
 * before the CSV row is built, and its return value is what the `ign` column
 * prints -- ONE pin read per report, so the column and ms_since_ign can never
 * disagree about the same instant.
 *
 * ms_since_ign IS STILL 0 ON THE FIRST ROW OF A KEY-ON, and no ordering fixes
 * that: the ON edge is latched to this report's own ms, so `now - ignOnMs` is
 * 0 by construction on that row, exactly as it is when the key is out. An
 * earlier comment here claimed moving the latch to the top had fixed it; it
 * had not, and could not. That ambiguity is precisely why `ign` is a real
 * column rather than something a reader derives (CARD_FORMAT.md §7). */
static bool latchIgn(uint32_t reportMs) {
  const bool high = digitalRead(PIN_IGN);
  if (!high && !ignOnMs) ignOnMs = reportMs ? reportMs : 1;
  else if (high)         ignOnMs = 0;
  return high;
}

const uint32_t STATUS_INTERVAL_MS = 60000;  // the periodic '#' notes (SPEC 7)
const uint32_t EARLY_STATUS_MS = 5000;      // rule 4.9: one early re-emission
const uint32_t INPUT_GUARD_MS = 500;        // rule 4.8: deaf after enumeration
const uint32_t INPUT_QUIET_MS = 20;         // rule 4.8: let a burst finish

uint32_t serialReadyMs = 0;
uint32_t ignoredBursts = 0;

void help() {
  firmwareInfo();
  Out.println(F("# w=wifi status  t=UTC clock  d=sd status (also every 60s)"));
  Out.println(F("# vsslog -- r=reset totals  m=mark  l=levels  ?=help"));
  Out.println(F("# columns: " CSV_COLUMNS));
  Out.println(F("# analog: RAW 12-bit counts, dividers NOT applied. fuel GP26 7.5k/4.7k,"));
  Out.println(F("#   supply GP27 22k/4.7k, die = RP2040 internal. fuel_lo/hi are the"));
  Out.println(F("#   burst spread = the float-noise estimate, and it is data."));
  Out.println(F("# supply_counts below ~155 means B11 is dark (key out): the analog"));
  Out.println(F("#   columns are still emitted, but they are not a measurement."));
  Out.println(F("# ms_since_ign: 0 while the key is out. Do NOT filter the first two"));
  Out.println(F("#   minutes -- the settling rise is an open question, not noise."));
  Out.println(F("# brake: 1 = BRAKE WARNING line grounded -- parking brake OR low fluid"));
  Out.println(F("# ign: 1 = ignition ON. GP5 reads LOW for on; unwired reads off."));
  Out.println(F("#   The column prints the MEANING, like brake. ms_since_ign cannot"));
  Out.println(F("#   substitute: it is 0 both for key-out and for the first row of a"));
  Out.println(F("#   key-on, because the ON edge is latched to that row's own ms."));
}

/* RULE 4.8 -- why input is parsed as whole bursts and not byte by byte.
 *
 * On 2026-10-18 this board executed its own banner. Nobody sent anything: the
 * kernel creates the CDC node in cooked mode with echo ON, and whatever runs
 * `stty raw -echo` cannot get there first, so for a second or so every byte
 * the board prints is fed straight back to it as input -- and the banner
 * contains "r=reset totals  m=mark  l=levels". The capture shows '# LEVELS'
 * and '# RESET' at boot with no host command behind them.
 *
 * Two defences, because the first alone is only a window:
 *
 *  1. Deaf for INPUT_GUARD_MS after Serial comes up, which covers the banner.
 *  2. A burst that contains ANY byte that is not a command character is
 *     discarded whole. Every line this firmware prints carries a '#', a space,
 *     a comma or a digit, so no echoed line can survive this test, while a
 *     lone 'r' from vssrec's /tmp/vssreset trigger still arrives intact. The
 *     20 ms quiet period before a burst is judged is what makes that safe: it
 *     stops a read from splitting a long echoed line and leaving a bare 'r'
 *     from "rssi=" looking like a deliberate reset.
 *
 * The host cannot fix this on its own -- vssrec does set raw -echo, but it
 * cannot run before the kernel creates the node. */
bool isCommandChar(char c) {
  return c == 'r' || c == 'm' || c == 'l' || c == 'w' || c == 't' ||
         c == 'd' || c == '?';
}

/* RULE 4.10 -- the host clock frame, and why it is not a command character.
 *
 * The Pico only learns the time from SNTP, which means only within reach of a
 * known AP. A boot anywhere else never gets a trusted clock, so its log keeps
 * the name /BOOT_<ms>.CSV and carries no date at all. The Pi is already on the
 * other end of this USB link and already knows the time, so it can simply say
 * so.
 *
 * It CANNOT be carried by the mechanism above. Rule 4.8 works precisely
 * because digits are not command characters -- that is what makes an echoed
 * data row (`6922003,85893,0.00,...`) impossible to mistake for input. Adding
 * digits to isCommandChar() would hand every split echo of a report row the
 * power to do something.
 *
 * So a clock arrives as a FRAME, judged whole and separately:
 *
 *     @<13 digits>\n        epoch milliseconds, e.g. @1792345678901
 *
 * Three things have to hold at once, and an echo cannot satisfy them:
 *
 *  1. '@' is the first byte of the burst.
 *  2. Exactly 13 digits follow, and nothing else.
 *  3. The value lands between 2026 and 2040.
 *
 * '@' APPEARS NOWHERE IN THIS FIRMWARE'S OUTPUT, and must not be added to it
 * -- not to the banner, not to help(), not to a status note. That invariant is
 * what makes rule 4.8's guarantee ("no echoed line can survive this test")
 * hold for frames too, rather than leaving it resting on the length check
 * alone. The frame is documented in README.md instead of in the banner for
 * exactly this reason.
 *
 * Milliseconds rather than seconds because it costs three characters and
 * removes the dominant error term; the host reads its clock immediately before
 * writing, and core 0 ages the value forward from the instant core 1 took
 * delivery. */
const char TIME_FRAME = logger_host_time::FRAME;

bool applyHostTime(const char *burst, uint8_t len) {
  uint64_t ms = 0;
  if (!logger_host_time::decode(burst, len, ms)) return false;
  networkSetHostTime(ms);
  return true;
}

void setup1() {
  powerSetup1(); // before USB wait, output, ADC or radio initialization
  /* No pull-up: the divider's lower leg sets the resting level, and an
   * internal pull-up would fight it. It also holds the pin low if the tap
   * ever falls off, so a disconnected probe reads zero instead of counting
   * noise. */
  pinMode(PIN_VSS,   INPUT);
  pinMode(PIN_TACH,  INPUT);
  pinMode(PIN_BRAKE, INPUT);
  pinMode(PIN_IGN, INPUT_PULLUP);
  /* No pinMode for the ADC pins: analogRead() configures them, and calling
   * pinMode(INPUT) first would leave the digital input buffer enabled on an
   * analog pin, which leaks and adds noise. */
  analogReadResolution(12);

  /* COUNTING STARTS BEFORE ANYTHING ELSE, and in particular before the wait
   * for Serial below.
   *
   * These two lines used to sit after that wait, which meant no pulse was
   * counted for the first three seconds of every boot -- `!Serial` stays true
   * until the USB host configures the device, and when the host is a Pi that is
   * still booting, the full 3000 ms elapses every time. On 2026-10-19 the first
   * card row landed at ms=4003 and its totals began from ms=3000.
   *
   * It costs nothing to fix and it is safe: the ISRs only bump a counter behind
   * a 100 us filter. They never print, never touch `Out`, and never touch the
   * card, so they have no dependency on anything initialised later.
   *
   * The counters are CUMULATIVE, so this is the whole of the problem. The first
   * report still arrives around ms=4000, but it now carries every edge since
   * power-on rather than every edge since the host turned up. Three seconds is
   * about 103 pulses at 30 mph -- 0.025 mi -- which is nothing on a boot where
   * the car is still stationary, and is a real loss on a brownout or a USB
   * glitch in the middle of a drive. That second case is why this matters. */
  attachInterrupt(digitalPinToInterrupt(PIN_VSS),  vssIsr,  RISING);
  attachInterrupt(digitalPinToInterrupt(PIN_TACH), tachIsr, RISING);

  Serial.begin(115200);
  uint32_t t0 = millis();
  while (!Serial && millis() - t0 < 3000) { }
  // Rule 4.8: the guard window opens here, before the first byte is printed,
  // because it is this firmware's own output that comes back as input.
  serialReadyMs = millis();

  help();
  /* The machine-readable block goes to the host too, so a USB-only recording
   * carries the same constants the card does. `log.file` is absent here on
   * purpose: it describes one card file, the card module prints it on every
   * open, and the host already learns the live name from the '# SD' note.
   * CARD_FORMAT.md rule 4 -- a reader tolerates a tag it does not get. */
  {
    logger_card_header::Facts f;
    cardHeaderFacts(f);
    char block[logger_card_header::BUFFER];
    if (logger_card_header::render(block, sizeof(block), f)) Out.print(block);
  }
  networkPrintWifi();
  networkPrintTime();
  sdPrintStatus();
  lastReport = millis();
  networkCounterReady();
  powerReady(1);
}

// Every command runs here, one character at a time, only after its burst has
// been judged deliberate (rule 4.8 above).
void command(char c) {
  if (c == 'r') {
    noInterrupts(); vssCount = 0; tachCount = 0; interrupts();
    lastVss = lastTach = 0;
    Out.println(F("# RESET"));
  } else if (c == 'm') {
    noInterrupts(); uint32_t v = vssCount, t = tachCount; interrupts();
    Out.print(F("# MARK ")); Out.print(++markNo);
    Out.print(F(" at ms=")); Out.print(millis());
    Out.print(F(" vss=")); Out.print(v);
    Out.print(F(" tach=")); Out.println(t);
  } else if (c == 'l') {
    /* Static tap check, for after someone has been in the loom. Sample both
     * pins for 200 ms and report the resting level.
     *
     * TACH is conclusive: with the ignition at II and the engine stopped the
     * line sits at battery through the cluster, so a connected tap reads
     * HIGH. There is no pull-up, so the divider's lower leg pulls the pin
     * LOW the moment the tap comes off -- HIGH here means the wire is on.
     *
     * VSS is NOT conclusive: the PCM's open collector idles LOW, which is
     * exactly what a fallen-off tap reads. Only motion above 2 km/h can
     * prove that one. */
    uint32_t t0 = millis();
    uint32_t nv = 0, nt = 0, nb = 0, n = 0;
    while (millis() - t0 < 200) {
      nv += digitalRead(PIN_VSS);
      nt += digitalRead(PIN_TACH);
      nb += digitalRead(PIN_BRAKE);
      n++;
    }
    Out.print(F("# LEVELS vss="));
    Out.print(nv * 2 > n ? F("HIGH") : F("LOW"));
    Out.print(F(" (")); Out.print(nv * 100.0f / n, 0);
    Out.print(F("% high)  tach="));
    Out.print(nt * 2 > n ? F("HIGH") : F("LOW"));
    Out.print(F(" (")); Out.print(nt * 100.0f / n, 0);
    Out.println(F("% high)"));
    /* The leading '#' is LOAD-BEARING, not cosmetic. vssrec classifies a
     * line as a note only if it starts with '#'; anything else it writes
     * into the CSV as a data row. This line began as "  brake=" and tripd
     * then dropped it on its `len(parts) < 7` truncated-row guard, which
     * makes the NEXT row 2000 ms after the last accepted one -- over
     * GAP_MS=1500 -- so a tap check during a drive scored gaps=1 on an
     * otherwise perfect trip. Found 2026-10-18. Never print a bare
     * continuation line from here. */
    Out.print(F("# brake="));
    Out.print(nb * 2 > n ? F("HIGH (off)") : F("LOW (ENGAGED)"));
    Out.print(F(" (")); Out.print(nb * 100.0f / n, 0);
    Out.println(F("% high)"));
    Out.println(F("# ign II + engine stopped: tach HIGH = tap on, LOW = tap off."));
    Out.println(F("# vss idles LOW either way -- only driving proves that tap."));
    Out.println(F("# brake: pull the handbrake and run 'l' again -- it must flip."));
  } else if (c == 'w') {
    networkPrintWifi();
  } else if (c == 't') {
    networkPrintTime();
  } else if (c == 'd') {
    sdPrintStatus();
  } else if (c == '?') {
    help();
  }
}

/* The '#' notes: one line each, every STATUS_INTERVAL_MS, plus whenever a
 * module's state actually moves, plus one re-emission at EARLY_STATUS_MS.
 *
 * RULE 4.9 -- why the early re-emission earns its keep. Serial becomes ready
 * when the host kernel configures the USB device, which is before
 * /dev/serial/by-id/... exists for anything in userspace to open, and SNTP
 * then succeeds in about two seconds. So the whole interesting part of a boot
 * -- synced=0, the join, the first sync -- can close before a capture can
 * attach: on 2026-10-18 witnessing '# TIME unset src=none synced=0' took a
 * replug that happened to be slow. One extra pair of notes a few seconds in
 * puts the early state inside a window a host can actually catch, and the same
 * blindness would otherwise hide a real regression later. */
void statusNotes() {
  static uint32_t lastStatus = 0, reportedBursts = 0, burstNoteAt = 0;
  static bool early = false;
  const uint32_t now = millis();
  const bool periodic = now - lastStatus >= STATUS_INTERVAL_MS;
  const bool emitEarly = !early && now >= EARLY_STATUS_MS;

  // Consumed unconditionally: asking clears the flag, so a periodic note must
  // not leave a stale "changed" behind to print again on the next pass.
  const bool wifiMoved = networkWifiChanged();
  const bool timeMoved = networkTimeChanged();
  const bool sdMoved = sdStatusChanged();
  if (periodic || emitEarly) firmwareInfo();
  if (periodic || emitEarly || wifiMoved) networkPrintWifi();
  if (periodic || emitEarly || timeMoved) networkPrintTime();
  if (periodic || emitEarly || sdMoved) sdPrintStatus();
  if (emitEarly) early = true;
  if (periodic) lastStatus = now;

  /* Rate-limited to the status interval, not one-shot: a note printed into a
   * still-cooked tty is echoed back as another ignored burst, so an unlimited
   * note would feed itself. A board that keeps reporting these is telling you
   * its port never reached raw mode. */
  if (ignoredBursts != reportedBursts &&
      (!burstNoteAt || now - burstNoteAt >= STATUS_INTERVAL_MS)) {
    char line[96];
    snprintf(line, sizeof(line),
             "# INPUT ignored bursts=%lu (rule 4.8 echo guard)",
             (unsigned long)ignoredBursts);
    Out.println(line);
    reportedBursts = ignoredBursts;
    burstNoteAt = now ? now : 1;
  }
}

void loop1() {
  powerProgress(1);
  sdProducerPoll();
  // Independent of the unchanged 1 Hz raw IGN column. Retry a contended
  // mailbox on the next 20 ms sample; never wait for network work here.
  static uint32_t lastNetworkIgn = 0;
  const uint32_t ignNow = millis();
  if (ignNow - lastNetworkIgn >= 20) {
    lastNetworkIgn = ignNow;
    networkSetIgn(digitalRead(PIN_IGN) == LOW);
  }
  // Rule 4.8. Bytes are collected, then judged once the line has stopped
  // arriving; a burst with anything but command characters in it is dropped
  // whole and counted.
  static char burst[64];
  static uint8_t burstLen = 0;
  static bool burstBad = false;
  static uint32_t burstLastMs = 0;

  unsigned inputBudget = 128;
  while (Serial.available() && (!LOGGER_POWER_QUALIFIED || inputBudget--)) {
    const int c = Serial.read();
    burstLastMs = millis();
    if (burstLastMs - serialReadyMs < INPUT_GUARD_MS) continue;
    if (c == '\r' || c == '\n') continue;          // separators, not commands
    // Rule 4.10. A burst that opens with '@' is a frame: it is buffered as-is
    // and validated whole below, because its payload is digits and digits are
    // deliberately not command characters. Everything else keeps rule 4.8's
    // per-character test untouched.
    const bool framed = (burstLen ? burst[0] : char(c)) == TIME_FRAME;
    if (burstLen < sizeof(burst)) burst[burstLen++] = char(c);
    else burstBad = true;
    if (!framed && !isCommandChar(char(c))) burstBad = true;
  }
  if (burstLen && millis() - burstLastMs >= INPUT_QUIET_MS) {
    if (burstBad) ++ignoredBursts;
    else if (burst[0] == TIME_FRAME) {
      // A malformed frame is an ignored burst like any other, so a host
      // sending rubbish shows up in the same place as an echo would.
      if (!applyHostTime(burst, burstLen)) ++ignoredBursts;
    }
    else for (uint8_t i = 0; i < burstLen; ++i) {
      command(burst[i]);
      // A finite command completes before refreshing health. Continuous input
      // is bounded above so it cannot indefinitely starve reports/quiescence.
      powerProgress(1);
      sdProducerPoll();
    }
    burstLen = 0;
    burstBad = false;
  }

  statusNotes();

  uint32_t now = millis();
  uint32_t dt = now - lastReport;
  if (dt < 1000) return;
  lastReport = now;

  const bool ignHigh = latchIgn(now);

  noInterrupts();
  uint32_t v = vssCount, t = tachCount;
  interrupts();

  float vssHz  = (v - lastVss)  * 1000.0f / dt;
  float tachHz = (t - lastTach) * 1000.0f / dt;
  lastVss = v; lastTach = t;

  /* 2 pulses per crank revolution, measured on the car 2026-10-15: 32.0 Hz
   * with the needle at ~1000 and 28.1 Hz at ~750. So rpm = Hz * 30. The drive
   * is what turns that from "the only integer that fits" into a real number. */
  Out.print(now);        Out.print(',');
  Out.print(v);          Out.print(',');
  Out.print(vssHz, 2);   Out.print(',');
  Out.print(t);          Out.print(',');
  Out.print(tachHz, 2);  Out.print(',');
  Out.print(tachHz * 30.0f, 0); Out.print(',');
  /* Printed as the MEANING, not the pin: 1 = engaged. A level needs no
   * debounce at 1 Hz -- one sample per report is the whole signal. */
  Out.print(digitalRead(PIN_BRAKE) ? 0 : 1); Out.print(',');

  /* Analog last, so every existing consumer that indexes the first eight
   * fields by position is untouched. vssrec's header and tripd's COLUMNS
   * both had to be widened to match -- they are the same contract. */
  adcBurst();
  /* fuel_counts and supply_counts are the burst MEDIAN from v0.7.0 and were
   * the mean through v0.6.0. The column names are deliberately unchanged --
   * renaming them would redefine every historical row and break readers that
   * index by position. Which statistic a file carries is declared once, in the
   * card header's `log.adc stat=`; CARD_FORMAT.md §8 has the rule. */
  Out.print(adcFuel.median());   Out.print(',');
  Out.print(adcFuel.lo);         Out.print(',');
  Out.print(adcFuel.hi);         Out.print(',');
  Out.print(adcSupply.median()); Out.print(',');
  Out.print((uint16_t)(analogReadTemp() * 100.0f)); Out.print(',');
  Out.print(ignOnMs ? (now - ignOnMs) : 0UL); Out.print(',');
  /* The ignition state, printed as the MEANING like brake: 1 = on, while the
   * GP5 pin reads LOW for on. Taken from latchIgn()'s own read, which is the
   * SAME read the ms_since_ign latch used, so the two can never disagree about
   * this instant. One instantaneous observation per report, undebounced on
   * purpose -- the grace window belongs with the thing that knows what a trip
   * is, which is tripd. */
  Out.println(ignHigh ? 0 : 1);

  networkSetLed(vssHz > 0.5f);
}
