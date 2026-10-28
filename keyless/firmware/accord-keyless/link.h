// Framed message format for the hondaPico <-> expansion-Pico link.
//
// TRANSPORT: a PIO UART on GP4/GP5 -- J5 pins 3 and 4 on the hondaPico PCB.
// Those are UART1's hardware pins, but UART1 is already the RS-485 (GP8/GP9),
// so the link uses SerialPIO instead. PIO makes pin assignment a non-issue.
//
// WHY A UART AND NOT I2C: with two signal pins, I2C was the only *standard*
// protocol that fit, and it was chosen for that reason rather than because it
// was right. A UART is full duplex, so EITHER SIDE CAN TRANSMIT AT ANY TIME --
// the expansion Pico pushes an event the moment a finger matches, instead of
// waiting to be polled. That removes the need for the interrupt line J5 has no
// pin for. It is also immune to I2C's bus-lockup failure, and does not require
// the peripheral to answer inside an ISR window.
//
// WIRING -- STRAIGHT THROUGH, so a ribbon cable can be pin-N-to-pin-N and there
// is no crossover to get backwards. The CROSS LIVES IN THE PIN ASSIGNMENT, which
// is the normal convention: J5's signals are named from the main board's point of
// view, and the daughterboard takes the opposite role on each.
//
//     hondaPico (main)            expansion (daughterboard)
//     GP4 = TX  ---- J5.3 ---->   GP4 = RX
//     GP5 = RX  <--- J5.4 ----    GP5 = TX
//     GND       ---- J5.2 ----    GND
//
// FRAME: deliberately the same shape planned for the RS-485 bus, so there is
// one parser to write and debug for both links.
//
//     0xA5   dst   type   len   payload[len]   crc8
//
// Fixed start byte to resync on, explicit length, CRC over dst+type+len+payload.
// A bad CRC means drop the frame and hunt for the next 0xA5.
//
// `dst` was added 2026-10-03 when the RS-485 side arrived. circuits.md requires
// that "every frame carries a destination address; all nodes hear every byte and
// drop what is not theirs". Rather than invent a second format for the bus, the
// SAME frame now carries an address on both links -- which is the whole point of
// having made them identical. hondaPico can then BRIDGE: a frame whose dst is
// not its own gets forwarded to the other link unchanged, so the CM5 addresses
// the expansion Pico directly and hondaPico needs no per-message translation.
//
// The one deliberate exception is T_ENROL, which hondaPico gates on its own IGN
// sense instead of blindly forwarding -- see uart_main.ino. That follows the
// rev-8 rule: the node that acts verifies locally, never on a bus assertion.
#pragma once
#include <stdint.h>

static const uint8_t  LINK_SOF      = 0xA5;

// Addresses. 0x00 is broadcast; every node accepts it.
static const uint8_t A_BCAST = 0x00;
static const uint8_t A_CM5   = 0x01;   // the only initiator on the RS-485 bus
static const uint8_t A_MAIN  = 0x10;   // hondaPico
static const uint8_t A_EXP   = 0x11;   // expansion Pico, behind hondaPico
static const uint8_t A_MEGA  = 0x20;   // OBD-II node
static const uint8_t  LINK_MAX_PAY  = 16;
static const uint32_t LINK_BAUD     = 115200;   // verified to compile at 1000000;
                                                // raise once the link is proven

enum LinkType : uint8_t {
  T_PING  = 0x01,   // either direction, no payload
  T_PONG  = 0x02,   // reply to PING
  T_EVENT = 0x10,   // expansion -> main, UNPROMPTED. seq, source, user_lo, user_hi, score
  T_ACK   = 0x11,   // main -> expansion, acknowledges an event seq
  T_HELLO = 0x20,   // announced on boot so the far end knows we restarted
  T_BOOTSEL = 0x30, // main -> expansion: reboot into BOOTSEL. payload must be
                    // the single byte LINK_BOOTSEL_MAGIC.
  T_ENROL  = 0x40,  // CM5 -> expansion (via hondaPico): begin enrolment.
                    // payload[0] = id, or 0xFF to pick the next free slot.
  T_STATUS = 0x41,  // request a status line; reply is T_STATUS with text
  T_NAK    = 0x42,  // refused. payload[0] = a LinkNak reason
  T_OUT    = 0x50,  // host -> main: drive one output. pay[0]=OutId, pay[1]=OutCmd
  T_IO     = 0x51,  // host -> main: request an I/O snapshot. reply carries LINK_IO_LEN
};

// The seven ULN/MOSFET channels, in the order hondaPico.ino lists them and the
// order the IO-snapshot bitmap uses. Index, not pin: the host never needs to know
// the pin map, which is what lets the same command work over USB, RS-485 or BLE.
enum OutId : uint8_t {
  O_LOCK = 0, O_UNLOCK, O_TRUNK, O_FLASHER, O_HORN, O_SEC_LED, O_CEILING, O_COUNT
};
// OC_AUTO applies only to sec_led: it hands the channel back to the on-board
// ignition rule. Without it, any manual command would strand the LED in manual
// for the rest of the boot, with no way back over the link.
enum OutCmd : uint8_t { OC_OFF = 0, OC_ON = 1, OC_PULSE = 2, OC_AUTO = 3 };

static inline const char* link_out_name(uint8_t o) {
  switch (o) { case O_LOCK: return "lock";       case O_UNLOCK:  return "unlock";
               case O_TRUNK: return "trunk";     case O_FLASHER: return "flasher";
               case O_HORN: return "horn";       case O_SEC_LED: return "sec_led";
               case O_CEILING: return "ceiling"; default: return "?"; }
}

// IO snapshot payload, 6 bytes. Deliberately fixed-width and binary rather than
// text: the same bytes have to fit a 16-byte BLE-friendly payload later.
//   [0] inputs  bit0 trunk_ajar, bit1 key_in, bit2 door, bit3 ign  (1 = active)
//   [1] outputs bit n = OutId n currently asserted
//   [2] vbat centivolts, low byte    1244 = 12.44 V
//   [3] vbat centivolts, high byte
//   [4] flags   bit0 = sec_led follows ignition automatically
//   [5] smoothed RSSI, signed int8 dBm; 127 = unknown (stale/disconnected)
//       Only meaningful with IOF_PROX_RSSI; old firmware leaves this byte zero.
static const uint8_t LINK_IO_LEN = 6;
enum LinkInBit : uint8_t { IN_TRUNK_AJAR = 1 << 0, IN_KEY_IN = 1 << 1,
                           IN_DOOR = 1 << 2, IN_IGN = 1 << 3 };
enum LinkIoFlag : uint8_t { IOF_SEC_LED_AUTO = 1 << 0,
                            IOF_PROX_ARMED   = 1 << 1,   // proximity actions armed
                            IOF_RELOCK_ON    = 1 << 2,   // auto-relock feature enabled
                            IOF_RELOCK_PEND  = 1 << 3,   // a relock window is open
                            IOF_PROX_RSSI    = 1 << 4 }; // byte 5 implements RSSI

// Which wire a frame arrived on, so one handler can answer on the right one.
// Declared here rather than in the sketch because arduino-cli hoists function
// prototypes above the sketch body, and a parameter type defined in the .ino is
// not visible to them yet.
enum Transport : uint8_t { TR_USB = 0, TR_BUS = 1, TR_BLE = 2 };

enum LinkNak : uint8_t { NAK_NO_IGN = 1, NAK_NO_READER, NAK_BUSY, NAK_BAD_ADDR,
                         NAK_INTERLOCK };
static inline const char* link_nak_name(uint8_t n) {
  switch (n) { case NAK_NO_IGN: return "ignition off";
               case NAK_NO_READER: return "no reader";
               case NAK_BUSY: return "busy";
               case NAK_INTERLOCK: return "interlock refused";
               default: return "bad address"; }
};

enum LinkSource : uint8_t { S_NONE = 0, S_FINGER = 1, S_FOB = 2, S_SWITCH = 3 };

// REMOTE BOOTSEL -- the escape hatch that makes the expansion node flashable
// without touching it. Its USB CDC proved unreliable while the application ran
// perfectly, which left no software route in: no serial port for the 1200-baud
// touch and no reset interface for picotool, so every firmware iteration cost a
// physical BOOTSEL press. The link does not depend on that USB at all, so the
// main node can simply ask it to reboot into the bootloader. The magic byte is
// required so a mangled frame can never trigger it; the CRC already makes that
// unlikely, and this makes it impossible.
//
// In the car this is worth keeping: the expansion Pico may end up behind a
// dashboard with no reachable USB socket, and this is how it gets updated.
static const uint8_t LINK_BOOTSEL_MAGIC = 0x5A;

// What the event is ASKING FOR. Values deliberately match ExpEvent in
// cred_link.h (A_UNLOCK/A_LOCK/A_DENIED == EV_UNLOCK/EV_LOCK/EV_DENIED), so the
// register map's semantics survived the change of transport -- only the wire
// format moved. Under I2C, "unlock" and "lock" each needed their OWN signal
// wire; here they are a field, which is why one UART replaces two lines and
// still leaves room for the user id and score.
enum LinkAction : uint8_t { A_NONE = 0, A_UNLOCK = 1, A_LOCK = 2, A_DENIED = 3 };

// EVENT payload, 6 bytes:  seq, action, source, user_lo, user_hi, score
static const uint8_t LINK_EVENT_LEN = 6;

// Acknowledgement chirps mirror hondaPico.ino: doUnlock() -> flashLights(2),
// doLock() -> flashLights(1). A_DENIED gets NOTHING -- it is reported, never
// actioned, which is the safety property main_node.ino called out.
static inline uint8_t link_action_chirps(uint8_t a) {
  return a == A_UNLOCK ? 2 : (a == A_LOCK ? 1 : 0);
}

static inline uint8_t link_crc8(const uint8_t* d, uint8_t n) {
  uint8_t c = 0;
  for (uint8_t i = 0; i < n; i++) {
    c ^= d[i];
    for (uint8_t b = 0; b < 8; b++) c = (c & 0x80) ? (uint8_t)((c << 1) ^ 0x07) : (uint8_t)(c << 1);
  }
  return c;
}
static inline const char* link_type_name(uint8_t t) {
  switch (t) { case T_PING: return "PING";   case T_PONG: return "PONG";
               case T_EVENT: return "EVENT"; case T_ACK:  return "ACK";
               case T_HELLO: return "HELLO"; case T_BOOTSEL: return "BOOTSEL";
               case T_ENROL: return "ENROL"; case T_STATUS: return "STATUS";
               case T_NAK: return "NAK";     case T_OUT: return "OUT";
               case T_IO: return "IO";       default: return "?"; }
}
static inline const char* link_action_name(uint8_t a) {
  switch (a) { case A_UNLOCK: return "UNLOCK"; case A_LOCK: return "LOCK";
               case A_DENIED: return "DENIED"; default: return "none"; }
}
static inline const char* link_src_name(uint8_t s) {
  switch (s) { case S_FINGER: return "finger"; case S_FOB: return "fob";
               case S_SWITCH: return "switch"; default: return "none"; }
}

// ---- incremental receiver: feed it bytes, it calls back on a good frame
struct LinkRx {
  uint8_t  buf[LINK_MAX_PAY + 5];
  uint8_t  n = 0, want = 0;
  uint32_t good = 0, badCrc = 0, resync = 0;

  // returns true and fills dst/type/pay/len when a frame completes
  bool feed(uint8_t b, uint8_t& dst, uint8_t& type, uint8_t* pay, uint8_t& len) {
    if (n == 0) { if (b != LINK_SOF) { resync++; return false; } buf[n++] = b; return false; }
    buf[n++] = b;
    if (n == 4) {                           // SOF, dst, type, len seen
      want = buf[3];
      if (want > LINK_MAX_PAY) { n = 0; resync++; return false; }
    }
    if (n >= 5 && n == (uint8_t)(5 + want)) {
      uint8_t crc = link_crc8(&buf[1], (uint8_t)(3 + want));
      if (crc == buf[4 + want]) {
        dst = buf[1]; type = buf[2]; len = want;
        for (uint8_t i = 0; i < want; i++) pay[i] = buf[4 + i];
        n = 0; good++; return true;
      }
      badCrc++; n = 0;
    }
    return false;
  }
};

template <class S>
static inline void link_send(S& port, uint8_t dst, uint8_t type, const uint8_t* pay, uint8_t len) {
  uint8_t f[LINK_MAX_PAY + 5];
  f[0] = LINK_SOF; f[1] = dst; f[2] = type; f[3] = len;
  for (uint8_t i = 0; i < len; i++) f[4 + i] = pay[i];
  f[4 + len] = link_crc8(&f[1], (uint8_t)(3 + len));
  port.write(f, (size_t)(5 + len));
}

// Same frame onto a half-duplex RS-485 transceiver. DE must go high before the
// first bit and stay high until the LAST STOP BIT has physically left the shift
// register, or the final character is truncated on the wire -- the classic
// half-duplex bug. flush() waits on the SDK's uart_tx_wait_blocking, which does
// watch the BUSY flag rather than just the FIFO, but one character time of
// margin costs nothing and removes all doubt.
template <class S>
static inline void link_send_de(S& port, uint8_t dePin, uint32_t baud,
                                uint8_t dst, uint8_t type, const uint8_t* pay, uint8_t len) {
  digitalWrite(dePin, HIGH);
  delayMicroseconds(10);                       // driver enable time
  link_send(port, dst, type, pay, len);
  port.flush();
  delayMicroseconds((10UL * 1000000UL) / baud + 20);   // one char + margin
  digitalWrite(dePin, LOW);
}
