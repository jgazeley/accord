// Zone logic for BLE RSSI proximity. Copied UNCHANGED from
// /srv/agent_share/ble/firmware/proximity.{c,h}, which has native unit tests
// covering every zone boundary, the hysteresis either side of each, smoothing,
// invalid values, stale readings, connection resets and timestamp wrap:
//
//   cc -std=c11 -Wall -Wextra -Werror -I. ../tests/proximity_test.c proximity.c -o t
//
// The only addition here is the extern "C" guard, because this copy is included
// from a C++ sketch. Do not "improve" the logic in one copy only -- if it
// changes, change it there, re-run those tests, and copy it back.
#ifndef PICO_PROXIMITY_H
#define PICO_PROXIMITY_H
#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// Zone 0 = unknown, 1 = weakest signal ... PROX_ZONE_COUNT = strongest.
#define PROX_ZONE_COUNT 6
// Duration of one LED cycle. Zone n (below the strongest) shows n flashes per cycle.
#define PROX_LED_CYCLE_MS 2000
#define PROX_LED_ON_MS 100
#define PROX_LED_FLASH_PERIOD_MS 250
// Hysteresis applied on each side of every zone boundary, in dB.
#define PROX_HYSTERESIS_DB 2

typedef struct {
    bool valid;
    int raw_dbm;
    int average_q8;
    uint32_t last_sample_ms;
    int zone;
} proximity_t;

void proximity_reset(proximity_t *p);
bool proximity_sample(proximity_t *p, int rssi, uint32_t now);
bool proximity_expire(proximity_t *p, uint32_t now);
int proximity_average(const proximity_t *p);
// Weakest smoothed RSSI (dBm) that nominally belongs to zone 2..PROX_ZONE_COUNT.
int proximity_zone_floor(int zone);
bool proximity_led(const proximity_t *p, bool connected, uint32_t now);

#ifdef __cplusplus
}
#endif
#endif
