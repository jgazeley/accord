/* Truth table for the trunk interlock, with the same polarity chain as the
 * firmware: the latch switch grounds orange when the lid is OPEN, the PC817
 * collector sits on INPUT_PULLUP, so ACTIVE == LOW == open. */
#include <stdio.h>
#include <stdbool.h>

#define O_TRUNK 2
#define O_LOCK  0

static int pin_level;                                  /* HIGH=1 LOW=0 */
static bool inActive(void)    { return pin_level == 0; }   /* LOW = active */
static unsigned char ix = 0;
static bool trunkIsOpen(void) { return ix != 0xFF && inActive(); }

static bool outPulse(int i) {
    if (i == O_TRUNK && trunkIsOpen()) return false;
    return true;
}

int main(void) {
    struct { int lvl; int out; bool want; const char *desc; } t[] = {
        { 1, O_TRUNK, true,  "trunk CLOSED (orange floats high) -> pulse allowed" },
        { 0, O_TRUNK, false, "trunk OPEN   (orange grounded)    -> pulse REFUSED" },
        { 0, O_LOCK,  true,  "trunk OPEN, lock channel          -> unaffected"    },
        { 1, O_LOCK,  true,  "trunk CLOSED, lock channel        -> unaffected"    },
    };
    int fail = 0;
    for (unsigned k = 0; k < sizeof t / sizeof *t; k++) {
        pin_level = t[k].lvl;
        bool got = outPulse(t[k].out);
        bool ok = got == t[k].want;
        if (!ok) fail++;
        printf("  %-4s %s\n", ok ? "ok" : "FAIL", t[k].desc);
    }
    /* lookup never ran: must fail OPEN, i.e. behave as before the interlock */
    ix = 0xFF; pin_level = 0;
    bool ok = outPulse(O_TRUNK) == true;
    if (!ok) fail++;
    printf("  %-4s lookup failed, trunk open -> fails OPEN (prior behaviour)\n",
           ok ? "ok" : "FAIL");
    printf("%s\n", fail ? "FAILURES" : "all pass");
    return fail != 0;
}
