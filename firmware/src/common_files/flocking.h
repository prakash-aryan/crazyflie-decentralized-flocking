#ifndef FLOCKING_H
#define FLOCKING_H

#include <stdbool.h>
#include <stdint.h>
#include "positions.h"

bool isFlockingEnabled(void);
float getFlockDuration(void);

// Boids steering target from P2P peer positions (2D: fixed altitude).
PositionWithYaw computeFlockingTarget(Position myPos, uint8_t myId);

#endif // FLOCKING_H
