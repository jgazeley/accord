#pragma once
// Deliberate build selection. Default is the existing manual-power wiring.
// Set to 1 ONLY for the reviewed LRA-01 qualified GP5 / GP6 HOLD interface.
#ifndef LOGGER_POWER_QUALIFIED
#define LOGGER_POWER_QUALIFIED 0
#endif
#if LOGGER_POWER_QUALIFIED != 0 && LOGGER_POWER_QUALIFIED != 1
#error "LOGGER_POWER_QUALIFIED must be 0 (manual) or 1 (LRA-01)"
#endif
