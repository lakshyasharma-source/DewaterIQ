#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if ! command -v streamlit >/dev/null 2>&1; then
  echo 'Streamlit not found. Run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt'
  exit 1
fi
make -C embedded
python -m dewateriq_backend.cli demo --samples 90
exec streamlit run app.py
