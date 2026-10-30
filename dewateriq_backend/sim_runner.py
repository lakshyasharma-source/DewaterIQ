"""Run locally compiled C simulator and ingest validated NDJSON. Never executes user code."""
import json
import subprocess
from pathlib import Path
from .historian import insert_records
from .schema import validate_record

ROOT=Path(__file__).resolve().parents[1]
BIN=ROOT/'embedded'/'dewateriq_sim'
SCENARIOS=('stable','load','pump-degradation','wet-cut','volume-loss','pit-imbalance',
           'bearing','power-fault','vfd-degradation','valve-restriction',
           'dosing-deviation','saturation','barite-recovery')


def build():
    subprocess.run(['make','-C',str(ROOT/'embedded')],check=True,capture_output=True,text=True,timeout=90)


def generate(scenario='stable',samples=80,seed=7,centrifuge_id='CENT-SIM-01'):
    if scenario not in SCENARIOS: raise ValueError('Unknown synthetic scenario')
    if not (1<=samples<=100000): raise ValueError('Sample count outside allowed range')
    if not (0<=seed<=4294967295): raise ValueError('Seed outside allowed range')
    if not centrifuge_id or len(centrifuge_id)>24 or any(not (c.isalnum() or c in '-_') for c in centrifuge_id):
        raise ValueError('Invalid synthetic equipment ID')
    if not BIN.is_file(): build()
    output=subprocess.run([str(BIN),'--scenario',scenario,'--samples',str(samples),'--seed',str(seed),'--centrifuge-id',centrifuge_id],
                          check=True,capture_output=True,text=True,timeout=60)
    records=[validate_record(json.loads(line)) for line in output.stdout.splitlines() if line.strip()]
    if len(records)!=samples: raise RuntimeError('Unexpected simulator record count')
    return records


def generate_and_store(scenario='stable',samples=80,seed=7,path=None,centrifuge_id='CENT-SIM-01'):
    records=generate(scenario,samples,seed,centrifuge_id)
    insert_records(records,path)
    return records[0]['run_id'],len(records)
