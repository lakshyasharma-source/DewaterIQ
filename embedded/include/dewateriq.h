#ifndef DEWATERIQ_H
#define DEWATERIQ_H
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#define DIQ_VERSION "1.1"
#define DIQ_MAX_PITS 6

typedef enum {
    S_STABLE, S_LOAD, S_PUMP, S_WET, S_VOLUME, S_PIT,
    S_BEARING, S_POWER, S_VFD, S_VALVE, S_DOSING, S_SATURATION, S_BARITE, S_COUNT
} Scenario;

typedef struct {
    uint32_t rng;
    int tick;
    Scenario scenario;
    double rpm, pump_rpm, vfd_hz, source_level, dest_level;
    double polymer_response, chemical_response;
} Simulator;

typedef struct {
    int tick;
    const char *scenario, *mode, *role, *mud_type, *formation;
    const char *rig_id, *centrifuge_id;
    double rpm_setpoint, rpm, pump_command_pct, pump_rpm, vfd_cmd_hz, vfd_hz;
    double flow_setpoint, flow, amps, torque_pct, vibration, bearing_temp;
    double source_level, destination_level, mud_weight_ppg, sg, lgs_pct, hgs_pct, ph;
    double polymer_cmd_pct, polymer_actual_pct, chemical_cmd_pct, chemical_actual_pct;
    double valve_pct, controller_error_rpm, controller_error_flow, rpm_control_output;
    double quality_index, solids_removed_pct;
    int controller_saturated, sensor_valid;
    const char *quality, *drive, *fault, *transfer_state;
    const char *source_pit, *destination_pit;
    const char *event;
} Record;

typedef struct {
    double amps[8], torque[8], flow[8], vib[8], temp[8], level[8];
    unsigned int count, cursor;
} Detector;

const char *scenario_name(Scenario s);
int scenario_parse(const char *name, Scenario *out);
void sim_init(Simulator *s, Scenario mode, uint32_t seed);
void sim_step(Simulator *s, Record *out);
const char *detect_event(Detector *state, const Record *cur);
void print_json(FILE *file, const Record *r, const char *run_id);
/* Bounded NDJSON for MCU; returns length, or -1 on truncation/error. */
int diq_format_json(char *buffer, size_t capacity, const Record *r, const char *run_id);
#endif
