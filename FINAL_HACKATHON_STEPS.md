# DewaterIQ — submit today: exact execution sequence (India)

**Official Devpost deadline:** Friday, **30 October 2026, 10:30 PM IST** (= 10:00 AM PDT). **Internal target:** 9:30 PM IST. Source: https://nebiusglobalaihackathon.devpost.com/rules

**IMPORTANT JUDGING UPDATE:** The official rules currently show **9–23 December 2026** (rather than December 1–15 from an earlier conversation). Keep judging access available until **23 December at noon Pacific time = 24 December 2026, 1:30 AM IST**, unless the organizer updates rules again. Credits' expiry is not guaranteed by these dates; check Nebius Billing or ask support.

Do the following on **your own Ubuntu/Linux laptop**. This repository DOES NOT contain your Nebius secret key. Cloud inference, STM32CubeIDE flashing, GitHub publishing, screen recording, YouTube upload, and Devpost final submission must be carried out on the computer/accounts to which you have access. Do not mislabel offline or simulated outputs as live/real.

## STEP 1 — get local C99 → Python → NVIDIA Nemotron inference working

Unzip `DewaterIQ_Submission_Ready_2026-10-30.zip`. Open terminal in its `DewaterIQ` folder.

```bash
sudo apt update && sudo apt install -y build-essential python3-venv
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
make -C embedded
python -m pytest -q tests
```

Copy the configuration template **inside the DewaterIQ root**:

```bash
cp .env.example .env
chmod 600 .env
nano .env
```

Put your secret key **only** on the line `NEBIUS_API_KEY=...` in this local `.env`. Keep `NEBIUS_MODEL=nvidia/nemotron-3-super-120b-a12b`. Save (`Ctrl+O`, `Enter`, `Ctrl+X`). Never paste the key in chat, screenshots, Devpost, GitHub, a public demo, or terminal command history. `.gitignore` excludes `.env`, but check before committing.

**One explicit Nebius request** (consumes small API credits, not run in tests):

```bash
python scripts/verify_nebius.py
```

**Pass criterion:** terminal must say `Status: live_nebius` and `SUCCESS: DewaterIQ C99 -> Python -> NVIDIA/Nebius live inference verified.` If it says `offline_api_unavailable`, **it is NOT a success**. Verify key type, Token Factory balance, account/model access and network, without sharing your key.

## STEP 2 — dashboard and proof-of-function

```bash
python -m dewateriq_backend.cli demo --scenario load --samples 90 --seed 7
python -m dewateriq_backend.cli demo --scenario bearing --samples 90 --seed 7
streamlit run app.py
```

Open `http://localhost:8501`. Sidebar: choose a relevant scenario → `Generate & historize run`; select it under `Historian run`, show charts. Scroll to **DewaterIQ Advisory Copilot** and click **Analyze with NVIDIA Nemotron via Nebius** once. Verify the green `LIVE NVIDIA NEMOTRON RESPONSE VIA NEBIUS TOKEN FACTORY` banner and `Result: live_nebius`. Capture proof as a screenshot **with no API key or banking details visible**. A Streamlit panel showing `offline` / `offline_api_unavailable` must NOT be presented as successful live inference.

You may also capture proof in terminal with `python scripts/verify_nebius.py`; be sure no secrets appear in the recording.

**The dashboard is local-only until you deploy it.** `localhost:8501` cannot be used as a public Devpost demo URL.

## STEP 3 — MCU physical STM32U575 build and flash (if feasible)

The firmware **sources** are already included and host-tested; this is **not** a ready-to-flash STM32CubeIDE `.ioc`/ELF. You need STM32CubeIDE and the physical NUCLEO-U575ZI-Q.

1. Connect your Nucleo via its **ST-LINK USB** connector to the laptop. In STM32CubeIDE create `File → New → STM32 Project → Board Selector → NUCLEO-U575ZI-Q` and name it `DewaterIQ_U575`. Use **single non-secure / TrustZone-disabled** demo configuration if requested (on the development board only).
2. Open the generated `.ioc`: set `USART1` to **Asynchronous**, `PA9 TX`, `PA10 RX`, baud **115200**, **8N1**, no flow control; enable **USART1 global interrupt** in NVIC. The board defaults connect USART1 to STLINK VCP; modified solder bridges may alter routing. Leave SWD enabled. Generate project code.
3. Close/conflict-check the target project, then from the DewaterIQ terminal:

   ```bash
   python scripts/stm32_copy_sources.py '/path/to/your/STM32CubeIDE/workspace/DewaterIQ_U575' --dry-run
   python scripts/stm32_copy_sources.py '/path/to/your/STM32CubeIDE/workspace/DewaterIQ_U575'
   ```

   This copies only **five C sources and three headers** to `Core/Src` and `Core/Inc` respectively and **does not replace Cube-generated main.c**. If CubeIDE already uses a different source directory layout, follow `stm32u575/PORTING_GUIDE.md` manually instead.
4. Refresh the project. Add only these hooks to existing **USER CODE** regions in `Core/Src/main.c`:

   In `/* USER CODE BEGIN Includes */`:

   ```c
   #include "diq_stm32_board.h"
   ```

   In `/* USER CODE BEGIN 2 */` after generated UART init:

   ```c
   DIQ_STM32_Init();
   ```

   In `/* USER CODE BEGIN 3 */` inside `while (1)`:

   ```c
   DIQ_STM32_Poll();
   ```

   In `/* USER CODE BEGIN 4 */`:

   ```c
   void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart) {
       DIQ_STM32_RxCpltCallback(huart);
   }
   void HAL_UART_ErrorCallback(UART_HandleTypeDef *huart) {
       DIQ_STM32_UartErrorCallback(huart);
   }
   ```

   Don't define duplicated callbacks: if generated code or libraries already have them, insert the delegating calls into existing implementations.
5. STM32CubeIDE Build Settings → Linker/Miscellaneous: add `-u _printf_float` (for `snprintf` floats) and `-lm` if needed. Build **Project → Build Project**, then **Run → Debug** or **Run** to flash with ST-LINK. If errors, inspect the first actual compiler/linker error and fix before continuing. There is no verified ARM build in this delivered package.

**Pass criterion:** CubeIDE builds an ARM ELF; ST-LINK programs the board; its ST-LINK VCP outputs a `# DewaterIQ...` status banner plus synthetic JSON lines every ~1 second at 115200 8N1.

## STEP 4 — STM32 → Python → SQLite → Streamlit

Stop any serial monitor before the bridge; two programs cannot own the same VCP.

```bash
source .venv/bin/activate
python -m dewateriq_backend.serial_bridge --list-ports
python -m dewateriq_backend.serial_bridge --port /dev/ttyACM0 --scenario load --samples 60
python -m dewateriq_backend.cli runs
streamlit run app.py
```

If the listed port isn't `/dev/ttyACM0`, use its actual path (Linux often `/dev/ttyACM1`, Windows `COMx`). On Ubuntu permission denied: `sudo usermod -aG dialout "$USER"`, then log out and log in (do not run Streamlit as root). New recorded historian IDs include `capture-...-stm32-synthetic...`. Select the run in the UI, show plots, then click live Nemotron advisory once. The board emits **synthetic telemetry on real MCU hardware**; it is not measuring oilfield sensors or commanding a centrifuge.

**Fallback if STM32 won't build in time:** demonstrate the full verified local C99 → Python → Streamlit → live Nebius path, and accurately mark STM32 hardware deployment as planned/unverified. Never claim the board was flashed unless it was.

## STEP 5 — demo video, public repository, Devpost

1. Record screen and, **if you verified it**, board with phone camera/OBS. The video must be **under 3 minutes**, on **public YouTube**. See `DEMO_VIDEO_SHOTLIST.md` for an exact timeline. For the Physical AI track, official rules ask for **at least one minute showing operating physical hardware**, or key modules if the project has no physical hardware. A plugged-in inactive board alone is not a meaningful demo.
2. Create a **public GitHub repository**, e.g. `dewateriq`. Run from project root:

   ```bash
   git init
   git add .
   git status --short
   git ls-files | grep -E '(^|/)(\.env$|secrets\.toml$)|\.key$|\.pem$' && echo 'STOP: inspect secrets' || echo 'No common secret filenames staged'
   git commit -m 'DewaterIQ simulated edge dewatering intelligence MVP'
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/dewateriq.git
   git push -u origin main
   ```

   Before `git add .`, check that the directory contains only distributable files, not recorded field data, private logos, or secret keys. GitHub account and remote repository must exist first. The project includes an MIT LICENSE and a README. Avoid committing the large SQLite demo DB; users can regenerate it.
3. **If choosing Best Apps & Agents**, provide a **working public app/test-build URL**, not localhost. One possible deployment path:
   - Push the repository to GitHub. Visit https://share.streamlit.io/ → **Create app** → choose the public repo, `main` branch, and entrypoint `app.py`.
   - The included `requirements.txt` and **`packages.txt`** install Python dependencies plus `build-essential` for the C99 simulator. Let the deployment run and open the resulting public `*.streamlit.app` URL; **verify** that the `Generate & historize run` button works from a *separate browser session*.
   - To enable live inference from the hosted app, use Streamlit Community Cloud **Advanced settings → Secrets**, adding a root-level `NEBIUS_API_KEY = "YOUR_REAL_KEY"` there **only** (NEVER in GitHub). Verify that the app reports the API key configured and a live inference succeeds. Publishing this service opens a path for strangers to spend your Nebius credits/card balance. **Do not enable uncontrolled public paid inference unless you have reviewed Nebius billing controls, credit expiry, and can accept the risk of charges.** This sample app has no global billing hard cap, multiuser concurrency protections, or robust abuse prevention.
   - If you keep the API key absent for safety, it operates in offline demonstration mode and **does not satisfy a live Nebius integration test by itself**. The app/demo and source code should accurately explain what is verifiable.
   - If no live hosted demo is available, this track risks noncompliance. Streamlit official deployment docs: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy .
4. **If choosing Physical AI**, the rules explicitly **waive the working demo URL**, but they may request physical hardware access and emphasize an operating hardware demo. Choose Physical AI only if your demonstrated work accurately fits the track; software-only alternatives are weaker.
5. Open https://nebiusglobalaihackathon.devpost.com/ and your **My projects/Submit project** form. Use `DEVPOST_SUBMISSION_DRAFT.md` as a starting point, adjusting **hardware and API assertions to what you actually verified**. Provide category, description, public source repository, YouTube demo link, requested feedback, and hosted demo/test build if required. Save, review, **final-submit**, and check the confirmation (a draft isn't final submission).

**Final evidence:** keep screenshots showing live model status, GitHub public repository, public YouTube video, and Devpost **submitted** status. Use `python scripts/check_submission.py` for a limited local preflight; it intentionally cannot prove cloud or Devpost success.
