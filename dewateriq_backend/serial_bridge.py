"""Receive synthetic DewaterIQ STM32 USART1/VCP NDJSON into the local SQLite historian.

This listener has no industrial-control interface. It can send ONLY simulator
scenario-selection commands to the DewaterIQ test firmware; those commands
change software-model state, never physical outputs.
"""
import argparse
from datetime import datetime, timezone
import json
from uuid import uuid4
from jsonschema import ValidationError

from .historian import insert_records
from .schema import validate_record
from .sim_runner import SCENARIOS


def decode_record(line):
    """Parse one record, ignoring explicit '#' firmware status messages."""
    if isinstance(line, bytes):
        line = line.decode('utf-8', errors='replace')
    line = line.strip()
    if not line or line.startswith('#'):
        return None
    raw = json.loads(line)
    validate_record(raw)
    if raw['data_source'] != 'synthetic':
        raise ValueError('STM32 demo bridge refuses non-synthetic records')
    return raw


def ingest_lines(lines, max_samples=30, db=None, capture_id=None, batch_size=10):
    """Unit-testable stream import. Keep a unique run ID per reset/role change."""
    if max_samples <= 0:
        raise ValueError('max_samples must be positive')
    if batch_size <= 0:
        raise ValueError('batch_size must be positive')
    if capture_id is None:
        capture_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid4().hex[:8]
    capture_id = ''.join(x for x in capture_id if x.isalnum() or x in '-_')[:55]
    pending, count = [], 0
    last_run_key, last_timestamp, segment = None, None, 0
    for line in lines:
        try:
            record = decode_record(line)
        except (ValueError, UnicodeError, ValidationError) as exc:
            print(f'Ignoring invalid or incomplete frame: {exc}')
            continue
        if record is None:
            continue
        raw_run = record['run_id']
        ts = record['timestamp_s']
        if raw_run != last_run_key:
            segment += 1
        elif last_timestamp is not None and ts <= last_timestamp:
            segment += 1
        record['run_id'] = f'capture-{capture_id}-part{segment}-{raw_run}'
        last_run_key, last_timestamp = raw_run, ts
        pending.append(record)
        count += 1
        if len(pending) >= batch_size:
            insert_records(pending, db)
            pending.clear()
        if count >= max_samples:
            break
    if pending:
        insert_records(pending, db)
    return count


def main():
    parser = argparse.ArgumentParser(description='DewaterIQ synthetic STM32 serial -> SQLite historian')
    parser.add_argument('--port', help='Linux /dev/ttyACM0 or Windows COM number')
    parser.add_argument('--baud', type=int, default=115200)
    parser.add_argument('--samples', type=int, default=60)
    parser.add_argument('--scenario', choices=SCENARIOS, default=None)
    parser.add_argument('--db', default=None)
    parser.add_argument('--list-ports', action='store_true')
    args = parser.parse_args()
    try:
        import serial
        from serial.tools import list_ports
    except ImportError:
        parser.error('Install pyserial: python -m pip install pyserial')
    if args.list_ports:
        for port in list_ports.comports():
            print(f'{port.device}\t{port.description}')
        return
    if not args.port:
        parser.error('--port is required unless --list-ports is used')
    if args.samples < 1 or args.samples > 1000000:
        parser.error('--samples must be 1..1000000')
    print(f'Listening to {args.port} at {args.baud} 8N1 (synthetic frames only)...')
    with serial.Serial(args.port, args.baud, timeout=3, write_timeout=3) as conn:
        if args.scenario:
            # Only our simulator's virtual-scenario command; not a control channel.
            conn.write(f'SCENARIO {args.scenario}\n'.encode('ascii'))
        def frames():
            while True:
                yield conn.readline()
        count = ingest_lines(frames(), max_samples=args.samples, db=args.db)
    print(f'Saved {count} validated STM32 synthetic telemetry records to SQLite.')

if __name__ == '__main__':
    main()
