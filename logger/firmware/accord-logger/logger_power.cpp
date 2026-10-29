#include <Arduino.h>
#include <hardware/gpio.h>
#include <hardware/irq.h>
#include <hardware/timer.h>
#include <hardware/watchdog.h>
#include <pico/time.h>
#include <hardware/structs/timer.h>
#include "logger_power.h"

#if LOGGER_POWER_QUALIFIED
namespace {
logger_power::Policy policy;
logger_power::Health health;
uint32_t alarmNumber = 0;
// Atomic 32-bit loads/stores only. The ISR publishes a seqlock; readers make
// bounded attempts and fail closed. No spinlock, mutex, allocation or IO in ISR.
uint32_t sequence = 0, generation = 0, phase = 0;
uint32_t beats[2] = {}, ready[2] = {};
uint32_t read(const uint32_t &v) { return __atomic_load_n(&v, __ATOMIC_ACQUIRE); }
void write(uint32_t &v, uint32_t n) { __atomic_store_n(&v, n, __ATOMIC_RELEASE); }
void tick() {
    timer_hw->intr = 1u << alarmNumber;
    const uint64_t now = time_us_64() / 1000;
    const auto s = policy.step(now, gpio_get(5) ? logger_power::Input::Off : logger_power::Input::On);
    gpio_put(6, s.hold()); // sole runtime HOLD writer
    const uint32_t seq = read(sequence);
    write(sequence, seq + 1);
    write(generation, s.generation);
    write(phase, uint32_t(s.phase));
    write(sequence, seq + 2);
    if (health.feed(now, read(ready[0]) | (read(ready[1]) << 1), read(beats[0]), read(beats[1])))
        watchdog_update();
    // Arm this exclusive hardware channel directly. SDK alarm pools and the
    // hardware_alarm callback dispatcher take shared spinlocks inside IRQ;
    // neither is used here. Re-arm from now, avoiding catch-up IRQ storms.
    timer_hw->alarm[alarmNumber] = timer_hw->timerawl + 5000;
}
}
#endif
void powerSetup1() {
#if LOGGER_POWER_QUALIFIED
    // Preload before OE, including SDK's gpio_init output clearing. Never
    // restore an earlier boot's permission, including watchdog/USB boots.
    gpio_init(6); gpio_put(6, false);
    gpio_set_drive_strength(6, GPIO_DRIVE_STRENGTH_4MA);
    gpio_set_dir(6, GPIO_OUT);
    gpio_init(5); gpio_set_dir(5, GPIO_IN); gpio_pull_up(5);
    health = logger_power::Health(time_us_64() / 1000);
    watchdog_enable(4000, false);
    // IRQ enable/handler installation are per-core. Claim on core 1 before
    // enabling, then use only this channel's registers from its sole ISR.
    if (get_core_num() != 1) return;
    const int claimed = hardware_alarm_claim_unused(false);
    if (claimed < 0) return; // no degraded grant; watchdog resets, HOLD stays LOW
    alarmNumber = uint32_t(claimed);
    const uint irq = TIMER_IRQ_0 + alarmNumber;
    irq_set_enabled(irq, false);
    irq_set_exclusive_handler(irq, tick);
    irq_set_priority(irq, 0); // highest RP2040 IRQ priority
    timer_hw->intr = 1u << alarmNumber;
    hw_set_bits(&timer_hw->inte, 1u << alarmNumber);
    timer_hw->alarm[alarmNumber] = timer_hw->timerawl + 5000;
    irq_set_enabled(irq, true);
#endif
}
void powerProgress(unsigned core) {
#if LOGGER_POWER_QUALIFIED
    if (core < 2) write(beats[core], uint32_t(time_us_64() / 1000));
#else
    (void)core;
#endif
}
void powerReady(unsigned core) {
#if LOGGER_POWER_QUALIFIED
    if (core < 2) { powerProgress(core); write(ready[core], 1); }
#else
    (void)core;
#endif
}
logger_power::Snapshot powerSnapshot() {
#if LOGGER_POWER_QUALIFIED
    for (unsigned tries = 0; tries < 3; ++tries) {
        const uint32_t before = read(sequence);
        if (before & 1) continue;
        logger_power::Snapshot s{read(generation), logger_power::Phase(read(phase))};
        if (before == read(sequence)) return s;
    }
    return {}; // conservative transient: never authorizes a new open/producer
#else
    return {1, logger_power::Phase::Run};
#endif
}
bool powerBackgroundAllowed() { return powerSnapshot().recording(); }
