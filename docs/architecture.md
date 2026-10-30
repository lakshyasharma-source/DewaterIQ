# Architecture and interface contracts

DewaterIQ is currently a **completely isolated software simulation**, not a field-deployed controller. Architecture is constrained by explicit non-actuation: no PLC/VFD control interface, serial/Modbus/OPC adapter, physical I/O, or dosing pathway.

```text
                      ┌──────────────────────────────┐
                      │ C99 process/equipment model  │
                      │ + virtual controller response│
                      │ + basic trend/event detector │
                      └─────────────┬────────────────┘
                                    │ NDJSON stdout
                                    ▼
                     ┌────────────────────────────────┐
                     │ Python schema validator / CLI  │
                     │ optional Paho publisher        │
                     └─────────────┬──────────────────┘
                                   │
           local                    │              optional trusted test MQTT broker
           stdout ───────────────► │ ◄── MQTT telemetry-only subscriber
                                   ▼
                     ┌────────────────────────────────┐
                     │ SQLite time-series / event DB  │
                     │ operator annotation table      │
                     └─────────────┬──────────────────┘
                                   │
                ┌──────────────────┴─────────────────┐
                ▼                                    ▼
      Streamlit/Plotly                         Analytics engine
      trend dashboard                   self-comparison, similar runs
                └──────────────────┬─────────────────┘
                                   ▼
                         Nemotron / Nebius
                          optional live API
                        diagnostics/explanation
                                   │
                                   ▼
                       ADVISORY TEXT ONLY
                       NEVER equipment commands
```

## Technology decisions

| Layer | Working implementation | Source of truth |
|---|---|---|
| Equipment/process | Native GCC-compiled ISO C99 `embedded/dewateriq_sim` | Synthetic only |
| Telemetry representation | NDJSON with schema 1.1 and explicit `data_source=synthetic` | C emitter validated by Python JSON Schema |
| Transport | stdout/subprocess guaranteed; optional MQTT QoS 1 | Simulator-only topic `dewateriq/sim/telemetry/v1` |
| Backend | Python modules / CLI | Read/validate/store/summarize |
| Historian | SQLite telemetry + events + operator notes | Run ID + centrifuge ID + relative sample second |
| Analytics | deterministic trends and comparable-run retrieval | Untrained, simulation-only |
| UI | Streamlit | Reads historian, generates local demo runs |
| AI | optional NVIDIA Nemotron via Nebius Token Factory | API call requires user-supplied key |

## Current implementation status

- C99 compilation, 13 deterministic scenarios, virtual changes in machine state: **implemented and locally tested**.
- JSON telemetry and schema validation: **implemented and locally tested**.
- SQLite historian and events/notes: **implemented and locally tested**.
- Offline analysis and comparable-run retrieval: **implemented**.
- Streamlit interface: **implemented**, requires installing runtime dependencies to launch.
- MQTT publish and receive code: **implemented**; external MQTT broker integration is optional and not verified in this environment.
- Live NVIDIA/Nebius inference: **implemented as real OpenAI-compatible API client**, not tested without the user's key or network access. Offline fallback is explicit and never represented as AI.
- Actual Kayden, Pason, rig PLC/VFD access: **not implemented**. No real hardware data was used.

## Telemetry and simulation limits

- `timestamp_s` is a *relative simulation second*, NOT a UTC timestamp. Production time synchronization requires new design and separate authorization.
- `commanded_virtual_*`, `simulated_*`, `controller_mode` indicate **software-model state only**.
- `mud_weight_ppg`, `ph`, `torque_percent` are mock values. The chemistry model is invented for demonstration, not calibrated against field tests.
- The simulator is intentionally a simple state machine with toy linear trends and deterministic pseudorandom jitter. It does **not** contain a centrifuge physics model and cannot predict real-world outputs.
- Every run has a unique `(scenario,seed)` identity; reimporting the same run replaces duplicate samples. Choose a new seed to compare runs.
- A real field pilot requires authorization, hazard-area review, OEM interface confirmation, process engineer validation, proper instrumentation and cybersecurity assessment.
