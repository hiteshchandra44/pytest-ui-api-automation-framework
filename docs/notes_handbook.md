# Notes UI automation — maintainer & debugging handbook

**Canonical copy:** maintain this file as the **single source of truth** for Notes UI flake RCA and `notes_page` / `test_notes` behavior. **`FRAMEWORK_ARCHITECTURE.md`** links here under the same heading so the handbook is discoverable from the repo overview.

---

## NOTES UI AUTOMATION — MAINTAINER & DEBUGGING HANDBOOK

This block is **maintainer-grade**: it documents **real runtime behavior** of the ExpandTesting Notes UI automation (`tests/ui/test_notes.py`, `pages/notes_page.py`, related `BasePage._dismiss_overlays`, `LoginPage.click_login`). It exists because **Notes UI is the flakiest surface** in this framework: third-party ads, SPA hydration races, shared-account state, and hybrid API/UI assertions interact in ways that **unit-style tests never see**.

---

### How to use this handbook

- When a Notes test fails **intermittently**, start at **NOTES FAILURE ROOT CAUSE ANALYSIS**, then **DEBUGGING PLAYBOOK FOR NOTES FAILURES**, then the **per-test** section for the failing node id.
- When changing `notes_page.py`, read **MAINTAINER WARNINGS** first; many “obvious” simplifications **increase** flake rate.

---

## NOTES UI AUTOMATION DEEP DIVE

### Why Notes automation became unstable (concrete mechanisms)

1. **Third-party ad iframes and fixed-position layers** load **after** the React shell and **after** Selenium thinks the page is “ready”. They sit above `z-index` of the app and **steal hit-testing**: `element.click()` dispatches to the **topmost** element at the viewport point, which is often **not** the Notes button.
2. **`page_load_strategy="eager"`** (see root `conftest.py`) intentionally returns from `driver.get()` when the DOM reaches `interactive` — **before** all subresources finish. For a Create React App bundle, that means **HTML shell first** (“You need to enable JavaScript…”), then **hydration**, then **XHR** for `/notes`. Locators that match **shell** vs **hydrated** DOM diverge across milliseconds to **seconds**.
3. **Shared UI account + long-lived data**: `tests/ui/conftest.py` runs a **session-scoped** `delete_all_notes_for_test_account` against a **hardcoded** API base (`.../notes/api/v1`). The **same** credentials in `config.ini` are used by UI tests and `create_note_via_api`. If cleanup fails or only partially runs, **hundreds of notes** accumulate. The UI **paginates or caps** rendered cards → assertions that depend on **DOM visibility** of a specific title **fail even when the note exists** on the server.
4. **Session expiry during long waits**: If `click_add_note` blocks on an overlay for tens of seconds, the SPA may **redirect to `/login`**. `create_note_via_api` still succeeds on the server (HTTP client uses fresh token), but the **browser** is on login — refresh/re-login paths then compete with **still-present overlays**.
5. **Parallel workers (`pytest -n auto`)** multiply page loads and logins against the **same SaaS tenant**, increasing **rate limiting**, **cold starts**, and **interleaved** server-side state.

### What changed in website / product behavior (observed, not assumed)

- **Notes app is a React SPA** under `https://practice.expandtesting.com/notes/app` with **client-side auth** (tokens in browser storage). Full navigation to `notes/app` without a warm session → **login route**.
- **Bootstrap modals** (`div.modal.show`) gate create/edit; **backdrop** captures clicks outside; **aria** and `data-testid` attributes exist on some controls (`note-submit`, `note-category`) but **not uniformly** on every interactive element.
- **Edit flow**: the **card-header text is not reliably clickable**; the app exposes an **Edit** control inside the **card body** (button with “edit” in text/class/`data-testid`). Clicking the header alone **does not** open `#title` — automation was wrong until `click_edit_note_by_title` targeted the **Edit** button.
- **Ad overlays are not part of the app DOM contract** — they change by geography, time, and A/B tests. Any locator strategy that assumes a **static** overlay DOM is **fragile**.

### Selenium-specific failure modes on this stack

| Symptom | Typical exception / log | Mechanism |
|--------|-------------------------|-----------|
| Click does nothing | No exception; later timeout on next step | **Hit target** was overlay; Selenium believed click succeeded |
| Click does nothing | `ElementClickInterceptedException` | Known overlay element in stack |
| Wrong element clicked | Assertion on wrong note / deleted first card | **Global XPath** `//button[contains(.,'Delete')]` matches **first** match in DOM order |
| “Found” but unusable | `StaleElementReferenceException` | React re-render between `find` and `click` |
| Immediate empty lists | No exception; fast failure | **`implicitly_wait(0)`** while polling — each `find_elements` returns **instantly** |
| Hang then `TimeoutException` | `WebDriverWait` + `expected_conditions` | Condition never satisfied — modal never opened, wrong phase of React mount, or still on `/login` |
| Renderer / load | `TimeoutException` from `driver.get` | `page_load_timeout` hit by ad network; mitigated by **tolerant `open()`** in `NotesPage` |

### Why `element.click()` became unreliable → JS click

Native `WebDriver.click()` synthesizes OS-level pointer events at the **element’s in-view center**. If another element receives the event, WebDriver may throw **intercepted** or may **succeed at the protocol level** while the app state does not change. **`execute_script("arguments[0].click()", el)`** invokes the DOM **click()** method on the node **even if covered** (browser-dependent nuances exist, but this is the **deliberate tradeoff** here). **Tradeoff:** JS click can **bypass HTML5 constraint validation** and **bypass** some React synthetic event paths — mitigated by using JS only where overlays are expected (login submit, add note, modal submit paths).

### Why `save_note()` became API-backed

The “pure UI” path required: open modal → fill → submit → wait for list. In production-like runs:

- Modal **never opens** (add blocked) but tests still set `_pending_title` / `_pending_description`.
- Submit clicks **hit backdrop**.
- List updates are **async** after POST.

`save_note()` therefore **clears pending fields** and calls **`create_note_via_api(title, description)`** for the **normal** case. The **empty-title negative** test still forces **UI submit** so HTML5 / server validation paths execute — see `save_note` branch on `raw_title is not None and title == ""`.

### React rendering timing vs locators

- **Wrong phase**: `div.card` can exist as an empty shell before XHR returns → waiting **only** for `div.card` is insufficient; **`_wait_for_react_ready`** phase 2 waits for **`div.card-header`** list **or** the “You don’t have any notes” empty state.
- **`EC.presence_of_element_located` vs `element_to_be_clickable`**: presence proves DOM node exists **under ads**; clickability proved **fragile** when ads cover “+ Add Note”. Current **Phase 1** uses **`EC.any_of`** across **Add Note**, **nav/navbar**, and **Notes/Logout** links so **hydration** is detected even when the add button is occluded.
- **Stale rows**: any pattern that finds `WebElement`, sleeps on network, then clicks **without re-location** is vulnerable — `delete_note` UI path re-queries within `WebDriverWait` lambdas where needed.

### Modal / backdrop interaction

- **`div.modal.show`** is used as “modal open” detector. **Risk**: if multiple stacked modals exist, visibility may not imply **the** create/edit modal you intend.
- **`submit_open_note_modal`** waits post-submit for **`EC.invisibility_of_element_located(div.modal.show)`** — if the app leaves another `.modal.show` in DOM, wait may **fail until timeout** (logged as warning only — by design so API-backed assertions can still pass).

---

## `tests/ui/test_notes.py` — COMPLETE FILE WALKTHROUGH

### Module-level helpers and imports

| Symbol | Role |
|--------|------|
| `login(driver)` | Constructs `LoginPage`, `open()`, types credentials from **`read_config("api", ...)`** (same identity as API tests), `click_login()`, then **`WebDriverWait(..., 30)`** until URL contains **`notes/app`**. This extra wait exists because **`click_login` does not throw** when redirect never happens — tests would otherwise proceed on `/login`. |
| `_unique_note_title(prefix)` | `f"{prefix}_{int(time.time()*1000)}"` — **millisecond** uniqueness; weaker than `uuid` for parallel collision but fast. |
| `logger` | Module logger; informational “Running test:” lines. |
| `pytest`, `TimeoutException`, `By`, `EC`, `WebDriverWait` | `TimeoutException` / `EC` are **imported** for historical or future use; **`test_edit_note`** uses `By` for DOM title probe only. |

### Fixture resolution (this module)

- Tests request **`driver`** from **root** `conftest.py` (function-scoped browser).
- **`tests/ui/conftest.py`** defines **`delete_all_notes_for_test_account`** (`scope="session"`, `autouse=True`) — runs **once per pytest session** when UI tests are collected. It uses a **hardcoded** `https://practice.expandtesting.com/notes/api/v1` base — **may diverge** from `config.ini` `api_base_url` if paths differ; if cleanup silently no-ops, **account bloat** worsens pagination flakes.
- **No** per-test `notes_page` fixture — each test constructs **`NotesPage(driver)`** inline.

### Teardown behavior

- **No explicit teardown** in test bodies; **`driver` fixture** quits browser. On failure, **screenshot** path `reports/screenshots/<node_name>.png`.
- **Session cleanup** of notes is **best-effort** at session start, not after each test.

---

#### `test_create_note` (`@pytest.mark.ui`, `smoke`, `positive`)

1. **Runtime flow**: `login` → `NotesPage.open()` → `_wait_for_react_ready` inside `open` → `click_add_note` (overlay dismissal + wait) → `enter_note_title` / `enter_note_description` (best-effort modal fill) → **`save_note()`** → API create + UI refresh path inside `create_note_via_api` → `assert is_note_visible(title)`.
2. **Selenium actions**: `get(notes_login)`, fills `#email`/`#password`, JS login click, URL wait, `get(base_url notes app)`, overlay passes, optional modal, explicit waits inside `is_note_visible`.
3. **Backend/API**: **`POST /users/login`** and **`POST /notes`** from **`create_note_via_api`** using **`requests`**, not browser network.
4. **Assertion strategy**: `is_note_visible(title)` — **title-specific** branch uses **20s** `WebDriverWait` polling `div.card-header` text + **DOM fallbacks** + **`_note_title_exists_via_api`** if token present (`_last_token` set during create). So assertion can pass **without** the card being on first page **if** API lists the note.
5. **Failure scenarios**: stuck on login; `click_add_note` timeout; API 401/500; `is_note_visible` false if **both** DOM and API checks fail.
6. **Debugging tips**: grep logs for `_wait_for_react_ready: current URL`, `create_note_via_api`, `click_add_note failed`; verify `config.ini` `api_base_url` vs UI cleanup fixture URL; run headed single test.
7. **Stability recommendations**: keep **`_dismiss_overlays`** before fragile clicks; avoid lowering **`_wait_for_react_ready`** default; consider **per-test API cleanup** for the shared user.

---

#### `test_note_appears_in_list` (`ui`, `smoke`, `positive`)

Same structural flow as `test_create_note` but title format `List_<uuid>_<ms>` and assertion uses **`is_note_visible_by_title`** (alias to `is_note_visible(title)`).

**Flaky angles**: identical to create note; title format is **stronger** against collision than `_unique_note_title`.

---

#### `test_delete_note` (`ui`, `regression`)

1. **Runtime flow**: login → open → create note via UI fields + **`save_note()`** → `assert is_note_visible(title)` → **`delete_note()` with `title=None`**.
2. **Selenium actions**: **`delete_note` without title** uses **first visible** global **`DELETE_BUTTON`** match after waits — **does not** target the created title’s card. **By design** the test only checks “something deleted / still on app”.
3. **Backend/API**: **`_delete_note_via_api(title)` is skipped** (no title). If title were passed, API path would **`GET /notes`**, **`DELETE /notes/{id}`**, refresh.
4. **Assertion strategy**: only **`notes/app` in URL`** — weak post-condition; does not assert note count.
5. **Failure scenarios**: `delete_note` UI path cannot find visible delete; stuck on login during create.
6. **Debugging tips**: if intent is to delete **the** created note, pass **`title=`** into `delete_note` — current test **may delete another card**.
7. **Stability**: API delete path (when title provided) avoids pagination; UI-first-delete remains fragile on busy accounts.

---

#### `test_edit_note` (`ui`, `regression`)

1. **Runtime flow**: create note → `assert is_note_visible_by_title(original)` → **immediate** `find_elements(div.card-header)` to compute **`title_in_dom`** (substring check, **not** `_title_matches` — can disagree slightly with `is_note_visible` logic).
2. **Branch A (`title_in_dom`)**: `click_edit_note_by_title` finds **`div.card`** with matching header, finds **Edit** button in that card, JS click, waits for modal/`#title`; `enter_note_title` / `enter_note_description`; **`submit_open_note_modal`**; optional modal invisibility wait (warning-only timeout).
3. **Branch B (pagination / not in first DOM slice)**: **`edit_note_via_api`** (`GET /notes`, `PUT /notes/{id}`) → **`driver.refresh()`** + **`_wait_for_react_ready()`** (test calls these explicitly).
4. **Backend/API**: `edit_note_via_api` uses full PUT body with preserved **category/completed** from GET.
5. **Assertion**: `is_note_visible_by_title(edited_title)` — API fallback may pass without edited card visible.
6. **Failure scenarios**: **`click_edit_note_by_title` False** if Edit button not matched (icon-only / unexpected class); deep link route unsupported → fallback false; **`submit_open_note_modal`** stuck modal; token missing for API branch.
7. **Debugging tips**: log **`click_edit_note_by_title`** warnings; verify button text/class in DOM; compare **`title_in_dom`** vs `is_note_visible` (different matchers).
8. **Stability**: align **`title_in_dom`** check with **`_title_matches`** if false branch taken incorrectly.

---

#### `test_empty_note_title` (`ui`, `regression`, `negative`)

1. **Runtime flow**: `enter_note_title("")` sets **`_pending_title` to `""`** — **important**: `save_note` distinguishes **`raw_title is not None and strip()==""`** for **UI validation** path.
2. **Selenium**: attempts to open/submit modal via **`save_note`** empty-title branch — **does not** call API create.
3. **Assertion**: URL still contains **`notes/app`** — does not assert toast text (fragile).
4. **Failures**: if modal never opens, branch may still no-op; test can **false-pass** if navigated elsewhere incorrectly.

---

#### `test_multiple_notes` (`ui`, `regression`, `positive`)

1. **Runtime flow**: create note1 → **`open()` again** (full navigation + `_wait_for_react_ready`) → create note2 → assert both titles via **`is_note_visible_by_title`**.
2. **Why `open()` between notes**: clears React state / ensures list fetch — **mitigates** stale UI after first API save without relying on test sleep loops.
3. **Failures**: second create fails if session dropped on `open`; API throttling under xdist.

---

#### `test_note_persists_after_refresh` (`ui`, `smoke`, `positive`)

1. **Runtime flow**: save via API path → assert visible → **`driver.refresh()`** (raw driver, not `NotesPage.open`) → **`notes_page._wait_for_react_ready()`** → assert.
2. **Risk**: bypassing **`NotesPage.open()`** means **no** `open()`-level **`_dismiss_overlays`** ordering — acceptable post-refresh but if ads inject on reload, **`_wait_for_react_ready`** may still succeed while cards delayed.
3. **Debugging**: if fail after refresh only, inspect **`_wait_for_react_ready`** phase-2 timeout logs and API fallback path.

---

### Parallel execution (`xdist`) and test isolation

- Each worker: **own browser**, **same config credentials**, **same remote account**. Isolation is **not** process-local — it is **server-side** contention.
- **Session autouse cleanup** runs **per worker process** (session scope is **per xdist worker**), not globally once — can mean **up to N cleanups** for N workers, still not guaranteeing empty account mid-session.

---

## `pages/notes_page.py` — FULL ARCHITECTURAL ANALYSIS

### Module-level helper: `_title_matches(text, want)`

- **Why**: tolerate duplicate timestamp suffix patterns when titles collide under parallel runs / double-save bugs.
- **Breaks if**: product changes title format away from `Prefix_<digits>`.

### Locator table (class attributes on `NotesPage`)

| Locator | Selector | Role / fragility |
|---------|----------|------------------|
| `ADD_NOTE_BUTTON` | XPath `//button[contains(text(),'+ Add Note')]` | Primary CTA; **fragile** to copy/locale; **occluded** by ads. |
| `REACT_MOUNT_NAV` | `nav.navbar, nav, .navbar` | Hydration signal for `_wait_for_react_ready` **Phase 1** `any_of`. |
| `REACT_MOUNT_NAV_LINKS` | XPath Notes/Logout anchors | Alternate mount signal. |
| `TITLE_INPUT` / `DESCRIPTION_INPUT` | `#title`, `#description` | Modal fields; **IDs reused** between add/edit modals in many CRAs — assumes single visible modal. |
| `CATEGORY_SELECT` / `NOTE_CATEGORY` | `#category` vs `[data-testid="note-category"]` | Legacy vs app; **`enter_note_category`** uses **testid** path. |
| `NOTE_SUBMIT` / `CREATE_BUTTON` | `[data-testid="note-submit"]` | **Preferred** submit hook. |
| `CANCEL_BUTTON` | `[data-testid="note-cancel"]` | Modal cancel. |
| `LOGOUT_BUTTON` | XPath text Logout | Navbar/footer drift risk. |
| `SEARCH_INPUT` / `SEARCH_BUTTON` | `#search-input`, `#search-btn` | Search UI (tests may not cover). |
| `NOTE_CARD` | `div.card` | **Too coarse** alone for “data loaded”. |
| `NOTE_TITLE` | `div.card-header.fw-bold` | **Subset** of headers — can miss cards without `fw-bold`. |
| `DELETE_BUTTON` | XPath Delete / class delete | **Global** — dangerous without scoping (see `delete_note`). |
| `CONFIRM_DELETE` | XPath Confirm/Yes/OK | Confirmation modal / dialog. |
| `CATEGORY_ALL` | XPath All button | Category chips. |
| `NO_NOTES_MSG` | `//h4[contains(.,'You don')]` | Empty-state detector for `_wait_for_react_ready` phase 2. |

### Instance state

| Field | Role |
|-------|------|
| `_pending_title` / `_pending_description` | Staging for **`save_note`** / modal fillers; cleared when entering API path. |
| `_last_token` | Last **HTTP API** token from **`create_note_via_api`** / **`_get_fresh_token`**; powers **`_note_title_exists_via_api`**, delete/edit API helpers. **Not** automatically synced with browser storage. |

### Method-by-method (summary grid)

| Method | Purpose | Waits / side effects | Breaks when |
|--------|---------|----------------------|-------------|
| `__init__` | Initializes pending + token | none | — |
| `_wait_for_react_ready` | SPA gate after navigation | implicit→0; Phase1 `any_of` 45s default; Phase2 `_notes_loaded` 15s; restores implicit | login route stuck; ads never allow mount signals (rare if nav visible) |
| `open` | `get(URL)` tolerant + `_dismiss_overlays` + `_wait_for_react_ready` | overlay JS + react wait | load timeout + URL not `notes/app` |
| `click_add_note` | Dismiss cookie/ad-like buttons via CSS list; `_dismiss_overlays`; remove tall fixed layers; **15s** presence wait `ADD_NOTE_BUTTON`; JS click; optional **5s** modal | logs warning on failure | all selectors noop + button absent |
| `enter_note_title` | Sets pending; fills `#title` with clear + optional JS `value=''` + value warning | 3s visibility wait | modal not open → silent skip except debug log |
| `enter_note_description` | Same pattern for `#description` | 3s | same |
| `select_category` / `enter_note_category` | category selection | immediate find | modal closed |
| `save_note` | **API path** or **empty-title UI path** | API path calls `create_note_via_api` | pending fields wrong |
| `_save_note_via_ui_modal` | Fallback UI create | `click_add_note`, waits submit, synthetic mouse events JS | overlay intercept |
| `create_note_via_api` | HTTP login+POST note; refresh or **re-login branch** with `_dismiss_overlays`; **`TimeoutException` on post-login wait → early `return`** skipping DOM waits | network, 401 handling | token extraction mismatch |
| `_note_title_exists_via_api` | `GET /notes` + `_title_matches` | uses `_last_token` | token null / pagination on API side (if API paginated) |
| `_wait_for_title_in_dom` | Polls card-header text | timeout→API fallback True/False | heavy DOM |
| `get_note_title` | reads first `NOTE_TITLE` | uses `get_text` wait | no cards |
| `is_note_visible` | title `None` → any card; else **20s** poll + XPath fallback + **API fallback** | toggles implicit 0 internally | implicit left 0 by foreign code (tests fixed) |
| `is_note_visible_by_title` | delegates | same | same |
| `edit_note_via_api` | GET match + PUT | 401 refresh retry | id mismatch |
| `_open_edit_via_deep_link_or_fail` | `GET` id + `driver.get(base/{id}/edit)` + wait | falls back `open()` + False | SPA route not implemented |
| `click_edit_note_by_title` | Card-scoped **Edit** button + modal wait; else deep link | 5s + 5s + 10s | icon-only edit |
| `submit_open_note_modal` | submit click + modal invisibility wait (warn) | 10+10s | modal stuck |
| `_get_fresh_token` | POST login → `_last_token` | 15s HTTP | bad creds |
| `_delete_note_via_api` | GET+DELETE w/ 401 retry | HTTP | note not in first API page if ever paginated |
| `delete_note` | **API-first by title** else scoped UI delete + confirm + staleness | refresh on API success | scoped UI fails if header not in DOM |
| `logout` | JS click logout + `WebDriverWait` `any_of` URL/login form | 15s | ads block logout |
| `react_type` | legacy typing helper | sleeps | — |

### Deep dives (methods called out by operators)

#### `save_note()`

- **Why**: single entry for tests after filling modal fields.
- **Normal path**: clears `_pending_*` then **`create_note_via_api(title, description)`** — decouples test stability from modal reliability.
- **Empty-title path**: ensures modal exists (re-`click_add_note` if needed), **`element_to_be_clickable` submit**, JS scroll/click — preserves **validation** semantics.
- **Breaks if**: `_pending_title` not set (test order bug) → API create with empty string filtered? (title stripped — watch edge cases).

#### `create_note_via_api()`

- **HTTP login** independent of browser session — sets **`_last_token`** even if browser logged out.
- **POST** note — source of truth for existence.
- **Browser sync**: if URL has **`login`**, **`_dismiss_overlays`**, `LoginPage.open/enter/click_login`, **`WebDriverWait` try/except**: on timeout **`return`** — **skips** `_wait_for_react_ready` and `_wait_for_title_in_dom` so test does not crash after successful POST.
- **Else**: `refresh()` then `_wait_for_react_ready` + `_wait_for_title_in_dom`.

#### `is_note_visible` / `is_note_visible_by_title`

- **20s** explicit polling with **`implicitly_wait(0)`** inside the titled branch so polling interval is controlled — **critical**; removing this reintroduces “instant false” failure mode documented in `test_notes.py` header.
- **API fallback**: if DOM never shows title, **`_note_title_exists_via_api`** may still return True — **by design** for pagination; implies **callers must not assume DOM** for subsequent interactions (see `test_edit_note`, `delete_note` API path).

#### `click_add_note()`

- **Overlay dismissal list** + **`BasePage._dismiss_overlays`** + **remove** large fixed layers → **then** wait **15s** for presence (not clickability) + JS click — reduces session expiry window vs old **30s** blind wait.

#### `logout()`

- JS click on logout button; **`EC.any_of`** URL contains login, `#email`, or login form — tolerates client routers that do not put “login” substring in URL immediately.

#### Refresh behavior (summary)

- **`create_note_via_api`**: `refresh()` on happy path preserves **same origin** storage vs cold `get(BASE_URL)` which historically caused **auth loss** in some timings.
- **Re-login path**: intentional **`open()` login URL** when session lost — different from refresh.

#### Modal synchronization

- **Open detection**: `div.modal.show` after add.
- **Submit close**: `submit_open_note_modal` waits **invisibility** of `.modal.show` (best-effort).

---

## NOTES FAILURE ROOT CAUSE ANALYSIS

### A) Selenium timing issues

| Issue | Symptoms | Likely stack / log | Root cause | Reruns sometimes pass? | Hardening |
|-------|----------|--------------------|------------|--------------------------|-----------|
| Explicit wait too short | `TimeoutException` in `WebDriverWait` | `WebDriverWait` line in traceback | Network/ad slow | yes | raise timeouts for *mount* waits cautiously; prefer condition-based |
| Implicit/explicit interference | fast empty finds | missing cards in polls | implicit 0 vs non-zero | yes | never set implicit 0 in tests; let POM manage |
| Phase-2 `_wait_for_react_ready` swallowed | proceeds before headers | later assert fail | empty list timeout swallowed by design | intermittent | consider logging metric when phase-2 times out |

### B) React rendering / async

| Issue | Symptoms | Root cause | Mitigation |
|-------|----------|------------|------------|
| Hydration race | random “element not interactable” | DOM replaced | `WebDriverWait` + re-find |
| List fetch async | cards empty then populated | XHR after mount | `_wait_for_react_ready` phase 2 + API fallback |

### C) Overlays / backdrops / intercepted clicks

| Issue | Symptoms | Root cause | Mitigation |
|-------|----------|------------|------------|
| Ad iframe | click no-op | z-order | `_dismiss_overlays`, JS click, shorter waits |
| Modal backdrop | intercept | Bootstrap | JS click on intended element |
| Cookie banner | hides controls | third-party | CSS click list in `click_add_note` |

### D) Stale elements

| Issue | Symptoms | Mitigation |
|-------|----------|------------|
| Node replaced | `StaleElementReferenceException` | re-query inside wait lambda |

### E) API latency / auth

| Issue | Symptoms | Mitigation |
|-------|----------|------------|
| Slow POST | long hangs | reasonable `requests` timeouts + logs |
| 401 on GET notes | API fallback false | `_get_fresh_token` / recreate |

### F) Parallel execution / xdist

| Issue | Symptoms | Mitigation |
|-------|----------|------------|
| Many workers hammer login | rate limit / slow redirect | reduce `-n`, add stagger (external), use fresh users (future) |

### G) Session / token drift

| Issue | Symptoms | Mitigation |
|-------|----------|------------|
| Browser logged out, HTTP ok | “on login URL before reload” | re-login branch + `_dismiss_overlays` + non-throwing wait |
| `_last_token` stale | API fallback wrong | `_get_fresh_token` in delete path |

### H) Browser / load strategy

| Issue | Symptoms | Mitigation |
|-------|----------|------------|
| `normal` load strategy | longer ad waits | keep `eager` |
| Renderer timeout | `TimeoutException` on `get` | tolerant `open()` |

---

## SELENIUM STABILITY ENGINEERING REVIEW (Notes-focused)

- **`eager` page load**: returns earlier → **must** pair with **`_wait_for_react_ready`** or equivalent SPA gate; otherwise locators run against shell.
- **Implicit + explicit**: implicit wait **polls** `find_element` under the hood; mixing with `WebDriverWait` **without** setting implicit 0 during tight polls causes **multiplied** wait times — `is_note_visible` sets implicit 0 temporarily for that reason.
- **JS click danger**: can skip validation and some React handlers — used **only** where interception is dominant; keep native paths where validation is the SUT (`empty_note_title`).
- **Native `send_keys`**: drives browser input pipeline (events) closer to user; **`execute_script` value set** is avoided in `enter_note_title` except **clearing stuck values** — still dispatches keys after.
- **ActionChains**: not central to current Notes fixes; older login doc may mention — **`click_login`** is JS-first now with **`BasePage._dismiss_overlays`** pre-click.
- **Modals/backdrops**: `element_to_be_clickable` ensures not disabled and **roughly** visible, but not “not covered by another element” — hence **JS click** still used.

---

## DEBUGGING PLAYBOOK FOR NOTES FAILURES

1. **Logs**: `logs/test_<date>.log` — search for test node name, `NotesPage`, `create_note_via_api`, `click_add_note`, `_wait_for_react_ready`, `LoginPage`, `TimeoutException`.
2. **Screenshots**: `reports/screenshots/<test_function>.png` — correlate timestamp with log block; look for overlays, login page, blank shell.
3. **Reproduce flake**: run single test repeatedly: `pytest tests/ui/test_notes.py::test_edit_note -vv --count=20` (if pytest-repeat installed) or shell loop; use **`-n0`** to disable xdist.
4. **Headed mode**: `config.ini` `[browser] headless=false` or CLI if wired — watch modal and ad timing.
5. **DOM inspection**: pause with `input()` temporarily (dev only) or `utilities/inspect_dom.py` / `inspect_locators.py`.
6. **Modal visibility**: in DevTools, `document.querySelectorAll('div.modal.show')`.
7. **Intercepted clicks**: stack often shows another element receiving pointer; compare with screenshot.
8. **Stale element**: reduce gap between find and action; use waits that re-query.
9. **Network/API**: log `create_resp.status_code` already; use browser DevTools Network tab for SPA XHR vs `requests` traffic (two channels).

---

## FAILURE FLOW DIAGRAMS (Notes-specific ASCII)

### 1) Successful note creation (API-backed happy path)

```
test: login() -> NotesPage.open() -> _wait_for_react_ready (mount+list gate)
     -> click_add_note (dismiss overlays -> wait Add Note -> JS click)
     -> enter_note_title/description (pending set; modal fill best-effort)
     -> save_note -> create_note_via_api
            -> requests POST login -> token
            -> requests POST /notes -> 200/201
            -> driver.refresh (if still on app URL)
            -> _wait_for_react_ready -> _wait_for_title_in_dom (DOM or API fallback)
test: assert is_note_visible[_by_title] (DOM poll -> API fallback)
```

### 2) Failed note creation (browser on /login after long ad wait)

```
click_add_note waits / dismisses -> still blocked -> WARNING timeout
enter_* sets pending anyway
save_note -> create_note_via_api POST succeeds
current_url contains login -> _dismiss_overlays -> LoginPage flow -> click_login
WebDriverWait post-login TIMEOUT -> WARNING + early return (no refresh/DOM wait)
test assert may still PASS via API fallback OR fail if token/DOM mismatch
```

### 3) Intercepted click flow (conceptual)

```
Selenium: move_to_element(btn) .click()
Browser: hit target = iframe/div at higher z-index
Outcome A: ElementClickInterceptedException
Outcome B: no exception, app state unchanged -> subsequent wait TIMEOUT
Mitigation: JS click(btn) + overlay dismissal scripts
```

### 4) API-assisted save flow (control/data planes)

```
Control plane (Selenium): open page, (optional) modal interactions
Data plane (requests): POST /notes with x-auth-token
Sync: refresh + _wait_for_react_ready + _wait_for_title_in_dom
Assertion plane: DOM poll with API fallback (_last_token)
```

### 5) Screenshot capture flow (unchanged mechanic)

```
test failure in call phase
pytest_runtest_makereport stores rep_call.failed
driver fixture teardown observes rep_call.failed
writes reports/screenshots/<node>.png
quits browser
```

### 6) Flaky rerun flow (`pytest --reruns 1`)

```
first run: transient overlay -> timeout
rerun: overlay absent -> pass
Note: pytest_stability.ini disables reruns -> exposes flake rate honestly
```

---

## MAINTAINER WARNINGS (Notes automation)

- **Do not casually remove** `_wait_for_react_ready` from `open()` — this reintroduces **shell-phase** races.
- **Do not remove** `implicitly_wait(0)` guard inside `is_note_visible` titled branch without re-measuring poll timings.
- **Fragile locators**: `ADD_NOTE_BUTTON` text XPath; global `DELETE_BUTTON`; `NO_NOTES_MSG` partial text.
- **Do not “simplify”** `create_note_via_api` re-login `try/except TimeoutException` return — tests rely on **non-crash** after POST success.
- **Anti-patterns**: setting `implicitly_wait(0)` in **tests**; using **global** XPath for per-card actions; assuming **`is_note_visible` implies DOM** for clicks.

---

## FUTURE STABILITY IMPROVEMENTS (enterprise-oriented)

| Direction | Notes |
|-----------|------|
| **Playwright** | Built-in **auto-wait**, **trace viewer**, **network** tab; migration cost: rewrite POM + fixtures; benefit: drastically fewer race classes for SPAs. |
| **Smarter retries** | Distinguish **infrastructure** vs **assert** failures; avoid rerunning on deterministic assertion failures. |
| **Custom wait wrappers** | `wait_for_spa_ready(url_pattern, conditions)` returning structured diagnostics. |
| **Locator strategy** | Prefer **`data-testid`** from engineering; maintain **locator map** per environment. |
| **Testability hooks** | Dev build flags exposing `window.__NOTES_TEST_STATE` (counts, last XHR) — requires product partnership. |
| **API/UI hybrid** | Already partially implemented — extend: **always** assert server state for mutations, use UI only for true UI coverage. |
| **Visual debugging** | Playwright traces / Percy / Applitools — cost vs value. |
| **Video** | Selenium 4 Grid video, or Playwright video on failure. |
| **HAR** | BrowserMob proxy or Playwright `route`/`har` export. |
| **Grid / Docker** | Pin images, CPU limits; headless stability differs from local headed. |
| **CI stabilization** | Single worker for UI smoke, shard suites, **synthetic monitoring** account separate from devs. |

