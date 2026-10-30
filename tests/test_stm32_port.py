"""STM32 portable core and serial bridge tests; no physical board or driver required."""
from pathlib import Path
import json
import subprocess
import pytest
from jsonschema import ValidationError
from dewateriq_backend.historian import get_run, runs
from dewateriq_backend.serial_bridge import decode_record, ingest_lines
from dewateriq_backend.schema import validate_record
from dewateriq_backend.sim_runner import SCENARIOS

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / 'stm32u575' / 'tools'


def test_c99_stm32_port_all_scenarios():
    subprocess.run(['make', '-C', str(TOOLS)], check=True, capture_output=True)
    for scenario in SCENARIOS:
        proc = subprocess.run([str(TOOLS / 'host_smoke'),scenario],check=True,
                              text=True,capture_output=True)
        frames = [validate_record(json.loads(l)) for l in proc.stdout.splitlines()]
        assert len(frames) == 65
        assert frames[0]['scenario'] == scenario
        assert frames[0]['data_source'] == 'synthetic'
        assert frames[-1]['timestamp_s'] == 65
        assert frames[-1]['centrifuge_id'] == 'CENT-STM32-SIM-01'


def test_serial_bridge_validates_and_historizes(tmp_path):
    subprocess.run(['make', '-C', str(TOOLS)], check=True, capture_output=True)
    proc = subprocess.run([str(TOOLS / 'host_smoke'), 'load'], check=True,
                          capture_output=True, text=True)
    lines = ['# firmware banner', 'invalid frame'] + proc.stdout.splitlines()
    db = tmp_path / 'stm32.sqlite3'
    saved = ingest_lines(lines, max_samples=65, db=db, capture_id='test-capture', batch_size=11)
    assert saved == 65
    allruns = runs(db)
    assert len(allruns) == 1
    assert allruns[0]['samples'] == 65
    assert allruns[0]['run_id'].startswith('capture-test-capture-')
    assert len(get_run(allruns[0]['run_id'],db)) == 65


def test_serial_bridge_rejects_real_source():
    subprocess.run(['make', '-C', str(TOOLS)], check=True, capture_output=True)
    record = json.loads(subprocess.run([str(TOOLS / 'host_smoke')],
        capture_output=True,text=True,check=True).stdout.splitlines()[0])
    record['data_source'] = 'real-rig'
    assert decode_record('# status') is None
    with pytest.raises(ValidationError):
        decode_record(json.dumps(record))


def test_capture_reset_does_not_overwrite(tmp_path):
    subprocess.run(['make', '-C', str(TOOLS)], check=True, capture_output=True)
    p = subprocess.run([str(TOOLS / 'host_smoke'),'stable'],
        capture_output=True,text=True,check=True)
    frames = p.stdout.splitlines()[:4]
    db = tmp_path / 'restarted.sqlite3'
    count = ingest_lines(frames+frames, max_samples=8, db=db,
                         capture_id='reset-test',batch_size=3)
    assert count == 8
    result = runs(db)
    assert len(result) == 2
    assert all(x['samples'] == 4 for x in result)
