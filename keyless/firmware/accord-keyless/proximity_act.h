// Proximity decisions, separate from the unchanged RSSI filter / LED zones.
// Shared with native tests so they exercise the firmware's actual transitions.
#pragma once
#include "proximity.h"
#include <ctype.h>
#include <errno.h>
#include <stdlib.h>

#define PROX_MIN_GAP_DB 6
#define PROX_RSSI_UNKNOWN 127

typedef struct {
    int unlock_dbm, lock_dbm;
    uint32_t dwell_ms, strong_since, weak_since;
    bool armed, is_near, strong, weak;
} proximity_act_t;
#define PROX_ACT_INITIALIZER { -58, -74, 3000, 0, 0, false, false, false, false }

typedef enum {
    PROX_ACT_NONE, PROX_ACT_UNLOCK, PROX_ACT_LOCK,
    PROX_ACT_UNLOCK_OCCUPIED, PROX_ACT_LOCK_OCCUPIED, PROX_ACT_LOCK_TRUNK
} proximity_action_t;

static inline void proximity_act_reset_dwell(proximity_act_t *a) {
    a->strong = a->weak = false;
}
static inline void proximity_act_arm(proximity_act_t *a, bool on) {
    a->armed = on;
    proximity_act_reset_dwell(a);
    if (on) a->is_near = false;
}
static inline bool proximity_act_set(proximity_act_t *a, int unlock, int lock) {
    if (unlock < -127 || unlock > 20 || lock < -127 || lock > 20 ||
        unlock - lock < PROX_MIN_GAP_DB) return false;
    a->unlock_dbm = unlock;
    a->lock_dbm = lock;
    proximity_act_reset_dwell(a);
    return true;
}
// Exactly two integers; reject partial numbers, extra tokens and overflow.
static inline bool proximity_act_parse(proximity_act_t *a, const char *args) {
    long values[2];
    const char *p = args;
    for (int i = 0; i < 2; ++i) {
        while (isspace((unsigned char)*p)) ++p;
        char *end;
        errno = 0;
        values[i] = strtol(p, &end, 10);
        if (end == p || errno || values[i] < -127 || values[i] > 20 ||
            (*end && !isspace((unsigned char)*end))) return false;
        p = end;
    }
    while (isspace((unsigned char)*p)) ++p;
    return !*p && proximity_act_set(a, (int)values[0], (int)values[1]);
}
static inline bool proximity_act_zones(proximity_act_t *a, int unlock, int lock,
                                       uint32_t dwell) {
    if (unlock < 2 || unlock > PROX_ZONE_COUNT || lock < 1 || lock >= unlock ||
        dwell < 200 || dwell > 60000) return false;
    // Z1 has no floor; -128 is proximity_zone_floor's sentinel, not an RSSI.
    int lock_dbm = lock == 1 ? -127 : proximity_zone_floor(lock);
    if (!proximity_act_set(a, proximity_zone_floor(unlock), lock_dbm)) return false;
    a->dwell_ms = dwell;
    return true;
}
static inline proximity_action_t proximity_act_sample(proximity_act_t *a,
        int avg, uint32_t now, bool occupied, bool trunk) {
    if (avg >= a->unlock_dbm) {
        if (!a->strong) a->strong_since = now;
        a->strong = true;
    } else a->strong = false;
    if (avg <= a->lock_dbm) {
        if (!a->weak) a->weak_since = now;
        a->weak = true;
    } else a->weak = false;
    if (!a->armed) return PROX_ACT_NONE;
    if (!a->is_near && a->strong && (uint32_t)(now - a->strong_since) >= a->dwell_ms) {
        a->is_near = true; // Suppressed unlocks also latch; no repeated attempts.
        return occupied ? PROX_ACT_UNLOCK_OCCUPIED : PROX_ACT_UNLOCK;
    }
    if (a->is_near && a->weak && (uint32_t)(now - a->weak_since) >= a->dwell_ms) {
        if (occupied) return PROX_ACT_LOCK_OCCUPIED;
        if (trunk) return PROX_ACT_LOCK_TRUNK;
        a->is_near = false;
        return PROX_ACT_LOCK;
    }
    return PROX_ACT_NONE;
}
// Read-only telemetry: never expose a disconnected or expired average.
static inline int8_t proximity_rssi_byte(const proximity_t *p, bool connected,
                                         uint32_t now) {
    return connected && p->valid && (uint32_t)(now - p->last_sample_ms) < 2500
        ? (int8_t)proximity_average(p) : PROX_RSSI_UNKNOWN;
}
