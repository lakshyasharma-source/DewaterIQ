#include "dewateriq.h"
#include <string.h>

/* Sliding-window trend observations. Constants below are DEMO sensitivity, NOT
 * equipment alarms or physically valid thresholds. The detector has no actuator. */
const char *detect_event(Detector *d, const Record *r) {
    const char *event="none";
    if (!r->sensor_valid) event="sensor_invalid";
    else if (!strcmp(r->drive,"fault")) event="drive_fault_observed";
    else if (r->controller_saturated) event="virtual_controller_saturation";
    else if (d->count>=8) {
        double a=0,t=0,f=0,v=0,c=0,l=0;
        for (int i=0;i<8;i++) {
            a+=d->amps[i]; t+=d->torque[i]; f+=d->flow[i];
            v+=d->vib[i]; c+=d->temp[i]; l+=d->level[i];
        }
        a/=8; t/=8; f/=8; v/=8; c/=8; l/=8;
        if (r->amps>a+2.2 && r->torque_pct>t+2.0) event="load_trend_rising";
        else if (r->vibration>v+0.55 && r->bearing_temp>c+1.6) event="bearing_trend_rising";
        else if (r->flow<f-22.0) event="flow_trend_falling";
        else if (r->source_level<l-1.2) event="pit_inventory_decreasing";
        else if (!strcmp(r->quality,"wet")) event="wet_cut_annotation";
    } else if (!strcmp(r->quality,"wet")) event="wet_cut_annotation";
    if (!strcmp(event,"none") && strcmp(r->fault,"none")!=0)
        event="simulated_fault_observed";
    const unsigned int i=d->cursor;
    d->amps[i]=r->amps; d->torque[i]=r->torque_pct; d->flow[i]=r->flow;
    d->vib[i]=r->vibration; d->temp[i]=r->bearing_temp;
    d->level[i]=r->source_level;
    d->cursor=(i+1)%8;
    if (d->count<8) d->count++;
    return event;
}
