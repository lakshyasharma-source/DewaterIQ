# DewaterIQ firmware port — NUCLEO-U575ZI-Q (STM32U575ZIT6Q)

**Status: source port prepared; STM32CubeIDE compilation and on-board flashing NOT yet performed.**

This is a firmware **simulation** running on a physical MCU. The project currently **does not measure real centrifuges, sensor signals, or physical process variables** and does not control industrial equipment. All control response variables remain **virtual**. This is not a certified industrial system.

## What runs on the board

All existing **13 synthetic scenarios**, complete schema-1.1 telemetry fields (RPM, pump RPM, VFD, flow, current, torque, temperature, vibration, pits, mud, pH, chemical simulator indices, etc.), windowed trend/event detector, bounded NDJSON output, and virtual scenario-selection commands. **No Python, SQLite, Streamlit, MQTT broker, Nebius key, or AI model runs on the MCU.**

## Board configuration in STM32CubeIDE

1. Plug the **ST-LINK USB** connector on your NUCLEO-U575ZI-Q into your Ubuntu PC.
2. Open STM32CubeIDE → File → New → STM32 Project → Board Selector → search **NUCLEO-U575ZI-Q**. Create a project, e.g. `DewaterIQ_U575`.
3. For this isolated demo, use the **TrustZone-disabled / single application** template if the wizard asks. Do not change security/protection settings on other equipment.
4. In the device configuration enable **USART1 → Asynchronous**, **PA9 = USART1_TX**, **PA10 = USART1_RX**; **115200 baud, 8 data bits, no parity, 1 stop bit, hardware flow control disabled**. Under NVIC enable **USART1 global interrupt** (RX is interrupt-driven). The Nucleo-U575ZI-Q default solder-bridge setup routes USART1 to the ST-LINK **Virtual COM Port**; if your board was modified, check UM2861 rather than assuming the wiring.
5. Keep the board's standard CubeMX SYS/SWD, clock, HAL configuration and Cube-generated USART1 initialization. Initial use requires **no external wiring**.
6. Add the following **existing** C99 sources to the STM32CubeIDE build (copy into `Core/Src/` or link them):
   - `DewaterIQ/embedded/src/simulator.c`
   - `DewaterIQ/embedded/src/detector.c`
   - `DewaterIQ/embedded/src/telemetry.c`
   Add the following **new** sources:
   - `DewaterIQ/stm32u575/Src/diq_app.c`
   - `DewaterIQ/stm32u575/Src/diq_stm32_board.c`
7. Add `DewaterIQ/embedded/include/` and `DewaterIQ/stm32u575/Inc/` to **Project Properties → C/C++ Build → Settings → MCU GCC Compiler → Include paths**. Add `-std=c99` if the project is not already built as C99 or later. `main.c` **from the desktop project must NOT be copied**: CubeIDE generates the board-specific `main.c`.
8. **Critical for floats:** under MCU GCC Linker → Miscellaneous, add **`-u _printf_float`** if the bundled newlib-nano configuration omits floating-point `printf`/`snprintf` support. This is necessary for numeric telemetry to be correctly encoded with `%.3f`. Add `-lm` if the toolchain project does not link math functions automatically.
9. Add the integration hooks below **only in `USER CODE` sections** of the generated `Core/Src/main.c`, so CubeMX code generation preserves them.
10. Build, flash using ST-LINK, open the ST-LINK Virtual COM Port at **115200 8N1**, and check that you receive one full JSON telemetry line each second.

### Cube-generated `main.c` hooks

In `/* USER CODE BEGIN Includes */`:

```c
#include "diq_stm32_board.h"
```

In `/* USER CODE BEGIN 2 */` **after `MX_USART1_UART_Init()`**:

```c
DIQ_STM32_Init();
```

In `/* USER CODE BEGIN 3 */` inside the main `while (1)` loop:

```c
DIQ_STM32_Poll();
```

In a suitable `/* USER CODE BEGIN 4 */` region:

```c
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart) {
    DIQ_STM32_RxCpltCallback(huart);
}

void HAL_UART_ErrorCallback(UART_HandleTypeDef *huart) {
    DIQ_STM32_UartErrorCallback(huart);
}
```

If callbacks already exist, **add the function calls to existing callbacks** instead of defining them twice. For printf/serial output use the built-in ST-LINK port, not the MCU's separate USB-C connector.

## From the Ubuntu development laptop

In the DewaterIQ project root with `.venv` active:

```bash
python -m pip install -r requirements.txt
python -m dewateriq_backend.serial_bridge --list-ports
python -m dewateriq_backend.serial_bridge --port /dev/ttyACM0 --scenario load --samples 60
python -m dewateriq_backend.cli runs
streamlit run app.py
```

Port may instead be `/dev/ttyACM1` or another device. On Linux, if access is denied, check `ls -l /dev/ttyACM*`; on standard Ubuntu configurations membership in the `dialout` group may be required. Never run your full dashboard as root.

Use an ordinary serial terminal if you just want to inspect STM32 text. **Close that terminal before running the Python bridge**, because only one program should own the port at a time.

The board boots in the `stable` synthetic scenario. You can send the virtual simulator text commands `LIST`, `HELP`, `SCENARIO load`, `SCENARIO wet-cut`, `SCENARIO barite-recovery`, `SEED 123`, or `RESET`, each followed by `\n`. The commands do not operate physical machinery. Status replies start with `#`; Python ignores these and validates only synthetic JSON records.

Streamlit re-runs the app after clicking **Refresh historian view**. Select the run whose ID begins with `capture-...-stm32-synthetic` to view the data received from the MCU.

## Verification criteria

- [ ] STM32CubeIDE produces a firmware ELF without build errors.
- [ ] ST-LINK flashes and can debug the target.
- [ ] USB VCP displays `# DewaterIQ ...` banner and well-formed JSON at 1 Hz.
- [ ] `SCENARIO load` changes the synthetic scenario, and `SCENARIO barite-recovery` selects the lower-speed model.
- [ ] Host serial bridge imports schema-valid JSON into SQLite with capture-specific run IDs.
- [ ] Streamlit plots the newly imported STM32 run; it remains labeled **synthetic**.
- [ ] All 13 scenarios are available. The board runs **one selected scenario at a time**, with all the implemented signals contained in each frame.
- [ ] No external industrial equipment is wired or controlled.

### Known limitations

No actual field signal has been validated. Simulation values, chemistry response, valve and VFD response are illustrative and not process control rules. UART communication is not encrypted: use only within an isolated lab environment. MCU transport is demonstration-grade and does not implement power-failure persistence, authenticated OTA, fault-tolerant historian buffering or a production watchdog design. High-speed real-sensor sampling, protection circuits, hazardous-area approvals, OEM authorization and industrial cybersecurity require separate engineering.

## Official board documentation

- ST Nucleo-U575ZI-Q board manual: **UM2861** (solder bridges and VCP)
- STM32CubeU5 getting-started manual: **UM2883** (project/examples)
