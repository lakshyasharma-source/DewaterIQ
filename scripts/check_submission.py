#!/usr/bin/env python3
"""Offline checklist: does not claim Devpost, hardware or cloud verification."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dewateriq_backend.historian import runs  # noqa: E402


def main():
    checks = {
        'MIT license': (ROOT / 'LICENSE').is_file(),
        'README': (ROOT / 'README.md').is_file(),
        'C99 simulator built': (ROOT / 'embedded/dewateriq_sim').is_file(),
        'STM32 source prepared': (ROOT / 'stm32u575/Src/diq_app.c').is_file(),
        'Python Nebius client present': (ROOT / 'dewateriq_backend/nebius.py').is_file(),
    }
    for label, result in checks.items():
        print(f'{"PASS" if result else "TODO"}: {label}')
    try:
        stored = runs()
        print(f'Historian: {len(stored)} stored runs')
    except Exception as exc:
        print(f'Historian unavailable: {type(exc).__name__}')
    for item in ('Live API from user computer', 'CubeIDE ARM build', 'STM32 physical flash and VCP',
                 'Public GitHub repository', 'Public YouTube demo video', 'Publicly accessible demo/test build',
                 'Devpost final submission'):
        print(f'USER VERIFICATION REQUIRED: {item}')
    return 0 if all(checks.values()) else 1


if __name__ == '__main__':
    raise SystemExit(main())
