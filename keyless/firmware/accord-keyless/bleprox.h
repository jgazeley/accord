// BLE peripheral + phone proximity for hondaPico.
//
// Three stages, in the order they are meant to be used:
//
//   1. OBSERVE   -- connect from the phone (no pairing: see bleprox.cpp), watch
//                   RSSI / zone on serial and on D41.
//                   Nothing actuates. This is the calibration stage.
//   2. ACT       -- `prox on` arms proximity lock/unlock using the dBm
//                   thresholds you settled on in stage 1. Disarmed at boot,
//                   every boot, on purpose.
//   3. CONTROL   -- write text commands to the cmd characteristic from
//                   nRF Connect: unlock, lock, trunk, horn, io, status, prox on/off ...
//
// RSSI is measured AT THE PICO, from the connected phone's transmissions. That
// is not the same number nRF Connect's own graph shows, which is the Pico's
// signal measured at the phone. The two directions differ, sometimes by a lot.
//
// SECURITY -- read this before trusting it with a door.
// The Arduino BLE library exposes only BLESecurityNone and BLESecurityJustWorks;
// there is no passkey and no bonded-key store here. We run BLESecurityNone,
// because JustWorks made the peripheral call sm_request_pairing() on every
// connect against a store that does not exist -- it bought nothing and hung
// phones. Either way this stage is a measurement and convenience tool, NOT entry
// authentication: the characteristics require no encryption in both modes. RSSI is also trivially spoofable by anything that can raise its
// transmit power. Real entry auth needs bonding with a passkey and keys persisted
// in flash -- that recipe already exists, against BlueZ and Android, in
// /srv/agent_share/ir (firmware/ble.c, docs/ble.md), and the two multicore traps
// that silently break btstack bond storage are written up in
// /srv/agent_share/ble/docs/pico-w-ble-lessons.md.
#pragma once
#include <Arduino.h>
#include <stdint.h>

// ---- implemented by the sketch, called by the BLE command parser ------------
// Kept as a narrow interface so this file knows nothing about the pin map.
bool     hp_out_pulse(uint8_t id);   // false = an interlock refused it
// A real entry action: pulse + illuminated entry + confirmation flashes.
// Use this, not hp_out_pulse(O_UNLOCK), for anything the owner would call
// "unlock the car" -- otherwise the car does not acknowledge.
void     hp_entry_action(bool unlocking);
void     hp_out_set(uint8_t id, bool on);
void     hp_sec_led_auto();
bool     hp_ignition_on();
// nullptr when the car looks empty, else a short reason ("door open", "key in",
// "ignition on"). Proximity lock and auto-relock share it so they can never
// disagree about whether somebody is in the car.
const char* hp_occupied_reason();
bool     hp_relock_enabled();
bool     hp_trunk_open();
uint32_t hp_relock_remaining_ms();          // 0 = no window open
bool     hp_relock_set(bool on, uint32_t ms);   // ms = 0 keeps the timeout
String   hp_status_text();     // one line: ign, vbat, outputs
String   hp_io_text();         // one line: every input and output

// ---- called by the sketch ---------------------------------------------------
void bleprox_begin(const char* name);
void bleprox_tick(uint32_t now);
bool bleprox_connected();
bool bleprox_led(uint32_t now);      // zone flash pattern; see the table below
String bleprox_text();               // "r-62 s-65 Z4", or "RSSI UNKNOWN"
void bleprox_print(bool verbose);    // serial dump of the current state
int8_t bleprox_rssi();              // smoothed dBm; 127 = disconnected/stale
bool bleprox_armed();
void bleprox_arm(bool on);
void bleprox_set_zones(int unlockZone, int lockZone, uint32_t dwellMs);

// LED, when a client is connected (from proximity_led in the tested copy):
//   Z6  solid            -50 dBm or stronger
//   Z5  5 flashes / 2 s  -58..-51
//   Z4  4 flashes        -66..-59
//   Z3  3 flashes        -74..-67
//   Z2  2 flashes        -82..-75
//   Z1  1 flash          weaker than -82
//   connected, no fresh reading: rapid 50 ms flicker
