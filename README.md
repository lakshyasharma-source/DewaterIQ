# DewaterIQ — Oilfield Solids-Control Process Intelligence

**Hackathon day-of-submission runbook:** [FINAL_HACKATHON_STEPS.md](FINAL_HACKATHON_STEPS.md). Includes live Nebius single-call verifier, prepared CubeIDE source-copy script, demo-video outline, and Devpost draft. The project has not been flashed to the STM32 or deployed publicly in this package.

**NVIDIA × Nebius hackathon demonstrator** combining compiled **C99**, **Python**, optional **MQTT**, **SQLite**, **Streamlit**, and optional **NVIDIA Nemotron on Nebius Token Factory**.

> **SIMULATION ONLY — ADVISORY / READ-ONLY — NO PHYSICAL EQUIPMENT CONNECTIONS.**
>
> All values, events and model outcomes are synthetic. Virtual control state in C changes only the simulation, not machinery. No PLC/VFD/valve/pump/dosing/safety-interlock integration exists.

## What is fully implemented

- Native GCC-compiled ISO C99 deterministic equipment/process simulator with **13 scenarios**: stable, rising load, pump degradation, wet cut, intentional volume loss, pit imbalance, bearing issue, power fault, VFD degradation, valve restriction, dosing deviation, virtual controller saturation, low-speed barite recovery.
- C-level telemetry and basic deterministic event tags, including virtual control response/degradation simulation.
- JSON Schema 2020-12 validation requiring `data_source=synthetic`.
- Local historian in SQLite storing machine/process telemetry, events, and operator annotations.
- Event/trend summaries and mode-aware similar-run retrieval.
- Interactive Streamlit dashboard with process/asset/chemistry trends, notes, and replay.
- Optional telemetry MQTT **publish & ingest** via trusted test broker; topics are simulation-only.
- Real API client for NVIDIA Nemotron hosted by Nebius Token Factory, with explicit no-key/offline fallback. API not tested without credentials.
- Automated offline integration tests and GitHub Actions CI.

## Quick start (Ubuntu / Linux / WSL)

**Prerequisites:** Python 3.10+, GCC, Make, pip. On Ubuntu: `sudo apt install build-essential python3-venv`.

```bash
cd DewaterIQ
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
make -C embedded
python -m dewateriq_backend.cli demo --samples 90
streamlit run app.py
```

Open the Streamlit URL shown in your terminal (typically http://localhost:8501).

**Windows:** use WSL2 Ubuntu (or compile the C99 sources using your preferred compatible toolchain). **Docker alternative:**

```bash
docker build -t dewateriq .
docker run --rm -p 8501:8501 dewateriq
```

## STM32U575ZI-Q embedded port (added October 29, 2026)

**Source-level port prepared and host tested — not yet flashed to the user's board.** This is a real STM32-targeted edge application using CubeIDE HAL/USART1, but the current telemetry remains a *simulated* oilfield process. All 13 scenarios and all existing C99 telemetry fields are preserved.

**[Step-by-step board setup](stm32u575/PORTING_GUIDE.md)** — shows exact CubeIDE board selection, ST-LINK Virtual COM/USART1 setup, linker options, USER CODE hooks and end-to-end Python bridge.

Files: `stm32u575/Inc/diq_app.h`, `stm32u575/Src/diq_app.c`, `stm32u575/Inc/diq_stm32_board.h`, `stm32u575/Src/diq_stm32_board.c`. They reuse the same C99 `embedded/src/simulator.c`, `detector.c`, `telemetry.c` and `embedded/include/dewateriq.h` as the native simulator. Board `main.c` must come from CubeMX, **not** from the Linux simulator.

Native build/port test without needing a physical board:

```bash
make -C embedded clean all test
make -C stm32u575/tools test
make -C stm32u575/tools board-stub
./stm32u575/tools/board-stub
python -m pytest tests -q
```

After you flash firmware and connect ST-LINK USB, from Ubuntu:

```bash
python -m dewateriq_backend.serial_bridge --list-ports
python -m dewateriq_backend.serial_bridge --port /dev/ttyACM0 --scenario load --samples 60
python -m dewateriq_backend.cli runs
streamlit run app.py
```

The serial bridge validates STM32 synthetic schema records before storing them. Dashboard **Refresh historian view** reloads the stored data. Python / SQLite / Streamlit / MQTT broker / Nebius remain on the host or future Jetson, **not on STM32**. No MCU flash result is claimed until verified on real hardware. No physical actuator interface exists.

## Explore without UI

```bash
# Native C99 standalone telemetry (no backend required)
./embedded/dewateriq_sim --scenario load --samples 60 --seed 7 > load.ndjson

# Populate the historian from the C binary
python -m dewateriq_backend.cli demo --scenario all --samples 90

# Run a second simulated centrifuge in barite-recovery duty
python -m dewateriq_backend.cli demo --scenario barite-recovery --samples 90 --centrifuge-id CENT-SIM-02

# Get a stored run ID
python -m dewateriq_backend.cli runs

# Get a local offline summary: NO AI required
python -m dewateriq_backend.cli report synthetic-load-seed7-CENT-SIM-01

# Run C + Python tests
make -C embedded test
python -m pytest tests -q
```

## Optional NVIDIA Nemotron via Nebius Token Factory

DewaterIQ uses Nebius's OpenAI-compatible `/v1/chat/completions` endpoint and the NVIDIA Nemotron model ID specified by `NEBIUS_MODEL`. Follow official Nebius documentation and verify the selected model is available with your key. The program defaults to `nvidia/nemotron-3-super-120b-a12b`.

```bash
cp .env.example .env
chmod 600 .env
# Edit .env locally; enter your secret on NEBIUS_API_KEY=... only; NEVER commit .env
python scripts/verify_nebius.py  # ONE intentional live API call, may use credits
streamlit run app.py
```

Click **Analyze with NVIDIA Nemotron via Nebius** in the dashboard. Without an API key, or if a live API call fails, the application visibly provides **OFFLINE RULE-BASED DEMO** instead. It **does not** pretend the offline text was generated by AI. Live inference is not tested in this package because user credentials are unavailable.

From CLI, use `python -m dewateriq_backend.cli report synthetic-load-seed7-CENT-SIM-01 --use-nebius` to explicitly request an AI call. Calls may consume Nebius credits.

## Optional MQTT test transport

No MQTT broker is needed for the normal demo. To exercise the optional publish/subscribe pathway, install Mosquitto and run **a trusted local test broker only**:

```bash
# Terminal 1 — local trusted development broker
mosquitto -p 1883
# Terminal 2 — MQTT -> validated SQLite importer
python -m dewateriq_backend.mqtt_bridge listen --count 60
# Terminal 3 — C99 -> synthetic MQTT publisher
python -m dewateriq_backend.mqtt_bridge publish --scenario load --samples 60
```

Only the `dewateriq/sim/telemetry/v1` topic is supported. No control-command topics exist. For deployments on any network, use authenticated TLS broker configuration and a separately reviewed security design; **do not connect this prototype to a rig OT network**.

## What the data represents

The C99 simulator models virtual RPM, feed pump speed, flow, motor current, torque, vibration, temperature, pH, mud weight, source/destination pit levels, virtual polymer/chemical percentage response and cut-quality annotations. Its trends are deliberately synthetic, with no physical fidelity guarantee. The reported **2044 RPM**, **1077 RPM**, ~**528 GPM**, and ~**2,150 RPM** figures from the field discussion have been used only as contextual inspiration, not imported datasets or universal setpoints. The unclear physical controller display previously interpreted as 55 Hz remains **unverified**. See `docs/field-evidence.md`.

The dashboard's operating mode distinguishes **intentional volume loss** from an assumed process failure — a key insight from field interviews.

## Repository map

```text
DewaterIQ/
├── embedded/include/dewateriq.h
├── embedded/src/{main.c, simulator.c, detector.c, telemetry.c}
├── embedded/Makefile
├── dewateriq_backend/
│   ├── cli.py, sim_runner.py, schema.py
│   ├── historian.py, analytics.py, nebius.py, mqtt_bridge.py
├── backend/schemas/telemetry.schema.json
├── app.py                 # Streamlit dashboard
├── tests/test_pipeline.py
├── docs/{architecture.md,field-evidence.md,safety.md}
├── .github/workflows/ci.yml
├── .env.example
├── Dockerfile
├── requirements.txt
└── README.md
```

## Important design limits

A diagram of production intent (not implemented): future authorized independent sensors/read-only exposed signals → industrial DAQ → edge historian → analytics/AI → operator advisory. A PLC and NVIDIA Jetson may be considered only later, subject to requirements and field validation; the STM32 firmware port is source-ready but **has not been flashed or field-tested**, **no real historian data**, **no closed-loop equipment automation** and **no predictive model trained on real rig data**.

The AI layer does not generate equipment setpoint outputs and has no technical route to drive simulated/physical actuators. The future field system is a separate engineering certification/approval effort.

## Hackathon demo script (2 minutes)

1. Introduce the field problem: scattered transient machine telemetry, manual mud chemistry observations, operator-experience dependency.
2. Show C99 compiler/build; generate stable run, then rising-load and intentional-volume-loss runs.
3. In Streamlit, overlay RPM, flow, amps/torque, pit levels and the two logical historian views.
4. Show similar-run evidence and operator annotations; point out the explicit **synthetic** badge.
5. Click Nemotron analysis **if Nebius API key configured**; show actual live call status `live_nebius` or transparently offline fallback.
6. Close with safety: **read-only simulation, no physical control**, field pilot only after equipment-owner authorization and validation.

## License

MIT, see `LICENSE`. Do not redistribute operator videos or proprietary site information without permission.
