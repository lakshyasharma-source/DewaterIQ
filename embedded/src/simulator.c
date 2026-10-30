#include "dewateriq.h"
#include <math.h>
#include <string.h>

static const char *names[] = {
    "stable", "load", "pump-degradation", "wet-cut", "volume-loss",
    "pit-imbalance", "bearing", "power-fault", "vfd-degradation",
    "valve-restriction", "dosing-deviation", "saturation", "barite-recovery"
};
const char *scenario_name(Scenario s) { return s >= 0 && s < S_COUNT ? names[s] : "unknown"; }
int scenario_parse(const char *name, Scenario *out) {
    for (int i=0;i<S_COUNT;i++) if (!strcmp(name,names[i])) { *out=(Scenario)i; return 1; }
    return 0;
}
static double clamp(double v, double a, double b) { return v < a ? a : v > b ? b : v; }
static double jitter(Simulator *s, double a) {
    s->rng = s->rng * 1664525u + 1013904223u;
    return (((double)((s->rng >> 8) & 0xFFFFu) / 65535.0)*2.0-1.0)*a;
}
void sim_init(Simulator *s, Scenario mode, uint32_t seed) {
    memset(s,0,sizeof(*s)); s->rng=seed; s->scenario=mode;
    s->rpm=2000.0; s->pump_rpm=1070.0; s->vfd_hz=55.0;
    s->source_level=72.0; s->dest_level=38.0;
    s->polymer_response=60; s->chemical_response=68;
}
void sim_step(Simulator *s, Record *r) {
    memset(r,0,sizeof(*r)); s->tick++;
    const double t=(double)s->tick;
    const double progress=clamp((t-10.0)/40.0,0.0,1.0);
    const double rising=(s->scenario==S_LOAD) ? progress : 0.0;
    const double pump_loss=(s->scenario==S_PUMP)?(1.0-0.52*progress):1.0;
    const double vfd_loss=(s->scenario==S_VFD)?(1.0-0.40*progress):1.0;
    const double restriction=(s->scenario==S_VALVE)?(1.0-0.57*progress):1.0;
    const int power_off=(s->scenario==S_POWER && t>35.0);
    const double mode_volume=s->scenario==S_VOLUME ? 0.52 : 1.0;
    double rpm_target=(s->scenario==S_BARITE)?1250.0:((s->scenario==S_VOLUME)?1700.0:(s->scenario==S_SATURATION?2550.0:2040.0));
    const double rpm_error=rpm_target-s->rpm;
    const double rpm_act=clamp(rpm_error*0.15,-55.0,55.0);
    s->rpm=clamp(s->rpm+rpm_act*0.28+jitter(s,1.0),0.0,2600.0);
    double vfd_command=55.0;
    s->vfd_hz+=(vfd_command*vfd_loss-s->vfd_hz)*0.24;
    double pump_rpm_target=1077.0*vfd_loss*pump_loss;
    s->pump_rpm+=(pump_rpm_target-s->pump_rpm)*0.20;
    double flow_setpoint=(s->scenario==S_BARITE)?350.0:420.0;
    double mud_weight=10.2+0.65*rising;
    double actual_flow=flow_setpoint * pump_loss * vfd_loss * restriction * mode_volume;
    actual_flow*=1.0-0.09*(mud_weight-10.2);
    if (s->scenario==S_LOAD) actual_flow += rising*75.0;
    if (power_off) { actual_flow=0.0; s->rpm*=0.90; s->pump_rpm*=0.55; s->vfd_hz*=0.55; }
    actual_flow=power_off?0.0:clamp(actual_flow+jitter(s,1.1),0.0,700.0);
    s->source_level=clamp(s->source_level-(actual_flow/420.0)*0.08
                         -(s->scenario==S_PIT?0.32*progress:0.0),0.0,100.0);
    s->dest_level=clamp(s->dest_level+(actual_flow/420.0)*0.05,0.0,100.0);
    double amps=power_off?0.0:(48.0 + rising*23.0 + (actual_flow-420.0)*0.018 + jitter(s,0.5));
    double torque=power_off?0.0:(39.0 + rising*25.0 + jitter(s,0.6));
    double vibration=2.4 + 0.4*rising + jitter(s,0.08);
    double temp=58.0 + 7.0*rising + jitter(s,0.15);
    if (s->scenario==S_BEARING) { vibration+=8.0*progress; temp+=22.0*progress; }
    double polymer_command=65.0, chemical_command=70.0;
    double polymer_target=polymer_command, chemical_target=chemical_command;
    if (s->scenario==S_WET) { polymer_target=46.0; chemical_target=50.0; }
    if (s->scenario==S_DOSING) { polymer_target=polymer_command*(1.0-0.62*progress);
                                    chemical_target=chemical_command*(1.0-0.55*progress); }
    s->polymer_response+=(polymer_target-s->polymer_response)*0.30;
    s->chemical_response+=(chemical_target-s->chemical_response)*0.30;
    const char *quality="acceptable";
    if (s->scenario==S_WET || s->scenario==S_DOSING || s->scenario==S_VOLUME) quality="wet";
    if (power_off) quality="unknown";
    const char *fault="none";
    if (s->scenario==S_PUMP && progress>0.35) fault="pump_response";
    if (s->scenario==S_BEARING && progress>0.35) fault="bearing";
    if (s->scenario==S_VFD && progress>0.35) fault="vfd_response";
    if (s->scenario==S_VALVE && progress>0.35) fault="valve_restriction";
    if (s->scenario==S_DOSING && progress>0.35) fault="dosing_response";
    if (power_off) fault="power";
    r->tick=s->tick;
    r->scenario=scenario_name(s->scenario);
    r->mode=s->scenario==S_BARITE?"barite_recovery":s->scenario==S_VOLUME?"intentional_volume_loss":s->scenario==S_WET||s->scenario==S_DOSING?"dewatering":"polishing";
    r->role=s->scenario==S_BARITE?"barite_recovery":"polisher"; r->rig_id="RIG-SYNTHETIC-01"; r->centrifuge_id="CENT-SIM-01";
    r->mud_type=s->scenario==S_WET||s->scenario==S_DOSING?"WBM":"OBM";
    r->formation="synthetic_formation";
    r->rpm_setpoint=rpm_target; r->rpm=s->rpm;
    r->pump_command_pct=72.0; r->pump_rpm=s->pump_rpm;
    r->vfd_cmd_hz=vfd_command; r->vfd_hz=s->vfd_hz;
    r->flow_setpoint=flow_setpoint; r->flow=actual_flow;
    r->amps=amps; r->torque_pct=torque; r->vibration=vibration; r->bearing_temp=temp;
    r->source_level=s->source_level; r->destination_level=s->dest_level;
    r->mud_weight_ppg=mud_weight; r->sg=mud_weight/8.3454;
    r->lgs_pct=4.0+3.5*rising; r->hgs_pct=1.2+2.0*rising;
    r->ph=(s->scenario==S_WET ? 9.0-0.8*progress : 9.2);
    r->polymer_cmd_pct=polymer_command; r->polymer_actual_pct=s->polymer_response;
    r->chemical_cmd_pct=chemical_command; r->chemical_actual_pct=s->chemical_response;
    r->valve_pct=82.0*restriction; r->controller_error_rpm=rpm_error;
    r->controller_error_flow=flow_setpoint-actual_flow;
    r->rpm_control_output=rpm_act;
    r->controller_saturated=s->scenario==S_SATURATION && fabs(rpm_error)>140.0;
    r->quality=quality;
    r->solids_removed_pct=clamp(78.0+0.01*(s->rpm-2000.0)-0.7*r->lgs_pct,0.0,100.0);
    r->quality_index=clamp(r->solids_removed_pct-(strcmp(quality,"wet")==0?17.0:0.0),0.0,100.0);
    r->fault=fault; r->sensor_valid=1;
    r->drive=power_off?"fault":"running";
    r->source_pit="PIT-6"; r->destination_pit="PIT-2";
    r->transfer_state=power_off?"idle":s->scenario==S_VOLUME?"intentional_loss":s->scenario==S_VALVE?"restricted":"active";
    r->event="none";
}
