/* Auto-relock state machine, lifted out of uart_main.ino so the transitions can
 * be tested without a board. Same polarity chain as the firmware: the door and
 * key-in cells ground their line when ACTIVE, the PC817 collector sits on
 * INPUT_PULLUP, so ACTIVE == LOW. The ignition cell is the 12 V-sense one but
 * reads the same way at the GPIO.
 *
 * NOT in the sketch root on purpose: arduino-cli compiles every .c there and an
 * object file's main() silently replaces the core's, producing firmware with no
 * Arduino init at all. tests/ is ignored by the build. */
#include <stdio.h>
#include <stdbool.h>
#include <stdint.h>

#define RELOCK_MIN_MS   5000
#define RELOCK_MAX_MS 300000

static bool door, key_in, ign;                 /* true = ACTIVE (line grounded) */
static bool     relockEnabled = true;
static uint32_t relockMs = 30000;
static uint32_t relockAt = 0;
static uint32_t nowMs    = 0;
static int      lockPulses = 0, ceilingOff = 0;

static const char *occupied(void) {
    if (door)   return "door open";
    if (key_in) return "key in";
    if (ign)    return "ignition on";
    return NULL;
}
static void relockNoteLock(void) { relockAt = 0; }
static void relockArm(void) {
    if (!relockEnabled)  { relockAt = 0; return; }
    if (occupied())      { relockAt = 0; return; }
    relockAt = nowMs + relockMs;
    if (!relockAt) relockAt = 1;
}
static void relockTick(void) {
    if (!relockAt) return;
    if (occupied()) { relockAt = 0; return; }
    if ((int32_t)(nowMs - relockAt) < 0) return;
    relockAt = 0;
    lockPulses++; ceilingOff++;               /* outPulse(O_LOCK); outSet(CEILING,0) */
}
static bool relockSet(bool on, uint32_t ms) {
    if (ms && (ms < RELOCK_MIN_MS || ms > RELOCK_MAX_MS)) return false;
    relockEnabled = on;
    if (ms) relockMs = ms;
    if (!on) relockAt = 0;
    return true;
}
static void reset(void) {
    door = key_in = ign = false;
    relockEnabled = true; relockMs = 30000; relockAt = 0; nowMs = 0;
    lockPulses = ceilingOff = 0;
}
/* advance time in 100 ms steps so the tick sees the window the way loop() does */
static void advance(uint32_t ms) {
    for (uint32_t t = 0; t < ms; t += 100) { nowMs += 100; relockTick(); }
}

static int fail = 0;
static void check(bool ok, const char *desc) {
    printf("%-4s %s\n", ok ? "ok" : "FAIL", desc);
    if (!ok) fail++;
}

int main(void) {
    /* 1. happy path: nobody gets in, it relocks exactly once */
    reset(); relockArm(); advance(29000);
    check(lockPulses == 0, "29 s after unlock, empty car           -> not yet");
    advance(2000);
    check(lockPulses == 1, "31 s after unlock, empty car           -> RELOCKED");
    advance(60000);
    check(lockPulses == 1, "a minute later                         -> fires once only");
    check(ceilingOff == 1, "relock also drops the dome lamp");

    /* 2. a door opens -> cancelled, and stays cancelled after it shuts */
    reset(); relockArm(); advance(5000);
    door = true;  advance(200);
    check(relockAt == 0, "door opens during the window           -> CANCELLED");
    door = false; advance(60000);
    check(lockPulses == 0, "door shuts again, long wait            -> stays cancelled");

    /* 3. key in, and ignition, cancel it too */
    reset(); relockArm(); key_in = true; advance(60000);
    check(lockPulses == 0, "key in during the window               -> CANCELLED");
    reset(); relockArm(); ign = true;    advance(60000);
    check(lockPulses == 0, "ignition on during the window          -> CANCELLED");

    /* 4. never arm a window we would immediately cancel */
    reset(); door = true;   relockArm();
    check(relockAt == 0, "unlock with a door already open        -> never armed");
    reset(); key_in = true; relockArm();
    check(relockAt == 0, "unlock with the key already in         -> never armed");

    /* 5. an explicit lock from any source closes the window */
    reset(); relockArm(); advance(5000); relockNoteLock(); advance(60000);
    check(lockPulses == 0, "manual lock during the window          -> window closed");

    /* 6. a fresh unlock restarts the clock rather than inheriting it */
    reset(); relockArm(); advance(25000); relockArm(); advance(10000);
    check(lockPulses == 0, "re-unlock at 25 s, then 10 s           -> clock restarted");
    advance(21000);
    check(lockPulses == 1, "...and fires 31 s after the SECOND one");

    /* 7. disabled does nothing at all */
    reset(); relockSet(false, 0); relockArm(); advance(60000);
    check(lockPulses == 0, "feature disabled                       -> never relocks");

    /* 8. timeout limits */
    reset();
    check(relockSet(true, 45000) && relockMs == 45000, "relock 45 s                            -> accepted");
    check(!relockSet(true, 1000),  "relock 1 s   (below RELOCK_MIN_MS)     -> refused");
    check(!relockSet(true, 600000),"relock 600 s (above RELOCK_MAX_MS)     -> refused");
    check(relockMs == 45000, "a refused timeout leaves the old one intact");

    /* 9. the custom timeout is actually honoured */
    reset(); relockSet(true, 10000); relockArm(); advance(9000);
    check(lockPulses == 0, "10 s timeout, 9 s elapsed              -> not yet");
    advance(2000);
    check(lockPulses == 1, "10 s timeout, 11 s elapsed             -> RELOCKED");

    /* 10. millis() rollover: relockAt wraps past zero mid-window */
    reset(); nowMs = 0xFFFFF000u; relockArm();
    check(relockAt != 0, "armed just before the millis() rollover");
    advance(31000);
    check(lockPulses == 1, "fires correctly across the rollover");

    printf("\n%s  (%d failure%s)\n", fail ? "FAILED" : "all pass", fail, fail == 1 ? "" : "s");
    return fail != 0;
}
