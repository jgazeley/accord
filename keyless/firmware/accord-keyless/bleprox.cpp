#include "bleprox.h"
#include "proximity.h"
#include "proximity_act.h"
#include "link.h"
#include <BLE.h>
#include <btstack.h>

// ---------------------------------------------------------------- UUIDs
// 7e42xxxx keeps the family of the proximity project's 7e40/7e41 services, so
// the nRF Connect walkthrough in /srv/agent_share/ble/README.md still applies.
#define SVC_UUID    "7e420001-b5a3-f393-e0a9-e50e24dcca9e"
#define PROX_UUID   "7e420002-b5a3-f393-e0a9-e50e24dcca9e"   // read + notify, text
#define STATUS_UUID "7e420003-b5a3-f393-e0a9-e50e24dcca9e"   // read + notify, text
#define CMD_UUID    "7e420004-b5a3-f393-e0a9-e50e24dcca9e"   // write, text

// DO NOT build these from the strings above. BLEUUID's String constructor parses
// with sscanf("%x-%x-%x-%x-%llx") and silently returns an ALL-ZERO uuid if that
// does not yield 5 fields -- which is what happens on this target, so every
// characteristic ended up registered under a null UUID and no client could find
// the service. The same 16 bytes, given directly, are unambiguous. Byte order is
// just the hex digits in reading order: uuid128[0] is the most significant.
static const uint8_t U_SVC[16]    = { 0x7e,0x42,0x00,0x01, 0xb5,0xa3, 0xf3,0x93,
                                      0xe0,0xa9, 0xe5,0x0e,0x24,0xdc,0xca,0x9e };
static const uint8_t U_PROX[16]   = { 0x7e,0x42,0x00,0x02, 0xb5,0xa3, 0xf3,0x93,
                                      0xe0,0xa9, 0xe5,0x0e,0x24,0xdc,0xca,0x9e };
static const uint8_t U_STATUS[16] = { 0x7e,0x42,0x00,0x03, 0xb5,0xa3, 0xf3,0x93,
                                      0xe0,0xa9, 0xe5,0x0e,0x24,0xdc,0xca,0x9e };
static const uint8_t U_CMD[16]    = { 0x7e,0x42,0x00,0x04, 0xb5,0xa3, 0xf3,0x93,
                                      0xe0,0xa9, 0xe5,0x0e,0x24,0xdc,0xca,0x9e };

static proximity_t prox;
static char        proxText[32] = "RSSI UNKNOWN";

// ---------------------------------------------------------------- RSSI plumbing
// The Arduino BLE library owns the GATT server and advertising, but does not
// expose the connection handle or any way to read a connected peer's RSSI
// (its only RSSI is from scan reports, i.e. the client role). So we register a
// SECOND btstack HCI event handler alongside it and track the handle ourselves
// from plain HCI events -- no dependency on library internals, which are
// protected members. Mechanism copied from /srv/agent_share/ble/firmware/main.c.
static hci_con_handle_t conHandle = HCI_CON_HANDLE_INVALID;
static bool     rssiPending = false;
static uint32_t rssiAskedAt = 0, nextRssi = 0;
static uint32_t samples = 0, timeouts = 0;
static uint32_t rstConn = 0, rstDisc = 0, rstExpire = 0, leMeta = 0, discEvt = 0;

// SINGLE WRITER. btstack delivers these events from its own context, which can
// preempt loop(), so the HCI handler below does not touch `prox`, `proxText` or
// the GATT characteristics at all -- it drops the reading in this mailbox and
// sets a flag. bleprox_tick() is the only thing that calls proximity_sample(),
// proximity_expire() or publishes. Mixing the two is what produced the original
// bug: loop() saw `valid == true` alongside a stale `last_sample_ms`, decided
// the reading had expired, and reset the filter -- 34 spurious expiries in 53
// samples, so roughly every other notification came out "RSSI UNKNOWN" and the
// smoothed value kept restarting from the raw one. The multicore traps in
// /srv/agent_share/ble/docs/pico-w-ble-lessons.md are the same hazard.
static volatile int      mbRssi  = 0;
static volatile uint32_t mbAt    = 0;
static volatile bool     mbFull  = false;
static volatile bool     evConn  = false, evDisc = false;

static btstack_packet_callback_registration_t hciReg;

static void prox_on_sample(int rssi, uint32_t now);

static void hci_handler(uint8_t type, uint16_t channel, uint8_t* packet, uint16_t size) {
  (void)channel;
  if (type != HCI_EVENT_PACKET) return;
  switch (hci_event_packet_get_type(packet)) {

    case HCI_EVENT_LE_META:
      leMeta++;
      if (hci_event_le_meta_get_subevent_code(packet) == HCI_SUBEVENT_LE_CONNECTION_COMPLETE) {
        rstConn++;
        conHandle   = hci_subevent_le_connection_complete_get_connection_handle(packet);
        rssiPending = false;
        evConn      = true;
      }
      break;

    case HCI_EVENT_DISCONNECTION_COMPLETE:
      discEvt++;
      if (hci_event_disconnection_complete_get_connection_handle(packet) == conHandle) {
        rstDisc++;
        conHandle   = HCI_CON_HANDLE_INVALID;
        rssiPending = false;
        evDisc      = true;
      }
      break;

    // gap_read_rssi() answers here on success. A failed read answers as a
    // command-complete with a non-zero status instead, handled below.
    case GAP_EVENT_RSSI_MEASUREMENT:
      if (size >= 5 && conHandle != HCI_CON_HANDLE_INVALID &&
          gap_event_rssi_measurement_get_con_handle(packet) == conHandle) {
        rssiPending = false;
        int rssi = gap_event_rssi_measurement_get_rssi(packet);
        if (rssi >= 128) rssi -= 256;           // the field is signed, read as u8
        mbRssi = rssi; mbAt = millis(); mbFull = true;   // mailbox; loop() filters
      }
      break;

    case HCI_EVENT_COMMAND_COMPLETE:
      if (size >= 8 && hci_event_command_complete_get_command_opcode(packet) == HCI_OPCODE_HCI_READ_RSSI
          && little_endian_read_16(packet, 6) == conHandle) {
        rssiPending = false;
        if (packet[5]) Serial.printf("ble: RSSI read error 0x%02x\n", packet[5]);
      }
      break;

    default: break;
  }
}

// ---------------------------------------------------------------- GATT service
class HondaBleService : public BLEService, public BLECharacteristicCallbacks {
public:
  HondaBleService() : BLEService(BLEUUID(U_SVC)) {
    cProx   = new BLECharacteristic(BLEUUID(U_PROX),   BLERead | BLENotify, "proximity r/s/zone");
    cStatus = new BLECharacteristic(BLEUUID(U_STATUS), BLERead | BLENotify, "hondaPico status");
    cCmd    = new BLECharacteristic(BLEUUID(U_CMD),    BLEWrite,            "command: unlock lock trunk flasher horn sec_led ceiling io prox relock thresh");
    cCmd->setCallbacks(this);
    cProx->setValue(String("RSSI UNKNOWN"));
    cStatus->setValue(String("booting"));
    cCmd->setValue(String("ready"));
    addCharacteristic(cProx);
    addCharacteristic(cStatus);
    addCharacteristic(cCmd);
  }

  void pubProx(const String& s)   { cProx->setValue(s); }
  void pubStatus(const String& s) { cStatus->setValue(s); }

private:
  void onWrite(BLECharacteristic* c) override;
  BLECharacteristic *cProx, *cStatus, *cCmd;
};

static HondaBleService svc;

// When the next periodic status telemetry publish is due. At file scope, not a
// local static in bleprox_tick(), because onWrite() has to push it back: the
// status characteristic serves BOTH periodic telemetry and command replies, and
// without this the 5 s telemetry publish overwrites a reply before the central
// has read it. See "status replies were being overwritten" in circuits.md.
static uint32_t nextStatus = 0;
#define STATUS_PERIOD_MS 5000
#define REPLY_HOLD_MS    3000

// ---------------------------------------------------------------- proximity act
// Volatile dBm thresholds; the dead band and near latch provide hysteresis.
static proximity_act_t act = PROX_ACT_INITIALIZER;
static uint32_t actUnlocks = 0, actLocks = 0;
static bool     verbose     = false;
static int      lastPrinted = -99;

static void prox_on_sample(int rssi, uint32_t now) {
  samples++;
  // proximity_sample() can expire internally, so reset dwell before it too.
  if (!prox.valid || (uint32_t)(now - prox.last_sample_ms) >= 2500)
    proximity_act_reset_dwell(&act);
  if (!proximity_sample(&prox, rssi, now)) {
    Serial.printf("ble: RSSI out of range (%d), ignored\n", rssi);
    return;
  }
  int z = prox.zone;
  snprintf(proxText, sizeof(proxText), "r%d s%d Z%d", prox.raw_dbm, proximity_average(&prox), z);
  svc.pubProx(String(proxText));

  if (verbose || z != lastPrinted) {
    Serial.printf("ble: %s  %s%s\n", proxText,
                  act.armed ? (act.is_near ? "[near]" : "[away]") : "[observing]",
                  z != lastPrinted ? "  <- zone change" : "");
    lastPrinted = z;
  }

  const char* occ = hp_occupied_reason();
  proximity_action_t action = proximity_act_sample(&act, proximity_average(&prox),
                                                   now, occ != nullptr, hp_trunk_open());
  switch (action) {
    case PROX_ACT_UNLOCK_OCCUPIED:
      Serial.printf("ble: proximity unlock SUPPRESSED, %s\n", occ);
      break;
    case PROX_ACT_LOCK_OCCUPIED:
      Serial.printf("ble: proximity lock SUPPRESSED, %s\n", occ);
      break;
    case PROX_ACT_LOCK_TRUNK:
      Serial.println("ble: proximity lock SUPPRESSED, trunk is open");
      break;
    case PROX_ACT_UNLOCK:
    case PROX_ACT_LOCK:
      if (action == PROX_ACT_UNLOCK) actUnlocks++; else actLocks++;
      hp_entry_action(action == PROX_ACT_UNLOCK);
      Serial.printf("ble: PROXIMITY %s  s%d held >= %lums  (unlocks=%lu locks=%lu)\n",
                    action == PROX_ACT_UNLOCK ? "UNLOCK" : "LOCK",
                    proximity_average(&prox), (unsigned long)act.dwell_ms,
                    (unsigned long)actUnlocks, (unsigned long)actLocks);
      svc.pubStatus(hp_status_text());
      break;
    default: break;
  }
  // Deliberately NO auto-lock on disconnect. A BLE link can drop while the
  // phone is still beside the car, and a disconnect is not reported until the
  // connection timeout expires, so acting on it would lock at the worst moment.
}

// ---------------------------------------------------------------- cmd characteristic
void HondaBleService::onWrite(BLECharacteristic* c) {
  String s((const char*)c->valueData(), c->valueLen());
  s.trim(); s.toLowerCase();
  String arg;
  int sp = s.indexOf(' ');
  if (sp > 0) { arg = s.substring(sp + 1); arg.trim(); s = s.substring(0, sp); }

  Serial.printf("ble: cmd \"%s%s%s\"\n", s.c_str(), arg.length() ? " " : "", arg.c_str());

  // Keep this reply readable: hold the periodic publisher off for REPLY_HOLD_MS.
  nextStatus = millis() + REPLY_HOLD_MS;

  if      (s == "unlock")  { hp_entry_action(true); }
  else if (s == "lock")    { hp_entry_action(false); }
  else if (s == "trunk")   {
    // The interlock lives in the output layer, so all this has to do is report.
    if (!hp_out_pulse(O_TRUNK)) {
      pubStatus(F("trunk REFUSED: already open"));
      Serial.println("ble: trunk REFUSED by interlock (trunk already open)");
      return;
    }
  }
  else if (s == "flasher") { hp_out_pulse(O_FLASHER); }
  else if (s == "horn")    { hp_out_pulse(O_HORN); }
  else if (s == "ceiling") { hp_out_set(O_CEILING, arg != "off"); }
  else if (s == "sec_led") {
    if (arg == "auto") hp_sec_led_auto();
    else               hp_out_set(O_SEC_LED, arg != "off");
  } else if (s == "prox") {
    bleprox_arm(arg == "on");
  } else if (s == "thresh") {
    if (arg.length() && !proximity_act_parse(&act, arg.c_str())) {
      pubStatus(F("thresh REFUSED: use thresh <unlock> <lock>; integers -127..20 dBm, unlock >= lock + 6 dB (minimum gap prevents chatter)"));
      return;
    }
    pubStatus(String("thresh unlock=") + String(act.unlock_dbm) + " lock=" +
              String(act.lock_dbm) + " dBm gap=" + String(act.unlock_dbm - act.lock_dbm) +
              " dB dwell=" + String(act.dwell_ms) + "ms (volatile)");
    return;
  } else if (s == "relock") {
    // "relock on" / "relock off" / "relock 45" (seconds, 5..300).
    if (arg == "on" || arg == "off") {
      hp_relock_set(arg == "on", 0);
    } else {
      long secs = arg.toInt();
      if (secs <= 0 || !hp_relock_set(true, (uint32_t)secs * 1000UL)) {
        pubStatus(F("relock: use on|off|<5..300 seconds>"));
        return;
      }
    }
  } else if (s == "io") {
    pubStatus(hp_io_text());
    return;
  } else if (s == "status") {
    // Read-only. Added because a central had no non-actuating way to refresh
    // this characteristic: every other recognised command drives an output, and
    // reading the characteristic cold just returns whatever was published last.
    pubStatus(hp_status_text());
    return;
  } else if (s == "help") {
    pubStatus(F("unlock lock trunk flasher horn ceiling on|off "
                "sec_led on|off|auto prox on|off relock on|off|<s> "
                "thresh [unlock lock] io status help"));
    return;
  } else {
    pubStatus(String("? ") + s);
    return;
  }
  pubStatus(hp_status_text());
}

// ---------------------------------------------------------------- public
void bleprox_begin(const char* name) {
  proximity_reset(&prox);
  // BLESecurityNone, not JustWorks, and NOT a security downgrade -- see below.
  //
  // With BLESecurityJustWorks the library does two things that break phones:
  //   BLE.cpp:90        sm_set_authentication_requirements(0 | SM_AUTHREQ_BONDING)
  //   BLEServer.cpp:147 sm_request_pairing(con_handle)   <- on EVERY connect
  // So the board itself asks to bond the moment anything connects. There is no
  // bonded-key store behind that request, so the phone sits on "Connected,
  // Bonding..." until it times out, and Android then caches the failure and
  // retries it on later connects. "Just tap CONNECT, do not Bond" does not help
  // -- the peripheral is the one initiating, not the phone.
  //
  // Nothing is lost by turning it off: every characteristic here is plain
  // BLERead | BLENotify / BLEWrite with no encryption requirement, so JustWorks
  // was never gating access to any of them. It pairs with anything that asks,
  // which is not authentication (see the SECURITY note in bleprox.h). Real entry
  // auth needs a passkey and keys in flash, which this library cannot do at all.
  BLE.setSecurity(BLESecurityNone);
  BLE.begin(name);
  BLE.server()->addService(&svc);
  BLE.startAdvertising();

  hciReg.callback = hci_handler;
  hci_add_event_handler(&hciReg);

  // Evidence for the comment on U_SVC above: parse the same UUID both ways and
  // print them. If the string form comes back all zeros, this target's sscanf
  // cannot do "%llx" and BLEUUID(String) is unusable here.
  {
    BLEUUID fromStr(String(SVC_UUID)), fromBytes(U_SVC);
    Serial.printf("ble:   uuid from bytes  = %s\n", fromBytes.toString().c_str());
    Serial.printf("ble:   uuid from string = %s%s\n", fromStr.toString().c_str(),
                  fromStr == fromBytes ? "" : "   <-- BLEUUID(String) IS BROKEN HERE");
  }

  Serial.printf("ble:   advertising as \"%s\"  svc %s\n", name, SVC_UUID);
  Serial.printf("ble:   prox %s (read+notify)\n", PROX_UUID);
  Serial.printf("ble:   cmd  %s (write: unlock lock trunk flasher horn sec_led ceiling io prox on|off thresh [unlock lock])\n", CMD_UUID);
  Serial.printf("ble:   proximity actions DISARMED (press P, or write \"prox on\")\n");
}

bool bleprox_connected() { return conHandle != HCI_CON_HANDLE_INVALID; }
String bleprox_text()    { return String(proxText); }
int8_t bleprox_rssi() {
  return proximity_rssi_byte(&prox, bleprox_connected() && !evConn && !evDisc, millis());
}
bool bleprox_armed()     { return act.armed; }

bool bleprox_led(uint32_t now) {
  return proximity_led(&prox, bleprox_connected(), now);
}

void bleprox_arm(bool on) {
  proximity_act_arm(&act, on);
  Serial.printf("ble: proximity actions %s  (unlock >= %d, lock <= %d dBm, dwell %lums)\n",
                on ? "ARMED" : "disarmed", act.unlock_dbm, act.lock_dbm,
                (unsigned long)act.dwell_ms);
}

void bleprox_set_zones(int unlockZone, int lockZone, uint32_t dwell) {
  if (!proximity_act_zones(&act, unlockZone, lockZone, dwell)) {
    Serial.println("ble: zones REFUSED: invalid zones/dwell or gap below 6 dB");
    return;
  }
  Serial.printf("ble: zones Z%d/Z%d -> unlock >= %d, lock <= %d dBm, dwell %lums\n",
                unlockZone, lockZone, act.unlock_dbm, act.lock_dbm,
                (unsigned long)act.dwell_ms);
}

void bleprox_print(bool v) {
  verbose = v;
  Serial.printf("ble: connected=%s %s  armed=%s state=%s  samples=%lu timeouts=%lu\n",
                bleprox_connected() ? "yes" : "no", proxText,
                act.armed ? "yes" : "no", act.is_near ? "near" : "away",
                (unsigned long)samples, (unsigned long)timeouts);
  Serial.printf("ble: unlock >= %d, lock <= %d dBm, dwell %lums   verbose=%s\n",
                act.unlock_dbm, act.lock_dbm, (unsigned long)act.dwell_ms, verbose ? "on" : "off");
  Serial.printf("ble: resets conn=%lu disc=%lu expire=%lu   leMeta=%lu discEvt=%lu  lastSample=%lums ago valid=%u\n",
                (unsigned long)rstConn, (unsigned long)rstDisc, (unsigned long)rstExpire,
                (unsigned long)leMeta, (unsigned long)discEvt,
                (unsigned long)(millis() - prox.last_sample_ms), prox.valid);
  Serial.print("ble: zone floors dBm:");
  for (int z = 2; z <= PROX_ZONE_COUNT; z++) Serial.printf(" Z%d>=%d", z, proximity_zone_floor(z));
  Serial.println();
}

void bleprox_tick(uint32_t caller_now) {
  // Use a FRESH millis(), not the caller's. loop() captures `now` once at the
  // top; a reading can be timestamped by the btstack callback microseconds
  // later, so last_sample_ms ends up GREATER than the cached now. Then
  //     (uint32_t)(now - last_sample_ms)
  // in proximity_expire() wraps to ~4.29e9, which is trivially >= 2500, so the
  // filter was declared stale and reset on essentially every sample: 34 expiries
  // in 53 samples, every other notification "RSSI UNKNOWN", and the smoothed
  // value permanently equal to the raw one because `valid` was always false.
  // The shared proximity.c is left alone -- it is the tested copy -- so the
  // ordering is fixed here, where it was broken.
  (void)caller_now;
  const uint32_t now = millis();

  // Connection changes, handled here so the filter is only ever touched from
  // this one context.
  if (evConn) {
    evConn = false;
    proximity_reset(&prox);
    proximity_act_reset_dwell(&act);
    strcpy(proxText, "RSSI UNKNOWN");
    svc.pubProx(String(proxText));
    lastPrinted = -99;
    nextRssi = now;
    Serial.println("ble: client connected");
  }
  if (evDisc) {
    evDisc = false;
    proximity_reset(&prox);
    proximity_act_reset_dwell(&act);
    strcpy(proxText, "RSSI UNKNOWN");
    svc.pubProx(String(proxText));
    lastPrinted = -99;
    Serial.println("ble: client disconnected (no auto-lock on disconnect, by design)");
  }

  bool connected = bleprox_connected();

  // Drain the mailbox BEFORE the expiry check, so a reading that arrived while
  // we were elsewhere in the loop counts as fresh.
  if (mbFull) {
    mbFull = false;
    if (connected) prox_on_sample(mbRssi, mbAt);
  }

  // A reading older than 2.5 s stops counting as valid, which is what turns the
  // LED to its "connected but no fresh reading" flicker.
  if (connected && proximity_expire(&prox, now)) {
    rstExpire++;
    proximity_act_reset_dwell(&act);
    strcpy(proxText, "RSSI UNKNOWN");
    svc.pubProx(String(proxText));
    lastPrinted = -99;
  }

  if (rssiPending && (uint32_t)(now - rssiAskedAt) >= 2000) {
    rssiPending = false; timeouts++;
  }
  if (connected && !rssiPending && (int32_t)(now - nextRssi) >= 0) {
    nextRssi = now + 500;                    // 2 Hz, same as the reference
    rssiAskedAt = now;
    rssiPending = true;
    if (!gap_read_rssi(conHandle)) rssiPending = false;
  }

  if (connected && (int32_t)(now - nextStatus) >= 0) {
    nextStatus = now + STATUS_PERIOD_MS;
    svc.pubStatus(hp_status_text());
  }
}
