// uart_main -- runs on the Pico W (the hondaPico role).
//
// The full board I/O set, driven by a framed protocol that is deliberately
// transport-independent:
//   * USB CDC      -- works today (Pi 4 on the bench)
//   * RS-485       -- UART1 + DE on GP10, through U5 (MAX3485, socketed);
//                     exercised extensively from the Pi 4
//   * BLE          -- phone pairing, RSSI proximity and a text command
//                     characteristic; see bleprox.h. TR_BLE in reply() is still
//                     reserved for carrying FRAMES over BLE later.
// The same frames, the same handler, the same host tool. Only the wire changes.
//
// That host tool is `cm5sim`, which stands in for the CM5 as the bus's only
// initiator, usually reached through the `hp` shortcut (`./hp out lock pulse`,
// `./hp io`, `./hp status`). It is bench tooling kept with the other bench
// scripts on the development host and is NOT part of this repository, so the
// cm5sim command lines below are usage notes, not paths into this tree.
//
// Carries over from the earlier version:
//   * PIO-UART link to the expansion Pico: HELLO on boot, PING every 2 s
//   * accepts an UNPROMPTED event from the expansion Pico and ACKs it
//   * chirps GP27 twice for UNLOCK, once for LOCK
//   * counts good frames, CRC errors and resyncs
//   * 'B' puts the expansion node into BOOTSEL over the link
//
// Replaces the WiFi dashboard (hondaPico.ino): same seven outputs, four input
// cells, battery sense and GP15 heartbeat, but commanded over a link instead of
// an HTTP endpoint. The dashboard's own UF2 is kept as the bench fallback.
//
// Link pins are GP4/GP5 = J5 pins 3 and 4 on the hondaPico PCB.
// Cable is a null modem: our GP4 -> their GP5, our GP5 <- their GP4, GND-GND.
//
// FLASH: both boards are attached, so pico-flash cannot target one of two.
//   picotool load --bus <bus> --address <addr> -v -x uart_main.ino.uf2
// Pico W application serial E6614C311B3A3231, BOOTSEL serial E0C9125B0D9B.
// The PCB's soldered-down Pico W is E66480454F711D2E; build it for rpipicow.

#include "link.h"
#include "bleprox.h"

// RS-485 to the CM5. UART1's hardware pins, which is why the inter-Pico link had
// to be PIO -- GP4/GP5 are also UART1 and this side gets the real peripheral.
// MAX3485 (U5 on the board) is the 3.3 V part; a 5 V MAX485 module would drive
// 5 V into GP9 and must not be wired directly.
#define RS_TX   8
#define RS_RX   9
#define RS_DE  10             // HIGH = transmit; DE and /RE tied together
#define RS_BAUD 115200

// Result of rs485SelfTest(), kept so `?` can report it long after boot -- the
// banner scrolls away, and on a board in a car it is usually missed entirely.
// Declared up here because the status dump reads it well before setup() runs;
// arduino-cli hoists function prototypes but NOT variables.
const char* rs485Verdict = "not run";

#define PIN_TX    4
#define PIN_RX    5
#define BUZZ_PIN  27          // bench only; the real board acknowledges with
                              // the flasher + ceiling lamp, not a beep

// D41 (red) on GP15 through R41. The real liveness indicator: it proves the
// sketch is running even when no link is connected. LED_BUILTIN cannot do that
// job here -- on a Pico W it hangs off the CYW43 over SPI, and in this firmware
// it is already the inter-Pico link heartbeat, ridden in the ping so both boards
// stay in step. D40 (green) is hard-wired +3V3 -> R40 -> GND and needs no code.
#define HB_PIN 15

// Battery sense: J1-1 -> D20 -> R19 100k / R20 20k -> GP26 (ADC0).
// Calibrated 2026-10-13 against a Fluke at the +12V net; see circuits.md.
// One constant for the whole chain because ADC_VREF is the Pico's own 3V3 and
// the divider resistors are 5% -- the two halves are not separately knowable.
#define PIN_VBAT 26
const float VBAT_V_PER_COUNT = 0.0049184f;

// ---------------------------------------------------------------- outputs
// ULN2803A ground-pulse outputs plus Q1's ceiling channel, same pins as
// hondaPico.ino. Active HIGH into the ULN input; the ULN sinks the car line to
// ground. Breadboard: GP17 -> ULN pin 2 (I2), output on ULN pin 17 (O2) --
// inputs count up 1..8 but outputs count DOWN, pin 11 = O8 ... pin 18 = O1,
// which is the easiest thing on this chip to miswire. A 10k pulldown on each
// input is not optional: RP2040 pins float until setup() runs and a floating ULN
// input can fire a channel, which on the real car means unlocking at power-on.
//
// pulseMs = 0 marks a LEVEL output. sec_led is a level because it is driven from
// the ignition rule below, and ceiling is a level with a 30 s hold because that
// is illuminated entry. Everything else is a momentary ground pulse.
struct Out {
  const char* name;
  uint8_t     pin;
  uint16_t    pulseMs;     // 0 = level output
  uint32_t    holdMs;      // level outputs: auto-off after this (0 = stay on)
  uint32_t    offAt;
  bool        on;
  bool        timed;
};

// Order MUST match enum OutId in link.h -- the IO bitmap and T_OUT index both
// rely on it.
Out outs[] = {
  { "lock",    16, 200, 0,     0, false, false },  // ULN I1 -> O1 -> J1-3,  stock 6  BLK/WHT
  { "unlock",  17, 200, 0,     0, false, false },  // ULN I2 -> O2 -> J1-4,  stock 8  GRN/RED
  { "trunk",   18, 500, 0,     0, false, false },  // ULN I3 -> O3 -> J1-5,  stock 20 GRN/BLU
  { "flasher", 19, 600, 0,     0, false, false },  // ULN I4 -> O4 -> J1-7,  stock 17 BLU/RED
  { "horn",    20, 300, 0,     0, false, false },  // ULN I5 -> O5 -> J1-6,  stock 18 LTGRN/BLU
  { "sec_led", 22,   0, 0,     0, false, false },  // ULN I6 -> O6 -> J1-13, LED cathode
  { "ceiling",  3,   0, 30000, 0, false, false },  // Q1 gate -> J1-8,       stock 16 BLK/WHT
};
static const uint8_t NUM_OUT = sizeof(outs) / sizeof(outs[0]);

// Non-blocking throughout. hondaPico.ino pulses with delay(200), which is fine
// in a request handler but would stall both links for 200 ms here, and blocking
// is exactly what degraded this link when the fingerprint reader shared the loop.
void outApply(uint8_t i, bool on, uint32_t offAt, bool timed) {
  outs[i].on = on; outs[i].offAt = offAt; outs[i].timed = timed;
  digitalWrite(outs[i].pin, on ? HIGH : LOW);
}
// Defined below, after the input table. Declared here because the trunk
// interlock in outPulse() needs it and the outputs are declared first.
bool trunkIsOpen();
// Defined below with the relock state. Declared here so outPulse() can end a
// pending auto-relock window from the one place every lock path already goes
// through, instead of from each of the four command parsers.
void relockNoteLock();

// Returns false if an interlock refused the pulse, so every caller can say why
// instead of silently reporting success.
bool outPulse(uint8_t i) {
  // INTERLOCK: never pulse the trunk latch when the trunk already reads open.
  // Deliberately in the output layer rather than in each command parser, so all
  // four paths -- BLE cmd, USB single-key, RS-485 T_OUT and proximity -- are
  // covered by this one check and none can be added later that bypasses it.
  if (i == O_TRUNK && trunkIsOpen()) return false;
  // A lock from ANY source closes the relock window -- same reasoning as the
  // interlock above: one choke point, so a path added later cannot miss it.
  if (i == O_LOCK) relockNoteLock();
  uint16_t ms = outs[i].pulseMs ? outs[i].pulseMs : 300;   // level output, nudged
  outApply(i, true, millis() + ms, true);
  return true;
}
void outSet(uint8_t i, bool on) {
  bool timed = on && outs[i].holdMs;
  outApply(i, on, timed ? millis() + outs[i].holdMs : 0, timed);
}
void outTick() {
  for (uint8_t i = 0; i < NUM_OUT; i++)
    if (outs[i].on && outs[i].timed && (int32_t)(millis() - outs[i].offAt) >= 0)
      outApply(i, false, 0, false);
}
uint8_t outBitmap() {
  uint8_t m = 0;
  for (uint8_t i = 0; i < NUM_OUT; i++) if (outs[i].on) m |= (uint8_t)(1 << i);
  return m;
}

// ---------------------------------------------------------------- inputs
// Opto-isolated input cells. Every PC817 collector goes to a GPIO with
// INPUT_PULLUP, so an ACTIVE line reads LOW -- grounded for the ground-sense
// cells (trunk ajar, key in, door), at +12 V for the 12 V-sense cell (ignition).
// On the bench: jumper the J1 pin to GND for the first three, to +12 V for IGN.
struct In { const char* name; uint8_t pin; uint8_t bit; };
In ins[] = {
  { "trunk_ajar", 21, IN_TRUNK_AJAR },  // U10, R9  1k,   D1, J1-10 ORN
  { "key_in",      0, IN_KEY_IN     },  // U11, R10 1k,   D2, J1-12 BLU/WHT
  { "door",        1, IN_DOOR       },  // U12, R11 1k,   D3, J1-16 BLK/YEL
  { "ign",        14, IN_IGN        },  // U13, R12 2.2k, D4, J1-11 YEL/BLU
};
static const uint8_t NUM_IN = sizeof(ins) / sizeof(ins[0]);
#define PIN_IGN 14
static inline bool inActive(uint8_t i) { return digitalRead(ins[i].pin) == LOW; }

// Index of trunk_ajar within ins[], resolved once in setup() by searching for
// its bit rather than hard-coding 0, so reordering the table above cannot
// quietly point the trunk interlock at the wrong input.
static uint8_t ixTrunkAjar = 0xFF;
// Fails OPEN (returns false, pulse allowed) if the lookup never ran, because a
// disabled interlock is just the previous behaviour, whereas failing closed
// would make the trunk button dead with no obvious cause. setup() prints a loud
// warning in that case. The latch is a short-duty solenoid, so a needless
// 500 ms pulse is wasted effort, not damage -- this interlock is about
// correctness, not protection.
bool trunkIsOpen() { return ixTrunkAjar != 0xFF && inActive(ixTrunkAjar); }
static inline bool ignitionOn()        { return digitalRead(PIN_IGN) == LOW; }
uint8_t inBitmap() {
  uint8_t m = 0;
  for (uint8_t i = 0; i < NUM_IN; i++) if (inActive(i)) m |= ins[i].bit;
  return m;
}

float batteryRaw() {
  uint32_t acc = 0;
  for (int i = 0; i < 16; i++) acc += analogRead(PIN_VBAT);
  return acc / 16.0f;
}
float batteryVolts() { return batteryRaw() * VBAT_V_PER_COUNT; }

// SEC_LED follows the ignition by default: lit when the ignition is OFF, i.e.
// "armed". Both pins are on this Pico, so this needs no bus traffic and keeps
// working with no host at all -- which is the point, since the host may be
// unpowered. An explicit T_OUT on sec_led takes manual control and clears this.
bool secLedAuto = true;
void secLedTick() {
  if (!secLedAuto) return;
  bool want = !ignitionOn();
  if (outs[O_SEC_LED].on != want) outApply(O_SEC_LED, want, 0, false);
}

// ---------------------------------------------------------------- auto-relock
// Stock keyless behaviour: an unlock nobody acts on relocks itself, so a pocket
// press cannot leave the car open all night. Honda's own timeout is about 30 s.
//
// Armed ONLY by a real entry action (hp_entry_action), never by a raw channel
// test -- the same entry-action/channel-test split the confirmation flashes
// use. Bench work on the unlock relay must not silently arm a lock 30 s later.
//
// Cancelled PERMANENTLY for the cycle once a door has opened: the question is
// "did anyone get in?", asked once, and it is not re-asked when the door shuts
// again. That is what the stock system does, and it is why the cancel is not
// re-armed on a falling edge.
#define RELOCK_DEFAULT_MS 30000
#define RELOCK_MIN_MS      5000
#define RELOCK_MAX_MS    300000
static bool     relockEnabled = true;        // default ON: this is stock behaviour
static uint32_t relockMs      = RELOCK_DEFAULT_MS;
static uint32_t relockAt      = 0;           // 0 = no window open
static uint32_t relockFired = 0, relockCancels = 0;

// Resolve an input by its protocol bit rather than its table position, for the
// same reason ixTrunkAjar is resolved by search: reordering ins[] must never
// quietly point a safety check at the wrong cell.
static bool inActiveBit(uint8_t bit) {
  for (uint8_t i = 0; i < NUM_IN; i++) if (ins[i].bit == bit) return inActive(i);
  return false;                              // cell absent from the table
}

// The reasons "the car is occupied", shared by relock and by proximity lock so
// the two can never disagree about it.
//
// CAVEAT: an input cell that is in the table but NOT PHYSICALLY FITTED reads
// inactive forever and is indistinguishable from a genuinely shut door, so
// relock would fire even though someone did get in. Harmless on this car (the
// interior lock lever is mechanical) but it is why this is reported in status
// rather than hidden.
const char* hp_occupied_reason() {
  if (inActiveBit(IN_DOOR))   return "door open";
  if (inActiveBit(IN_KEY_IN)) return "key in";
  if (ignitionOn())           return "ignition on";
  return nullptr;
}

uint32_t hp_relock_remaining_ms() {
  if (!relockAt) return 0;
  int32_t d = (int32_t)(relockAt - millis());
  return d > 0 ? (uint32_t)d : 1;            // 1 = due, still non-zero
}
bool hp_relock_enabled() { return relockEnabled; }
bool hp_trunk_open()     { return trunkIsOpen(); }
void relockNoteLock()    { relockAt = 0; }

void relockArm() {
  if (!relockEnabled) { relockAt = 0; return; }
  const char* why = hp_occupied_reason();
  if (why) {                                 // never open a window we would cancel
    relockAt = 0;
    Serial.printf("   relock not armed: %s\n", why);
    return;
  }
  relockAt = millis() + relockMs;
  if (!relockAt) relockAt = 1;               // 0 is the idle sentinel
  Serial.printf("   relock armed: %lus unless a door opens\n",
                (unsigned long)(relockMs / 1000));
}

void relockTick(uint32_t now) {
  if (!relockAt) return;
  const char* why = hp_occupied_reason();
  if (why) {
    relockAt = 0; relockCancels++;
    Serial.printf("-- relock CANCELLED: %s\n", why);
    return;
  }
  if ((int32_t)(now - relockAt) < 0) return;
  relockAt = 0; relockFired++;
  // SILENT on purpose: no confirmation flash. You are not there to see it, and
  // a blink half a minute after you walked away reads as a fault rather than an
  // acknowledgement. The dome lamp is dropped early for the same reason.
  outPulse(O_LOCK);
  outSet(O_CEILING, false);
  Serial.printf("-> AUTO-RELOCK  no door opened in %lus  (relocks=%lu)\n",
                (unsigned long)(relockMs / 1000), (unsigned long)relockFired);
}

// ms = 0 leaves the timeout alone. Returns false for an out-of-range timeout so
// the caller can say why instead of silently clamping.
bool hp_relock_set(bool on, uint32_t ms) {
  if (ms && (ms < RELOCK_MIN_MS || ms > RELOCK_MAX_MS)) return false;
  relockEnabled = on;
  if (ms) relockMs = ms;
  if (!on) relockAt = 0;
  Serial.printf("-> relock %s, %lus\n", on ? "ON" : "off",
                (unsigned long)(relockMs / 1000));
  return true;
}

// ---- interface used by bleprox.cpp, so it needs no knowledge of the pin map
bool hp_out_pulse(uint8_t id)        { return id < NUM_OUT && outPulse(id); }
void hp_out_set(uint8_t id, bool on) { if (id < NUM_OUT) { if (id == O_SEC_LED) secLedAuto = false; outSet(id, on); } }
void hp_sec_led_auto()               { secLedAuto = true; }
bool hp_ignition_on()                { return ignitionOn(); }

String hp_status_text() {
  char b[112], rl[16];
  uint32_t rem = hp_relock_remaining_ms();
  if (rem) snprintf(rl, sizeof(rl), "%lus", (unsigned long)((rem + 999) / 1000));
  else     snprintf(rl, sizeof(rl), "%s", relockEnabled ? "on" : "off");
  snprintf(b, sizeof(b), "ign=%s vbat=%.2fV out=0x%02X sec=%s relock=%s",
           ignitionOn() ? "ON" : "off", batteryVolts(), outBitmap(),
           secLedAuto ? "auto" : "man", rl);
  return String(b);
}

String hp_io_text() {
  String s;
  for (uint8_t i = 0; i < NUM_IN; i++) {
    s += ins[i].name; s += inActive(i) ? "=1 " : "=0 ";
  }
  for (uint8_t i = 0; i < NUM_OUT; i++) {
    s += outs[i].name; s += outs[i].on ? "=1 " : "=0 ";
  }
  return s;
}

SerialPIO expLink(PIN_TX, PIN_RX, 256);
LinkRx    rx;        // expansion link
LinkRx    bus;       // RS-485
LinkRx    usb;       // USB CDC -- same frames, so the host tool works without U5

uint32_t lastPing = 0, lastStat = 0, pings = 0, pongs = 0, events = 0;
bool     ledState = false;
uint32_t lastPongMs = 0;
uint32_t hbAt = 0;
bool     hbOn = false;

// Lifted unchanged from main_node.ino. Two things matter and my first version
// got both wrong: tone() drives a real 2 kHz square wave, which a PASSIVE
// piezo needs to make any sound at all -- a bare digitalWrite is just a click;
// and this is non-blocking, so chirping never stalls the link the way a
// delay() loop does.
uint8_t chirpsLeft = 0; bool chirpOn = false; uint32_t chirpAt = 0;
void startChirps(uint8_t n) { chirpsLeft = n; chirpOn = false; chirpAt = 0; }
void chirpTick(uint32_t now) {
  if (!chirpsLeft && !chirpOn) return;
  if ((int32_t)(now - chirpAt) < 0) return;
  // LED_BUILTIN deliberately NOT touched here. main_node.ino:39-41 flashed it in
  // step with the beep, but it is the link heartbeat now: both boards drive their
  // LED from the ping, so letting a chirp move it desynchronised the pair.
  if (chirpOn) { noTone(BUZZ_PIN); digitalWrite(BUZZ_PIN, LOW);
                 chirpOn = false; chirpAt = now + 90; }
  else if (chirpsLeft) { tone(BUZZ_PIN, 2000, 90);
                         chirpOn = true; chirpsLeft--; chirpAt = now + 90; }
}

// Confirmation flashes: unlock = two, lock = one. Fired only on a credential
// EVENT, never on a direct T_OUT, so a host driving one channel for a test does
// not set the lights off.
//
// TIMING comes from the owner's earlier Pi implementation of this same car,
// which is the only record of what the car actually did -- the stock Alpine
// module has been out for years, and the Mitsuba RC-2201 is a plain switch with
// no timer, so the pattern was always firmware and was never measured from
// stock. That reference, with PLIGHTS active-low (0 = lights on):
//
//   lock:    on 600ms, off                                  -> 1 blink
//   unlock:  on 600ms, off 700ms, on 700ms, off             -> 2 blinks
//
// So pulseMs is 600 and the gap is 700. The reference's second blink is 700 ms
// rather than 600; that 100 ms asymmetry is almost certainly incidental to how
// it was written rather than anything the car did, and it is below the
// threshold of noticing, so both blinks here are 600 ms. Changing pulseMs also
// lengthens a manual `flasher` command to 600 ms, which is wanted -- a single
// blink should look like the real thing.
#define FLASH_GAP_MS 700
uint8_t flashLeft = 0; uint32_t flashAt = 0;
void hp_entry_action(bool unlocking);
void startFlashes(uint8_t n) { flashLeft = n; flashAt = millis(); }
void flashTick(uint32_t now) {
  if (!flashLeft) return;
  if ((int32_t)(now - flashAt) < 0) return;
  if (outs[O_FLASHER].on) return;                 // let the current pulse finish
  outPulse(O_FLASHER);
  flashLeft--;
  flashAt = now + outs[O_FLASHER].pulseMs + FLASH_GAP_MS;
}

// THE one place a real entry action becomes the car's whole response: the
// lock/unlock pulse, illuminated entry, and the confirmation flashes that
// BUZZ_PIN's comment above calls this board's acknowledgement.
//
// Why it exists: the flashes used to fire only from a credential EVENT off the
// expansion link, reasoning that a host poking one channel for a test should
// not set the lights off. That is right about T_OUT, but it left the flash
// unreachable in practice -- the expansion node does not exist yet, and the
// entry paths that DO (a BLE `unlock`/`lock`, and proximity) called
// hp_out_pulse() directly and so never flashed. The owner pressed lock and
// unlock, saw no flash, and that is what found it.
//
// The distinction that matters is ENTRY ACTION vs CHANNEL TEST, not which
// transport it arrived on. So: BLE commands, proximity and credential events
// all come through here; T_OUT and the USB single-key pulses stay silent,
// deliberately, so there is still a way to exercise one channel at 2 a.m.
// without lighting up the street.
void hp_entry_action(bool unlocking) {
  uint8_t n = unlocking ? 2 : 1;             // matches link_action_chirps()
  startFlashes(n);
  startChirps(n);                            // bench piezo on GP27; unfitted = silent
  if (unlocking) {
    outPulse(O_UNLOCK);
    outSet(O_CEILING, true);                 // illuminated entry
    relockArm();                             // stock: relock if nobody gets in
  } else {
    outPulse(O_LOCK);
  }
}

// ---------------------------------------------------------------- transports
// One handler, three wires. Adding BLE means filling in the TR_BLE arm and
// feeding its bytes to a fourth LinkRx -- no change to handleFrame() at all.
static const char* trName(Transport t) {
  return t == TR_USB ? "usb" : (t == TR_BUS ? "485" : "ble");
}

void reply(Transport via, uint8_t type, const uint8_t* pay, uint8_t len) {
  switch (via) {
    case TR_USB: link_send(Serial, A_CM5, type, pay, len); break;
    case TR_BUS: link_send_de(Serial2, RS_DE, RS_BAUD, A_CM5, type, pay, len); break;
    case TR_BLE: break;   // reserved: write to the command characteristic
  }
}

void sendIo(Transport via) {
  uint16_t cv = (uint16_t)(batteryVolts() * 100.0f + 0.5f);   // centivolts
  uint8_t p[LINK_IO_LEN] = {
    inBitmap(), outBitmap(), (uint8_t)(cv & 0xFF), (uint8_t)(cv >> 8),
    (uint8_t)((secLedAuto                 ? IOF_SEC_LED_AUTO : 0) |
              (bleprox_armed()            ? IOF_PROX_ARMED   : 0) |
              (relockEnabled              ? IOF_RELOCK_ON    : 0) |
              (hp_relock_remaining_ms()   ? IOF_RELOCK_PEND  : 0) |
              IOF_PROX_RSSI), (uint8_t)bleprox_rssi()
  };
  reply(via, T_IO, p, LINK_IO_LEN);
}

uint32_t busFrames = 0, busFwd = 0, busNak = 0, busText = 0, usbFrames = 0;

// Plain text out on the bus, DE handled. Not part of the protocol -- this
// exists so the link can be proved with picocom and the Enter key before any
// framing is involved. Prove the wire, then prove the protocol.
void busSay(const char* s) {
  digitalWrite(RS_DE, HIGH);
  delayMicroseconds(10);
  Serial2.print(s);
  Serial2.flush();
  delayMicroseconds((10UL * 1000000UL) / RS_BAUD + 20);
  digitalWrite(RS_DE, LOW);
}

// ---- the CM5 (or the Pi standing in for it) is the only initiator; we answer,
// never volunteer. Identical behaviour whichever transport the frame arrived on.
void handleFrame(Transport via, uint8_t dst, uint8_t type, const uint8_t* pay, uint8_t len) {
  // Addressed to the expansion Pico: bridge it. T_ENROL is the deliberate
  // exception -- rev 8 says a bus message is not an acceptable interlock, so
  // we verify ignition on OUR OWN sense before relaying, rather than trusting
  // the host's say-so.
  if (dst == A_EXP) {
    if (type == T_ENROL && !ignitionOn()) {
      uint8_t n = NAK_NO_IGN;
      reply(via, T_NAK, &n, 1);
      busNak++;
      Serial.printf("<= [%s] ENROL   REFUSED: ignition off at our own sense\n", trName(via));
      return;
    }
    link_send(expLink, A_EXP, type, pay, len);
    busFwd++;
    Serial.printf("<= [%s] %-7s dst=EXP len=%u -> forwarded\n", trName(via), link_type_name(type), len);
    return;
  }
  if (dst != A_MAIN && dst != A_BCAST) return;      // not ours

  switch (type) {
    case T_PING:
      reply(via, T_PONG, nullptr, 0);
      Serial.printf("<= [%s] PING    -> PONG\n", trName(via));
      break;

    case T_HELLO:
      Serial.printf("<= [%s] HELLO   host is up\n", trName(via));
      reply(via, T_HELLO, nullptr, 0);
      break;

    case T_STATUS: {
      uint8_t s[4] = { (uint8_t)(ignitionOn() ? 1 : 0),
                       (uint8_t)((millis() - lastPongMs) < 6000 ? 1 : 0),
                       (uint8_t)(events & 0xFF), (uint8_t)(rx.badCrc & 0xFF) };
      reply(via, T_STATUS, s, 4);
      Serial.printf("<= [%s] STATUS  -> replied\n", trName(via));
      break;
    }

    case T_IO:
      sendIo(via);
      Serial.printf("<= [%s] IO      -> snapshot\n", trName(via));
      break;

    case T_OUT: {
      if (len < 2 || pay[0] >= NUM_OUT) {
        uint8_t n = NAK_BAD_ADDR;
        reply(via, T_NAK, &n, 1);
        Serial.printf("<= [%s] OUT     bad args (len=%u)\n", trName(via), len);
        break;
      }
      uint8_t id = pay[0], cmd = pay[1];
      if (cmd == OC_AUTO) {
        if (id != O_SEC_LED) {                      // only sec_led has a rule
          uint8_t n = NAK_BAD_ADDR;
          reply(via, T_NAK, &n, 1);
          Serial.printf("<= [%s] OUT     auto is sec_led only\n", trName(via));
          break;
        }
        secLedAuto = true;
        secLedTick();                               // so the reply is not stale
        Serial.printf("<= [%s] OUT     sec_led -> auto (lit when ignition is OFF)\n", trName(via));
        sendIo(via);
        break;
      }
      // Taking manual control of sec_led drops the ignition rule, otherwise the
      // next secLedTick() would immediately undo what the host just asked for.
      if (id == O_SEC_LED) secLedAuto = false;
      if      (cmd == OC_PULSE) {
        if (!outPulse(id)) {                        // trunk interlock, today
          uint8_t n = NAK_INTERLOCK;
          reply(via, T_NAK, &n, 1);
          Serial.printf("<= [%s] OUT     %s REFUSED by interlock\n",
                        trName(via), link_out_name(id));
          break;
        }
      }
      else if (cmd == OC_ON)    outSet(id, true);
      else                      outSet(id, false);
      Serial.printf("<= [%s] OUT     %s %s -> GP%d\n", trName(via), link_out_name(id),
                    cmd == OC_PULSE ? "pulse" : (cmd == OC_ON ? "on" : "off"), outs[id].pin);
      sendIo(via);                                  // reply is the new state
      break;
    }

    default:
      Serial.printf("<= [%s] %-7s len=%u (no handler)\n", trName(via), link_type_name(type), len);
  }
}

void busPump() {
  uint8_t dst, type, pay[LINK_MAX_PAY], len;
  while (Serial2.available()) {
    uint8_t b = (uint8_t)Serial2.read();

    // A bare CR/LF is someone on a terminal, not a frame. Answer in English.
    // Valid frames always start 0xA5, so this can never collide with one, and
    // the framer would have discarded these bytes as resync noise anyway.
    if (b == '\r' || b == '\n') {
      busText++;
      char line[140];
      snprintf(line, sizeof(line),
               "hondaPico alive  ign=%s  vbat=%.2fV  explink=%s  events=%lu  busFrames=%lu  crcErr=%lu\r\n",
               ignitionOn() ? "ON" : "off", batteryVolts(),
               (millis() - lastPongMs) < 6000 ? "UP" : "DOWN",
               (unsigned long)events, (unsigned long)busFrames,
               (unsigned long)bus.badCrc);
      busSay(line);
      Serial.println("<= [485] [enter] -> replied in plain text");
      continue;
    }

    if (!bus.feed(b, dst, type, pay, len)) continue;
    busFrames++;
    handleFrame(TR_BUS, dst, type, pay, len);
  }
}

// USB CDC carries the SAME frames, so the whole protocol is testable without
// going through U5 -- `cm5sim --port /dev/ttyACM0 ping`. The single-key bench
// commands still work alongside them: a frame always starts 0xA5, which is not
// ASCII, so "is this a frame byte or a keypress" is decidable with no mode
// switch. usb.n != 0 means we are already mid-frame and every byte belongs to it.
void usbKey(int c);

void usbPump() {
  uint8_t dst, type, pay[LINK_MAX_PAY], len;
  while (Serial.available()) {
    uint8_t b = (uint8_t)Serial.read();
    if (b == LINK_SOF || usb.n != 0) {
      if (usb.feed(b, dst, type, pay, len)) {
        usbFrames++;
        handleFrame(TR_USB, dst, type, pay, len);
      }
      continue;
    }
    usbKey(b);
  }
}

void printStatusLine() {
  Serial.printf("link=%s frames=%lu crcErr=%lu resync=%lu events=%lu pings=%lu pongs=%lu\n",
                (millis() - lastPongMs) < 6000 ? "UP" : "DOWN",
                (unsigned long)rx.good, (unsigned long)rx.badCrc, (unsigned long)rx.resync,
                (unsigned long)events, (unsigned long)pings, (unsigned long)pongs);
  Serial.printf("  rs485: self-test %s\n", rs485Verdict);
  Serial.printf("  rs485: frames=%lu fwd=%lu nak=%lu crcErr=%lu resync=%lu   usb: frames=%lu crcErr=%lu\n",
                (unsigned long)busFrames, (unsigned long)busFwd, (unsigned long)busNak,
                (unsigned long)bus.badCrc, (unsigned long)bus.resync,
                (unsigned long)usbFrames, (unsigned long)usb.badCrc);
  Serial.printf("  in:");
  for (uint8_t i = 0; i < NUM_IN; i++)
    Serial.printf(" %s=%s", ins[i].name, inActive(i) ? "ON" : "off");
  Serial.printf("   vbat=%.2fV (raw %.1f)\n", batteryVolts(), batteryRaw());
  Serial.printf("  out:");
  for (uint8_t i = 0; i < NUM_OUT; i++)
    Serial.printf(" %s=%s", outs[i].name, outs[i].on ? "ON" : "off");
  Serial.printf("   sec_led=%s\n", secLedAuto ? "auto(ign)" : "manual");
  uint32_t rem = hp_relock_remaining_ms();
  const char* occ = hp_occupied_reason();
  Serial.printf("  relock: %s %lus", relockEnabled ? "ON" : "off",
                (unsigned long)(relockMs / 1000));
  if (rem) Serial.printf("   PENDING, fires in %lums", (unsigned long)rem);
  Serial.printf("   fired=%lu cancelled=%lu   occupied=%s\n",
                (unsigned long)relockFired, (unsigned long)relockCancels,
                occ ? occ : "no");
}

// Single-key bench commands.
//
// SAFETY -- why the '!' prefix exists. A terminal opened on this port in the
// default cooked mode has ECHO on, so the kernel echoes the board's own output
// back to it as input. The letters in "-> UNLOCK pulse" are themselves commands,
// so the board read its own log and pulsed the locks, the trunk and the horn in
// a self-sustaining loop. Observed 2026-10-14 with a plain `cat /dev/ttyACM0`.
//
// So every command that ACTUATES now needs '!' immediately before it, within
// PREFIX_MS. Read-only keys (? p q i H) still work bare. The board never emits
// '!' directly followed by an action letter, which is what makes this safe
// rather than merely inconvenient. Open the port with `stty raw -echo` anyway.
static const uint32_t PREFIX_MS = 2000;
static uint32_t prefixAt = 0;
static inline bool armedKey() {
  bool ok = prefixAt && (uint32_t)(millis() - prefixAt) < PREFIX_MS;
  prefixAt = 0;                       // one shot, whether it was valid or not
  return ok;
}

void usbKey(int c) {
  // Read-only keys: always allowed.
  switch (c) {
    case '?': printStatusLine(); bleprox_print(false); return;
    case 'p': bleprox_print(true);  return;
    case 'q': bleprox_print(false); return;
    case 'i': sendIo(TR_USB); Serial.println("-> IO frame on USB"); return;
    case 'H':
      Serial.println("read-only keys: ? status   p verbose RSSI   q quiet   i IO frame   H help");
      Serial.println("ACTUATING keys need '!' first, e.g. \"!u\" to unlock:");
      Serial.println("  !l lock  !u unlock  !t trunk  !f flasher  !h horn  !s sec_led  !c ceiling");
      Serial.println("  !U ENTRY unlock  !L ENTRY lock   (channel pulse + flashes + dome + relock)");
      Serial.println("  !a sec_led auto      !B expansion BOOTSEL");
      Serial.println("  !P arm/disarm proximity actions   !R auto-relock on/off");
      Serial.println("  !Z zones 5/3/3000ms (default)   !z zones 4/2/4000ms (looser)");
      return;
    case '!': prefixAt = millis(); return;
    default: break;
  }
  // Everything below actuates, so it needs the prefix.
  if (!armedKey()) {
    Serial.printf("(ignored '%c' -- actuating keys need '!' first, e.g. \"!%c\")\n",
                  (c >= 32 && c < 127) ? c : '?', (c >= 32 && c < 127) ? c : '?');
    return;
  }
  switch (c) {
    case 'B': {
      uint8_t m = LINK_BOOTSEL_MAGIC;
      link_send(expLink, A_EXP, T_BOOTSEL, &m, 1);
      Serial.println("-> BOOTSEL sent to the expansion node");
      break;
    }
    case 'l': outPulse(O_LOCK);    Serial.println("-> LOCK    pulse"); break;
    case 'u': outPulse(O_UNLOCK);  Serial.println("-> UNLOCK  pulse"); break;
    // Capitals are the ENTRY ACTIONS -- pulse plus confirmation flashes plus
    // illuminated entry plus, on unlock, the relock window. Lower case stays a
    // bare channel test. Without these the console, which is the one transport
    // guaranteed to be there, could not exercise what the owner calls
    // "unlocking the car" at all; only BLE and proximity could.
    case 'U': Serial.println("-> ENTRY UNLOCK (flashes + dome + relock window)");
              hp_entry_action(true);  break;
    case 'L': Serial.println("-> ENTRY LOCK   (flash)");
              hp_entry_action(false); break;
    case 't': Serial.println(outPulse(O_TRUNK) ? "-> TRUNK   pulse"
                : "-- TRUNK   REFUSED: trunk already open (interlock)"); break;
    case 'f': outPulse(O_FLASHER); Serial.println("-> FLASHER pulse"); break;
    case 'h': outPulse(O_HORN);    Serial.println("-> HORN    pulse  (the car WILL honk)"); break;
    case 's':
      secLedAuto = false;
      outSet(O_SEC_LED, !outs[O_SEC_LED].on);
      Serial.printf("-> SEC_LED %s (manual; 'a' returns it to the ignition rule)\n",
                    outs[O_SEC_LED].on ? "on" : "off");
      break;
    case 'c':
      outSet(O_CEILING, !outs[O_CEILING].on);
      Serial.printf("-> CEILING %s (%lu ms hold)\n", outs[O_CEILING].on ? "on" : "off",
                    (unsigned long)outs[O_CEILING].holdMs);
      break;
    case 'a':
      secLedAuto = true;
      Serial.println("-> SEC_LED back to auto: lit when the ignition is OFF");
      break;
    case 'P':
      bleprox_arm(!bleprox_armed());
      if (bleprox_armed())
        Serial.println("   WARNING: proximity will now PULSE THE LOCKS. Disarm with the same key.");
      break;
    case 'R': hp_relock_set(!relockEnabled, 0); break;
    case 'Z': bleprox_set_zones(5, 3, 3000); break;   // defaults
    case 'z': bleprox_set_zones(4, 2, 4000); break;   // looser: acts further out
    default:
      Serial.printf("(no action for '%c')\n", (c >= 32 && c < 127) ? c : '?');
      break;
  }
}

// ---------------------------------------------------------------- RS-485 self-test
// Run once at boot, BEFORE Serial2 claims GP8/GP9. U5 can test its own wiring,
// which is worth doing because an unsoldered Pico castellation is a real and
// already-experienced failure here: GP18 (trunk) was unsoldered and cost three
// test cycles on the car before anyone suspected the pin rather than the code.
// GP8/9/10 have never carried a signal, so they are the same lottery.
//
// The trick is that DE and /RE are tied together on RS_DE, so the receiver is
// enabled exactly when the driver is not:
//
//   DE low  (receive): the bias resistors hold A > B, so RO drives HIGH.
//                      Read GP9 with a PULLDOWN -- RO is push-pull CMOS and
//                      wins, so HIGH proves U5 is powered, the bias network is
//                      present, AND GP9's joint is good. LOW means one of
//                      those three is wrong.
//   DE high (transmit): /RE high disables the receiver, so RO goes high-Z and
//                      the pulldown wins -> GP9 reads LOW. If it still reads
//                      HIGH, RS_DE never reached U5: R13 is holding DE low on
//                      its own, i.e. GP10 is not soldered.
//
// GP8 (DI) cannot be checked this way -- there is no loopback with the receiver
// disabled -- so it is driven to its idle level and left. A dead GP8 shows up
// later as frames sent but no reply.
void rs485SelfTest() {
  pinMode(RS_TX, OUTPUT); digitalWrite(RS_TX, HIGH);  // DI idle = mark, so if the
                                                      // driver does enable it asserts
                                                      // the same polarity as the bias
  digitalWrite(RS_DE, LOW);                           // receive
  pinMode(RS_RX, INPUT_PULLDOWN);
  delayMicroseconds(200);
  bool roIdle = digitalRead(RS_RX);

  digitalWrite(RS_DE, HIGH);                          // transmit: receiver off
  delayMicroseconds(200);
  bool roMuted = digitalRead(RS_RX);

  digitalWrite(RS_DE, LOW);                           // back to receive
  pinMode(RS_RX, INPUT);

  if      (roIdle && !roMuted)  rs485Verdict = "OK (U5 powered, bias present, GP9+GP10 wired)";
  else if (roIdle && roMuted)   rs485Verdict = "GP10 NOT WIRED (R13 alone holds DE low)";
  else if (!roIdle && !roMuted) rs485Verdict = "NO RO: U5 absent/unpowered, GP9 unsoldered, or bias missing";
  else                          rs485Verdict = "unexpected -- RO low in receive, high when muted";
  Serial.printf("rs485: self-test RO idle=%d muted=%d -> %s\n",
                roIdle, roMuted, rs485Verdict);
}

void setup() {
  Serial.begin(115200);

  // Outputs LOW before they become outputs, so the ULN inputs are held off as
  // early as possible after boot -- on the car a glitch here pulses a door lock.
  for (uint8_t i = 0; i < NUM_OUT; i++) {
    digitalWrite(outs[i].pin, LOW);
    pinMode(outs[i].pin, OUTPUT);
  }
  pinMode(BUZZ_PIN, OUTPUT); digitalWrite(BUZZ_PIN, LOW);
  digitalWrite(HB_PIN, LOW); pinMode(HB_PIN, OUTPUT);
  pinMode(LED_BUILTIN, OUTPUT);
  for (uint8_t i = 0; i < NUM_IN; i++) pinMode(ins[i].pin, INPUT_PULLUP);
  for (uint8_t i = 0; i < NUM_IN; i++)
    if (ins[i].bit == IN_TRUNK_AJAR) ixTrunkAjar = i;
  if (ixTrunkAjar == 0xFF)
    Serial.println("WARNING: trunk_ajar not in ins[] -- trunk interlock DISABLED");
  analogReadResolution(12);
  pinMode(RS_DE, OUTPUT); digitalWrite(RS_DE, LOW);   // receive by default

  rs485SelfTest();          // BEFORE Serial2 claims GP8/GP9

  expLink.begin(LINK_BAUD);
  Serial2.setTX(RS_TX); Serial2.setRX(RS_RX);
  Serial2.begin(RS_BAUD);

  uint32_t t0 = millis();
  while (!Serial && millis() - t0 < 3000) { }
  Serial.println();
  Serial.println("=== uart_main (Pico W) -- full I/O, transport-independent ===");
  Serial.printf("link:  PIO UART tx=GP%d rx=GP%d @ %lu baud\n", PIN_TX, PIN_RX, (unsigned long)LINK_BAUD);
  Serial.printf("usb:   framed protocol on this port -- cm5sim --port /dev/ttyACM0\n");
  Serial.printf("rs485: UART1 tx=GP%d rx=GP%d de=GP%d @ %lu baud (via U5)\n",
                RS_TX, RS_RX, RS_DE, (unsigned long)RS_BAUD);
  Serial.printf("ble:   phone proximity + cmd characteristic (see bleprox.h)\n");
  Serial.printf("outs:");
  for (uint8_t i = 0; i < NUM_OUT; i++) Serial.printf(" %s=GP%d", outs[i].name, outs[i].pin);
  Serial.println();
  Serial.printf("ins: ");
  for (uint8_t i = 0; i < NUM_IN; i++) Serial.printf(" %s=GP%d", ins[i].name, ins[i].pin);
  Serial.println();
  bleprox_begin("hondaPico");
  while (Serial.available()) Serial.read();   // drop boot-time junk, incl. echo
  Serial.println("press H for the key list");
  link_send(expLink, A_EXP, T_HELLO, nullptr, 0);
}

void loop() {
  uint32_t now = millis();

  chirpTick(now);
  flashTick(now);
  outTick();
  secLedTick();
  relockTick(now);
  busPump();
  usbPump();
  bleprox_tick(now);

  uint8_t dst, type, pay[LINK_MAX_PAY], len;
  while (expLink.available()) {
    if (!rx.feed((uint8_t)expLink.read(), dst, type, pay, len)) continue;
    if (dst != A_MAIN && dst != A_BCAST && dst != A_CM5) continue;
    if (dst == A_CM5) {            // the expansion answering the host -- relay out
      reply(TR_BUS, type, pay, len);
      Serial.printf("=> %-7s from EXP relayed to CM5\n", link_type_name(type));
      continue;
    }

    switch (type) {
      case T_HELLO:
        Serial.println("<- HELLO   expansion Pico booted");
        link_send(expLink, A_EXP, T_HELLO, nullptr, 0);   // announce back
        break;

      case T_PONG:
        pongs++; lastPongMs = millis();
        Serial.printf("<- PONG    rtt<=%lums  (ping %lu / pong %lu)\n",
                      (unsigned long)(millis() - lastPing), (unsigned long)pings, (unsigned long)pongs);
        break;

      case T_PING:                                  // they can ping us too
        link_send(expLink, A_EXP, T_PONG, nullptr, 0);
        Serial.println("<- PING    -> PONG");
        break;

      case T_EVENT: {
        if (len < LINK_EVENT_LEN) { Serial.printf("<- EVENT   short (len=%u), ignored\n", len); break; }
        events++;
        uint8_t  seq = pay[0], act = pay[1], src = pay[2];
        uint16_t uid = (uint16_t)(pay[3] | (pay[4] << 8));
        uint8_t  sc  = pay[5];
        Serial.printf("<- EVENT   seq=%u %s src=%s user=%u score=%u   *** UNPROMPTED ***\n",
                      seq, link_action_name(act), link_src_name(src), uid, sc);
        link_send(expLink, A_EXP, T_ACK, &seq, 1);
        // A_DENIED is reported and never actioned -- carried over from
        // main_node.ino, where it was a stated safety property.
        if (act == A_DENIED) {
          Serial.println("           DENIED -> no pulse, no chirp, no flash");
        } else {
          if (act == A_UNLOCK) {
            hp_entry_action(true);
            Serial.printf("           UNLOCK: GP%d %u ms -> ULN I2/O2, ceiling on %lu ms,"
                          " 2 flashes\n",
                          outs[O_UNLOCK].pin, outs[O_UNLOCK].pulseMs,
                          (unsigned long)outs[O_CEILING].holdMs);
          } else if (act == A_LOCK) {
            hp_entry_action(false);
            Serial.printf("           LOCK:   GP%d %u ms -> ULN I1/O1, 1 flash\n",
                          outs[O_LOCK].pin, outs[O_LOCK].pulseMs);
          }
        }
        break;
      }

      default:
        Serial.printf("<- %-7s len=%u\n", link_type_name(type), len);
    }
  }

  // Inter-Pico heartbeat. The LED state rides IN the ping rather than each board
  // toggling its own, so the two LEDs are always in step instead of only being
  // locked to whatever phase they happened to start in. Toggling independently
  // meant the expansion node missing an odd number of pings while probing left
  // the pair permanently inverted, which is self-consistent but looks wrong.
  if (now - lastPing > 2000) {
    lastPing = now; pings++;
    ledState = !ledState;
    digitalWrite(LED_BUILTIN, ledState);
    uint8_t p = ledState ? 1 : 0;
    link_send(expLink, A_EXP, T_PING, &p, 1);
  }

  // D41 does double duty. With a phone connected it shows the proximity zone --
  // count the flashes per 2 s cycle, Z6 is solid (see the table in bleprox.h).
  // Otherwise 1 Hz means "this sketch is running". Deliberately NOT tied to link
  // state: on the bench neither link may be connected, and a permanently fast
  // blink would say "fault" when nothing is wrong.
  if (bleprox_connected()) {
    digitalWrite(HB_PIN, bleprox_led(now));
  } else if ((int32_t)(now - hbAt) >= 0) {
    hbOn = !hbOn;
    digitalWrite(HB_PIN, hbOn);
    hbAt = now + 500;
  }

  if (now - lastStat > 10000) {
    lastStat = now;
    bool up = (millis() - lastPongMs) < 6000;
    Serial.printf("[stat] link=%s frames=%lu crcErr=%lu resync=%lu events=%lu  ign=%s vbat=%.2fV  ble=%s %s%s\n",
                  up ? "UP" : "DOWN", (unsigned long)rx.good,
                  (unsigned long)rx.badCrc, (unsigned long)rx.resync, (unsigned long)events,
                  ignitionOn() ? "ON" : "off", batteryVolts(),
                  bleprox_connected() ? "conn" : "adv",
                  bleprox_text().c_str(), bleprox_armed() ? " ARMED" : "");
  }
}
