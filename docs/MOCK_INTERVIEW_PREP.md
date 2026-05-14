# Senior QA / SDET Mock Interview Handbook — Notes Automation Framework

**Purpose:** Interview-ready explanations of **this repository’s** Pytest + Selenium + API automation stack — from elevator pitch to architecture defense, aligned with [FRAMEWORK_ARCHITECTURE.md](FRAMEWORK_ARCHITECTURE.md), [PROJECT_DETAILED_EXPLANATION.md](PROJECT_DETAILED_EXPLANATION.md), [TEST_CASE_DETAILED_EXPLANATION.md](TEST_CASE_DETAILED_EXPLANATION.md), and [TEST_PLAN.md](TEST_PLAN.md).

**Suite facts (current):** **75** automated tests — **25 UI**, **50 API** — against the Expand Testing **Notes** practice application (`practice.expandtesting.com`).

---

## 1. Introduction

### What this framework is

A **hybrid** test automation solution: **pytest** drives **Selenium 4** UI tests (Page Object Model) and **HTTP API** tests (`requests` via a small `APIClient`). Configuration is centralized in **`config/config.ini`**. Execution is **profile-based** (`pytest_ui.ini`, `pytest_api.ini`, `pytest_all.ini`, `pytest_stability.ini`) with **pytest-xdist** for parallelism, **pytest-rerunfailures** on UI/API profiles, **pytest-html** for reports, and hooks in **`conftest.py`** for timestamped artifacts and failure screenshots.

### Why it was built

To provide **reliable regression** on a **React SPA** that sits on an **ad-heavy** practice host — where **pure UI-only** note creation was flaky. The design deliberately uses **API-backed note creation** in `NotesPage.save_note()` (with a **UI-only exception** for empty-title validation) so assertions reflect **server truth** while still validating **what the user sees**.

### Technologies

| Layer | Stack |
|-------|--------|
| Runner | pytest, pytest-xdist, pytest-html, pytest-rerunfailures |
| UI | Selenium 4, webdriver-manager (Chrome/Firefox), POM |
| API | requests.Session, custom `_ResponseProxy` |
| Config | configparser, `read_config()` |
| Logging | stdlib `logging` → console + `logs/test_<date>.log` |

### Real project complexity

- **Dual HTTP paths:** `APIClient` for tests vs **raw `requests`** inside `NotesPage` for UI stability — same backend, **intentional** tradeoff (document it in interviews).
- **React + eager loading:** `page_load_strategy = "eager"` + **`_wait_for_react_ready()`** before trusting DOM.
- **Parallelism:** xdist workers = **isolated processes**; **`auth_token`** is **function-scoped** (fresh login **per test**) to reduce token/expiry races.
- **Stability profile:** **`pytest_stability.ini`** uses **`-n 4`** and **omits reruns** so flakes are **not masked**.

---

## 2. Elevator pitch

### ~30 seconds

“I built a **pytest** framework with **75 tests** — **50 API** and **25 UI** — against Expand Testing’s **Notes** app. UI uses **Selenium Page Objects**; API uses a **session-based client** with **response normalization** for nested JSON. We run **parallel** (`pytest-xdist`), separate **HTML reports per profile**, **reruns** on day-to-day runs, but a **stability config without reruns** to measure real flakiness. **Notes** creation in UI is **API-backed** because the React app plus ads made pure UI saves unreliable.”

### ~1 minute

Add: **`conftest.py`** wires **`driver`** (function-scoped browser, **eager** page load, screenshots on failure), **`api_client`**, and **`auth_token`**. **`pytest_configure`** injects **timestamped** HTML and log paths. **`NotesPage`** waits for React mount, dismisses overlays, uses **JS clicks** where clicks are intercepted, and **`save_note()`** creates data via **REST** then syncs the browser. **`APIClient`** wraps responses so `resp.json()` matches how tests assert on **token** and **lists**. Stability runs use **`-n 4`**; batch scripts can run **10×** API/UI with different worker counts.

### ~3 minutes (deep)

Cover: **hookwrapper** `pytest_runtest_makereport` + **`rep_call`** for screenshot timing; **`_ResponseProxy`** merge rules; **`_normalize_note_payload`** for short note titles; **`tests/ui/conftest.py`** session cleanup of notes; **marker** strategy (`smoke`, `regression`, `ui`, `api`); **`run_10_times_api-ui.bat`** (e.g. API `-n 8`, UI `-n 4`); risks (**shared config user**, `test_delete_all_notes`); improvements (Grid, env-based secrets, single HTTP service layer).

### Senior SDET angle

Emphasize **tradeoffs**: reliability vs purity of “UI-only” tests; **observability** (logs + HTML + screenshots); **testability** of SPA (explicit hydration gates); **CI contract** (exit codes, headless, artifacts); **maintainability** (POM, markers, ini profiles); **known debt** (dual HTTP stacks, `read_config` re-reads file, secrets in ini).

---

## 3. Framework architecture interview questions

**How to use each block below:** every question includes **10 answer layers** so you can answer at the depth the interviewer probes.

---

### Q-A1. Why does `NotesPage.save_note()` use the API by default?

| Layer | Content |
|-------|---------|
| **1. Interview question** | Why not create notes only through the Selenium modal? |
| **2. Short answer** | The modal path was **flaky** (ads, overlays, React timing); **API create + UI sync** is reliable. |
| **3. Detailed answer** | `save_note()` clears pending fields then calls **`create_note_via_api()`**: `requests` login → `POST /notes` → **`window.location.assign`** to notes URL (avoids `refresh()` token loss where possible) → **`_wait_for_react_ready()`** → **`_wait_for_title_in_dom()`**. **Empty title** still uses **UI submit** so **client validation** is exercised. |
| **4. Beginner** | “The website was hard to click through every time, so we create the note on the server first, then show it in the browser.” |
| **5. Advanced** | Separates **data plane** (HTTP) from **view plane** (DOM). Reduces **non-deterministic** UI events; assertions can use **`is_note_visible`** with **GET /notes fallback** when DOM pagination hides titles. |
| **6. Real implementation** | `pages/notes_page.py` — `save_note`, `create_note_via_api`, `_note_title_exists_via_api`. |
| **7. Follow-ups** | “Does that still test the UI?” → Yes: modal typing, React gates, visibility. “How do you test negative title?” → UI branch in `save_note`. |
| **8. Best practices** | Use **fast reliable setup**, assert **user-visible outcomes**, document hybrid approach for auditors. |
| **9. Common mistakes** | Claiming “we don’t test the UI for notes” — false; claiming “100% UI-only” — also false. |
| **10. Production ideas** | Feature-flag **pure UI path** in lower envs; contract tests on API; visual snapshot for modal. |

---

### Q-A2. What does `_ResponseProxy` in `APIClient` do, and why?

| Layer | Content |
|-------|---------|
| **1. Interview question** | How do you handle APIs that wrap payloads in `{ "data": ... }`? |
| **2. Short answer** | A thin proxy makes **`resp.json()`** return **merged** or **unwrapped** shapes so tests stay readable. |
| **3. Detailed answer** | If body has **`data` as list**, `json()` returns the **list**. If **`data` is dict**, returns **shallow merge**: top-level keys preserved, inner keys promoted with **`setdefault`** so `token` can appear top-level without breaking envelope fields. |
| **4. Beginner** | “The server wraps answers in `data`; we flatten that for simple asserts.” |
| **5. Advanced** | Avoids rewriting **50 tests** when contract uses envelope; **`__getattr__`** delegates other `Response` attributes. Risk: tests may assume merged shape that diverges from raw wire format — document for contract testing maturity. |
| **6. Real implementation** | `utilities/api_client.py` — `_ResponseProxy`, `_wrap`. |
| **7. Follow-ups** | “Is this a good long-term pattern?” → Good for migration; eventually **Pydantic** / OpenAPI validators may replace ad hoc merges. |
| **8. Best practices** | Keep normalization **one place**; log raw body in **DEBUG** only in prod. |
| **9. Common mistakes** | Confusing **proxy `json()`** with **`response.text`** parsing; forgetting **`setdefault`** doesn’t overwrite existing top-level keys. |
| **10. Production ideas** | Explicit response models per endpoint; golden-file fixtures from Swagger. |

---

### Q-A3. Why is `auth_token` function-scoped, not session-scoped?

| Layer | Content |
|-------|---------|
| **1. Interview question** | How do you handle auth under **pytest-xdist**? |
| **2. Short answer** | **Fresh token per test** reduces **stale token** and **cross-test interference** when workers hit the same practice account. |
| **3. Detailed answer** | `auth_token` calls `api_client.post("users/login", …)` each test. With **xdist**, each worker is a **process** — session scope would still be **per worker**, but function scope avoids **logout** / **password change** in one test breaking the next test’s token on the **same worker**. |
| **4. Beginner** | “Every test that needs a token logs in again so tests don’t step on each other.” |
| **5. Advanced** | Tradeoff: **more logins** → rate limits / slower suite. Mitigation: isolated users (`_token_from_fresh_user` pattern in `test_notes_api.py`) for heavy suites; avoid **`test_delete_all_notes`** style wipes on shared users in parallel. |
| **6. Real implementation** | `conftest.py` — `@pytest.fixture(scope="function") def auth_token`. |
| **7. Follow-ups** | “Performance?” → Cache token with TTL in a **module-scoped** fixture only if API guarantees stability — risky here. |
| **8. Best practices** | Prefer **dedicated test users** in CI for parallel safety. |
| **9. Common mistakes** | Stating **`auth_token` is session-scoped** — **incorrect in this repo**. |
| **10. Production ideas** | OAuth2 client-credentials for test service account; vault-injected secrets. |

---

### Q-A4. Explain `pytest_runtest_makereport` + screenshot ordering.

| Layer | Content |
|-------|---------|
| **1. Interview question** | How can the `driver` fixture know if the test failed **before** quitting the browser? |
| **2. Short answer** | A **hookwrapper** runs early, attaches **`rep_call`** to the test item; teardown reads **`item.rep_call.failed`**. |
| **3. Detailed answer** | `@pytest.hookimpl(hookwrapper=True, tryfirst=True)` wraps `pytest_runtest_makereport`; after `yield`, sets `item.rep_{when}`. **`driver`** teardown checks **`rep_call`** after call phase — **ordering matters** (`tryfirst`). |
| **4. Beginner** | “Pytest tells the browser fixture whether the test passed or failed before closing the browser.” |
| **5. Advanced** | Alternative: **pytest_runtest_logreport** — less common for fixture-driven screenshots. |
| **6. Real implementation** | `conftest.py` — `pytest_runtest_makereport`, `driver` fixture teardown. |
| **7. Follow-ups** | “Setup failures?” → Could extend pattern to **`rep_setup`**. |
| **8. Best practices** | Keep screenshot path **deterministic** (`<test name>.png`); avoid overwriting in parallel (each worker separate). |
| **9. Common mistakes** | Checking failure **before** hook runs — race; omitting **`tryfirst`**. |
| **10. Production ideas** | Attach screenshot to **Allure** / XRay; S3 upload in CI. |

---

### Q-A5. Why does stability use `pytest_stability.ini` with `-n 4` and **no** reruns?

| Layer | Content |
|-------|---------|
| **1. Interview question** | Why disable reruns for stability? |
| **2. Short answer** | **Reruns hide intermittent failures**; stability runs should **surface** flake rate truthfully. |
| **3. Detailed answer** | UI/API profiles use **`--reruns 1`** for day-to-day noise reduction. **`pytest_stability.ini`** sets **`addopts = -n 4`** only — parallel like production-ish load but **no retry** so CI/stakeholders see **real** pass rate. |
| **4. Beginner** | “Stability mode doesn’t give tests a second chance, so we see how flaky they really are.” |
| **5. Advanced** | Pair with **10× batch scripts** and summaries (`generate_stability_report.py`, `run_10_times_api-ui.bat`). |
| **6. Real implementation** | `pytest_stability.ini`; `run_all_10_times.bat`, `run_stability_10x.bat`. |
| **7. Follow-ups** | “Why `-n 4` not `auto`?” → UI **browser count** vs machine stability; API batches may use **`-n 8`**. |
| **8. Best practices** | Track stability **trend over time**, not single green run. |
| **9. Common mistakes** | Using reruns in stability and claiming “100% stable.” |
| **10. Production ideas** | Flaky test quarantine; automatic bisect on main. |

---

## 4. Large question banks

### 4.1 Pytest — quick reference topics

| Topic | Talking points (this repo) |
|-------|------------------------------|
| **Fixtures / scopes** | `driver`, `api_client`, `auth_token` → **function**; `config`, `log_browser_choice` → **session**; `setup_teardown` → **function autouse**. |
| **Hooks** | `pytest_configure` (reports/logs), `pytest_html_report_title`, `pytest_addoption` (`--browser`), `pytest_runtest_makereport`. |
| **Collection** | Driven by **`testpaths`** in active `-c` ini; **75** tests under `tests/` for stability profile. |
| **Markers** | `@pytest.mark.smoke`, `regression`, `positive`, `negative`, `ui`, `api` — use `-m` for slices. |
| **Parametrization** | Not heavily used — mention as **future** for data-driven cases. |
| **xdist** | Worker **process isolation**; `-n auto` in `pytest_all.ini` / default `pytest.ini`; **`-n 4`** in stability ini; CLI `-n 4` on UI in README example. |
| **Reruns** | UI/API ini: `--reruns 1 --reruns-delay 2`; **stability: none**. |
| **Teardown** | Fixture `yield` order; `quit()` always; screenshot **before** quit on failure. |
| **Assertion rewriting** | pytest’s default clearer diffs on `assert`. |
| **Fixture DAG** | `auth_token` depends on `api_client`; pytest resolves dependency order. |
| **Autouse** | `setup_teardown`, `log_browser_choice`. |
| **Hookwrapper** | `pytest_runtest_makereport` yields to other hooks first. |
| **`pytest_configure`** | Sets `htmlpath`, `log_file` with timestamp; prefix from ini basename (`ui`, `api`, `stability`, `all`, `ini`). |

**Deep follow-up:** “What breaks if `read_config` is called at **import** in page classes?” → Changing `config.ini` at runtime **won’t** update `URL` class attributes until re-import — interview nuance.

---

### 4.2 Selenium — quick reference topics

| Topic | Talking points |
|-------|----------------|
| **WebDriver architecture** | Test code → WebDriver → **driver executable** → browser. |
| **Waits** | **Implicit** from `conftest`; **explicit** `WebDriverWait` in `BasePage` / `NotesPage`; custom predicates for React. |
| **Stale elements** | Handled in `NotesPage` polling (`StaleElementReferenceException` continue). |
| **Overlays** | `BasePage._dismiss_overlays()` JS hides ads/iframes. |
| **JS click** | `LoginPage.click_login`, `NotesPage` modal/submit paths — avoids **click interception**. |
| **Headless** | `[browser] headless` + Chrome `--headless=new` / Firefox `--headless`. |
| **Explicit vs implicit** | Implicit can **mask** slow predicates — `NotesPage` sometimes sets implicit **0** inside tight polls then **restores**. |
| **React sync** | `_wait_for_react_ready` — `any_of` mount signals + note list hydration. |
| **POM** | Locators + behavior in `pages/`; tests orchestrate. |
| **Flakiness** | Ads, SPA hydration, shared SaaS account — mitigated by API hybrid + waits + reruns (non-stability). |
| **Screenshots** | `reports/screenshots/<test_function>.png` on call failure. |
| **Driver lifecycle** | Per test **function** fixture; **eager** page load; **webdriver-manager** downloads drivers. |
| **Browser options** | Chrome/Firefox only in `conftest`; CLI `--browser` override. |

---

### 4.3 API automation — quick reference topics

| Topic | Talking points |
|-------|----------------|
| **`requests.Session`** | Default headers; cookies reused **within** a test’s `APIClient` instance. |
| **Token auth** | Header **`x-auth-token`** (not Bearer in this project — **be precise** in interviews). |
| **Response validation** | Status first, then `resp.json()` fields / lists. |
| **Status codes** | 200/201 success; 400 validation; 401 auth; 409 conflict — as implemented per test. |
| **CRUD** | Notes + user profile flows in `tests/api/`. |
| **Contract validation** | Partial — mostly status + key fields; room for **schema** tools. |
| **Normalization** | `_ResponseProxy.json()`. |
| **Shared fixtures** | `auth_token` uses **config user** — document **shared-state risk** with `test_delete_all_notes`. |
| **`auth_token` lifecycle** | New login **each test** via fixture. |
| **Negative testing** | Large portion of API suite — missing fields, bad ids, no auth. |

---

### 4.4 Framework design — “Why?” cheat sheet

| Decision | Why (interview soundbite) |
|----------|---------------------------|
| **Hybrid UI/API in NotesPage** | **Reliability** and **speed** on ad-heavy React SPA while still asserting UI. |
| **Response proxy** | **Stabilize assertions** against nested `{data:…}` without rewriting entire suite. |
| **xdist** | **Throughput**; separate worker memory space. |
| **No reruns in stability** | Measure **true** flake rate for governance. |
| **Function-scoped fixtures** | **Isolation** + parallel safety for browser and token. |
| **POM** | **Single place** for locators when UI changes. |
| **`config.ini`** | **Low ceremony** practice project; enterprise would add **env overlays**. |
| **Central logging** | One pattern (`get_logger`) for pages, client, fixtures. |
| **Screenshots in teardown** | Forensics **only on failure** after call phase known. |
| **Timestamped reports** | **No overwrite** of historical evidence (`pytest_configure`). |

---

### 4.5 Advanced SDET topics — soundbites

| Topic | Answer skeleton |
|-------|-----------------|
| **Scalability** | Split suites by marker; add workers until **SaaS** or **CPU** limits; cache config; reduce logging volume in CI. |
| **CI/CD** | `python -m pytest -c pytest_stability.ini` in headless; publish `reports/*.html`, `reports/*.txt`, `reports/screenshots/`. |
| **Grid / Docker** | Not in repo today — `Remote` driver + containerized browser is natural next step. |
| **Cloud** | Browserless / vendor farms (Sauce, Lambda) — same pytest command with capabilities JSON. |
| **Flaky reduction** | Stability metrics, remove sleeps, improve waits, isolate data, avoid shared-account deletes in parallel. |
| **Parallel risks** | **Shared user** mutations; **rate limits**; **ordering**. |
| **Debug intermittent** | Single test, `-n0`, DEBUG logs, screenshot, HAR (future), API correlation id. |
| **Isolation** | Fresh driver; fresh token; fresh users where coded (`_token_from_fresh_user`). |
| **Maintainability** | POM + markers + ini profiles + docs (`TEST_CASE_DETAILED_EXPLANATION.md`). |
| **Extensibility** | Add `tests/ui/packages/` by feature; introduce service layer for HTTP. |

---

## 5. Real framework walkthrough questions (sample answers)

### “Walk me through `conftest.py`.”

> “Root `conftest.py` is pytest’s plugin file. **`pytest_configure`** runs at startup: it reads which **ini** was loaded, builds a **timestamp**, and sets **pytest-html** output path and **pytest log file** path under `reports/` so runs never overwrite each other. **`pytest_addoption`** adds **`--browser`**. Session autouse **`log_browser_choice`** logs Chrome vs Firefox from CLI or config. **`config`** fixture loads the full INI once per session. **`driver`** is function-scoped: builds Chrome or Firefox with **webdriver-manager**, **eager** page load, implicit and page-load timeouts from config, yields to the test, and on teardown checks **`rep_call.failed`** from **`pytest_runtest_makereport`** to optionally screenshot, then **`quit()`**. **`api_client`** returns a new `APIClient` per test. **`auth_token`** logs in via **`APIClient`** each test and returns the token string. **`setup_teardown`** autouse logs SETUP/TEARDOWN. The **hookwrapper** makereport attaches phase reports to the item for the driver fixture.”

### “Explain `save_note()` strategy.”

> “For non-empty titles, **`save_note`** delegates to **`create_note_via_api`**: HTTP login with `requests`, POST note, then sync the browser with **`location.assign`** to the notes URL and **`_wait_for_react_ready`**. If the browser fell back to `/login`, it can re-login via **`LoginPage`**. For **empty title**, we intentionally stay on the **UI** path so React validation still runs. **`is_note_visible`** can confirm via DOM or **GET /notes** using **`_last_token`** when the UI list doesn’t show every note.”

### “Explain `_ResponseProxy` in one technical minute.”

> “We wrap `requests.Response`. When tests call **`resp.json()`**, if the API used an envelope with a **`data` list**, we return that list directly so `len(resp.json())` works. If **`data` is an object**, we shallow-merge inner keys to the top level with **`setdefault`** so **`token`** assertions keep working without breaking access to the original **`data`** key. Other attributes delegate via **`__getattr__`** to the real response.”

---

## 6. Scenario-based questions

### S1. Test passes locally, fails in CI.

| Step | Action |
|------|--------|
| 1 | Compare **Python version**, **dependencies**, **headless** vs headed. |
| 2 | Collect **artifacts** (HTML, pytest log, screenshot). |
| 3 | Re-run **single node** with `python -m pytest …::test_name -n0 -vv`. |
| 4 | Check **timing** (CI slower → expose waits); **network** egress to practice host. |
| 5 | Check **parallelism** — shared account collision? |

### S2. Login UI test is flaky.

| Step | Action |
|------|--------|
| 1 | Inspect **screenshot** + **`LoginPage`** logs. |
| 2 | Verify **`_dismiss_overlays`** + **JS click** path still runs; increase diagnostic logging temporarily. |
| 3 | Run **`pytest_stability.ini`** (no reruns) or **10×** script for rate. |
| 4 | Consider **deterministic wait** on post-login URL (already `WebDriverWait` in `test_notes.login`). |

### S3. API intermittent 500.

| Step | Action |
|------|--------|
| 1 | Correlate **timestamp** with `APIClient` logged body. |
| 2 | Retry policy: **reruns** already on UI/API profiles — do not mis-attribute to app if infra. |
| 3 | Open ticket to **service owner** with request id if available. |

### S4. Parallel execution causes failures.

| Step | Action |
|------|--------|
| 1 | Classify: **data race** (shared user) vs **resource** (too many browsers). |
| 2 | Lower **`-n`** for UI; run API **sequential** (`-n0`) for diagnosis. |
| 3 | Refactor tests to **create isolated users** (`_token_from_fresh_user`) instead of mutating shared account. |

### S5. Clicks intercepted by overlay.

| Step | Action |
|------|--------|
| 1 | **`_dismiss_overlays()`** before critical actions (already in `BasePage` / flows). |
| 2 | **JS click** + **scrollIntoView** center. |
| 3 | If iframe ad persists, **target z-index** strategy or **test-only** ad suppression (policy-dependent). |

### S6. Stale element in React list.

| Step | Action |
|------|--------|
| 1 | Re-find in **loop** / **WebDriverWait** custom predicate; catch **StaleElementReferenceException** (pattern in `NotesPage.is_note_visible`). |
| 2 | Avoid long-lived **WebElement** references across **SPA re-renders**. |

### S7. HTML report missing.

| Step | Action |
|------|--------|
| 1 | Confirm **pytest-html** installed; check **`pytest_configure`** ran (plugin loaded). |
| 2 | If CLI passed conflicting **`--html`**, verify path writable. |
| 3 | Default **`pytest.ini`** prefix **`ini_report_*.html`** — look for unexpected filename. |

### S8. Shared `auth_token` user causes failures.

| Step | Action |
|------|--------|
| 1 | Identify tests that **delete** or **mutate** account (`test_delete_all_notes`, password change). |
| 2 | Run destructive tests **serially** or use **disposable users**. |
| 3 | Long-term: **per-worker** test accounts from pool. |

---

## 7. Code walkthrough interview preparation

### `conftest.py`

| Interview angle | What to say |
|-----------------|--------------|
| **Patterns** | Fixture-based DI, pytest hooks for cross-cutting concerns. |
| **Decisions** | Timestamped reports for audit trail; **tryfirst** hook for screenshot correctness. |
| **Tradeoffs** | No built-in Grid — simplicity vs scale. |
| **Improvements** | Remote URL from env; structured JSON logging. |

### `utilities/api_client.py`

| Interview angle | What to say |
|-----------------|--------------|
| **Patterns** | Facade over `requests`; proxy for **adapter** pattern to legacy assertions. |
| **Decisions** | `_normalize_note_payload` avoids accidental **400** on short strings unrelated to test intent. |
| **Tradeoffs** | Verbose logging — great for practice, **PII risk** in prod. |
| **Improvements** | Typed responses; redact tokens in logs. |

### `pages/base_page.py`

| Interview angle | What to say |
|-----------------|--------------|
| **Patterns** | Template method for wait-then-act. |
| **Decisions** | **`find_element`** without wait — performance vs footgun (callers must know). |
| **Tradeoffs** | `_dismiss_overlays` uses fixed **sleep(0.3)** — stability vs speed. |

### `pages/notes_page.py`

| Interview angle | What to say |
|-----------------|--------------|
| **Patterns** | Hybrid **facade** over UI + HTTP; **retry** loops for modal open. |
| **Decisions** | API-first create; **GET /notes** fallback for visibility assertions. |
| **Tradeoffs** | Dual stack vs `APIClient` — maintenance cost. |
| **Improvements** | Extract `NotesApiService` shared by tests and page. |

### `pages/login_page.py`

| Interview angle | What to say |
|-----------------|--------------|
| **Patterns** | Defensive login: overlay dismiss, **JS click**, URL wait with **retry**. |
| **Decisions** | Tolerant `open()` on timeout if URL already correct — handles slow ads. |

---

## 8. Mock interview simulation rounds

### Beginner round (sample Q&A)

- **Q:** What is pytest? **A:** Python test runner with fixtures and plugins; we use it for UI and API.  
- **Q:** What is POM? **A:** Page Object Model — page classes encapsulate locators and actions.  
- **Q:** Where are credentials? **A:** `config/config.ini` under `[api]` — not hardcoded in tests.

### Intermediate round

- **Q:** How do parallel UI tests get browsers? **A:** xdist workers are separate processes; each **`driver`** fixture instance launches its own browser per test.  
- **Q:** Why separate `pytest_ui.ini`? **A:** Different `testpaths` and reports/logs prefix **`ui`** vs **`api`**.

### Advanced SDET round

- **Q:** Hookwrapper ordering for screenshots? **A:** `tryfirst=True` on `pytest_runtest_makereport` ensures `rep_call` exists before `driver` teardown reads failure state.  
- **Q:** Risks of `_ResponseProxy`? **A:** Assertions may diverge from wire format; masking server contract drift.

### Rapid-fire (answers in one line)

| Q | A |
|---|---|
| Eager page load? | Return after `DOMContentLoaded`-like point — React may still be mounting; we gate with `_wait_for_react_ready`. |
| Stability reruns? | **None** in `pytest_stability.ini`. |
| Token header name? | **`x-auth-token`**. |
| Total tests? | **75** (25 UI + 50 API). |

### Architecture discussion (closing statement)

> “This is a **pragmatic** pytest framework for a **hostile** UI environment: we lean on **POM**, **explicit waits**, **overlay handling**, and **API-backed setup** where the UI alone is unreliable. On the API side we normalize responses to keep tests readable. Execution is **profile-driven** with **xdist** and **reruns** for daily feedback, plus a **stability profile** without reruns for honest flake measurement. The main technical debt I’d call out is **dual HTTP clients** between `APIClient` and `NotesPage` raw `requests`, which I’d unify behind a service layer next.”

---

## 9. STAR format — use in behavioral interviews

### Situation — flaky Notes UI automation

**S:** React SPA on Expand Testing with ads; UI-only note creation failed intermittently.  
**T:** Stabilize create/list assertions without abandoning UI coverage.  
**A:** Implemented **`_wait_for_react_ready`**, improved overlays/JS click paths, and **`create_note_via_api`** with UI sync + optional **GET /notes** visibility fallback; removed harmful **`implicitly_wait(0)`** in tests per root-cause analysis.  
**R:** Notes suite **actionable** under parallel runs; documented in `notes_handbook.md` / `TEST_CASE_DETAILED_EXPLANATION.md`.

### Situation — nested API JSON broke assertions

**S:** API returned tokens and lists under `data`.  
**T:** Keep tests readable without mass rewrite.  
**A:** Introduced **`_ResponseProxy`** merging/unwrapping in `APIClient._wrap`.  
**R:** Assertions like `resp.json()["token"]` and list lengths stable across envelope.

### Situation — stability / stakeholder trust

**S:** Need evidence suite is repeatable.  
**T:** Measure flake rate honestly.  
**A:** `pytest_stability.ini` with **`-n 4`**, **no reruns**; batch **10×** scripts + summary markdown.  
**R:** Clear pass-rate narrative for leads; separate from day-to-day **rerun** smoothing.

---

## 10. Corrections vs outdated interview answers

| Wrong claim | Correct for this repo |
|-------------|------------------------|
| `auth_token` is **session**-scoped | **`function`**-scoped — fresh login **per test** |
| Auth header is **Bearer** | Header is **`x-auth-token`** |
| All note creation is UI-only | **`save_note`** → **`create_note_via_api`** by default |
| Only `pytest` command | Prefer **`python -m pytest`** for interpreter consistency |

---

## 11. Document index

| Need | Open |
|------|------|
| Architecture diagram + risks | [FRAMEWORK_ARCHITECTURE.md](FRAMEWORK_ARCHITECTURE.md) |
| File / fixture internals | [PROJECT_DETAILED_EXPLANATION.md](PROJECT_DETAILED_EXPLANATION.md) |
| Every `test_*` inventory + encyclopedia | [TEST_CASE_DETAILED_EXPLANATION.md](TEST_CASE_DETAILED_EXPLANATION.md) |
| Enterprise test plan | [TEST_PLAN.md](TEST_PLAN.md) |

---

*This handbook is aligned with the current codebase: 75 tests, function-scoped `auth_token`, hybrid `NotesPage`, `_ResponseProxy`, xdist profiles, and stability strategy described in `pytest_stability.ini` and related scripts.*
