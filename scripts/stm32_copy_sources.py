#!/usr/bin/env python3
"""Copy only DewaterIQ firmware module files to a new CubeIDE-generated project.

NEVER overwrites CubeIDE main.c or generated HAL sources. Intended for an empty
CubeIDE NUCLEO-U575ZI-Q project with USART1 enabled.
"""
import argparse
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [
    ROOT / 'embedded/src/simulator.c',
    ROOT / 'embedded/src/detector.c',
    ROOT / 'embedded/src/telemetry.c',
    ROOT / 'stm32u575/Src/diq_app.c',
    ROOT / 'stm32u575/Src/diq_stm32_board.c',
]
HEADERS = [
    ROOT / 'embedded/include/dewateriq.h',
    ROOT / 'stm32u575/Inc/diq_app.h',
    ROOT / 'stm32u575/Inc/diq_stm32_board.h',
]


def copy_sources(project, dry_run=False):
    project = Path(project).expanduser().resolve()
    src, inc = project / 'Core' / 'Src', project / 'Core' / 'Inc'
    if not (src.exists() and inc.exists() and (src / 'main.c').exists()):
        raise ValueError('Select the generated STM32CubeIDE project root (requires Core/Src/main.c and Core/Inc).')
    if not (project / '.project').exists():
        raise ValueError('The selected folder does not appear to be an STM32CubeIDE project (.project missing).')
    planned = [(p, (src if p.suffix == '.c' else inc) / p.name) for p in SOURCES + HEADERS]
    for origin, dest in planned:
        if dest.exists() and dest.read_bytes() != origin.read_bytes():
            raise FileExistsError(f'Will NOT overwrite an existing modified file: {dest}')
    for origin, dest in planned:
        if not dry_run:
            shutil.copy2(origin, dest)
        print(f'{"WOULD COPY" if dry_run else "COPIED"}: {origin.name} -> {dest}')
    print('\nNEXT: In CubeIDE refresh project, add USER CODE hooks in main.c,')
    print('enable USART1 interrupt, check -u _printf_float and -lm, then Build/Flash.')
    return len(planned)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('cubeide_project', help='Path to CubeIDE-generated project root')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    try:
        copy_sources(args.cubeide_project, args.dry_run)
        return 0
    except (ValueError, FileExistsError, OSError) as exc:
        print(f'ERROR: {exc}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
