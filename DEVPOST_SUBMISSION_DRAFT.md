# Devpost draft — DewaterIQ

**Project:** DewaterIQ — Embedded Simulation and NVIDIA Nemotron Copilot for Oilfield Dewatering

**One-line pitch:** A simulation-first, read-only process-intelligence prototype that turns synthetic centrifuge and mud-handling telemetry into explainable anomalies and NVIDIA Nemotron-assisted operator review.

**Track:** Choose after validation: **Physical AI** if the STM32 hardware demo actually runs and you can credibly demonstrate an edge application; otherwise **Best Apps & Agents** is thematically closer to the software AI advisory workflow **provided you can supply a working public demo/test-build URL**, as required.

## Inspiration

Oilfield solids-control and dewatering operations involve interacting mechanical, electrical, fluid-flow and mud-chemistry indicators. A single threshold alarm may not explain changing loads, recovery modes, fluid transfers and cut quality. DewaterIQ explores how edge-first telemetry and an AI copilot could help an operator reason about *possible* causes, with explicit uncertainty and a strict safety boundary.

## What it does

DewaterIQ generates **synthetic** time-series telemetry for centrifuge RPM, feed pump RPM, flow, current, torque, vibration, temperature, VFD frequency, mud properties and pit levels. A C99 edge simulator supports 13 operating/fault scenarios. Python validates incoming NDJSON against a JSON schema, stores events and traces in SQLite, and provides trend analytics, historical comparisons and a Streamlit dashboard. An optional operator-triggered LLM advisory request uses **NVIDIA Nemotron 3 Super 120B via Nebius Token Factory** to generate cautious, explainable hypotheses and suggested verification checks. When the API is unavailable, an explicitly labeled offline rule-based explanation replaces it; the offline output is never represented as an AI result.

## How we built it

C99 deterministic simulator and event logic; Python 3 API/backend; JSON Schema; SQLite historian; Streamlit for the UI; Nebius Token Factory's OpenAI-compatible API for NVIDIA Nemotron 3 Super 120B; optional UART VCP serial bridge for the ST NUCLEO-U575ZI-Q. The firmware port source builds in a host HAL mock test but **actual CubeIDE compilation and MCU flashing must be verified before claiming it in the submission**.

## Challenges

We separated simulated operating modes from actual faults, made safe read-only advisory output explicit, preserved deterministic replay, and kept AI access optional while ensuring the demo identifies whether a real model call succeeded. The biggest limitation is the absence of calibrated real equipment measurements and a field-tested MCU pipeline.

## Accomplishments

13 deterministic scenarios; C99/Python validation; historian and visualization; explainable offline fallback; a Nebius/Nemotron inference interface; C99 STM32 source port. **Update this line with "live API integration tested from application" only after `python scripts/verify_nebius.py` returns `live_nebius`. Update with "MCU flashed and serial telemetry verified" only after actual physical demonstration.**

## What is next

Validate hardware VCP ingestion on the Nucleo board; incorporate authorized real sensor acquisition using isolation/protection and OEM constraints; create physics-calibrated models with field data; add security/identity, bounded compute cost, observability and safety certification, all subject to engineering review.

## Safety and data disclosure

All telemetry and scenario outputs are generated from an illustrative simulator and are **not** field sensor readings. No PLC, VFD, pump, valve or dosing command path is connected. Nemotron's output is a hypothesis for review, not operating instructions or certified diagnostic advice.

## Tech stack

C99; STM32U575 port source; Python 3; SQLite; JSON Schema; Streamlit; Nebius Token Factory; NVIDIA Nemotron 3 Super 120B; optional MQTT/serial VCP.

## Required Devpost fields to fill in yourself

- **Public source:** https://github.com/YOUR_USERNAME/dewateriq (replace after publishing)
- **Public video:** https://www.youtube.com/watch?v=YOUR_VIDEO_ID (replace after uploading)
- **Public application or test build (required except Physical AI):** actual working HTTPS URL — **do not use localhost**
- **Tool feedback:** Nebius Token Factory enabled an OpenAI-compatible hosted NVIDIA-model inference endpoint while keeping control and telemetry handling separate. Add authentic observations and difficulties from your own testing.
- **New work during hackathon:** state precisely which features and integrations you implemented during Aug 26–Oct 30, 2026. Do not claim historical parts as new if not true.
