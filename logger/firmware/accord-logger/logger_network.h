#pragma once

// Core 0 owns the radio, DNS, SNTP and the CYW43 LED. Core 1 is the only
// serial writer and owns all counter variables and both pulse interrupts.
void networkSetup();
void networkLoop();
void networkCounterReady();
void networkSetLed(bool moving);
// Core 1 samples GP5; a nonblocking mailbox keeps radio work on core 0.
void networkSetIgn(bool on);
void networkPrintWifi();
void networkPrintTime();

// Change detection for the status notes. Core 1 drives the cadence (see
// statusNotes() in the sketch); each module only answers "has my state moved
// since you last asked".
bool networkWifiChanged();
bool networkTimeChanged();

// True once a trusted reply -- SNTP, or the host over USB -- has set the system
// clock, so gettimeofday() may be believed. CORE 0 ONLY -- it reads core 0's
// own working state, and it exists for the card's file naming, which is core 0
// work.
bool networkClockTrusted();

// The host handing over its own clock, in epoch MILLISECONDS. CORE 1 ONLY: it
// is called from command(), so it may not touch core 0's state. It leaves the
// value in the mailbox and core 0 adopts it on its next pass -- the same shape
// as networkCounterReady() and networkSetLed().
//
// The arrival instant is captured here rather than where it is adopted,
// because sdLoop() can block for most of a second on a slow card and the delay
// would otherwise be charged to the clock. Validation is the caller's job.
void networkSetHostTime(uint64_t epochMs);
