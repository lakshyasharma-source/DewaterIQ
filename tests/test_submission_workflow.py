"""Offline verification of the LIVE request wiring via a mock, NOT a Nebius test."""
import sys
import types

from dewateriq_backend.nebius import analyze, DEFAULT_BASE, DEFAULT_MODEL
from dewateriq_backend.sim_runner import generate
from scripts.stm32_copy_sources import copy_sources


def test_nebius_wrapper_builds_real_nvidia_model_request(monkeypatch):
    observed = {}

    class Completions:
        def create(self, **kwargs):
            observed.update(kwargs)
            return types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content='Simulated API test response'))])

    class OpenAI:
        def __init__(self, **kwargs):
            observed['client_config'] = kwargs
            self.chat = types.SimpleNamespace(completions=Completions())

    monkeypatch.setitem(sys.modules, 'openai', types.SimpleNamespace(OpenAI=OpenAI))
    monkeypatch.setenv('NEBIUS_API_KEY', 'TEST-FAKE-KEY-DO-NOT-USE')
    monkeypatch.delenv('NEBIUS_MODEL', raising=False)
    monkeypatch.delenv('NEBIUS_BASE_URL', raising=False)
    response = analyze(generate('load', 15, 7))
    assert response['status'] == 'live_nebius'
    assert observed['client_config']['base_url'] == DEFAULT_BASE
    assert observed['model'] == DEFAULT_MODEL
    assert observed['max_tokens'] == 550
    assert observed['temperature'] == 0.15
    assert 'synthetic' in observed['messages'][1]['content']
    assert 'TEST-FAKE-KEY-DO-NOT-USE' not in str(response)


def test_copy_cubeide_sources_never_overwrites_main(tmp_path):
    p = tmp_path / 'CubeProject'
    (p / 'Core' / 'Src').mkdir(parents=True)
    (p / 'Core' / 'Inc').mkdir(parents=True)
    (p / '.project').write_text('test')
    (p / 'Core' / 'Src' / 'main.c').write_text('CUBEMX GENERATED CODE DO NOT REPLACE')
    assert copy_sources(p, dry_run=True) == 8
    assert not (p / 'Core' / 'Src' / 'diq_app.c').exists()
    assert copy_sources(p) == 8
    assert (p / 'Core' / 'Src' / 'main.c').read_text() == 'CUBEMX GENERATED CODE DO NOT REPLACE'
    assert (p / 'Core' / 'Inc' / 'dewateriq.h').exists()
