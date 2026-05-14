# Pytest Automation Framework — UI & API Testing

Enterprise-oriented **pytest** automation for the **Expand Testing Notes** practice application. This repository gives new QA engineers a clear path from clone to green runs, with three supported execution profiles: **UI**, **API**, and **stability** (combined collection).

---

## 1. 📋 Project title & overview

### What this framework does

Automates **end-to-end UI** flows (Selenium) and **REST API** checks (`requests`) against a shared practice environment. Tests are organized with **Page Object Model (POM)** for UI, a small **`APIClient`** wrapper for HTTP, and **pytest fixtures** for browser lifecycle, auth tokens, and configuration.

### Key features

| Area | Capability |
|------|------------|
| Test runner | **pytest** with markers (`smoke`, `regression`, `positive`, `negative`, `ui`, `api`) |
| UI | Selenium WebDriver, POM under `pages/`, `webdriver-manager` for drivers |
| API | Reusable client, token fixture, JSON payloads |
| Resilience | **`pytest-rerunfailures`** on UI/API configs (not on stability — flakiness stays visible) |
| Scale | **`pytest-xdist`** for parallel workers where configured |
| Reporting | **`pytest-html`** self-contained HTML + timestamped names via `conftest.py` |
| Ops | Batch/shell helpers, optional `python -m utilities.run_tests` launcher (`ui`, `api`, `stability` only) |

### Tech stack

- **Python** (3.10+ recommended), **pytest**, **Selenium**, **requests**
- **pytest-xdist**, **pytest-html**, **pytest-rerunfailures**
- **webdriver-manager**, **configparser**

### Supported test types

| Type | Scope | Typical use |
|------|--------|-------------|
| **UI** | `tests/ui/` | Login, registration, notes CRUD in the browser |
| **API** | `tests/api/` | Auth, users, notes REST contracts |
| **Stability** | Entire `tests/` tree (combined UI + API collection) | Single pass with parallelism, **no** reruns — reliability signal |

Official execution profiles use **`pytest_ui.ini`**, **`pytest_api.ini`**, and **`pytest_stability.ini`** only.

---

## 2. ✨ Framework features

- **Pytest-first layout** — discovery under `tests/`, shared hooks in root `conftest.py`.
- **Parallel execution** — `pytest-xdist` (`-n 4`, `-n 8`, or `-n auto` depending on config/script).
- **Stability-oriented runs** — `pytest_stability.ini` runs the combined collection with **`-n 4`** and **omits `--reruns`** so intermittent failures are not masked.
- **HTML reporting** — timestamped files such as `reports/ui_report_YYYY-MM-DD_HH-MM-SS.html` (prefix matches the active profile: `ui`, `api`, or `stability`).
- **Logging** — pytest file + CLI logs under `reports/`; application-style logs from `utilities/logger.py` → `logs/test_YYYY-MM-DD.log`.
- **Config-driven execution** — URLs, timeouts, browser, headless, and credentials in `config/config.ini`; browser override via **`--browser`**.
- **Scalable structure** — `pages/`, `tests/`, `utilities/`, `testdata/` separation.
- **Page Object Model** — `BasePage` + feature pages (`login`, `register`, `notes`).
- **API utilities** — `APIClient`, `auth_token` fixture (API login using config credentials).
- **Retry mechanism** — UI/API default: `--reruns 1 --reruns-delay 2` (see each `.ini`).
- **CI/CD readiness** — headless flag, non-interactive pytest exit codes, portable HTML artifacts.

---

## 3. 🗂️ Project structure

> **Repository layout** (source and automation assets; generated folders like `logs/` and `reports/` are created at runtime and may be gitignored).

```
Pytest-automation/
├── config/
│   └── config.ini                 # Environment URLs, timeouts, browser, credentials
├── pages/                         # Page Object Model (UI)
│   ├── base_page.py
│   ├── login_page.py
│   ├── register_page.py
│   └── notes_page.py
├── tests/
│   ├── api/                       # API test modules
│   │   ├── test_auth_api.py
│   │   ├── test_notes_api.py
│   │   └── test_user_api.py
│   └── ui/                        # UI test modules + UI-only fixtures
│       ├── conftest.py            # e.g. session cleanup for shared UI account
│       ├── test_login.py
│       ├── test_register.py
│       └── test_notes.py
├── testdata/                      # JSON fixtures (optional; see utilities/data_loader.py)
│   ├── api_test_data.json
│   └── ui_test_data.json
├── utilities/
│   ├── api_client.py              # HTTP helper used by API tests
│   ├── config_reader.py           # Thin wrapper over config.ini
│   ├── data_loader.py             # Load JSON from testdata/
│   ├── logger.py                  # Shared logger → console + logs/test_<date>.log
│   ├── run_tests.py               # Runnable as: python -m utilities.run_tests
│   ├── generate_stability_report.py
│   └── …                          # debug/inspect helpers for local troubleshooting
├── logs/                          # (generated) dated logs, batch run logs
├── reports/                       # (generated) HTML + text logs; subfolders for batch runs
│   ├── api/                       # e.g. 10× stability HTML from run_10_times_api-ui.bat
│   ├── ui/
│   └── screenshots/             # Failure screenshots from driver fixture
├── conftest.py                    # Global fixtures, timestamped report/log injection
├── pytest.ini                     # Default pytest options when no -c is passed
├── pytest_ui.ini
├── pytest_api.ini
├── pytest_stability.ini
├── requirements.txt
├── run_tests.bat / run_tests.sh
├── run_10_times_api-ui.bat
├── run_all_10_times.bat / run_all_10_times.sh
├── run_stability_10x.bat
└── README.md
```

### Folder guide for new engineers

| Location | Purpose | What belongs here | How to use it |
|----------|---------|-------------------|---------------|
| **`config/`** | Single source for non-secret *defaults* and environment-specific values | `config.ini` | Edit URLs, timeouts, `headless`, and **your** test account fields (see [Configure Your Test Credentials](#8-configure-your-test-credentials)). Prefer a **local** copy or secret store for real credentials in forked repos. |
| **`pages/`** | UI abstraction (locators + actions) | One page class per major screen | Add/modify locators and navigation here — **not** scattered inside tests. |
| **`tests/ui/`** | Browser tests | `test_*.py`, optional `conftest.py` for UI-only hooks | New UI scenarios: new `test_<feature>.py`, reuse `driver` + page objects. |
| **`tests/api/`** | HTTP tests | `test_*_api.py` | New endpoints: extend or add modules; use `api_client` / `auth_token`. |
| **`testdata/`** | Externalized JSON payloads/strings | `*.json` | Load via `utilities.data_loader.load_test_data(...)` to avoid huge literals in tests. |
| **`utilities/`** | Shared code, runners, diagnostics | Clients, logging, runners | Import from tests/pages; do not duplicate HTTP or config logic in tests. |
| **`reports/`** | Outputs from pytest-html and batch scripts | `*_report_*.html`, `*_log_*.txt`, summaries | Open HTML in a browser; attach to tickets. **Do not** rely on paths in CI without uploading artifacts. |
| **`logs/`** | Logger output + redirected batch logs | `test_<date>.log`, `*_run_*.log` | Tail during debugging; rotate or clean locally as needed. |

---

## 4. ✅ Prerequisites

| Requirement | Notes |
|-------------|--------|
| **Python** | **3.10 or newer** recommended (matches modern Selenium/pytest stacks). Verify with `python --version`. |
| **pip** | Bundled with Python; always invoke upgrades via `python -m pip` (see below). |
| **Virtual environment** | **Strongly recommended** — isolates dependencies per project. |
| **Browsers** | **Google Chrome** and/or **Mozilla Firefox** installed (UI tests). **Microsoft Edge** is not wired in `conftest.py` today — use `chrome` or `firefox`. |
| **Drivers** | **Not manual** — `webdriver-manager` downloads matching ChromeDriver/GeckoDriver. |
| **Network** | Outbound HTTPS to `practice.expandtesting.com` and driver CDN endpoints. |
| **Git** | For clone/pull workflows. |

---

## 5. 📥 Clone repository

From your terminal (PowerShell, CMD, or bash):

```bash
git clone <YOUR_REPOSITORY_URL>
cd Pytest-automation
```

Replace `<YOUR_REPOSITORY_URL>` with the HTTPS or SSH URL of this repository.

---

## 6. 🐍 Create virtual environment

### Windows (project root)

```bash
python -m venv venv
```

### Activate the virtual environment

| Shell | Command |
|-------|---------|
| **Windows CMD** | `venv\Scripts\activate.bat` |
| **Windows PowerShell** | `venv\Scripts\Activate.ps1` |
| **macOS / Linux (bash/zsh)** | `source venv/bin/activate` |

You should see `(venv)` in your prompt. **Run all install and test commands only after activation** (unless you intentionally use a global interpreter).

---

## 7. 📦 Install dependencies

Upgrade **pip** using the interpreter you intend to run tests with:

```bash
python -m pip install --upgrade pip
```

Install project packages:

```bash
python -m pip install -r requirements.txt
```

### Why `python -m pip` and `python -m pytest`?

Using **`python -m <module>`** guarantees that **the same Python executable** that is active in your shell (for example, the one inside `venv`) runs **pip** or **pytest**. That avoids the common failure mode where `pip`/`pytest` on `PATH` points to a different installation than `python`, which causes missing packages or wrong versions.

---

## 8. Configure Your Test Credentials

**Before running any tests**, you **must** edit **`config/config.ini`** and set **your own** valid practice-account **email** (`username`) and **password** values. The framework **does not work** without credentials that match a real registered user on the Notes app.

### Why this file matters

The same settings drive:

- **UI login tests** — browser flows sign in with `[api]` user fields read by page objects and fixtures.
- **API login and authentication** — HTTP tests obtain tokens using the configured account.
- **`auth_token` fixture** — logs in via the API using `[api]` `username` / `password`.
- **Notes-related API-backed flows** — authenticated requests expect a valid token tied to your account.
- **Stability runs** — combined UI + API collection still depends on this account for every path that authenticates.

### Example (`[api]` section)

Replace the placeholders with **your** registered test email and passwords (keep `wrong_password` as an intentionally invalid value for negative tests if your suite expects it):

```ini
[api]
username = your_email@example.com
password = YourPassword123
wrong_password = WrongPassword123
default_password = YourPassword123
```

> **Security**  
> Treat `config/config.ini` as **sensitive** in real projects. Use dedicated test accounts, rotate passwords after sharing, and avoid committing production secrets. For enterprise setups, consider environment variables or a secret manager and thin `config_reader` extensions.

---

## 9. ⚙️ Environment configuration

### Pytest INI files

| File | Role |
|------|------|
| **`pytest.ini`** | Default project pytest settings (`testpaths = tests`, optional parallelism/reruns when no `-c` is passed). |
| **`pytest_ui.ini`** | UI only (`tests/ui`), reruns enabled, **no** default `-n` in file — parallelism is optional on CLI. |
| **`pytest_api.ini`** | API only (`tests/api`), reruns enabled. |
| **`pytest_stability.ini`** | Entire `tests/` tree, **`-n 4`**, **no reruns** — exposes flakiness. |

### `config/config.ini` (beyond credentials)

Controls:

- **`[browser]`** — `browser` (`chrome` / `firefox`), `headless` (`true` / `false`).
- **`[urls]`** — `base_url`, `api_base_url`, deep links for login/register.
- **`[timeouts]`** — `implicit_wait`, `explicit_wait`, `page_load_timeout` (seconds).
- **`[api]`** — `content_type`, **credentials** (see [section 8](#8-configure-your-test-credentials)), plus fields used by negative paths (`wrong_password`, `already_registered_email`, etc.).

### Environment variables

The framework’s **primary** configuration path is **`config.ini`**. You can still set generic environment variables for CI (for example `CI=true`) and extend `config_reader` if your team standardizes on env-based secrets.

### Test data

- **`testdata/*.json`** — optional structured data.
- **`utilities/data_loader.py`** — `load_test_data("ui_test_data.json")` pattern.

### UI-only session hook

`tests/ui/conftest.py` may perform **one-time cleanup** (for example clearing notes for the shared UI account). Keep shared-account side effects documented when adding new UI tests.

---

## 10. ▶️ Running tests

> **Convention**  
> Always invoke pytest as **`python -m pytest`**. Examples below include **`-c <ini>`** for the correct profile and **`--no-header -q`** for a compact console; add **`-v`** when you need per-test names.

### UI test execution

```bash
python -m pytest -c pytest_ui.ini --no-header -q -n 4
```

| Topic | Explanation |
|-------|-------------|
| **What runs** | All tests under **`tests/ui/`** (login, register, notes). |
| **Why `-n 4`** | Four **pytest-xdist** workers balance **speed vs. machine load** and **browser stability** on ad-heavy or dynamic sites; the batch script `run_10_times_api-ui.bat` uses the same idea for UI. |
| **Reports** | `conftest.py` injects **`reports/ui_report_<timestamp>.html`** and **`reports/ui_log_<timestamp>.txt`** unless you pass an explicit `--html=...`. |
| **Flow** | Workers collect tests → each UI test gets a **fresh `driver`** (function-scoped fixture) → teardown quits the browser; failures capture **`reports/screenshots/<test_name>.png`**. |
| **Reruns** | From `pytest_ui.ini`: failing tests **retry once** after a short delay. |

**Cross-browser override (still `python -m`):**

```bash
python -m pytest -c pytest_ui.ini --no-header -q -n 4 --browser=firefox
```

### API test execution

```bash
python -m pytest -c pytest_api.ini --no-header -q
```

| Topic | Explanation |
|-------|-------------|
| **What runs** | All tests under **`tests/api/`**. |
| **Parallelism** | The shown command is **sequential** (no `-n`). That is often easier for **shared practice APIs** (rate limits, account state). You *may* add **`-n auto`** or **`-n 4`** if your team accepts the ordering/state risk. |
| **Reports** | **`reports/api_report_<timestamp>.html`** + **`reports/api_log_<timestamp>.txt`**. |
| **Auth** | Tests use **`api_client`** and **`auth_token`** (fixture logs in via API using `[api]` credentials in `config.ini`). |

### Stability test execution

```bash
python -m pytest -c pytest_stability.ini --no-header -q
```

| Topic | Explanation |
|-------|-------------|
| **Scope** | Combined **UI + API** tests collected from the full **`tests/`** tree. |
| **Why it exists** | Longer combined run to validate **stability** under **parallel load** without hiding flakes behind reruns. |
| **Configuration** | **`pytest_stability.ini`** sets **`addopts = -n 4`** and **does not** add `--reruns` — any failure is a true failure for that run. |
| **Reports** | **`reports/stability_report_<timestamp>.html`** and **`reports/stability_log_<timestamp>.txt`**. |

### Optional launcher (timestamped HTML path on CLI)

```bash
python -m utilities.run_tests ui
python -m utilities.run_tests api
python -m utilities.run_tests stability
```

This wraps **`python -m pytest`** with an explicit **`--html=reports/<prefix>_<timestamp>.html`**. Use **`ui`**, **`api`**, or **`stability`** only.

### Windows / Unix helper scripts

| Script | Role |
|--------|------|
| `run_tests.bat` / `run_tests.sh` | Example `python -m pytest -c …` sequences (align these scripts with the three supported `.ini` files above). |
| `run_10_times_api-ui.bat` | **10×** API then **10×** UI with per-run HTML under `reports/api/` and `reports/ui/` + summaries. |
| `run_stability_10x.bat` / `run_all_10_times.*` | Extended stability / multi-run workflows (typically **`pytest_stability.ini`** / `utilities.run_tests stability`). |

---

## 11. ⚡ Parallel execution

- **`pytest-xdist`** is activated with **`-n <N>`** or **`-n auto`**.
- **Benefits**: shorter wall-clock time, better CPU use for I/O-bound API tests.
- **Risks**: shared **mutable** backend state, **UI** contention, and **non-deterministic** ordering — increase workers only after observing stable passes.
- **Guidance**: **`pytest_stability.ini`** uses **`-n 4`** as a compromise for the combined collection; **API-only** sequential runs are the safest default for beginners; add **`-n`** on UI only when your machine and the target app tolerate the load.

---

## 12. 📊 Reports & logs

| Artifact | Location | Description |
|----------|----------|-------------|
| **HTML report** | `reports/<suite>_report_<YYYY-MM-DD_HH-MM-SS>.html` | Self-contained **pytest-html** report (embedded assets). |
| **Pytest text log** | `reports/<suite>_log_<YYYY-MM-DD_HH-MM-SS>.txt` | DEBUG-level file log path injected in **`pytest_configure`**. |
| **Framework log** | `logs/test_<YYYY-MM-DD>.log` | From **`utilities.logger`** (shared logger used in fixtures/helpers). |
| **Failure screenshots** | `reports/screenshots/<test_function_name>.png` | Captured on **call** phase failure in `driver` fixture. |
| **Batch / stability outputs** | `reports/api/`, `reports/ui/`, `reports/final_stability_summary.txt`, etc. | Created by `.bat` / `.sh` wrappers for multi-run evidence. |

**Timestamp naming** is implemented in **`conftest.py`**: the prefix (`ui`, `api`, `stability`) is derived from the basename of the **`-c`** INI file so runs never overwrite each other by accident.

---

## 13. ➕ Adding new test cases

### UI tests

1. Add or extend a **page object** in `pages/` if new elements or flows are involved.  
2. Create **`tests/ui/test_<area>.py`**.  
3. Use the **`driver`** fixture and **explicit waits** via page objects (avoid raw `time.sleep` except rare cases).  
4. Name tests **`test_<behavior>_<condition>`** for readability.  
5. Apply **markers** when you need selective runs, for example `@pytest.mark.smoke`.

### API tests

1. Prefer **`api_client`** for verbs and headers.  
2. Use **`auth_token`** when the endpoint requires login.  
3. Place files under **`tests/api/`** with naming **`test_<domain>_api.py`**.  
4. Keep payloads **small**; move large bodies to **`testdata/`** + `load_test_data`.

### Practices

- One **assertable** outcome per test where possible.  
- **No hardcoded credentials** in Python — read from `config.ini` or data files.  
- Keep tests **independent**; use fixtures for setup instead of relying on run order.

---

## 14. 🧭 Common commands

| Goal | Command |
|------|---------|
| Upgrade pip | `python -m pip install --upgrade pip` |
| Install deps | `python -m pip install -r requirements.txt` |
| UI (parallel 4) | `python -m pytest -c pytest_ui.ini --no-header -q -n 4` |
| API (quiet) | `python -m pytest -c pytest_api.ini --no-header -q` |
| Stability (`-n 4` from INI) | `python -m pytest -c pytest_stability.ini --no-header -q` |
| List tests only | `python -m pytest -c pytest_stability.ini --collect-only -q` |
| Firefox UI | `python -m pytest -c pytest_ui.ini -n 4 --browser=firefox` |
| Launcher (UI) | `python -m utilities.run_tests ui` |
| Single file | `python -m pytest -c pytest_api.ini tests/api/test_auth_api.py --no-header -q` |
| Marker example | `python -m pytest -c pytest_ui.ini -m smoke --no-header -q` |

---

## 15. 🔧 Troubleshooting guide

| Symptom | Likely cause | What to try |
|---------|----------------|-------------|
| **`ModuleNotFoundError`** | Wrong interpreter or venv not activated | Activate `venv`; confirm `where python` (Windows) / `which python` (Unix); reinstall with `python -m pip install -r requirements.txt`. |
| **`pytest: command not found`** | Script dir not on PATH | Use **`python -m pytest`** instead of bare `pytest`. |
| **Worker crashes / `BrokenProcessPool`** | Too many browsers or resource exhaustion | Reduce **`-n`** for UI (try **2** or **1**). |
| **Browser fails to start** | Missing browser, blocked download, or headless flags | Install Chrome/Firefox; set `headless = true` for CI; corporate proxy may block driver download — allow `webdriver-manager` endpoints. |
| **`ValueError: Unsupported browser`** | Typo in `config.ini` or `--browser` | Use **`chrome`** or **`firefox`** only (see `conftest.py`). |
| **Dependency conflicts** | Mixed pip/global installs | New venv + `python -m pip install --upgrade pip` + reinstall requirements. |
| **Wrong Python version** | Old system Python | Install Python **3.10+** and recreate `venv`. |
| **Parallel API failures** | Shared account race | Run API **without** `-n` or lower workers; review tests that mutate the same user. |
| **Stale elements / timeouts** | UI timing | Adjust `[timeouts]` in `config.ini`; improve waits in page objects. |
| **401 / login failures everywhere** | Missing or wrong `config/config.ini` credentials | Complete [section 8](#8-configure-your-test-credentials) with a valid registered account. |

---

## 16. 💡 Best practices

- **Always use a virtual environment** per project clone.  
- **Always prefer `python -m pip` and `python -m pytest`** for consistent environments.  
- **Centralize locators** in `pages/`; tests should read like scenarios, not CSS/XPath lists.  
- **Prefer explicit waits** (WebDriverWait) over fixed sleeps.  
- **Reuse fixtures** (`driver`, `api_client`, `auth_token`, `config`) instead of duplicating setup.  
- **Keep tests independent** — no order dependency between modules.  
- **Treat stability runs seriously** — fix flakes rather than relying only on reruns.  
- **Attach HTML + screenshots** to defect reports for faster triage.

---

## 17. 🚀 CI/CD readiness

- **Non-interactive**: pytest exits with **non-zero** on failures — suitable for **Jenkins**, **GitHub Actions**, **Azure DevOps**, etc.  
- **Headless**: set **`headless = true`** under `[browser]` in `config/config.ini` for agents without a display.  
- **Artifacts**: publish **`reports/*.html`**, **`reports/*.txt`**, and **`reports/screenshots/`** as build artifacts.  
- **Workers**: start with **`-n 2` or `-n 4`** for UI on shared agents; use **API sequential** or low `-n` until stable.

---

## 18. 🔮 Future enhancements

- Pipeline matrix for **Chrome + Firefox** nightly.  
- Secret injection via **environment variables** or vault integration.  
- Visual regression or **Playwright** evaluation for faster UI checks.  
- Test **tagging strategy** linked to Jira/Xray or similar.  
- Docker image with browsers preinstalled for reproducible CI.

---

## 19. 👥 Contributors & ownership

Document your team’s ownership here (for example squad name, Slack channel, and escalation path). For external contributions, add **`CONTRIBUTING.md`** with branch naming, PR checklist, and review rules when your organization requires it.

---

**Happy testing** — configure **`config/config.ini`**, then start with **`python -m pytest -c pytest_api.ini --no-header -q`** for a quick API smoke, then **`python -m pytest -c pytest_ui.ini --no-header -q -n 4`** once Chrome/Firefox is installed.
