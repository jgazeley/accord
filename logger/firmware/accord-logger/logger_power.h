#pragma once
#include "power_config.h"
#include "power_policy.h"
void powerSetup1();
void powerReady(unsigned core);
void powerProgress(unsigned core);
logger_power::Snapshot powerSnapshot();
bool powerBackgroundAllowed();
