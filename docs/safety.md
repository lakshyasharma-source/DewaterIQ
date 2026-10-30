# Safety, privacy and deployment boundaries

## What is explicitly excluded

- No interface to real centrifuges, industrial PLCs, VFDs, pumps, valves, chemical dosing, interlocks, rig control networks, Pason systems or OEM controllers.
- No device reading from serial ports, GPIO, CAN, Modbus, OPC UA, EtherNet/IP or actual sensor/telemetry sources.
- No model output accepted as input by the C simulator or any future controller API.
- No automatic chemical dosage calculations or actuator commands.
- No nonvalidated parameter used as a protective trip or an actual site limit.
- No claim that observed amp, speed, pH, torque or chemical thresholds are generally safe.
- No reproduction of third-party rig videos or private equipment details.

## Virtual control fields are not physical

The fields `commanded_virtual_*` and `controller_mode=automatic_virtual_simulation` refer to an isolated software model. They are necessary to demonstrate tracking/degradation/saturation scenarios. They do NOT support sending commands to hardware, nor can model inference affect their value. The operator dashboard is advisory-only. Using the software at a real rig would require a fundamentally new design and rigorous validation.

## Deployment checklist — not completed

Before any potential field trial: written equipment-owner permission, approved network boundaries, hazardous-area/ATEX/IECEx/NEC requirements as applicable, power isolation, EMC, safety assessment, qualified mud/chemical engineer approval, data ownership, calibration, interlock responsibility, operator training, secure authentication, audit logs and fail-safe behavior. This prototype is not approved for use on physical equipment.

## Inference key handling

Set `NEBIUS_API_KEY` as an environment variable; never put it in Git, screenshots or live transcripts. The client sends only **synthetic generated data** to Nebius for analysis. Inference costs and model IDs depend on the user's Nebius account; the key, if present, can incur charges. The app never automatically triggers paid inference — user must click the button.
