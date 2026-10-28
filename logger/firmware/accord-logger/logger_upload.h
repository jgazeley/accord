#pragma once
#include <stdint.h>
// Core 0 only, after sdLoop(). Never called by pulse/report core.
void uploadLoop(bool wifiUp);
void uploadDisconnect(); // abort TCP before removing the radio netif
void uploadBeginWindow();
uint64_t uploadProgress();
bool uploadCaughtUp(); // eligible captured prefixes only, not current-file completion
