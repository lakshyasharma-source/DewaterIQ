#!/usr/bin/env python3
"""One deliberately triggered LIVE Nemotron/Nebius backend integration check.

Does not display or record an API key. Exits nonzero on fallback / failure.
Consumes a small amount of promotional/paid credits if the call succeeds.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dewateriq_backend.sim_runner import generate  # noqa: E402
from dewateriq_backend.nebius import analyze, DEFAULT_MODEL  # noqa: E402


def main():
    if not (os.getenv('NEBIUS_API_KEY') or os.getenv('NEBIUS_TOKEN_FACTORY_KEY')):
        print('ERROR: No NEBIUS_API_KEY found in local .env or terminal. No API request sent.')
        return 2
    print('Nebius key: present (secret withheld)')
    print('Model:', os.getenv('NEBIUS_MODEL', DEFAULT_MODEL))
    print('Producing synthetic centrifuge load telemetry from compiled C99...')
    try:
        data = generate('load', 60, 7)
    except Exception as exc:
        print(f'ERROR: Unable to run local C99 simulator ({type(exc).__name__}). Build with make -C embedded.')
        return 3
    print('Sending ONE explicit advisory-only API request; this may use account credits...')
    result = analyze(data)
    print('Status:', result['status'])
    print('Reported model:', result.get('model'))
    print('Note:', result.get('note', ''))
    print('--- Advisory response (synthetic simulation) ---')
    print(result['text'])
    if result['status'] != 'live_nebius':
        print('FAILED: API integration NOT verified. Offline result is not proof of a live call.')
        return 1
    print('SUCCESS: DewaterIQ C99 -> Python -> NVIDIA/Nebius live inference verified.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
