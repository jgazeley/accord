#include "proximity.h"

// Nominal lower edge of zones 2..6 in dBm; zone 1 is everything weaker than
// zone 2's floor. Adjust these to move the bands; keep them ascending.
static const int zone_floor_dbm[PROX_ZONE_COUNT - 1] = {-82, -74, -66, -58, -50};

int proximity_zone_floor(int zone) {
    return zone >= 2 && zone <= PROX_ZONE_COUNT ? zone_floor_dbm[zone - 2] : -128;
}

void proximity_reset(proximity_t *p) {
    *p = (proximity_t){0};
}

int proximity_average(const proximity_t *p) {
    return p->average_q8 >= 0 ? (p->average_q8 + 128) / 256
                            : -((-p->average_q8 + 128) / 256);
}

bool proximity_expire(proximity_t *p, uint32_t now) {
    if (p->valid && (uint32_t)(now - p->last_sample_ms) >= 2500) {
        proximity_reset(p);
        return true;
    }
    return false;
}

bool proximity_sample(proximity_t *p, int rssi, uint32_t now) {
    // Bluetooth RSSI 127 means unavailable; accepted LE range is -127..20 dBm.
    if (rssi < -127 || rssi > 20) return false;
    proximity_expire(p, now);
    p->raw_dbm = rssi;
    p->average_q8 = p->valid ? p->average_q8 + (rssi * 256 - p->average_q8) / 4
                             : rssi * 256;
    p->last_sample_ms = now;
    p->valid = true;
    int avg = proximity_average(p);
    if (p->zone == 0) {
        p->zone = 1;
        while (p->zone < PROX_ZONE_COUNT && avg >= proximity_zone_floor(p->zone + 1)) p->zone++;
        return true;
    }
    // Existing zone: a boundary must be crossed by the hysteresis margin.
    // A large change still steps through several zones in one sample.
    while (p->zone < PROX_ZONE_COUNT
           && avg >= proximity_zone_floor(p->zone + 1) + PROX_HYSTERESIS_DB) p->zone++;
    while (p->zone > 1
           && avg < proximity_zone_floor(p->zone) - PROX_HYSTERESIS_DB) p->zone--;
    return true;
}

bool proximity_led(const proximity_t *p, bool connected, uint32_t now) {
    if (!connected) return false;
    // Connected without a fresh reading: rapid 50 ms flicker.
    if (!p->valid) return now % 100 < 50;
    // Strongest zone is solid; zone n shows n short flashes per cycle.
    if (p->zone >= PROX_ZONE_COUNT) return true;
    uint32_t phase = now % PROX_LED_CYCLE_MS;
    return phase < (uint32_t)p->zone * PROX_LED_FLASH_PERIOD_MS
        && phase % PROX_LED_FLASH_PERIOD_MS < PROX_LED_ON_MS;
}
