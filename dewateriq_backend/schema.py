"""Offline JSON Schema validation for synthetic telemetry."""
import json
from pathlib import Path
from jsonschema import Draft202012Validator

SCHEMA_FILE = Path(__file__).resolve().parent.parent / 'backend' / 'schemas' / 'telemetry.schema.json'


def validate_record(record):
    schema = json.loads(SCHEMA_FILE.read_text(encoding='utf-8'))
    Draft202012Validator(schema).validate(record)
    return record
