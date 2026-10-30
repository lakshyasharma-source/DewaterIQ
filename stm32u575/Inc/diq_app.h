#ifndef DIQ_APP_H
#define DIQ_APP_H
#include <stddef.h>
#include <stdint.h>
#include "dewateriq.h"

#define DIQ_STM32_JSON_CAPACITY 4096u

typedef struct {
    Simulator simulator;
    Detector detector;
    Scenario scenario;
    uint32_t seed;
    char run_id[96];
} DiqApp;

/* All model state is virtual. No hardware acquisition or actuator calls exist. */
void diq_app_init(DiqApp *app, Scenario scenario, uint32_t seed);
/* Emit one COMPLETE schema-1.1 synthetic record with trailing newline. */
int diq_app_step(DiqApp *app, char *output, size_t output_capacity);
/* Commands change only simulated state. Return a short human-readable reply. */
int diq_app_command(DiqApp *app, const char *command, char *reply, size_t reply_capacity);
#endif
