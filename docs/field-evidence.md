# Field interview evidence register (not engineering specifications)

Use these four labels consistently:

- **A — operator-reported facts:** described directly in interview; not independently audited.
- **B — site/machine-specific observations:** no universal alarm/setpoint status.
- **C — proposals:** solutions/models/concepts not observed on site.
- **D — uncertain/unverified:** field investigation required.

| Category | Topic | Information | Next validation |
|---|---|---|---|
| A | Rig | Direct on-rig solids-control/dewatering in backyard operation | Site diagram/P&ID and approvals |
| A | Equipment duties | Low-speed barite-recovery centrifuge ahead of high-speed polisher | Process connections and sampling points |
| A | Pit network | Approximately six pits, equalizers; 4–6 interconnected, transfers 4→3, 6→2 reportedly used | Map connections/valve states and real flow direction |
| B | Pit inventory | Approx 100 bbl per pit, ~600 total | Actual capacity, usable volume |
| B | Flow | Operator indicated ~528 GPM measured in one operating context | Exact sensor, units, calibration, conditions |
| B | Machine speed | WBM examples ~1100–1300 RPM; OBM examples ~2100–2150 RPM | Manufacturer + field context |
| B | Current | ~35 A, 45–51 A, 60–70 A, 80–90 A as anecdotes | Motor/VFD model, actual runs, normalized load |
| B | Polymer pH | ~10–11.5 in one particular treatment | Actual product chemical engineer data |
| B | Panel | 2044 RPM centrifuge; 1077 RPM feed pump at one observed moment | Signaling/sensor channel identity |
| D | Additional control display | ~75.53 from video reinspection; earlier 55.0 interpretation retracted | What parameter/unit is displayed? |
| A | Data gap | Amp/torque traces not routinely logged in worker's reporting workflow | Service technician HMI logs check |
| A | Operation | Intentional wet-discharge and fluid-volume loss can be desired during reconditioning | explicit operating mode and operator target |
| A | Cut quality | Wet/dry discharge currently judged visually by operator | laboratory reference labels |
| A | Chemistry | polymer hydration/dilution, pH, calcium nitrate, lime etc. involved | process engineer procedure, fluid test records |
| A | Constraints | rented/proprietary control; no unauthorized experimental connection | written owner/OEM agreement |
| D | Kayden model | Mammoth centrifuge family; 2276 strongly suggested by public brochure specs | nameplate/serial and technician |
| D | Rig data system | “Payson” spoken; could be Pason | software/system exact name and permission |
| D | Signals | external Modbus/OPC/MQTT/other machine data access not confirmed | vendor register map; no network probing |
| C | Sensors | independent pH, flow, level, isolated motor current, possible output moisture | hazardous-area rated procurement & installation review |
| C | AI | trends, similar-runs, operator decision support, later chemistry optimization | real labeled datasets and offline evaluation |

## OEM material vs local facts

Manufacturer brochures and educational sources can validate generic process principles but **cannot** prove which exact machine or calibration is installed. The 528 GPM / ~1312 G match to public Mammoth-2276 specs is a useful lead, not a nameplate identification. Likewise, software showing virtual VFD frequency of 55 Hz is not evidence that the filmed physical panel read 55 Hz.

## What the hackathon demonstration claims

The implemented simulator represents *illustrative* variables from the field interview; all generated RPM, current, torque, pH, flow, fault, dosing and quality values are fabricated within code. NO recorded process value from a real drilling rig is imported or redistributed. This separation avoids inadvertently treating private data, operator accounts, or manufacturer brochures as verified design inputs.
