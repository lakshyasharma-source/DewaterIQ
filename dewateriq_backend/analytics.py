"""Observed mathematical descriptors, not validated diagnostics or operating limits."""
from math import sqrt


def metric(r, group, name):
    return float(r[group][name])


def summary(records):
    if not records: return {}
    first,last=records[0],records[-1]
    def change(group,name):
        return round(metric(last,group,name)-metric(first,group,name),2)
    return {
        'run_id':last['run_id'], 'scenario':last['scenario'],
        'operating_mode':last['operating_mode'], 'samples':len(records),
        'sample_source':last['data_source'],
        'current_delta_a':change('machine','motor_current_a'),
        'torque_delta_pct_points':change('machine','torque_percent'),
        'flow_delta_gpm':change('hydraulic_process','actual_flow_gpm'),
        'source_level_delta_pct_points':change('hydraulic_process','source_pit_level_percent'),
        'latest_flow_gpm':metric(last,'hydraulic_process','actual_flow_gpm'),
        'latest_current_a':metric(last,'machine','motor_current_a'),
        'latest_rpm':metric(last,'machine','simulated_actual_centrifuge_rpm'),
        'latest_cut':last['output']['cut_quality'],
        'latest_fault':last['fault'],
        'any_fault':any(x['fault']!='none' for x in records),
        'sensor_valid':all(x['sensor_valid'] for x in records)
    }

FEATURES=(('machine','motor_current_a',30),('machine','torque_percent',30),
          ('hydraulic_process','actual_flow_gpm',180),('mud_chemistry','mud_weight_ppg',4),
          ('machine','simulated_actual_centrifuge_rpm',800))

def similar_runs(target_records, candidates, limit=3):
    """End-of-run engineering comparisons of completed synthetic runs; not a model."""
    if not target_records: return []
    tail=target_records[-1]
    output=[]
    for records in candidates:
        if not records: continue
        r=records[-1]
        if r['run_id']==tail['run_id']: continue
        if r['operating_mode']!=tail['operating_mode'] or r['mud_type']!=tail['mud_type']: continue
        score=sqrt(sum(((metric(tail,g,key)-metric(r,g,key))/scale)**2 for g,key,scale in FEATURES))
        output.append({'run_id':r['run_id'],'scenario':r['scenario'],
                       'distance':round(score,4),'cut_quality':r['output']['cut_quality'],
                       'data_source':r['data_source']})
    return sorted(output,key=lambda z:z['distance'])[:limit]


def offline_explanation(records, similar=None):
    """Rule-based demonstration summary: deliberately no inference or actual safety claim."""
    s=summary(records)
    if not s: return 'No records available.'
    observations=[]
    if s['any_fault']: observations.append('A synthetic fault flag appears in this run.')
    if s['current_delta_a']>8 and s['torque_delta_pct_points']>8:
        observations.append('Current and torque rose together in the synthetic trace.')
    if s['flow_delta_gpm']< -70:
        observations.append('Synthetic throughput decreased during the run.')
    if s['source_level_delta_pct_points']<-12:
        observations.append('The synthetic source pit level decreased materially.')
    if s['latest_cut']=='wet': observations.append('The scenario reports a wet-cut annotation.')
    if s['operating_mode']=='intentional_volume_loss':
        observations.append('Intentional volume loss is the specified operating objective, not automatically a fault.')
    if not observations: observations.append('No marked scenario change was detected in these sampled values.')
    others='' if not similar else ' Comparable synthetic runs: '+', '.join(x['run_id'] for x in similar)+'.'
    return ('OFFLINE RULE-BASED DEMO (not an AI or an operational diagnosis): '
            +' '.join(observations)+others+' Review flow, levels, loading and operator observations; '
            'no setpoints, chemical doses or machine commands are generated.')
