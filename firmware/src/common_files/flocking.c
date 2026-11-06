#include "flocking.h"
#include "ds_p2p_interface.h"
#include "settings.h"

#include "FreeRTOS.h"
#include "task.h"
#include "param.h"
#include <math.h>

extern copter_full_state_t copters[MAX_ADDRESS];

static uint8_t flock_enable = 0;   // 0 = random roaming, 1 = boids flocking
static float sep_weight   = 2.0f;
static float coh_weight   = 0.8f;
static float bound_weight = 2.5f;
static float mig_weight   = 0.4f;
static float sep_radius   = 0.5f;  // start pushing apart within this (m)
static float coh_radius   = 1.2f;  // cohere with peers within this (m)
static float lookahead    = 0.35f; // place the goto target this far ahead (m)
static float flock_z      = 1.0f;  // fixed altitude for 2D flocking (m)
static float flock_dur    = 1.0f;  // goto duration per re-steer (s)
static float mig_period   = 40.0f; // migration goal circle period (s)
static float form_r       = 0.35f; // circle radius / line spacing (m)

bool isFlockingEnabled(void) { return flock_enable != 0; }
float getFlockDuration(void) { return flock_dur; }

static PositionWithYaw computeFormationTarget(Position myPos, uint8_t myId) {
    int M = 0, myRank = 0;                             // rank among currently-flying drones (by id)
    for (uint8_t i = 1; i < MAX_ADDRESS; i++) {
        if (i == myId) { myRank = M; M++; }
        else if (isCopterFlying(i)) { M++; }
    }
    if (M < 1) M = 1;

    float phase = 2.0f * (float)M_PI * ((float)T2M(xTaskGetTickCount()) / 1000.0f) / mig_period;
    float tx = CENTER_X_BOX, ty = CENTER_Y_BOX;
    if (getFormationMode() == 1) {                     // rotating circle
        float ang = 2.0f * (float)M_PI * (float)myRank / (float)M + phase;
        tx = CENTER_X_BOX + form_r * cosf(ang);
        ty = CENTER_Y_BOX + form_r * sinf(ang);
    } else {                                           // line along Y, centered
        ty = CENTER_Y_BOX + form_r * ((float)myRank - (float)(M - 1) / 2.0f);
    }

    PositionWithYaw t;
    t.x = CLAMP(tx, MIN_X_BOX, MAX_X_BOX);
    t.y = CLAMP(ty, MIN_Y_BOX, MAX_Y_BOX);
    t.z = flock_z;
    t.yaw = NO_YAW;
    return t;
}

PositionWithYaw computeFlockingTarget(Position myPos, uint8_t myId) {
    if (getFormationMode() != 0) return computeFormationTarget(myPos, myId);
    float sepx = 0.0f, sepy = 0.0f;
    float cohx = 0.0f, cohy = 0.0f;
    int cohN = 0;

    for (uint8_t i = 1; i < MAX_ADDRESS; i++) {   // id 0 is the sniffer
        if (i == myId) continue;
        if (!isCopterFlying(i)) continue;

        float dx = myPos.x - copters[i].position.x;
        float dy = myPos.y - copters[i].position.y;   // 2D: ignore z
        float d = sqrtf(dx * dx + dy * dy);
        if (d < 0.001f) d = 0.001f;

        if (d < sep_radius) {                          // separation: away, stronger when closer
            float w = (sep_radius - d) / sep_radius;
            sepx += (dx / d) * w;
            sepy += (dy / d) * w;
        }
        if (d < coh_radius) {                          // cohesion: gather neighbor positions
            cohx += copters[i].position.x;
            cohy += copters[i].position.y;
            cohN++;
        }
    }

    float sx = sep_weight * sepx;
    float sy = sep_weight * sepy;

    if (cohN > 0) {                                    // cohesion: steer toward neighbor centroid
        float cx = cohx / (float)cohN - myPos.x;
        float cy = cohy / (float)cohN - myPos.y;
        float cm = sqrtf(cx * cx + cy * cy);
        if (cm < 0.001f) cm = 0.001f;
        sx += coh_weight * cx / cm;
        sy += coh_weight * cy / cm;
    }

    if (myPos.x < MIN_X_BOX) sx += bound_weight;       // bounds: back toward the box
    if (myPos.x > MAX_X_BOX) sx -= bound_weight;
    if (myPos.y < MIN_Y_BOX) sy += bound_weight;
    if (myPos.y > MAX_Y_BOX) sy -= bound_weight;

    float ang = 2.0f * (float)M_PI * ((float)T2M(xTaskGetTickCount()) / 1000.0f) / mig_period;
    sx += mig_weight * cosf(ang);                      // migration: slowly circling shared drift
    sy += mig_weight * sinf(ang);

    float m = sqrtf(sx * sx + sy * sy);
    if (m < 0.001f) m = 0.001f;

    PositionWithYaw t;
    t.x = CLAMP(myPos.x + (sx / m) * lookahead, MIN_X_BOX, MAX_X_BOX);
    t.y = CLAMP(myPos.y + (sy / m) * lookahead, MIN_Y_BOX, MAX_Y_BOX);
    t.z = flock_z;
    t.yaw = NO_YAW;
    return t;
}

PARAM_GROUP_START(flock)
PARAM_ADD(PARAM_UINT8 | PARAM_PERSISTENT, enable, &flock_enable)
PARAM_ADD(PARAM_FLOAT, sep_w, &sep_weight)
PARAM_ADD(PARAM_FLOAT, coh_w, &coh_weight)
PARAM_ADD(PARAM_FLOAT, bnd_w, &bound_weight)
PARAM_ADD(PARAM_FLOAT, mig_w, &mig_weight)
PARAM_ADD(PARAM_FLOAT, sep_r, &sep_radius)
PARAM_ADD(PARAM_FLOAT, coh_r, &coh_radius)
PARAM_ADD(PARAM_FLOAT, look, &lookahead)
PARAM_ADD(PARAM_FLOAT, z, &flock_z)
PARAM_ADD(PARAM_FLOAT, dur, &flock_dur)
PARAM_ADD(PARAM_FLOAT | PARAM_PERSISTENT, form_r, &form_r)
PARAM_GROUP_STOP(flock)
