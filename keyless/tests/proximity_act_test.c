// cc -std=c11 -Wall -Wextra -Werror tests/proximity_act_test.c -o /tmp/prox-test && /tmp/prox-test
#include <stdio.h>
#include <string.h>
#include "../firmware/accord-keyless/proximity_act.h"
#include "../firmware/accord-keyless/proximity.c"
static int checks, failures;
#define CHECK(expr) do { ++checks; if (!(expr)) { ++failures; printf("FAIL line %d: %s\n", __LINE__, #expr); } } while (0)
static proximity_act_t act;
static void reset(void) {
    act = (proximity_act_t)PROX_ACT_INITIALIZER;
    proximity_act_set(&act, -80, -90);
    proximity_act_arm(&act, true);
}
static proximity_action_t sample(int avg, uint32_t now) {
    return proximity_act_sample(&act, avg, now, false, false);
}
int main(void) {
    act = (proximity_act_t)PROX_ACT_INITIALIZER;
    CHECK(!act.armed && !act.is_near && act.unlock_dbm == -58 && act.lock_dbm == -74);
    CHECK(sample(-40, 0) == PROX_ACT_NONE && sample(-40, 4000) == PROX_ACT_NONE);
    reset();
    CHECK(proximity_act_parse(&act, "-80 -86")); // exactly six
    const char *bad[] = {"-80 -85", "-80 -80", "-90 -80", "-128 -140", "21 -90",
        "-80", "", "-80 -90 extra", "-80x -90", "-80.0 -90", "-80-90", "-80 -90.0",
        "9999999999999999999999999999 -90", "-80 -9999999999999999999999999"};
    for (unsigned i = 0; i < sizeof(bad)/sizeof(bad[0]); ++i) {
        proximity_act_t before = act;
        CHECK(!proximity_act_parse(&act, bad[i]));
        CHECK(memcmp(&before, &act, sizeof(act)) == 0);
    }
    CHECK(proximity_act_parse(&act, " \t-80  -90\t "));
    CHECK(proximity_act_parse(&act, "20 -127"));
    reset();
    CHECK(sample(-80, 0) == PROX_ACT_NONE); // zero timestamp must not underflow
    CHECK(sample(-80, 2999) == PROX_ACT_NONE);
    CHECK(sample(-80, 3000) == PROX_ACT_UNLOCK && act.is_near);
    CHECK(sample(-70, 6000) == PROX_ACT_NONE);
    CHECK(sample(-85, 7000) == PROX_ACT_NONE && act.is_near);
    CHECK(sample(-90, 8000) == PROX_ACT_NONE);
    CHECK(sample(-90, 10999) == PROX_ACT_NONE);
    CHECK(sample(-90, 11000) == PROX_ACT_LOCK && !act.is_near);
    CHECK(sample(-100, 15000) == PROX_ACT_NONE);
    CHECK(sample(-85, 16000) == PROX_ACT_NONE && !act.is_near);
    reset();
    CHECK(sample(-80, 100) == PROX_ACT_NONE);
    CHECK(sample(-81, 3099) == PROX_ACT_NONE);
    CHECK(sample(-80, 3100) == PROX_ACT_NONE);
    CHECK(sample(-80, 6099) == PROX_ACT_NONE);
    CHECK(sample(-80, 6100) == PROX_ACT_UNLOCK);
    CHECK(sample(-90, 6200) == PROX_ACT_NONE);
    CHECK(sample(-89, 9199) == PROX_ACT_NONE);
    CHECK(sample(-90, 9200) == PROX_ACT_NONE);
    CHECK(sample(-90, 12199) == PROX_ACT_NONE);
    CHECK(sample(-90, 12200) == PROX_ACT_LOCK);
    // Door/key/ign all arrive as the shared hp_occupied_reason() boolean.
    reset(); sample(-80, 100);
    CHECK(proximity_act_sample(&act, -80, 3100, true, false) == PROX_ACT_UNLOCK_OCCUPIED);
    CHECK(act.is_near && sample(-80, 4000) == PROX_ACT_NONE);
    sample(-90, 4100);
    CHECK(proximity_act_sample(&act, -90, 7100, true, false) == PROX_ACT_LOCK_OCCUPIED);
    CHECK(act.is_near);
    CHECK(proximity_act_sample(&act, -90, 7200, false, true) == PROX_ACT_LOCK_TRUNK);
    CHECK(act.is_near && sample(-90, 7300) == PROX_ACT_LOCK);
    reset();
    CHECK(proximity_act_sample(&act, -80, 100, false, true) == PROX_ACT_NONE);
    CHECK(proximity_act_sample(&act, -80, 3100, false, true) == PROX_ACT_UNLOCK);
    // Reset on arming, configuration, disconnect or expiry restarts full dwell.
    reset(); sample(-80, 100); proximity_act_arm(&act, true);
    CHECK(sample(-80, 4000) == PROX_ACT_NONE);
    CHECK(sample(-80, 7000) == PROX_ACT_UNLOCK);
    proximity_act_arm(&act, false);
    CHECK(sample(-90, 8000) == PROX_ACT_NONE && sample(-90, 12000) == PROX_ACT_NONE);
    reset(); sample(-80, 100);
    CHECK(proximity_act_set(&act, -80, -90));
    CHECK(sample(-80, 4000) == PROX_ACT_NONE);
    proximity_act_reset_dwell(&act);
    CHECK(sample(-80, 8000) == PROX_ACT_NONE);
    CHECK(sample(-80, 11000) == PROX_ACT_UNLOCK);
    reset(); sample(-80, UINT32_MAX - 999);
    CHECK(sample(-80, 1999) == PROX_ACT_NONE);
    CHECK(sample(-80, 2000) == PROX_ACT_UNLOCK);
    CHECK(proximity_act_zones(&act, 5, 3, 3000));
    CHECK(act.unlock_dbm == proximity_zone_floor(5) && act.lock_dbm == proximity_zone_floor(3) && act.dwell_ms == 3000);
    CHECK(proximity_act_zones(&act, 4, 2, 4000));
    CHECK(act.unlock_dbm == -66 && act.lock_dbm == -82 && act.dwell_ms == 4000);
    CHECK(proximity_act_zones(&act, 2, 1, 3000) && act.lock_dbm == -127);
    CHECK(!proximity_act_zones(&act, 4, 4, 3000));
    CHECK(!proximity_act_zones(&act, 7, 2, 3000));
    CHECK(!proximity_act_zones(&act, 4, 0, 3000));
    CHECK(!proximity_act_zones(&act, 4, 2, 199));
    CHECK(!proximity_act_zones(&act, 4, 2, 60001));
    proximity_t p; proximity_reset(&p);
    CHECK(proximity_rssi_byte(&p, true, 0) == 127);
    CHECK(proximity_sample(&p, -80, 100));
    CHECK(proximity_rssi_byte(&p, true, 100) == -80);
    CHECK(proximity_rssi_byte(&p, false, 100) == 127);
    CHECK(proximity_rssi_byte(&p, true, 2599) == -80);
    CHECK(proximity_rssi_byte(&p, true, 2600) == 127);
    CHECK(proximity_sample(&p, -96, 600) && proximity_rssi_byte(&p, true, 600) == -84);
    CHECK(proximity_sample(&p, -127, 4000) && proximity_rssi_byte(&p, true, 4000) == -127);
    CHECK(!proximity_sample(&p, 127, 4100));
    proximity_reset(&p); proximity_sample(&p, 0, UINT32_MAX - 99);
    CHECK(proximity_rssi_byte(&p, true, 0) == 0);
    printf("%d checks, %d failures\n", checks, failures);
    return failures != 0;
}
