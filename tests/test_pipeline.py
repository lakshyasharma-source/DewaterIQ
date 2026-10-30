"""Offline end-to-end integration tests: C99 -> JSON Schema -> SQLite -> analytics."""
import json
import subprocess
from pathlib import Path
import pytest
from jsonschema import ValidationError
from dewateriq_backend.analytics import offline_explanation, similar_runs, summary
from dewateriq_backend.historian import add_note, get_events, get_notes, get_run, insert_records, runs
from dewateriq_backend.nebius import analyze
from dewateriq_backend.schema import validate_record
from dewateriq_backend.sim_runner import SCENARIOS, build, generate

@pytest.fixture(scope='session',autouse=True)
def build_simulator(): build()

@pytest.mark.parametrize('scenario',SCENARIOS)
def test_all_scenarios_valid(scenario):
    data=generate(scenario,60,7)
    assert len(data)==60
    assert all(x['data_source']=='synthetic' for x in data)
    assert all(x['sensor_valid'] for x in data)
    assert all(x['machine']['simulated_actual_centrifuge_rpm']>=0 for x in data)
    assert data[0]['timestamp_s']==1 and data[-1]['timestamp_s']==60


def test_replay_is_deterministic():
    assert generate('load',75,11)==generate('load',75,11)
    assert generate('load',75,11)!=generate('load',75,12)


def test_schema_rejects_unapproved_sources():
    data=generate('stable',1,7)[0]
    data['data_source']='real-rig'
    with pytest.raises(ValidationError): validate_record(data)


def test_historian_notes_and_evidence(tmp_path):
    path=tmp_path/'run.sqlite3'
    records=generate('load',80,7)
    assert insert_records(records,path)==80
    assert len(get_run(records[0]['run_id'],path))==80
    assert runs(path)[0]['samples']==80
    add_note(records[0]['run_id'],30,'Experienced operator would inspect loading','acceptable',path)
    assert get_notes(records[0]['run_id'],path)[0]['cut_quality']=='acceptable'
    assert get_events(records[0]['run_id'],path)
    assert summary(records)['current_delta_a']>10
    assert 'OFFLINE RULE-BASED DEMO' in offline_explanation(records)


def test_mode_avoids_false_volume_loss_alarm():
    volume=generate('volume-loss',65,7)
    text=offline_explanation(volume)
    assert 'intentional' in text.lower()
    assert volume[-1]['operating_mode']=='intentional_volume_loss'


def test_nebius_no_key_offline(monkeypatch):
    monkeypatch.delenv('NEBIUS_API_KEY',raising=False)
    monkeypatch.delenv('NEBIUS_TOKEN_FACTORY_KEY',raising=False)
    result=analyze(generate('stable',60,7))
    assert result['status']=='offline'
    assert result['model'] is None


def test_similarity_same_mode_and_mud_only():
    target=generate('load',80,7)
    same_mode=generate('pump-degradation',80,7)
    other=generate('volume-loss',80,7)
    matches=similar_runs(target,[same_mode,other])
    assert len(matches)==1
    assert matches[0]['scenario']=='pump-degradation'


def test_simulator_cli_blocks_unexpected_args():
    from dewateriq_backend.sim_runner import BIN
    rc=subprocess.run([str(BIN),'--connect-to-real-vfd'],capture_output=True)
    assert rc.returncode!=0


def test_simulated_multi_machine_and_barite():
    barite=generate('barite-recovery',70,7,'CENT-SIM-02')
    polisher=generate('stable',70,7,'CENT-SIM-01')
    assert barite[0]['centrifuge_role']=='barite_recovery'
    assert barite[0]['operating_mode']=='barite_recovery'
    assert barite[0]['run_id']!=polisher[0]['run_id']
    assert barite[-1]['machine']['simulated_actual_centrifuge_rpm'] < polisher[-1]['machine']['simulated_actual_centrifuge_rpm']
