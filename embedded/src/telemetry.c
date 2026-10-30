#include "dewateriq.h"
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include <limits.h>

/* Bounded formatting prevents UART frame overflow and avoids heap allocation. */
typedef struct { char *buffer; size_t cap; size_t used; int failed; } JsonWriter;
static void append_json(JsonWriter *w, const char *fmt, ...) {
    if (w->failed || w->used >= w->cap) { w->failed=1; return; }
    va_list args;
    va_start(args,fmt);
    int n=vsnprintf(w->buffer+w->used,w->cap-w->used,fmt,args);
    va_end(args);
    if (n<0 || (size_t)n >= w->cap-w->used) { w->failed=1; return; }
    w->used += (size_t)n;
}
/* All strings are fixed simulation labels or compiler-controlled run IDs. */
int diq_format_json(char *buffer, size_t cap, const Record *r, const char *run_id) {
    if (!buffer || !cap || !r || !run_id) return -1;
    JsonWriter w={buffer,cap,0,0};
    append_json(&w,"{\"schema_version\":\"1.1\",\"data_source\":\"synthetic\",\"timestamp_s\":%d,",r->tick);
    append_json(&w,"\"rig_id\":\"%s\",\"centrifuge_id\":\"%s\",\"run_id\":\"%s\",",r->rig_id,r->centrifuge_id,run_id);
    append_json(&w,"\"scenario\":\"%s\",\"operating_mode\":\"%s\",\"centrifuge_role\":\"%s\",",r->scenario,r->mode,r->role);
    append_json(&w,"\"mud_type\":\"%s\",\"formation\":\"%s\",",r->mud_type,r->formation);
    append_json(&w,"\"machine\":{\"commanded_virtual_centrifuge_rpm\":%.3f,\"simulated_actual_centrifuge_rpm\":%.3f,",r->rpm_setpoint,r->rpm);
    append_json(&w,"\"commanded_virtual_feed_pump_percent\":%.3f,\"simulated_feed_pump_rpm\":%.3f,",r->pump_command_pct,r->pump_rpm);
    append_json(&w,"\"virtual_vfd_frequency_hz\":%.3f,\"simulated_vfd_frequency_hz\":%.3f,",r->vfd_cmd_hz,r->vfd_hz);
    append_json(&w,"\"motor_current_a\":%.3f,\"torque_percent\":%.3f,\"bearing_temperature_c\":%.3f,\"vibration_mm_s\":%.3f,",r->amps,r->torque_pct,r->bearing_temp,r->vibration);
    append_json(&w,"\"drive_status\":\"%s\",\"runtime_hours\":%.6f},",r->drive,r->tick/3600.0);
    append_json(&w,"\"hydraulic_process\":{\"commanded_virtual_flow_gpm\":%.3f,\"actual_flow_gpm\":%.3f,",r->flow_setpoint,r->flow);
    append_json(&w,"\"source_pit\":\"%s\",\"destination_pit\":\"%s\",",r->source_pit,r->destination_pit);
    append_json(&w,"\"source_pit_level_percent\":%.3f,\"destination_pit_level_percent\":%.3f,",r->source_level,r->destination_level);
    append_json(&w,"\"virtual_valve_position_percent\":%.3f,\"transfer_state\":\"%s\"},",r->valve_pct,r->transfer_state);
    append_json(&w,"\"mud_chemistry\":{\"mud_weight_ppg\":%.3f,\"specific_gravity\":%.3f,",r->mud_weight_ppg,r->sg);
    append_json(&w,"\"lgs_percent\":%.3f,\"hgs_percent\":%.3f,\"ph\":%.3f,",r->lgs_pct,r->hgs_pct,r->ph);
    append_json(&w,"\"polymer_dose_command_percent\":%.3f,\"simulated_polymer_dose_percent\":%.3f,",r->polymer_cmd_pct,r->polymer_actual_pct);
    append_json(&w,"\"chemical_dose_command_percent\":%.3f,\"simulated_chemical_dose_percent\":%.3f,",r->chemical_cmd_pct,r->chemical_actual_pct);
    append_json(&w,"\"polymer_type\":\"synthetic_polymer\",\"preparation_state\":\"simulation_only\"},");
    append_json(&w,"\"control_response\":{\"controller_mode\":\"automatic_virtual_simulation\",\"rpm_setpoint\":%.3f,",r->rpm_setpoint);
    append_json(&w,"\"flow_setpoint_gpm\":%.3f,\"rpm_controller_output\":%.3f,\"rpm_error\":%.3f,",r->flow_setpoint,r->rpm_control_output,r->controller_error_rpm);
    append_json(&w,"\"flow_error\":%.3f,\"controller_saturated\":%s,\"control_loop_status\":\"%s\"},",r->controller_error_flow,r->controller_saturated?"true":"false",r->controller_saturated?"saturated":"tracking");
    append_json(&w,"\"output\":{\"cut_quality\":\"%s\",\"simulated_solids_removal_percent\":%.3f,\"process_quality_index\":%.3f},",r->quality,r->solids_removed_pct,r->quality_index);
    append_json(&w,"\"fault\":\"%s\",\"event\":\"%s\",\"sensor_valid\":%s}\n",r->fault,r->event,r->sensor_valid?"true":"false");
    if (w.failed || w.used > INT_MAX) { buffer[0]='\0'; return -1; }
    return (int)w.used;
}

/* Native desktop compatibility; firmware never needs stdout or files. */
void print_json(FILE *f, const Record *r, const char *run_id) {
    char buffer[4096];
    int n=diq_format_json(buffer,sizeof(buffer),r,run_id);
    if (n<0) { fputs("JSON serialization exceeded buffer\n",stderr); return; }
    (void)fwrite(buffer,1,(size_t)n,f);
}
