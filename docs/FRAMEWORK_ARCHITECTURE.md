# Framework Architecture — Engineering Reference

**Audience:** Senior QA automation engineers, SDETs, maintainers, reviewers.  
**Companion docs:** **[PROJECT_DETAILED_EXPLANATION.md](PROJECT_DETAILED_EXPLANATION.md)** (beginner / file-by-file depth), **[README.md](README.md)** (setup & commands), **[notes_handbook.md](notes_handbook.md)** (Notes UI maintainer playbook).

---

## 1. Executive summary

| Layer | Implementation | Pattern |
|-------|----------------|---------|
| Runner | **pytest** + multiple **`pytest_*.ini`** profiles | `testpaths`, `addopts`, markers |
| UI | **Selenium 4**, **webdriver-manager**, **POM** (`pages/`) | Function-scoped `driver`; explicit waits in `BasePage` |
| API | **`requests`** via **`APIClient`** + **`_ResponseProxy`** | Session + JSON normalization for nested `"data"` |
| Config | **`config/config.ini`** + **`read_config()`** | URLs, timeouts, browser, credentials |
| Parallelism | **pytest-xdist** | Profile-specific: `-n auto` (default / all), `-n 4` (stability ini + many UI batches), optional CLI `-n` on UI/API |
| Resilience | **pytest-rerunfailures** | UI/API profiles: `--reruns 1 --reruns-delay 2`; **stability profile omits reruns** |
| Reporting | **pytest-html** + **`pytest_configure`** hook | Timestamped `reports/<prefix>_report_<ts>.html` unless `--html` overridden |
| Logging | **stdlib `logging`** via **`get_logger()`** | Console + daily `logs/test_<date>.log`; pytest file log under `reports/` |

**Product under test:** Expand Testing **Notes** practice app (`practice.expandtesting.com`) — shared UI + REST API.

**Suite size (current):** **75** collected tests (**25** UI, **50** API) when `testpaths = tests`.

---

## 2. System architecture

### 2.1 Logical diagram

```
                         ┌──────────────────┐
                         │  python -m pytest │
                         │  -c pytest_*.ini  │
                         └─────────┬────────┘
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         ▼                         ▼                         ▼
 ┌───────────────┐        ┌─────────────────┐       ┌──────────────┐
 │ pytest hooks   │        │ xdist workers   │       │ plugins:     │
 │ pytest_configure│       │ (optional)      │       │ html, reruns │
 │ makereport     │        └────────┬────────┘       └──────────────┘
 └───────┬───────┘                 │
         │                         ▼
         │               ┌─────────────────────┐
         │               │ conftest.py         │
         │               │ fixtures + hooks    │
         │               └─────────┬───────────┘
         │                         │
         ▼                         ▼
 ┌───────────────┐        ┌─────────────────────┐
 │ reports/*.html│        │ driver / api_client │
 │ reports/*_log │        │ auth_token / config │
 └───────────────┘        └─────────┬───────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
            ┌───────────────┐               ┌───────────────┐
            │ WebDriver      │               │ APIClient     │
            │ Chrome/Firefox │               │ Session+proxy │
            └───────┬───────┘               └───────┬───────┘
                    │                               │
                    ▼                               ▼
            ┌───────────────┐               ┌───────────────┐
            │ pages/*.py     │               │ tests/api     │
            │ (POM)          │               │ HTTPS API     │
            └───────────────┘               └───────────────┘
```

### 2.2 Module dependency graph

```
tests/ui/*.py ──► pages/*_page.py ──► pages/base_page.py ──► utilities/{config_reader,logger}
                         │
                         └──► utilities/config_reader (URLs at class import)

tests/api/*.py ──► utilities/api_client.py ──► utilities/{config_reader,logger}

conftest.py ──► selenium + webdriver_manager + utilities/{config_reader,logger,api_client}

pages/notes_page.py ──► requests (inline) for API-first note CRUD; optional pages/login_page (re-login)
```

**Important coupling:** `NotesPage` uses **`requests`** directly for API-backed create/edit/delete and token refresh, while API tests use **`APIClient`** (same backend, different code path — intentional for UI stability).

### 2.3 Repository layout (concise)

| Path | Role |
|------|------|
| `tests/ui`, `tests/api` | Pytest collections (see `pytest_*.ini` `testpaths`) |
| `pages/` | Page Object Model |
| `utilities/` | `APIClient`, config/logging helpers, runners, diagnostics |
| `config/` | `config.ini` — environment + credentials |
| `testdata/` | Optional JSON for `data_loader` |
| `reports/`, `logs/` | Generated HTML, pytest logs, screenshots (may be gitignored) |

---

## 3. Execution profiles (`pytest_*.ini`)

| Profile | `testpaths` | Default `addopts` (high level) | HTML / log prefix (`pytest_configure`) |
|---------|-------------|--------------------------------|--------------------------------------------|
| **`pytest.ini`** | `tests` | `-n auto --reruns 1 --reruns-delay 2` | **`ini`** (hook strips `pytest_` + `.ini` from basename `pytest.ini` → prefix `ini`, e.g. `ini_report_<ts>.html`) |
| **`pytest_ui.ini`** | `tests/ui` | reruns only (no `-n` in file) | `ui` |
| **`pytest_api.ini`** | `tests/api` | reruns only | `api` |
| **`pytest_all.ini`** | `tests` | `-n auto` + reruns | `all` |
| **`pytest_stability.ini`** | `tests` | **`-n 4` only** (no reruns) | `stability` |

**Timestamped artifacts:** Root `conftest.py` → `pytest_configure` sets `config.option.htmlpath` and `config.inicfg["log_file"]` when pytest-html is present and CLI did not already pass `--html`. **`utilities/run_tests.py`** passes explicit `--html=reports/<prefix>_<ts>.html` and invokes `python -m pytest`; batch scripts use either raw pytest or `utilities/run_tests.py`.

---

## 4. Runtime execution flow

### 4.1 Pytest bootstrap

1. **Interpreter** loads plugins (`xdist`, `html`, `rerunfailures`, …).
2. **`pytest_configure(config)`** runs: derive **`prefix`** from `config.inifile.basename`, build timestamped **`reports/{prefix}_report_{ts}.html`** and **`reports/{prefix}_log_{ts}.txt`**.
3. **Collection** over `testpaths`; markers registered in INI (`smoke`, `regression`, `ui`, `api`, …) — **tests use these markers** for filtering.
4. **Session start:** `log_browser_choice` (session, autouse) logs resolved browser.
5. **Per test node** (order depends on xdist scheduling when enabled):
   - `pytest_runtest_makereport` (hookwrapper, tryfirst) stores `rep_setup` / `rep_call` / `rep_teardown` on `item`.
   - Autouse `setup_teardown` → SETUP log.
   - Fixtures: `driver` and/or `api_client` / `auth_token` per signature.
   - Test body.
   - `driver` teardown: if `rep_call.failed` → screenshot `reports/screenshots/<node.name>.png`; always `quit()`.
   - `setup_teardown` → TEARDOWN log.

### 4.2 Fixture scopes (actual code)

| Fixture | Scope | Depends on | Role |
|---------|-------|------------|------|
| `log_browser_choice` | session, autouse | — | Log CLI/config browser |
| `config` | session | — | `ConfigParser` for whole `config.ini` |
| `setup_teardown` | function, autouse | — | SETUP/TEARDOWN logs |
| `driver` | function | request | Browser lifecycle |
| `api_client` | function | — | New `APIClient()` per test |
| `auth_token` | function | `api_client` | **Fresh login per test** via `api_client.post("users/login", …)` — reduces token expiry / cross-test coupling under xdist |

**Ordering note:** `driver` teardown consults `request.node.rep_call` **after** the **call** phase report exists — ensured by `pytest_runtest_makereport` being **tryfirst** hookwrapper.

### 4.3 WebDriver lifecycle

- **Creation:** `conftest.driver` reads `browser`, `headless`, timeouts; sets **`page_load_strategy = "eager"`**; applies `implicitly_wait` + `set_page_load_timeout`.
- **Navigation:** **No** automatic `get(base_url)` — each **`Page.open()`** drives URL transitions.
- **Teardown:** Always `quit()`; screenshot only on **call** failure.

### 4.4 Parallel model (xdist)

- **Worker processes:** Each worker has **isolated** Python state → **separate** fixture instances.
- **UI:** One browser **per test** remains true **per worker**; many workers ⇒ many concurrent browsers (resource contention on host and on target SaaS).
- **API:** Parallel safe for *read-mostly* tests; **order-dependent** or **shared-account mutation** tests remain risky at high `-n`.
- **Stability:** `pytest_stability.ini` fixes **`-n 4`** to balance throughput vs. UI flakiness; **no reruns** so intermittent defects surface as hard failures.

---

## 5. Selenium / POM architecture

### 5.1 `BasePage`

- Centralizes **`WebDriverWait` + `EC.visibility_of_element_located`** (`explicit_wait` from config).
- **`_dismiss_overlays()`**: JS to hide/remove ad/cookie layers + short sleep — **critical** for practice sites with iframe/overlays.
- **`click` / `type_text` / `get_text`**: wait-then-act; **`find_element`** alone does **not** wait (callers must know this).

### 5.2 `LoginPage` / `RegisterPage`

- **`open()`**: `driver.get(URL)` with tolerant handling where `get()` raises but URL is already usable.
- **Submit actions:** prefer **JS click** after scroll + overlay dismissal to avoid **click interception**.
- **`LoginPage.click_login()`**: overlay dismiss → JS click → wait URL leave `/login` (up to ~30s + one retry path).

### 5.3 `NotesPage` (hybrid UI + direct HTTP)

**Strategic intent:** The Notes UI is a **React SPA** on an **ad-heavy** host. The framework uses:

1. **`_wait_for_react_ready()`** — waits for shell mount (Add Note / nav / links) and optional note list hydration.
2. **`save_note()`** — **default path:** API create via **`create_note_via_api()`** then sync UI (`location.assign` vs `refresh` to reduce token loss); **exception:** **empty title** validation uses **UI modal submit** so React client-side rules fire.
3. **Read/assert helpers** — **`is_note_visible` / `_wait_for_title_in_dom`** with **GET /notes** fallback when DOM pagination/caps hide titles but API proves existence.
4. **Mutations** — **`edit_note_via_api`**, **`_delete_note_via_api`**, **`delete_note`** (API-first when title known), **`click_edit_note_by_title`** (UI + deep-link fallback).

**Locator strategy:** mix of **ID**, **`data-testid`**, CSS, XPath text — centralized as class attributes on `NotesPage`.

**For exhaustive method-by-method and flake RCA:** see **`notes_handbook.md`** and **`PROJECT_DETAILED_EXPLANATION.md`** (Notes section).

---

## 6. API architecture

### 6.1 `APIClient`

- **`requests.Session`** with default `Content-Type` from config.
- **URL join:** `{api_base_url}/{endpoint.lstrip('/')}`.
- **Logging:** request line + response status + body (verbose — fine for practice env; noisy in prod-like logging).

### 6.2 `_ResponseProxy` (response normalization)

- Real API envelope: `{ success, status, message, data: {...}|[...] }`.
- **`json()` override:** if `data` is **list** → return list; if **dict** → **shallow merge** `body` + inner keys (without overwriting top-level keys) so tests can keep using `resp.json()["token"]` style assertions.

### 6.3 `_normalize_note_payload`

- For `notes` endpoints, pads very short `title` / `description` strings to satisfy server min length when tests use tiny placeholders **without** intending to hit validation errors.

### 6.4 `auth_token` fixture vs `NotesPage` token

- **`auth_token`:** uses **`APIClient.post`** → normalized JSON — good for **test** code consistency.
- **`NotesPage._last_token`:** obtained via raw **`requests.post`** in page helpers — must parse both `{data:{token}}` and top-level token patterns. **Two token sources** — maintainers must keep parsing logic aligned when API shape changes.

---

## 7. Stability & batch execution

| Asset | Role |
|-------|------|
| **`run_10_times_api-ui.bat`** | 10× API (often `-n 8`) + 10× UI (`-n 4`), per-run HTML under `reports/api/`, `reports/ui/`, logs under `logs/`, summaries |
| **`run_stability_10x.bat`** | Full stability strategy: UI/API per iteration with override-ini / timing |
| **`run_all_10_times.bat` / `.sh`** | Loops **`python utilities/run_tests.py stability --path …`** (no reruns in underlying `pytest_stability.ini`), then **`generate_stability_report.py`** |
| **`utilities/generate_stability_report.py`** | Parses `Run N: …` lines → markdown summary table |

---

## 8. Logging & reporting

| Stream | Mechanism | Location |
|--------|-----------|----------|
| Framework log | `get_logger()` handlers | `logs/test_<YYYY-MM-DD>.log` + console |
| Pytest file log | `log_file` from `pytest_configure` | `reports/<prefix>_log_<ts>.txt` |
| Pytest CLI | `log_cli*` in INI | Terminal |
| HTML | pytest-html `self_contained_html` | `reports/<prefix>_report_<ts>.html` |
| Screenshots | `driver` fixture on failure | `reports/screenshots/<test_name>.png` |

---

## 9. Design patterns & principles

| Pattern | Where |
|---------|-------|
| **Page Object** | `pages/*` |
| **Fixture-based DI** | `driver`, `api_client`, `auth_token`, `config` |
| **Hybrid UI/API** | `NotesPage` — API for reliability, UI for user-visible assertions |
| **Defensive waits** | React mount gates, implicit-wait toggling inside hot polling paths in `NotesPage` |
| **Proxy** | `_ResponseProxy` for backward-compatible assertions |

---

## 10. Scalability, risks, and improvement backlog

### Strengths

- Clear separation POM / API client / config.
- Markers enable selective runs (`-m smoke`, etc.).
- Timestamped reports reduce overwrites.
- Function-scoped `auth_token` + API-backed note creation improve **parallel** stability vs. older session-token approaches.

### Risks

| Risk | Impact |
|------|--------|
| **Secrets in `config.ini`** | Leakage in VCS; prefer env/secret store for enterprise |
| **`read_config` uncached** | Extra I/O; acceptable at current scale |
| **Dual HTTP stacks** (`APIClient` vs raw `requests` in `NotesPage`) | Drift in URL building / auth parsing |
| **Heavy parallelism on UI** | Local resource exhaustion; SaaS rate limiting |
| **Reruns on UI/API profiles** | Can mask flakes — use **`pytest_stability.ini`** for honest signal |

### Improvement directions

1. Single HTTP abstraction shared by `NotesPage` and tests (thin service layer).
2. Cached config object per session.
3. Environment overlays (`config.local.ini`, gitignored).
4. Optional Remote WebDriver / Grid URL.
5. CI workflow YAML with artifact upload for `reports/` + screenshots.

---

## 11. Document map

| Question | Read |
|----------|------|
| How do I install and run commands? | **README.md** |
| How does each file work (beginner + deep)? | **PROJECT_DETAILED_EXPLANATION.md** |
| Per-test inventory & every `test_*` behavior | **TEST_CASE_DETAILED_EXPLANATION.md** |
| Notes page flake RCA / maintainer | **notes_handbook.md** |
| High-level engineering view (this file) | **FRAMEWORK_ARCHITECTURE.md** |

---

*Last synchronized with repository implementation: engineering pass (conftest, all `pages/`, `utilities/api_client.py`, `pytest_*.ini`, stability batch scripts).*
