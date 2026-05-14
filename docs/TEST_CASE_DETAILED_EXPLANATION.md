# Test Case Detailed Explanation — Knowledge Base & QA Handbook

**Purpose:** A **complete test inventory** and **per-test encyclopedia** for every automated test in this repository.  
**Companion docs:** [README.md](README.md) · [PROJECT_DETAILED_EXPLANATION.md](PROJECT_DETAILED_EXPLANATION.md) · [FRAMEWORK_ARCHITECTURE.md](FRAMEWORK_ARCHITECTURE.md) · [notes_handbook.md](notes_handbook.md)

**How to read this document**

- Start with **§1 Complete test case inventory** (tables).
- Jump to a file under **§2–§7** for file-level purpose, helpers, and **every** `test_*` function.
- Each test uses a **17-row table** (Purpose → Advanced explanation) so new QAs can scan quickly or read deeply.

**17-row schema (every `### test_*` table uses these rows):** (1) Purpose (2) Business scenario (3) Why it matters (4) Preconditions (5) Fixtures used (6) Runtime execution flow summary (7) Step-by-step Selenium/API flow (8) Page object methods called — or “None” for API (9) Indirect locators / HTTP details (10) Assertions (11) Expected result (12) Failure scenarios (13) Flakiness causes (14) Screenshots/logs (15) Real-world importance (16) Beginner explanation (17) Advanced explanation.

**Convention:** Unless stated otherwise, **base URL** for API calls is `read_config("urls", "api_base_url")` (e.g. `https://practice.expandtesting.com/notes/api`). **`APIClient`** joins `base_url + "/" + endpoint.lstrip("/")`, so both `notes` and `/notes` resolve correctly.

---

## 1. Complete test case inventory

**Legend — type:** `API` = HTTP only · `UI` = browser · **Priority** from markers: `smoke` > `regression` (smoke = higher run priority in many teams). **Complexity:** subjective (L/M/H). **Stability risk:** flakiness / shared-state / timing sensitivity.

### 1.1 API tests (`tests/api/`)

| Test file | Test function | Type | Feature | Fixtures | Priority | Complexity | Stability risk |
|-----------|----------------|------|---------|----------|----------|------------|----------------|
| `test_auth_api.py` | `test_register_user_success` | API | Register new user | `api_client` | smoke | M | L — unique email |
| `test_auth_api.py` | `test_register_duplicate_email` | API | Duplicate register → conflict | `api_client` | regression | M | L |
| `test_auth_api.py` | `test_register_missing_email` | API | Validation — missing email | `api_client` | regression | L | L |
| `test_auth_api.py` | `test_register_missing_password` | API | Validation — missing password | `api_client` | regression | L | L |
| `test_auth_api.py` | `test_login_success` | API | Login returns token | `api_client` | smoke | M | L |
| `test_auth_api.py` | `test_login_wrong_password` | API | Auth failure | `api_client` | regression | M | L |
| `test_auth_api.py` | `test_login_invalid_email` | API | Validation — bad email | `api_client` | regression | L | L |
| `test_auth_api.py` | `test_get_profile_success` | API | Profile with token | `api_client` | regression | M | L |
| `test_auth_api.py` | `test_get_profile_no_token` | API | Profile 401 | `api_client` | regression | L | L |
| `test_auth_api.py` | `test_get_profile_invalid_token` | API | Profile 401 + message | `api_client` | regression | M | L |
| `test_auth_api.py` | `test_logout_success` | API | Logout invalidates session | `api_client`, `auth_token` | regression | M | **M** — shared user token |
| `test_auth_api.py` | `test_logout_no_token` | API | Logout without token | `api_client` | regression | L | L |
| `test_notes_api.py` | `test_create_note_success` | API | POST note 200 | `api_client` | smoke | M | L — fresh user |
| `test_notes_api.py` | `test_create_note_missing_title` | API | POST note 400 | `api_client`, `auth_token` | regression | M | **M** — shared `auth_token` user |
| `test_notes_api.py` | `test_create_note_missing_description` | API | POST note 400 | `api_client` | regression | M | L |
| `test_notes_api.py` | `test_create_note_no_auth` | API | POST note 401 | `api_client` | regression | L | L |
| `test_notes_api.py` | `test_get_all_notes` | API | GET list | `api_client` | regression | M | L |
| `test_notes_api.py` | `test_get_all_notes_no_auth` | API | GET 401 | `api_client` | regression | L | L |
| `test_notes_api.py` | `test_get_note_by_id` | API | GET by id | `api_client` | regression | M | L |
| `test_notes_api.py` | `test_get_note_invalid_id` | API | GET bad id | `api_client`, `auth_token` | regression | M | M |
| `test_notes_api.py` | `test_get_note_no_auth` | API | GET by id 401 | `api_client`, `auth_token` | regression | M | M |
| `test_notes_api.py` | `test_update_note_success` | API | PUT note | `api_client`, `auth_token` | regression | M | M |
| `test_notes_api.py` | `test_update_note_missing_title` | API | PUT 400 | `api_client` | regression | M | L |
| `test_notes_api.py` | `test_update_note_no_auth` | API | PUT 401 | `api_client`, `auth_token` | regression | M | M |
| `test_notes_api.py` | `test_update_note_invalid_id` | API | PUT 400/404 | `api_client`, `auth_token` | regression | M | M |
| `test_notes_api.py` | `test_delete_note_success` | API | DELETE note | `api_client`, `auth_token` | regression | M | **M–H** — mutates shared user notes |
| `test_notes_api.py` | `test_delete_note_no_auth` | API | DELETE 401 | `api_client`, `auth_token` | regression | M | M |
| `test_notes_api.py` | `test_delete_note_invalid_id` | API | DELETE bad id | `api_client`, `auth_token` | regression | M | M |
| `test_notes_api.py` | `test_create_multiple_notes` | API | List count +3 | `api_client` | regression | H | L — isolated new user |
| `test_notes_api.py` | `test_note_category_home` | API | Category Home | `api_client`, `auth_token` | regression | L | M |
| `test_notes_api.py` | `test_note_category_work` | API | Category Work | `api_client`, `auth_token` | regression | L | M |
| `test_notes_api.py` | `test_note_category_personal` | API | Category Personal | `api_client`, `auth_token` | regression | L | M |
| `test_notes_api.py` | `test_toggle_note_complete` | API | PATCH completed | `api_client` | regression | M | L |
| `test_notes_api.py` | `test_toggle_note_incomplete` | API | PATCH toggle | `api_client` | regression | M | L |
| `test_notes_api.py` | `test_note_title_max_length` | API | Long title boundary | `api_client`, `auth_token` | regression | M | **M** — uses raw `auth_token` string in headers dict |
| `test_notes_api.py` | `test_update_only_description` | API | PUT partial semantics | `api_client`, `auth_token` | regression | H | **H** — expects `resp.json()["data"]["id"]` (differs from `_note_id` helper) |
| `test_notes_api.py` | `test_delete_all_notes` | API | Mass delete | `api_client`, `auth_token` | regression | H | **H** — wipes **all** notes for **config user** |
| `test_user_api.py` | `test_update_profile_success` | API | PATCH profile | `api_client`, `auth_token` | smoke | M | **M** |
| `test_user_api.py` | `test_update_profile_no_auth` | API | PATCH 401 | `api_client` | regression | L | L |
| `test_user_api.py` | `test_change_password_success` | API | POST change-password | `api_client` | regression | H | **H** — may affect shared `auth_token` account |
| `test_user_api.py` | `test_change_password_wrong_old` | API | Negative change pwd | `api_client` | regression | M | L |
| `test_user_api.py` | `test_change_password_mismatch` | API | Mismatch confirm | `api_client` | regression | M | M |
| `test_user_api.py` | `test_get_profile_after_update` | API | Read-after-write | `api_client`, `auth_token` | regression | M | M |
| `test_user_api.py` | `test_login_after_password_change` | API | Login after pwd change | `api_client` | regression | H | **H** |
| `test_user_api.py` | `test_access_after_logout` | API | Token invalid after logout | `api_client` | regression | M | L |
| `test_user_api.py` | `test_register_empty_name` | API | Register 400 | `api_client` | regression | L | L |
| `test_user_api.py` | `test_create_note_after_relogin` | API | Token after double login | `api_client` | regression | M | M |
| `test_user_api.py` | `test_profile_fields_present` | API | Profile schema | `api_client`, `auth_token` | regression | M | M |
| `test_user_api.py` | `test_note_response_fields` | API | POST note schema | `api_client`, `auth_token` | regression | M | M |
| `test_user_api.py` | `test_delete_account` | API | DELETE account | `api_client` | regression | H | **H** — destructive; may skip on 404 |

### 1.2 UI tests (`tests/ui/`)

| Test file | Test function | Type | Feature | Fixtures | Priority | Complexity | Stability risk |
|-----------|----------------|------|---------|----------|----------|------------|----------------|
| `test_login.py` | `test_valid_login` | UI | Happy-path login | `driver` | smoke | M | **M** — ads, redirect timing |
| `test_login.py` | `test_invalid_password` | UI | Wrong password error | `driver` | regression | M | M |
| `test_login.py` | `test_invalid_username` | UI | Bad email format | `driver` | regression | M | M |
| `test_login.py` | `test_empty_username` | UI | Empty email | `driver` | regression | L | L |
| `test_login.py` | `test_empty_password` | UI | Empty password | `driver` | regression | M | L |
| `test_login.py` | `test_both_fields_empty` | UI | Both empty | `driver` | regression | L | L |
| `test_login.py` | `test_login_page_title` | UI | URL smoke | `driver` | regression | L | L |
| `test_login.py` | `test_login_redirects_to_notes` | UI | Redirect after login | `driver` | smoke | M | M |
| `test_login.py` | `test_logout_after_login` | UI | Logout flow | `driver` | smoke | H | **H** — Notes SPA + logout |
| `test_login.py` | `test_invalid_email_format` | UI | Explicit wait + error | `driver` | regression | H | M |
| `test_register.py` | `test_successful_registration` | UI | Register happy path | `driver` | regression | M | M |
| `test_register.py` | `test_mismatched_passwords` | UI | Validation | `driver` | regression | M | L |
| `test_register.py` | `test_empty_name_field` | UI | Validation | `driver` | regression | M | L |
| `test_register.py` | `test_empty_email_field` | UI | Validation | `driver` | regression | M | L |
| `test_register.py` | `test_short_password` | UI | Validation | `driver` | regression | M | L |
| `test_register.py` | `test_already_registered_email` | UI | Duplicate email | `driver` | regression | M | M — depends on config email |
| `test_register.py` | `test_register_page_loads` | UI | Smoke load | `driver` | regression | L | L |
| `test_register.py` | `test_valid_email_format_check` | UI | Field accepts input | `driver` | regression | L | L |
| `test_notes.py` | `test_create_note` | UI | Create + visible | `driver` | smoke | **H** | **H** — hybrid API/UI, React |
| `test_notes.py` | `test_note_appears_in_list` | UI | Title in list | `driver` | smoke | **H** | **H** |
| `test_notes.py` | `test_delete_note` | UI | Delete first note | `driver` | regression | **H** | **H** — may delete wrong note if list shared |
| `test_notes.py` | `test_edit_note` | UI | Edit UI or API fallback | `driver` | regression | **H** | **H** |
| `test_notes.py` | `test_empty_note_title` | UI | Client validation | `driver` | regression | M | M |
| `test_notes.py` | `test_multiple_notes` | UI | Two notes visible | `driver` | regression | **H** | **H** |
| `test_notes.py` | `test_note_persists_after_refresh` | UI | Persistence | `driver` | smoke | **H** | **H** — refresh + React |

**Inventory count:** 50 API + 25 UI = **75** tests (matches `python -m pytest -c pytest_stability.ini --collect-only`).

---

## 2. Testing strategy (why the suite looks this way)

| Topic | Simple explanation | Technical explanation |
|-------|--------------------|-------------------------|
| **API-backed UI note `save_note()`** | The website is hard to automate reliably because of ads and React timing. Creating the note on the server first makes the test stable. | `NotesPage.save_note()` calls `create_note_via_api()` which uses `requests` + token, then syncs UI via `location.assign` / re-login. Empty-title case still uses UI submit for React validation. |
| **Why Selenium-only create was unreliable** | Clicks were blocked and the page was not ready when assertions ran. | Overlays, eager page load, modal interception; mitigated by `_wait_for_react_ready`, `_dismiss_overlays`, JS clicks, and API truth. |
| **Response normalization** | Old tests expected `token` at top level; API returns nested `data`. | `_ResponseProxy.json()` merges or unwraps lists so `api_client` responses stay assertion-friendly. |
| **Function-scoped fixtures** | Each test gets a clean browser and fresh token. | Prevents cross-test pollution under **pytest-xdist** workers. |
| **Why xdist** | Faster feedback. | `-n auto` or `-n 4` trades isolation for throughput; UI risk rises with worker count. |
| **Why reruns** | One retry reduces noise from network blips. | `pytest-rerunfailures` on UI/API profiles — **stability profile removes reruns** so flakes are visible. |

---

## 3. Test execution flow maps (representative chains)

### 3.1 `test_valid_login` (UI)

```
pytest schedules test
    → driver fixture: launch Chrome/Firefox (eager, timeouts)
    → test_valid_login body
        → _get_valid_credentials() [read_config]
        → _login(driver, email, password)
            → LoginPage(driver)
            → login_page.open()  → driver.get(LOGIN_URL), tolerant timeout
            → enter_email / enter_password → BasePage.type_text → WebDriverWait visibility → send_keys
            → click_login → _dismiss_overlays → JS click submit → URL wait (≤30s + retry)
        → login_page.is_login_successful()  → assert URL contains notes/app, not login
    → teardown: screenshot if failed → driver.quit()
```

### 3.2 `test_create_note_success` (API)

```
api_client fixture (new APIClient session)
    → _token_from_fresh_user(api_client)
        → POST users/register  (unique email)
        → POST users/login     → resp.json() normalized → token
    → _create_note(api_client, token, title, desc)
        → api_client.post("notes", json body, headers x-auth-token)
        → _normalize_note_payload may pad short title/description
    → assert status 200
    → assert _note_id(resp) non-empty
```

### 3.3 `test_create_note` (UI)

```
driver fixture
    → login(driver)  → LoginPage open/enter/click + WebDriverWait URL contains notes/app
    → NotesPage(driver).open()  → maybe skip get if already on app → _dismiss_overlays → _wait_for_react_ready
    → click_add_note (overlay loop, JS click, modal wait)
    → enter_note_title / enter_note_description (React-safe fills, retries)
    → save_note()  → create_note_via_api (requests login+POST /notes) → assign URL → _wait_for_react_ready → _wait_for_title_in_dom
    → is_note_visible(title)  → WebDriverWait on card headers + optional API fallback
    → assert
```

---

## 4. New QA engineer learning path

1. **Read first:** [README.md](README.md) (run commands) → **§1 inventory** in this file (you are here).
2. **Easiest tests to read first:** `test_login_page_title`, `test_register_page_loads`, `test_get_all_notes_no_auth`, `test_register_missing_email`.
3. **Intermediate:** `test_auth_api.py` full file — patterns repeat (status code + optional JSON).
4. **Advanced / highest risk:** `test_notes.py`, `test_delete_all_notes`, `test_change_password_success`, `test_update_only_description`, `test_logout_after_login`.
5. **Dangerous to modify without review:** `tests/ui/conftest.py` (session cleanup), `pages/notes_page.py`, anything using **`auth_token`** that **deletes** or **changes password** for the shared config user.
6. **Debugging failed tests:** HTML report → `logs/test_<date>.log` → `reports/screenshots/<test_name>.png` → re-run single node with `-n0`.
7. **Adding new tests:** Copy marker style from neighbors; API tests prefer fresh users (`_token_from_fresh_user` pattern) over mutating shared `auth_token` user when possible.

---

## 5. Test coverage analysis

| Area | Covered | Gaps / risks |
|------|---------|----------------|
| **Auth** | Register, login, profile, logout, token errors | OAuth/third-party not applicable |
| **Notes API** | CRUD, categories, toggles, list, no-auth | Rate limits, concurrent mutations on shared token |
| **User** | Profile patch, password flows, delete account | `test_delete_account` may skip if endpoint 404 |
| **UI login** | Valid/invalid/empty, redirect, logout | Does not exhaust every HTML5 constraint combo |
| **UI register** | Happy + common negatives | Captcha (if ever added) not covered |
| **UI notes** | Create, list, delete, edit, empty title, multi, refresh | Visual regression not covered; strict DOM coupling |
| **API/UI overlap** | Same backend exercised twice | Drift if UI API path (`requests` in `NotesPage`) diverges from `APIClient` |

**High flakiness risk (monitor in stability runs):** all of `test_notes.py`, `test_logout_after_login`, shared-account API tests (`auth_token` + delete/PUT storms).

---

## 6. File: `tests/api/test_auth_api.py`

### File purpose

| Topic | Detail |
|-------|--------|
| **Why it exists** | Validates **authentication lifecycle** for the Notes API: register, login, profile read, logout. |
| **Feature / module** | `users/register`, `users/login`, `users/profile`, `users/logout`. |
| **Why important** | Every other API test depends on correct auth semantics and status codes. |

### Dependencies

| Category | Items |
|----------|--------|
| **Fixtures** | `api_client` (all tests); `auth_token` (`test_logout_success` only). |
| **Page objects** | None (API-only). |
| **Utilities** | `read_config`, `get_logger`. |
| **Helpers** | `_unique_email()`, `_auth_headers(token)`. |

### Execution type

**API only.** Mix of **smoke** (`test_login_success`) and **regression** tests. **Stability-sensitive:** `test_logout_success` uses **`auth_token`** (shared config user) — can interact badly with parallel tests that also use that user.

### Helpers (detailed)

| Helper | Purpose | Parameters | Returns |
|--------|---------|------------|---------|
| `_unique_email()` | Collision-free email | — | `api_user_<ms>@example.com` |
| `_auth_headers(token)` | Auth header dict | token string | `{"x-auth-token": token}` |

---

### `test_register_user_success`

| # | Detail |
|---|--------|
| **1. Purpose** | Prove **new user registration** succeeds with valid payload. |
| **2. Business scenario** | First-time user signs up via API. |
| **3. Why it matters** | Gate for all user-specific features. |
| **4. Preconditions** | API reachable; email not already registered (UUID minimizes collision). |
| **5. Fixtures** | `api_client`. |
| **6. Runtime flow** | Build payload → `api_client.post` → assert **201**. |
| **7. Step-by-step API** | `POST {base}/users/register` JSON `{name,email,password}`. |
| **8. Page objects** | None. |
| **9. Locators** | N/A. |
| **10. Assertions** | `status_code == 201`. |
| **11. Expected** | **201** Created. |
| **12. Failure** | 409 if email collision; 4xx/5xx if API down or payload rejected. |
| **13. Flakiness** | Very low (unique email). |
| **14. Debug** | `APIClient` logs full response body in `logs/`. |
| **15. Real-world** | Contract test for onboarding API. |
| **16. Beginner** | “POST register → expect 201.” |
| **17. Advanced** | Uses normalized client; body logged — watch PII in real envs. |

---

### `test_register_duplicate_email`

| # | Detail |
|---|--------|
| **1. Purpose** | Second registration with same email → **409** conflict. |
| **2. Business scenario** | User tries to create account with email already in system. |
| **3. Why it matters** | Prevents duplicate identities. |
| **4. Preconditions** | API up; `_unique_email()` produces unused email for first call. |
| **5. Fixtures used** | `api_client`. |
| **6. Runtime flow** | POST register (success) → POST register identical body → assert second status. |
| **7. API flow** | Two `POST {base}/users/register` with same JSON payload. |
| **8. Page object methods** | None. |
| **9. HTTP/locators** | N/A. |
| **10. Assertions** | Second response `status_code == 409`. |
| **11. Expected** | **409 Conflict** on duplicate. |
| **12. Failure** | If first POST fails, second might be 201 — false negative/positive interplay. |
| **13. Flakiness** | Low under normal API health. |
| **14. Screenshots/logs** | Compare both bodies in logs. |
| **15. Real-world** | Identity uniqueness enforcement. |
| **16. Beginner** | “Same email twice should error.” |
| **17. Advanced** | Uses millisecond email from `_unique_email` — collision only if clock rolls back or extreme reuse. |

---

### `test_register_missing_email`

| # | Detail |
|---|--------|
| **1. Purpose** | Verify API rejects registration when **`email`** is omitted. |
| **2. Business scenario** | User submits register form without email. |
| **3. Why it matters** | Prevents anonymous/invalid accounts; enforces contract. |
| **4. Preconditions** | API up; `default_password` present in config. |
| **5. Fixtures used** | `api_client`. |
| **6. Runtime flow** | Build payload `{name, password}` only → POST → assert. |
| **7. API flow** | `POST {base}/users/register` JSON `{"name":"API User","password":<default_password>}` — **no email key**. Default `Content-Type: application/json`. |
| **8. Page object methods** | None. |
| **9. HTTP/locators** | No `x-auth-token`. |
| **10. Assertions** | `resp.status_code == 400`. |
| **11. Expected** | **400 Bad Request**. |
| **12. Failure** | 500 server error; API changed to different status. |
| **13. Flakiness** | Low. |
| **14. Screenshots/logs** | `APIClient` logs request + full response text in `logs/test_<date>.log`. |
| **15. Real-world** | Input validation contract for mobile/web clients. |
| **16. Beginner** | “If we forget the email, the server should say no.” |
| **17. Advanced** | Response body shape not asserted — only status. |

### `test_register_missing_password`

| # | Detail |
|---|--------|
| **1. Purpose** | Verify API rejects registration when **`password`** is omitted. |
| **2. Business scenario** | User submits register without password. |
| **3. Why it matters** | Security baseline — no empty-password accounts. |
| **4. Preconditions** | API up; unique email from `_unique_email()`. |
| **5. Fixtures used** | `api_client`. |
| **6. Runtime flow** | Payload `{name, email}` only → POST → assert 400. |
| **7. API flow** | `POST {base}/users/register` JSON `{"name":"API User","email":<unique>}`. |
| **8. Page object methods** | None. |
| **9. HTTP/locators** | No auth header. |
| **10. Assertions** | `resp.status_code == 400`. |
| **11. Expected** | **400**. |
| **12. Failure** | If server accepts empty password (bug), test fails — good. |
| **13. Flakiness** | Low. |
| **14. Screenshots/logs** | Same logging as all `APIClient` calls. |
| **15. Real-world** | OWASP-style validation coverage. |
| **16. Beginner** | “Can’t register without a password.” |
| **17. Advanced** | Pair with missing-email test for full required-field matrix. |

---

### `test_login_success`

| # | Detail |
|---|--------|
| **1. Purpose** | After registering a user, **login** returns **200** and a **non-empty token**. |
| **2. Business scenario** | New user returns to app and signs in. |
| **3. Why it matters** | Unlocks all authenticated API/UI flows. |
| **4. Preconditions** | `default_password` in config; register endpoint healthy. |
| **5. Fixtures used** | `api_client`. |
| **6. Runtime flow** | `POST users/register` → `POST users/login` → parse JSON → assert. |
| **7. API flow** | `POST {base}/users/register` then `POST {base}/users/login` with same email/password; no auth header on either. |
| **8. Page object methods** | None. |
| **9. HTTP/locators** | JSON bodies only; `Content-Type` from session. |
| **10. Assertions** | Login `status_code == 200`; `resp.json().get("token") or resp.json().get("access_token")` truthy. |
| **11. Expected** | Session token issued. |
| **12. Failure** | Register 4xx/5xx; login missing token in body — assertion fails. |
| **13. Flakiness** | Low (fresh user). |
| **14. Screenshots/logs** | Full login response logged — contains token (sensitive). |
| **15. Real-world** | Core smoke for auth pipeline. |
| **16. Beginner** | “Sign up then sign in — you get a token.” |
| **17. Advanced** | `_ResponseProxy` may promote nested `data.token` so `.get("token")` still works. |

---

### `test_login_wrong_password`

| # | Detail |
|---|--------|
| **1. Purpose** | Valid email + wrong password → **401**. |
| **2. Business scenario** | User mistypes password. |
| **3. Why it matters** | Ensures failed auth does not leak tokens. |
| **4. Preconditions** | `wrong_password` in `config.ini`; valid `username` email. |
| **5. Fixtures used** | `api_client`. |
| **6. Runtime flow** | Register fresh user with good password → login with `wrong_password`. |
| **7. API flow** | `POST users/register` then `POST users/login` with mismatched password. |
| **8. Page object methods** | None. |
| **9. HTTP/locators** | No `x-auth-token` on login. |
| **10. Assertions** | `resp.status_code == 401`. |
| **11. Expected** | Unauthorized. |
| **12. Failure** | If server returns 400 instead of 401, assertion fails — document actual API. |
| **13. Flakiness** | Low. |
| **14. Screenshots/logs** | Response body logged. |
| **15. Real-world** | Core auth negative path. |
| **16. Beginner** | “Wrong password should not log you in.” |
| **17. Advanced** | Uses config user email only for address; password comes from `[api] wrong_password`. |

### `test_login_invalid_email`

| # | Detail |
|---|--------|
| **1. Purpose** | Malformed email string on login → **400**. |
| **2. Business scenario** | Client sends garbage email. |
| **3. Why it matters** | Validation before hitting credential store. |
| **4. Preconditions** | `default_password` in config. |
| **5. Fixtures used** | `api_client`. |
| **6. Runtime flow** | Single `POST users/login` with `email=notanemail`. |
| **7. API flow** | `POST {base}/users/login` JSON `{"email":"notanemail","password":<default_password>}`. |
| **8. Page object methods** | None. |
| **9. HTTP/locators** | N/A. |
| **10. Assertions** | `status_code == 400`. |
| **11. Expected** | Validation error. |
| **12. Failure** | Server returns 401 instead — test would fail. |
| **13. Flakiness** | Low. |
| **14. Screenshots/logs** | Logged response. |
| **15. Real-world** | Prevents junk traffic. |
| **16. Beginner** | “Not an email → server rejects.” |
| **17. Advanced** | Complements UI `test_invalid_email_format`. |

### `test_get_profile_success`

| # | Detail |
|---|--------|
| **1. Purpose** | Authenticated `GET profile` returns profile with **email** field. |
| **2. Business scenario** | Logged-in user opens profile. |
| **3. Why it matters** | Downstream features need stable profile schema. |
| **4. Preconditions** | Register+login succeeds. |
| **5. Fixtures used** | `api_client`. |
| **6. Runtime flow** | Register → login → parse token from multiple possible JSON shapes → GET profile. |
| **7. API flow** | `POST users/register` → `POST users/login` → `GET users/profile` with `x-auth-token`. |
| **8. Page object methods** | None. |
| **9. HTTP/locators** | Header `_auth_headers(token)`. |
| **10. Assertions** | GET **200**; `resp.json().get("email")` truthy. |
| **11. Expected** | Profile JSON includes email (normalized top-level). |
| **12. Failure** | `pytest.skip` if login has no token. |
| **13. Flakiness** | Low (fresh user). |
| **14. Screenshots/logs** | Full profile body may be logged — PII in real systems. |
| **15. Real-world** | Session validation + user context. |
| **16. Beginner** | “After login we can read who we are.” |
| **17. Advanced** | Manual token extraction duplicates `auth_token` fixture logic — historical pattern in file. |

### `test_get_profile_no_token`

| # | Detail |
|---|--------|
| **1. Purpose** | `GET users/profile` without auth → **401**. |
| **2. Business scenario** | Anonymous access to protected resource. |
| **3. Why it matters** | Security gate. |
| **4. Preconditions** | None. |
| **5. Fixtures used** | `api_client`. |
| **6. Runtime flow** | Single GET with default session headers only (no `x-auth-token`). |
| **7. API flow** | `GET {base}/users/profile`. |
| **8. Page object methods** | None. |
| **9. HTTP/locators** | No `x-auth-token`. |
| **10. Assertions** | `status_code == 401`. |
| **11. Expected** | Unauthorized. |
| **12. Failure** | 403/404 if API changes — update test. |
| **13. Flakiness** | Low. |
| **14. Screenshots/logs** | Response logged. |
| **15. Real-world** | OWASP authz baseline. |
| **16. Beginner** | “No token → no profile.” |
| **17. Advanced** | Session default headers still include `Content-Type`; token absent is key. |

### `test_get_profile_invalid_token`

| # | Detail |
|---|--------|
| **1. Purpose** | Garbage token on profile GET → **401** and some error payload/text. |
| **2. Business scenario** | Expired/tampered token. |
| **3. Why it matters** | Client error messaging for support/debug. |
| **4. Preconditions** | None. |
| **5. Fixtures used** | `api_client`. |
| **6. Runtime flow** | GET with `x-auth-token: invalid.token.value` → parse JSON safely → assert message keys. |
| **7. API flow** | `GET users/profile` headers `{"x-auth-token":"invalid.token.value"}`. |
| **8. Page object methods** | None. |
| **9. HTTP/locators** | Custom invalid token string. |
| **10. Assertions** | `401`; `data.get("message") or data.get("error") or resp.text` truthy. |
| **11. Expected** | Unauthorized + non-empty error signal. |
| **12. Failure** | Empty body on 401 — assertion fails. |
| **13. Flakiness** | Low. |
| **14. Screenshots/logs** | Logs raw text. |
| **15. Real-world** | Helps API consumers show errors. |
| **16. Beginner** | “Fake token should be rejected with a message.” |
| **17. Advanced** | Uses try/except on `resp.json()` — resilient to HTML error pages. |

---

### `test_logout_success`

| # | Detail |
|---|--------|
| **1. Purpose** | Authenticated **DELETE** logout returns **200**. |
| **5. Fixtures** | `api_client`, **`auth_token`** (config user). |
| **7. API** | `DELETE users/logout` + `x-auth-token: <auth_token>`. |
| **10. Assertions** | **200**. |
| **13. Flakiness** | **Medium** — uses **shared** account; parallel tests may race. |
| **17. Advanced** | Immediately after, another test’s `auth_token` may still be “old” token in same worker — fixture is per test so OK per worker; cross-worker still hits same server user. |

---

### `test_logout_no_token`

| # | Detail |
|---|--------|
| **7. API** | `DELETE users/logout` no headers. |
| **10. Assertions** | **401** + message presence. |

---

## 7. File: `tests/api/test_notes_api.py`

### File purpose

Validates **Notes CRUD** and related behaviors (`GET/POST/PUT/PATCH/DELETE` on `notes`).

### Dependencies

| Category | Items |
|----------|--------|
| **Fixtures** | `api_client` always; `auth_token` on many tests. |
| **Helpers** | `_auth_headers`, `_token_from_fresh_user`, `_create_note`, `_note_id`. |

### Helpers

| Helper | Behavior |
|--------|----------|
| `_token_from_fresh_user` | Register+login new user; `pytest.skip` if no token. |
| `_create_note` | Pads short title/desc (mirrors client normalization intent) then `POST notes`. |
| `_note_id(resp)` | Parses `id` from `data.id` or top-level (handles wrapped/unwrapped). |

---

### `test_create_note_success`

| # | Detail |
|---|--------|
| **7. API** | Fresh user token → `POST notes` with unique title. |
| **10. Assertions** | **200** + id present via `_note_id`. |
| **17. Advanced** | `_create_note` pads title/desc < 4 chars — overlaps conceptually with `APIClient._normalize_note_payload`. |

---

### `test_create_note_missing_title`

| # | Detail |
|---|--------|
| **5. Fixtures** | `auth_token` (**config user**). |
| **7. API** | `POST notes` body **without** title. |
| **10. Assertions** | **400**. |
| **13. Flakiness** | Medium if shared user note list affects server state. |

---

### `test_create_note_missing_description`

| # | Detail |
|---|--------|
| **6** | Uses `_token_from_fresh_user` (not `auth_token` fixture). |
| **7. API** | `POST notes` with title only. |
| **10. Assertions** | **400**. |

---

### `test_create_note_no_auth`

| # | Detail |
|---|--------|
| **7. API** | `POST notes` **no** `x-auth-token`. |
| **10. Assertions** | **401**. |

---

### `test_get_all_notes`

| # | Detail |
|---|--------|
| **7. API** | Fresh user → create note (skip if create fails) → `GET notes`. |
| **10. Assertions** | **200**; JSON is `list` or `dict`. |

---

### `test_get_all_notes_no_auth`

| # | Detail |
|---|--------|
| **7. API** | `GET notes` without token. |
| **10. Assertions** | **401**. |

---

### `test_get_note_by_id`

| # | Detail |
|---|--------|
| **7. API** | Create → extract id → `GET notes/{id}`. |
| **10. Assertions** | **200**. |

---

### `test_get_note_invalid_id`

| # | Detail |
|---|--------|
| **7. API** | `GET notes/invalidid` with token. |
| **10. Assertions** | **400 or 404** (server-dependent). |

---

### `test_get_note_no_auth`

| # | Detail |
|---|--------|
| **7. API** | Create note → `GET notes/{id}` **without** token. |
| **10. Assertions** | **401**. |

---

### `test_update_note_success`

| # | Detail |
|---|--------|
| **7. API** | `PUT notes/{id}` full body `{title, description, category, completed}`. |
| **10. Assertions** | **200**. |

---

### `test_update_note_missing_title`

| # | Detail |
|---|--------|
| **7. API** | Fresh user → create → `PUT` missing title field. |
| **10. Assertions** | **400**. |

---

### `test_update_note_no_auth`

| # | Detail |
|---|--------|
| **7. API** | `PUT notes/{id}` **no** headers. |
| **10. Assertions** | **401**. |

---

### `test_update_note_invalid_id`

| # | Detail |
|---|--------|
| **7. API** | `PUT notes/000...` bogus ObjectId-style id. |
| **10. Assertions** | **400 or 404**. |

---

### `test_delete_note_success`

| # | Detail |
|---|--------|
| **1. Purpose** | Delete an existing note by id → **200**. |
| **2. Business scenario** | User removes a note. |
| **3. Why it matters** | Core destructive operation; must be authorized. |
| **4. Preconditions** | `auth_token` valid; note creation succeeds. |
| **5. Fixtures used** | `api_client`, `auth_token`. |
| **6. Runtime flow** | `_create_note` → read id → `DELETE notes/{id}` with token. |
| **7. API flow** | `POST notes` (setup) → `DELETE {base}/notes/{id}` header `x-auth-token`. |
| **8. Page object methods** | None. |
| **9. HTTP/locators** | Uses `_auth_headers(auth_token)`. |
| **10. Assertions** | DELETE returns **200**. |
| **11. Expected** | Note removed server-side. |
| **12. Failure** | 404 if id wrong; 401 if token bad. |
| **13. Flakiness** | **Medium–High** — mutates **shared config user** note list under parallel runs. |
| **14. Screenshots/logs** | API logs. |
| **15. Real-world** | Data deletion must be correct and scoped. |
| **16. Beginner** | “Delete my note.” |
| **17. Advanced** | Prefer isolated user pattern like `_token_from_fresh_user` for delete tests to avoid cross-test coupling. |

### `test_delete_note_no_auth`

| # | Detail |
|---|--------|
| **1. Purpose** | DELETE without token → **401**. |
| **2. Business scenario** | Anonymous delete attempt. |
| **3. Why it matters** | Prevents unauthorized data loss. |
| **4. Preconditions** | Note created with valid token first. |
| **5. Fixtures used** | `api_client`, `auth_token` (only for setup create). |
| **6. Runtime flow** | Create note → DELETE same URL **without** `x-auth-token`. |
| **7. API flow** | `DELETE {base}/notes/{id}` no auth header. |
| **8. Page object methods** | None. |
| **9. HTTP/locators** | N/A. |
| **10. Assertions** | **401**. |
| **11. Expected** | Rejected. |
| **12. Failure** | If id invalid, might get 404 — different from 401. |
| **13. Flakiness** | Medium — depends on create succeeding. |
| **14. Screenshots/logs** | Logged. |
| **15. Real-world** | Authz for destructive verbs. |
| **16. Beginner** | “Can’t delete without logging in.” |
| **17. Advanced** | Create uses `_create_note` which may pad short titles via helper. |

### `test_delete_note_invalid_id`

| # | Detail |
|---|--------|
| **1. Purpose** | DELETE with malformed id → **400 or 404**. |
| **2. Business scenario** | Client sends bad id. |
| **3. Why it matters** | Robust error handling. |
| **4. Preconditions** | `auth_token` valid. |
| **5. Fixtures used** | `api_client`, `auth_token`. |
| **6. Runtime flow** | `DELETE notes/badid` with token. |
| **7. API flow** | `DELETE {base}/notes/badid` + `x-auth-token`. |
| **8. Page object methods** | None. |
| **9. HTTP/locators** | Literal path `badid`. |
| **10. Assertions** | status in `(400, 404)`. |
| **11. Expected** | Server-dependent validation/not-found. |
| **12. Failure** | If API returns 500 — test fails. |
| **13. Flakiness** | Low. |
| **14. Screenshots/logs** | Logged. |
| **15. Real-world** | Defensive API design. |
| **16. Beginner** | “Bad id should error.” |
| **17. Advanced** | Accepts two statuses because practice API may map differently. |

---

### `test_create_multiple_notes`

| # | Detail |
|---|--------|
| **1. Purpose** | List length increases by **≥3** after creating three notes. |
| **6–7** | Dedicated new user → `GET notes` before/after; parses list whether JSON is list or `{data:[]}`. |
| **10. Assertions** | `len(after) >= len(before)+3`. |
| **17. Advanced** | Isolates user to avoid cross-test interference — **best practice** pattern. |

---

### `test_note_category_home`

| # | Detail |
|---|--------|
| **1. Purpose** | `POST notes` with `category=Home` succeeds (**200**). |
| **2. Business scenario** | User files note under Home. |
| **3. Why it matters** | Category enum accepted by API. |
| **4. Preconditions** | `auth_token` non-empty. |
| **5. Fixtures used** | `api_client`, `auth_token`. |
| **6. Runtime flow** | `_create_note(..., category="Home")` → assert. |
| **7. API flow** | `POST notes` JSON includes `"category":"Home"`. |
| **8. Page object methods** | None. |
| **9. HTTP/locators** | `x-auth-token` from fixture. |
| **10. Assertions** | `status_code == 200`. |
| **11. Expected** | Created. |
| **12. Failure** | 400 if category invalid on server. |
| **13. Flakiness** | Medium on shared user quota. |
| **14. Screenshots/logs** | API logs. |
| **15. Real-world** | Taxonomy / filtering features. |
| **16. Beginner** | “Home category works.” |
| **17. Advanced** | Title `"Home"` may be padded by `_create_note` if length rules apply. |

### `test_note_category_work`

| # | Detail |
|---|--------|
| **1. Purpose** | `POST notes` with `category=Work` returns **200**. |
| **2. Business scenario** | User categorizes note as Work. |
| **3. Why it matters** | Validates enum value distinct from Home/Personal. |
| **4. Preconditions** | `auth_token` non-empty. |
| **5. Fixtures used** | `api_client`, `auth_token`. |
| **6. Runtime flow** | `_create_note(api_client, auth_token, "Work", "D", category="Work")` → assert. |
| **7. API flow** | `POST {base}/notes` body `title`, `description`, `"category":"Work"` + `x-auth-token`. |
| **8. Page object methods** | None. |
| **9. HTTP/locators** | `_auth_headers(auth_token)`. |
| **10. Assertions** | `resp.status_code == 200`. |
| **11. Expected** | Note created under Work. |
| **12. Failure** | 400 if category not allowed. |
| **13. Flakiness** | Medium on shared user. |
| **14. Screenshots/logs** | APIClient logs. |
| **15. Real-world** | Workspace / GTD style categorization. |
| **16. Beginner** | “Work category is accepted.” |
| **17. Advanced** | Title `"Work"` may be length-padded inside `_create_note` like other short titles. |

### `test_note_category_personal`

| # | Detail |
|---|--------|
| **1. Purpose** | `POST notes` with `category=Personal` returns **200**. |
| **2. Business scenario** | User categorizes note as Personal. |
| **3. Why it matters** | Third category value in UI/API taxonomy. |
| **4. Preconditions** | `auth_token` non-empty. |
| **5. Fixtures used** | `api_client`, `auth_token`. |
| **6. Runtime flow** | `_create_note(..., "Personal", "D", category="Personal")` → assert. |
| **7. API flow** | `POST {base}/notes` with `"category":"Personal"`. |
| **8. Page object methods** | None. |
| **9. HTTP/locators** | `x-auth-token` header. |
| **10. Assertions** | `status_code == 200`. |
| **11. Expected** | Created. |
| **12. Failure** | 400/401 per server rules. |
| **13. Flakiness** | Medium on shared user. |
| **14. Screenshots/logs** | Logged request/response. |
| **15. Real-world** | Privacy-oriented grouping. |
| **16. Beginner** | “Personal category works.” |
| **17. Advanced** | Run after other category tests on same user — note list grows; still only checks HTTP 200 not list order. |

---

### `test_toggle_note_complete`

| # | Detail |
|---|--------|
| **1. Purpose** | `PATCH` note to `completed: true` → **200**. |
| **2. Business scenario** | User marks task done. |
| **3. Why it matters** | Partial update path distinct from PUT full body. |
| **4. Preconditions** | Fresh user + created note with id. |
| **5. Fixtures used** | `api_client` only. |
| **6. Runtime flow** | `_token_from_fresh_user` → create → `PATCH notes/{id}` `{completed:true}`. |
| **7. API flow** | `PATCH {base}/notes/{id}` JSON body one key; `x-auth-token`. |
| **8. Page object methods** | None. |
| **9. HTTP/locators** | Uses `_auth_headers` with token from fresh user. |
| **10. Assertions** | `status_code == 200`. |
| **11. Expected** | Toggle persisted. |
| **12. Failure** | Skip if create fails or no id. |
| **13. Flakiness** | Low (isolated user). |
| **14. Screenshots/logs** | Standard API logging. |
| **15. Real-world** | Checkbox sync mobile/web. |
| **16. Beginner** | “Mark complete via API.” |
| **17. Advanced** | Uses `api_client.patch` — ensure server supports PATCH semantics. |

### `test_toggle_note_incomplete`

| # | Detail |
|---|--------|
| **1. Purpose** | After marking complete, PATCH back to **`completed: false`** → **200**. |
| **2. Business scenario** | User unchecks completed task. |
| **3. Why it matters** | Bidirectional toggle. |
| **4. Preconditions** | Same as complete test. |
| **6. Runtime flow** | Create → PATCH `true` → PATCH `false` → assert last **200**. |
| **7. API flow** | Two sequential `PATCH` calls on same id. |
| **10. Assertions** | Final PATCH **200**. |
| **13. Flakiness** | Low. |
| **16. Beginner** | “Uncheck works too.” |
| **17. Advanced** | Stateful sequence — fails if first PATCH fails mid-test. |

---

### `test_note_title_max_length`

| # | Detail |
|---|--------|
| **5. Fixtures** | `auth_token` — **bug/footgun:** passes raw token string into `headers=` dict; works because value is truthy. |
| **7. API** | `POST /notes` with 500-char title (leading slash on endpoint — normalized). |
| **10. Assertions** | Status in **[200, 400]** — documents **either** server policy. |
| **17. Advanced** | Accepts two outcomes — good for unknown server limits; weaker as strict contract test. |

---

### `test_update_only_description`

| # | Detail |
|---|--------|
| **7. API** | `POST /notes` then `PUT /notes/{id}` with same title, new description. |
| **10. Assertions** | Create **200**; update **200**; `update_resp.json()["data"]["description"]` equals expected. |
| **12. Failure** | Will **fail** if `_ResponseProxy` flattens such that `data` is not nested as test expects — maintainer must align assertion with actual `json()` shape. |
| **17. Advanced** | Uses **leading-slash** endpoints and **raw** `["data"]` access — inconsistent with `_note_id` helper elsewhere in same file. |

---

### `test_delete_all_notes`

| # | Detail |
|---|--------|
| **1. Purpose** | Deletes **every** note returned for **`auth_token` user** (config account). |
| **13. Flakiness** | **HIGH** for parallel + UI tests using same account. |
| **15. Real-world** | Dangerous in shared env — essentially “wipe user data”. |
| **17. Advanced** | After loop, asserts `GET notes` still **200** (list accessible), not that list is empty. |

---

## 8. File: `tests/api/test_user_api.py`

### File purpose

Covers **profile update**, **password change**, **logout access rules**, **register validation edge**, **note after re-login**, **schema checks**, **delete account**.

### Dependencies

| Fixtures | Helpers |
|----------|---------|
| `api_client`, `auth_token` (subset) | `_auth_headers`, `_new_user` |

### `_new_user(api_client)`

Returns `(email, password, token)` by registering + logging in a **new** user — reduces collision with config user for password-change flows.

---

### `test_update_profile_success`

| # | Detail |
|---|--------|
| **7. API** | `PATCH users/profile` with `{name}` + token. |
| **10. Assertions** | **200**. |
| **13. Flakiness** | Medium — mutates profile of **shared** `auth_token` user. |

---

### `test_update_profile_no_auth`

| # | Detail |
|---|--------|
| **7. API** | `PATCH users/profile` no token. |
| **10. Assertions** | **401**. |

---

### `test_change_password_success`

| # | Detail |
|---|--------|
| **7. API** | `_new_user` → `POST users/change-password` with current/new/confirm. |
| **10. Assertions** | Status in **(200, 400)** — acknowledges policy variance. |
| **13. Flakiness** | High if run order interacts with `auth_token` user (separate user here mitigates). |

---

### `test_change_password_wrong_old`

| # | Detail |
|---|--------|
| **1. Purpose** | Change password with incorrect `currentPassword` → **400**. |
| **2. Business scenario** | Attacker or mistaken user enters wrong old password. |
| **3. Why it matters** | Prevents unauthorized password rotation. |
| **4. Preconditions** | `_new_user` succeeds. |
| **5. Fixtures used** | `api_client`. |
| **6. Runtime flow** | `_new_user` → `POST users/change-password` with wrong `currentPassword`. |
| **7. API flow** | `POST {base}/users/change-password` JSON `currentPassword`, `newPassword`, `confirmPassword` + `x-auth-token`. |
| **8. Page object methods** | None. |
| **9. HTTP/locators** | `_auth_headers(token)`. |
| **10. Assertions** | **400**. |
| **11. Expected** | Rejected. |
| **12. Failure** | If API returns 401 instead — update expectation. |
| **13. Flakiness** | Low (new user). |
| **14. Screenshots/logs** | API logs. |
| **15. Real-world** | Account security. |
| **16. Beginner** | “Wrong old password → error.” |
| **17. Advanced** | Uses `read_config` for wrong/new password strings. |

### `test_change_password_mismatch`

| # | Detail |
|---|--------|
| **1. Purpose** | `newPassword` ≠ `confirmPassword` → server responds **200 or 400** (accepted ambiguity). |
| **2. Business scenario** | User typo in confirm field. |
| **3. Why it matters** | UX validation — but test allows both outcomes. |
| **4. Preconditions** | `_new_user` works. |
| **5. Fixtures used** | `api_client`. |
| **6. Runtime flow** | `_new_user` → POST change-password with mismatched confirm. |
| **7. API flow** | Same endpoint; `confirmPassword` set to `wrong_password` from config. |
| **10. Assertions** | `status_code in (200, 400)`. |
| **11. Expected** | Either policy accepted by test author. |
| **12. Failure** | If API returns 422 — may need widening assertion. |
| **13. Flakiness** | Low. |
| **17. Advanced** | **Loose assertion** — weaker regression signal; tighten when API contract is fixed. |

---

### `test_get_profile_after_update`

| # | Detail |
|---|--------|
| **7. API** | `PATCH profile` then `GET profile`. |
| **10. Assertions** | GET **200** (does not assert name equality in body). |

---

### `test_login_after_password_change`

| # | Detail |
|---|--------|
| **7. API** | Change password for `_new_user` then `POST login` with new password. |
| **10. Assertions** | Status in **(200,401,400)** — loose assertion. |
| **17. Advanced** | Looseness avoids brittleness but **weakens** regression signal — consider tightening once API behavior is fixed. |

---

### `test_access_after_logout`

| # | Detail |
|---|--------|
| **7. API** | `_new_user` → `DELETE logout` → `GET profile` with same token → expect **401**. |

---

### `test_register_empty_name`

| # | Detail |
|---|--------|
| **7. API** | `POST users/register` without `name`. |
| **10. Assertions** | **400**. |

---

### `test_create_note_after_relogin`

| # | Detail |
|---|--------|
| **7. API** | Register → login twice → extract token manually → `POST notes`. |
| **10. Assertions** | **200**. |

---

### `test_profile_fields_present`

| # | Detail |
|---|--------|
| **10. Assertions** | `id`, `name`, `email` all truthy in `GET profile` JSON. |

---

### `test_note_response_fields`

| # | Detail |
|---|--------|
| **10. Assertions** | `POST notes` JSON has `id` at top level **or** under `data.id`. |

---

### `test_delete_account`

| # | Detail |
|---|--------|
| **7. API** | `_new_user` → `DELETE users/delete-account` with token. |
| **10. Assertions** | **200** or `pytest.skip` if **404** (endpoint absent). |
| **15. Real-world** | Destructive — isolated user reduces blast radius. |

---

## 9. File: `tests/ui/test_login.py`

### File purpose

Validates **Notes web login** at `/notes/app/login` using **`LoginPage`** (and **`NotesPage`** for logout test).

### Dependencies

| Fixtures | Page objects | Utilities |
|----------|--------------|-----------|
| `driver` | `LoginPage`, `NotesPage` | `read_config`, `get_logger`, Selenium `WebDriverWait`/`EC`/`By` in one test |

### Helpers

| Helper | Detail |
|--------|--------|
| `_get_valid_credentials()` | Reads `[api] username/password`; used for “real” login tests. |
| `_login(driver, email, password)` | `LoginPage` flow: `open` → `enter_email` → `enter_password` → `click_login`. |

### Execution type

**UI**, smoke + regression mix. **Hybrid:** none except logout uses `NotesPage`.

---

### `test_valid_login`

| # | Detail |
|---|--------|
| **1. Purpose** | Valid credentials → lands on Notes app. |
| **5. Fixtures** | `driver`. |
| **6–8** | `_login` → `is_login_successful()` URL check. |
| **9. Locators (indirect)** | `EMAIL_INPUT`, `PASSWORD_INPUT`, `LOGIN_BUTTON` via page methods. |
| **10. Assertions** | `is_login_successful()` True. |
| **12. Failure** | Wrong creds in `config.ini`; ads block login; timeout on redirect. |
| **13. Flakiness** | **Medium** — external site + overlays. |
| **14. Debug** | Screenshot on failure; logs from `LoginPage` and driver fixture. |
| **16. Beginner** | “Logs in like a user and checks URL.” |
| **17. Advanced** | Skips if email contains `(` or creds empty — guard against bad placeholder config. |

---

### `test_invalid_password`

| # | Detail |
|---|--------|
| **10. Assertions** | `LoginPage.is_displayed(ERROR_MESSAGE)` after wrong password. |
| **13. Flakiness** | Toast timing — mitigated by custom `is_displayed` on `LoginPage`. |

---

### `test_invalid_username`

| # | Detail |
|---|--------|
| **1. Purpose** | Non-email string cannot authenticate; stays on login URL. |
| **2. Business scenario** | User types malformed email. |
| **3. Why it matters** | Client-side/server-side validation UX. |
| **4. Preconditions** | None (uses literal invalid email). |
| **5. Fixtures used** | `driver`. |
| **6. Runtime flow** | `_login(driver, "invalid-email-format", "somepassword")` → assertions. |
| **7. Selenium/API flow** | `LoginPage.open` → `type_text` email/password → `click_login` (overlays + JS click + URL wait). |
| **8. Page object methods** | `LoginPage.open`, `enter_email`, `enter_password`, `click_login`, `is_login_successful`. |
| **9. Indirect locators** | `EMAIL_INPUT`, `PASSWORD_INPUT`, `LOGIN_BUTTON`, broad error locators if toasts appear. |
| **10. Assertions** | `not is_login_successful()`; `"login" in driver.current_url.lower()`. |
| **11. Expected** | Remain on or return to login experience. |
| **12. Failure** | Redirect bug allows bad login — security issue. |
| **13. Flakiness** | Medium — URL timing. |
| **14. Screenshots/logs** | Screenshot on failure; `LoginPage` logs. |
| **15. Real-world** | Prevents garbage identifiers. |
| **16. Beginner** | “Bad email should not open Notes.” |
| **17. Advanced** | Does not assert toast text — only URL + `is_login_successful` false. |

### `test_empty_username`

| # | Detail |
|---|--------|
| **1. Purpose** | Empty email field cannot log in; URL stays login. |
| **2. Business scenario** | User submits blank email. |
| **3. Why it matters** | Required field enforcement. |
| **4. Preconditions** | None. |
| **5. Fixtures used** | `driver`. |
| **6. Runtime flow** | `_login(driver, "", "somepassword")`. |
| **7. Selenium flow** | Same as invalid username with empty string email. |
| **8. Page object methods** | Same `LoginPage` flow. |
| **9. Indirect locators** | Same as other login tests. |
| **10. Assertions** | `not is_login_successful()`; URL contains `login`. |
| **11. Expected** | Blocked login. |
| **12. Failure** | HTML5 validation might auto-block submit — still expect no success URL. |
| **13. Flakiness** | Medium. |
| **14. Screenshots/logs** | Screenshot + logs. |
| **15. Real-world** | Form validation parity. |
| **16. Beginner** | “Empty email → no login.” |
| **17. Advanced** | May hit `LoginPage.is_displayed` indirectly in other tests but this one uses URL assertion. |

### `test_empty_password`

| # | Detail |
|---|--------|
| **1. Purpose** | Empty password cannot log in; stays on login. |
| **2. Business scenario** | User clears password. |
| **3. Why it matters** | Prevents empty-credential auth attempts. |
| **4. Preconditions** | `[api] username` present in config. |
| **5. Fixtures used** | `driver`. |
| **6. Runtime flow** | Read username → `_login(driver, email, "")`. |
| **7. Selenium flow** | `type_text` password with empty string after email fill. |
| **8. Page object methods** | `LoginPage` methods. |
| **9. Indirect locators** | `PASSWORD_INPUT` cleared/filled. |
| **10. Assertions** | `not is_login_successful()`; URL has `login`. |
| **11. Expected** | Failure to reach notes app. |
| **12. Failure** | Skip if username missing. |
| **13. Flakiness** | Medium. |
| **14. Screenshots/logs** | Standard UI artifacts. |
| **15. Real-world** | Password required policy. |
| **16. Beginner** | “No password → no login.” |
| **17. Advanced** | Uses `read_config` directly for email unlike `_get_valid_credentials` in some tests. |

### `test_both_fields_empty`

| # | Detail |
|---|--------|
| **1. Purpose** | Both email and password empty → no successful login. |
| **2. Business scenario** | User clicks submit with empty form. |
| **3. Why it matters** | Double-empty edge case. |
| **4. Preconditions** | None. |
| **5. Fixtures used** | `driver`. |
| **6. Runtime flow** | `_login(driver, "", "")`. |
| **7. Selenium flow** | Both fields empty → `click_login`. |
| **8. Page object methods** | `LoginPage` full flow. |
| **9. Indirect locators** | Both inputs. |
| **10. Assertions** | `not is_login_successful()`; URL login. |
| **11. Expected** | Stay on login. |
| **12. Failure** | Browser HTML5 may prevent navigation — assertion still URL-based. |
| **13. Flakiness** | Medium. |
| **14. Screenshots/logs** | Screenshot on failure. |
| **15. Real-world** | Empty form protection. |
| **16. Beginner** | “Empty form should not log in.” |
| **17. Advanced** | Similar to single-field empties but exercises both fields together. |

---

### `test_login_page_title`

| # | Detail |
|---|--------|
| **8** | Only `open()` — minimal interaction. |
| **10. Assertions** | URL contains `notes/app/login`. |

---

### `test_login_redirects_to_notes`

| # | Detail |
|---|--------|
| **10. Assertions** | URL contains `notes/app` after `_login`. |

---

### `test_logout_after_login`

| # | Detail |
|---|--------|
| **6–8** | `_login` → `NotesPage.open()` → `logout()` → `WebDriverWait` until URL has `login` → assert. |
| **13. Flakiness** | **High** — SPA navigation + `NotesPage.logout` fallbacks. |
| **17. Advanced** | Combines **two** page objects and explicit wait — representative of hardest UI path. |

---

### `test_invalid_email_format`

| # | Detail |
|---|--------|
| **6–8** | `_login` with `notanemail` → explicit `WebDriverWait` for XPath-visible error → `is_displayed(ERROR_MESSAGE)`. |
| **13. Flakiness** | Medium — depends on DOM error visibility. |

---

## 10. File: `tests/ui/test_register.py`

### File purpose

Covers **registration** UI at `/notes/app/register` via **`RegisterPage`**.

### Helpers

| Helper | Detail |
|--------|--------|
| `_unique_email()` | `testuser_<6 hex>@test.com` for uniqueness. |

### Execution type

**UI**, regression-heavy.

---

### `test_successful_registration`

| # | Detail |
|---|--------|
| **1. Purpose** | Happy-path UI registration with unique email shows success feedback. |
| **2. Business scenario** | New user completes register form successfully. |
| **3. Why it matters** | Core onboarding UX for the web app. |
| **4. Preconditions** | `default_password` in `config.ini`; site reachable. |
| **5. Fixtures used** | `driver`. |
| **6. Runtime flow** | `RegisterPage` → fill all fields with `_unique_email()` → `click_register` → assert success alert. |
| **7. Selenium flow** | `open` (get + overlay dismiss + wait submit) → `enter_*` → JS register click. |
| **8. Page object methods** | `open`, `enter_name`, `enter_email`, `enter_password`, `enter_confirm_password`, `click_register`, `is_displayed`. |
| **9. Indirect locators** | `SUCCESS_ALERT` composite selector. |
| **10. Assertions** | `is_displayed(RegisterPage.SUCCESS_ALERT)`. |
| **11. Expected** | Success toast/alert visible. |
| **12. Failure** | Email collision if UUID collides (rare); ads block submit. |
| **13. Flakiness** | Medium — toast visibility. |
| **14. Screenshots/logs** | Screenshot on failure; `RegisterPage` logs. |
| **15. Real-world** | Validates end-user can sign up. |
| **16. Beginner** | “Fill form → see success message.” |
| **17. Advanced** | Uses `BasePage` waits inside `type_text`; register button waited in `open()`. |

---

### `test_mismatched_passwords`

| # | Detail |
|---|--------|
| **1. Purpose** | Password and confirm differ → error UI. |
| **2. Business scenario** | Registration typo in confirm password. |
| **3. Why it matters** | Prevents accidental wrong password storage. |
| **4. Preconditions** | `default_password` and `wrong_password` in config. |
| **5. Fixtures used** | `driver`. |
| **6. Runtime flow** | `RegisterPage.open` → fill fields with mismatched confirm → `click_register` → assert error alert. |
| **7. Selenium flow** | `enter_*` methods use `BasePage` waits; register uses JS click. |
| **8. Page object methods** | `RegisterPage.open`, `enter_name`, `enter_email`, `enter_password`, `enter_confirm_password`, `click_register`, `is_displayed`. |
| **9. Indirect locators** | `ERROR_ALERT` composite CSS. |
| **10. Assertions** | `is_displayed(RegisterPage.ERROR_ALERT)`. |
| **11. Expected** | Visible error feedback. |
| **12. Failure** | If app uses inline only, locator might miss — flaky. |
| **13. Flakiness** | Medium — toast timing. |
| **14. Screenshots/logs** | Screenshot on failure; page logs. |
| **15. Real-world** | Registration validation. |
| **16. Beginner** | “Passwords must match.” |
| **17. Advanced** | Uses `_unique_email()` to avoid duplicate user conflict. |

### `test_empty_name_field`

| # | Detail |
|---|--------|
| **1. Purpose** | Name empty → error on register. |
| **2. Business scenario** | User omits display name. |
| **3. Why it matters** | Required profile field. |
| **4. Preconditions** | `default_password` configured. |
| **5. Fixtures used** | `driver`. |
| **6. Runtime flow** | `enter_name("")` → fill email/passwords → submit → assert `ERROR_ALERT`. |
| **7. Selenium flow** | Same as successful registration but name blank. |
| **8. Page object methods** | `RegisterPage` methods. |
| **9. Indirect locators** | `NAME_INPUT` empty; `ERROR_ALERT`. |
| **10. Assertions** | `is_displayed(ERROR_ALERT)`. |
| **11. Expected** | Validation error visible. |
| **12. Failure** | HTML5 might block — still expect error path. |
| **13. Flakiness** | Medium. |
| **14. Screenshots/logs** | UI failure screenshot. |
| **15. Real-world** | Required name policy. |
| **16. Beginner** | “No name → error.” |
| **17. Advanced** | May overlap with API `test_register_empty_name` semantically (UI vs API layer). |

### `test_empty_email_field`

| # | Detail |
|---|--------|
| **1. Purpose** | Email empty → error. |
| **2. Business scenario** | User forgets email. |
| **3. Why it matters** | Unique account key required. |
| **4. Preconditions** | `default_password` configured. |
| **5. Fixtures used** | `driver`. |
| **6. Runtime flow** | Fill name, empty email, passwords → submit. |
| **7. Selenium flow** | `enter_email("")`. |
| **8. Page object methods** | `RegisterPage` flow. |
| **9. Indirect locators** | `EMAIL_INPUT`. |
| **10. Assertions** | `is_displayed(ERROR_ALERT)`. |
| **11. Expected** | Error. |
| **12. Failure** | Browser native validation might prevent submit — locator still expected eventually or test fails. |
| **13. Flakiness** | Medium. |
| **14. Screenshots/logs** | Standard. |
| **15. Real-world** | Email required. |
| **16. Beginner** | “No email → error.” |
| **17. Advanced** | Pair with API missing-email test. |

### `test_short_password`

| # | Detail |
|---|--------|
| **1. Purpose** | Password below minimum length → error. |
| **2. Business scenario** | Weak password rejected. |
| **3. Why it matters** | Security posture. |
| **4. Preconditions** | `short_password` from config (e.g. `123`). |
| **5. Fixtures used** | `driver`. |
| **6. Runtime flow** | Use short password for both fields → submit. |
| **7. Selenium flow** | Standard register flow. |
| **8. Page object methods** | `RegisterPage` methods. |
| **9. Indirect locators** | Password fields; `ERROR_ALERT`. |
| **10. Assertions** | `is_displayed(ERROR_ALERT)`. |
| **11. Expected** | Error displayed. |
| **12. Failure** | If server accepts short password — product bug. |
| **13. Flakiness** | Medium. |
| **14. Screenshots/logs** | Screenshot + logs. |
| **15. Real-world** | Password policy enforcement. |
| **16. Beginner** | “Too short password is rejected.” |
| **17. Advanced** | Config-driven length keeps test data centralized. |

### `test_already_registered_email`

| # | Detail |
|---|--------|
| **1. Purpose** | Register with email that already exists → error. |
| **2. Business scenario** | Duplicate signup attempt. |
| **3. Why it matters** | Integrity + clear UX for existing users. |
| **4. Preconditions** | `already_registered_email` or fallback `username` in config. |
| **5. Fixtures used** | `driver`. |
| **6. Runtime flow** | Fill form with known email → submit → assert error. |
| **7. Selenium flow** | Standard register. |
| **8. Page object methods** | `RegisterPage` methods. |
| **9. Indirect locators** | `ERROR_ALERT`. |
| **10. Assertions** | `is_displayed(ERROR_ALERT)`. |
| **11. Expected** | Duplicate error feedback. |
| **12. Failure** | If email not actually registered server-side — may get success (false negative). |
| **13. Flakiness** | **Medium–High** — depends on environment data. |
| **14. Screenshots/logs** | Critical to capture when investigating env drift. |
| **15. Real-world** | Prevents account hijack confusion. |
| **16. Beginner** | “Can’t register twice with same email.” |
| **17. Advanced** | Uses `already_registered_email` first else `username` — understand config semantics. |

---

### `test_register_page_loads`

| # | Detail |
|---|--------|
| **1. Purpose** | Smoke that register route loads and primary CTA exists. |
| **2. Business scenario** | User opens sign-up page. |
| **3. Why it matters** | Catches deploy/routing failures early. |
| **4. Preconditions** | None. |
| **5. Fixtures used** | `driver`. |
| **6. Runtime flow** | `RegisterPage.open()` → URL + button checks. |
| **7. Selenium flow** | `driver.get` via `open`, overlay handling, wait for submit. |
| **8. Page object methods** | `RegisterPage.open`, `is_displayed`. |
| **9. Indirect locators** | `REGISTER_BUTTON`. |
| **10. Assertions** | `"/register" in driver.current_url`; `is_displayed(REGISTER_BUTTON)`. |
| **11. Expected** | Register URL and visible submit. |
| **12. Failure** | Wrong base URL in config; page blocked. |
| **13. Flakiness** | Low. |
| **14. Screenshots/logs** | Screenshot on failure. |
| **15. Real-world** | Deep link health. |
| **16. Beginner** | “Sign-up page opens.” |
| **17. Advanced** | Minimal assertion depth — pair with `test_successful_registration`. |

---

### `test_valid_email_format_check`

| # | Detail |
|---|--------|
| **1. Purpose** | Type syntactically valid email; field remains usable. |
| **2. Business scenario** | User enters normal-looking email while exploring form. |
| **3. Why it matters** | Basic input sanity (not full validation suite). |
| **4. Preconditions** | None. |
| **5. Fixtures used** | `driver`. |
| **6. Runtime flow** | `open` → `enter_email("valid.email@example.com")` → assert field displayed. |
| **7. Selenium flow** | `type_text` on `EMAIL_INPUT`. |
| **8. Page object methods** | `RegisterPage.open`, `enter_email`, `is_displayed`. |
| **9. Indirect locators** | `EMAIL_INPUT`. |
| **10. Assertions** | `is_displayed(RegisterPage.EMAIL_INPUT)`. |
| **11. Expected** | Field still displayed after input. |
| **12. Failure** | If field re-renders and loses attachment — rare. |
| **13. Flakiness** | Low. |
| **14. Screenshots/logs** | Standard. |
| **15. Real-world** | Light regression guard; not a substitute for email RFC tests. |
| **16. Beginner** | “I can type a normal email in the box.” |
| **17. Advanced** | Weak assertion by design — does not assert absence of error. |

---

## 11. File: `tests/ui/test_notes.py`

### File purpose

End-to-end **Notes app** scenarios after login — highest **UI + hybrid** complexity.

### Dependencies

| Fixtures | Page objects | Utilities |
|----------|--------------|-----------|
| `driver` | `LoginPage`, `NotesPage` | `read_config`, `get_logger`, Selenium waits |

### Helpers

| Helper | Detail |
|--------|--------|
| `login(driver)` | Opens login, types config creds, `click_login`, **30s** wait for `notes/app` in URL. |
| `_unique_note_title(prefix)` | Time-based unique title. |

### Maintainer warnings

- **Never** reintroduce `driver.implicitly_wait(0)` before `is_note_visible*` — see file header comment and `notes_handbook.md`.
- **`test_delete_note`** calls `delete_note()` **without title** — deletes **first** visible note → risky if account has pre-existing notes.

---

### `test_create_note`

| # | Detail |
|---|--------|
| **1. Purpose** | Logged-in user creates a note and sees it in the UI. |
| **2. Business scenario** | User adds first note from dashboard. |
| **3. Why it matters** | Core product value — capture and display notes. |
| **4. Preconditions** | Valid `[api] username/password`; session cleanup may have run (`tests/ui/conftest.py`). |
| **5. Fixtures used** | `driver`. |
| **6. Runtime flow** | `login(driver)` → `NotesPage.open` → modal interactions → `save_note` → visibility assert. |
| **7. Selenium/API hybrid** | UI: `click_add_note`, `enter_note_title`, `enter_note_description`. Then `save_note` → **`create_note_via_api`** (HTTP) → JS navigation / re-login → `_wait_for_react_ready`. |
| **8. Page object methods** | `LoginPage.*` via `login()`; `NotesPage.open`, `click_add_note`, `enter_note_title`, `enter_note_description`, `save_note`, `is_note_visible`. |
| **9. Indirect locators** | `ADD_NOTE_BUTTON`, `#title`, `#description`, `div.card` / headers via `is_note_visible`. |
| **10. Assertions** | `assert notes_page.is_note_visible(title)`. |
| **11. Expected** | Note visible in DOM (or API fallback path inside page object reports success). |
| **12. Failure** | Token loss, React not ready, overlay blocking modal, API 4xx. |
| **13. Flakiness** | **High** if hybrid path regresses. |
| **14. Screenshots/logs** | Screenshot on test failure; verbose `NotesPage` logs. |
| **15. Real-world** | Validates most critical user journey. |
| **16. Beginner** | “Log in, add note, see the note.” |
| **17. Advanced** | Never set `implicitly_wait(0)` in test before visibility polls — see module docstring. |

---

### `test_note_appears_in_list`

| # | Detail |
|---|--------|
| **1. Purpose** | Created note’s **title** appears in list (title-centric assertion). |
| **2. Business scenario** | User verifies the note they typed is the one shown. |
| **3. Why it matters** | Catches wrong-note or caching issues. |
| **4. Preconditions** | Same as `test_create_note`. |
| **5. Fixtures used** | `driver`. |
| **6. Runtime flow** | Same create path as `test_create_note` with UUID-heavy title → `is_note_visible_by_title`. |
| **7. Selenium/API hybrid** | Identical hybrid save path. |
| **8. Page object methods** | `is_note_visible_by_title` → delegates to `is_note_visible(title)`. |
| **9. Indirect locators** | Card header text nodes; `_title_matches` handles suffix variants. |
| **10. Assertions** | `assert notes_page.is_note_visible_by_title(title)`. |
| **11. Expected** | Title string visible in list UI. |
| **12. Failure** | Pagination hides title but API has note — fallback may still pass; if both fail, assert fails. |
| **13. Flakiness** | **High** — list rendering + timing. |
| **14. Screenshots/logs** | Same as create note. |
| **15. Real-world** | User trust in displayed data. |
| **16. Beginner** | “The note I created shows the right title.” |
| **17. Advanced** | Title includes UUID + timestamp to reduce collision under parallelism. |

---

### `test_delete_note`

| # | Detail |
|---|--------|
| **1. Purpose** | After creating a note, user can invoke delete flow and remain on Notes app. |
| **2. Business scenario** | User removes a note from dashboard. |
| **3. Why it matters** | Validates delete UX path exists; **does not strictly assert the created note was deleted**. |
| **4. Preconditions** | Login; note created via hybrid `save_note`. |
| **5. Fixtures used** | `driver`. |
| **6. Runtime flow** | Create → `is_note_visible` → `delete_note()` **without title** → URL assert. |
| **7. Selenium/API** | `delete_note()` prefers **API delete** when title known — here **no title** → UI path deletes **first** visible Delete button scope. |
| **8. Page object methods** | `delete_note` (may call `_delete_note_via_api` or UI scoped delete), `is_note_visible`. |
| **9. Indirect locators** | Delete buttons scoped by card; confirm dialog `CONFIRM_DELETE`. |
| **10. Assertions** | Pre: note visible; Post: `"notes/app" in driver.current_url.lower()`. |
| **11. Expected** | Still on app after delete action. |
| **12. Failure** | May delete **wrong** note; may leave app on error — both fail differently. |
| **13. Flakiness** | **High** — first-card selection ambiguity + overlays. |
| **14. Screenshots/logs** | Failure screenshot shows which card was active. |
| **15. Real-world** | Risky pattern for production tests — prefer title-scoped delete. |
| **16. Beginner** | “Delete something and stay on notes.” |
| **17. Advanced** | Maintainer should consider passing `title=` to align delete target with setup. |

---

### `test_edit_note`

| # | Detail |
|---|--------|
| **1. Purpose** | Change an existing note’s title (and description) and see updated title. |
| **2. Business scenario** | User edits note from list or deep link. |
| **3. Why it matters** | Update workflow + pagination fallback. |
| **4. Preconditions** | Login; note created with unique `original_title`. |
| **5. Fixtures used** | `driver`. |
| **6. Runtime flow** | Create → scan DOM headers → **if** title visible: UI edit (`click_edit_note_by_title` + `submit_open_note_modal`) **else** `edit_note_via_api` + `refresh` + `_wait_for_react_ready`. |
| **7. Selenium/API** | UI branch: JS clicks, modal waits, `submit_open_note_modal` guards empty title. API branch: raw `requests` PUT via page object. |
| **8. Page object methods** | `click_edit_note_by_title`, `enter_note_title`, `enter_note_description`, `submit_open_note_modal`, `edit_note_via_api`, `_wait_for_react_ready`. |
| **9. Indirect locators** | Edit buttons in cards; `#title`; modal selectors. |
| **10. Assertions** | `is_note_visible_by_title(edited_title)`. |
| **11. Expected** | Edited title visible after flow completes. |
| **12. Failure** | Edit modal never opens; API 401 token expiry; pagination hides card. |
| **13. Flakiness** | **Very high** — dual-path logic. |
| **14. Screenshots/logs** | Essential for knowing which branch ran. |
| **15. Real-world** | Models real users on large note lists. |
| **16. Beginner** | “Rename my note and see the new name.” |
| **17. Advanced** | DOM scan uses raw `find_elements` in test — coupling to layout; API fallback compensates. |

---

### `test_empty_note_title`

| # | Detail |
|---|--------|
| **1. Purpose** | Saving with **empty title** should not silently succeed as a normal create. |
| **2. Business scenario** | User tries to save incomplete note. |
| **3. Why it matters** | Data quality + client validation. |
| **4. Preconditions** | Logged in. |
| **5. Fixtures used** | `driver`. |
| **6. Runtime flow** | `login` → `NotesPage.open` → modal → `enter_note_title("")` → description → `save_note`. |
| **7. Selenium/API** | `NotesPage.save_note` detects empty title → **UI submit** path (not API create). |
| **8. Page object methods** | `click_add_note`, `enter_note_title`, `enter_note_description`, `save_note`. |
| **9. Indirect locators** | Modal `note-submit`, `#title`. |
| **10. Assertions** | `"notes/app" in driver.current_url.lower()` — soft negative (does not assert toast). |
| **11. Expected** | User remains in Notes app; validation blocks bad save. |
| **12. Failure** | If API path wrongly taken, note might be created — would weaken test intent. |
| **13. Flakiness** | Medium — depends on React validation behavior. |
| **14. Screenshots/logs** | Screenshot on failure helps see modal state. |
| **15. Real-world** | Required-field UX. |
| **16. Beginner** | “No title → should not behave like a good save.” |
| **17. Advanced** | Assertion is intentionally weaker than strict toast text — improve if product shows stable error selector. |

---

### `test_multiple_notes`

| # | Detail |
|---|--------|
| **1. Purpose** | Two distinct notes can exist and both titles appear. |
| **2. Business scenario** | User adds multiple items to workspace. |
| **3. Why it matters** | List rendering with more than one card. |
| **4. Preconditions** | Login + Notes app reachable. |
| **5. Fixtures used** | `driver`. |
| **6. Runtime flow** | Create note1 → `notes_page.open()` → create note2 → assert both titles. |
| **7. Selenium/API** | Two full `click_add_note` / enter / `save_note` cycles; each `save_note` uses API hybrid. |
| **8. Page object methods** | Same as single create, repeated; `NotesPage.open` between creates refreshes SPA context. |
| **9. Indirect locators** | Card headers for both titles. |
| **10. Assertions** | Two `is_note_visible_by_title` asserts. |
| **11. Expected** | Both visible concurrently. |
| **12. Failure** | Second save overwrites state if SPA bug — would fail second assert. |
| **13. Flakiness** | **High** — ordering and list refresh. |
| **14. Screenshots/logs** | Failure screenshot shows which title missing. |
| **15. Real-world** | Multi-item workflows. |
| **16. Beginner** | “Add two notes, see both.” |
| **17. Advanced** | `open()` between saves intentional — see in-file comments on SPA state. |

---

### `test_note_persists_after_refresh`

| # | Detail |
|---|--------|
| **1. Purpose** | Note survives **browser refresh** (server persistence + React re-fetch). |
| **2. Business scenario** | User reloads page and expects data still there. |
| **3. Why it matters** | Catches client-only state bugs. |
| **4. Preconditions** | Note created successfully first. |
| **5. Fixtures used** | `driver`. |
| **6. Runtime flow** | Create → assert pre-refresh → `driver.refresh()` → `_wait_for_react_ready()` → assert again. |
| **7. Selenium/API** | Refresh may drop SPA session; `NotesPage` waits re-mount; API-backed data still on server. |
| **8. Page object methods** | `_wait_for_react_ready` called **directly** from test (acceptable here post-refresh). |
| **9. Indirect locators** | Same visibility locators as other note tests. |
| **10. Assertions** | `is_note_visible_by_title(title)` after refresh. |
| **11. Expected** | Title still visible. |
| **12. Failure** | Session expired to login — would fail visibility; screenshot critical. |
| **13. Flakiness** | **High** — refresh + auth + React race. |
| **14. Screenshots/logs** | Compare before/after screenshots. |
| **15. Real-world** | Browser reload is common user action. |
| **16. Beginner** | “Refresh page, note still there.” |
| **17. Advanced** | Uses `_wait_for_react_ready` because `open()` may skip `get` when URL already notes app. |

---

## 12. Maintainer checklist (quick reference)

| If you change… | Re-run these tests first |
|----------------|---------------------------|
| `APIClient._ResponseProxy` | Entire `tests/api/` |
| `auth_token` fixture | `test_logout_success`, `test_notes_api.py` tests using `auth_token`, `test_delete_all_notes` |
| `NotesPage.save_note` / `create_note_via_api` | Entire `tests/ui/test_notes.py` |
| `LoginPage.click_login` | `tests/ui/test_login.py` + `test_notes.py` (login helper) |
| `read_config` keys | Any test reading new keys + all page `URL` constants |

---

## Appendix A — API CRUD “short entry” template (used by several `test_notes_api` tests)

Some note tests above use a **compact table** (fewer than 17 visible rows) when they follow the same mechanical pattern. Use this **full template** and substitute **endpoint / method / body / expected status**:

| # | Detail |
|---|--------|
| **1. Purpose** | *(e.g. enforce 401 on GET list without token)* |
| **2. Business scenario** | *(anonymous or invalid access)* |
| **3. Why it matters** | Authz on REST resource. |
| **4. Preconditions** | API reachable; token rules as per test. |
| **5. Fixtures used** | Usually `api_client` ± `auth_token`. |
| **6. Runtime flow** | Optional setup (`_create_note` / `_token_from_fresh_user`) → primary HTTP call → assert. |
| **7. API flow** | **Method** `GET|POST|PUT|PATCH|DELETE` **`{base}/notes...`**; headers `Content-Type` + optional `x-auth-token`; JSON body if applicable. |
| **8. Page object methods** | None. |
| **9. HTTP/locators** | `_auth_headers(token)` when authenticated. |
| **10. Assertions** | Status code ± optional JSON shape. |
| **11. Expected** | Documented HTTP semantics. |
| **12. Failure** | Wrong status → read `APIClient` logged body. |
| **13. Flakiness** | Higher when using **`auth_token`** shared user with parallel **DELETE**/**PUT** storms. |
| **14. Screenshots/logs** | No screenshot; `logs/test_<date>.log` has response text. |
| **15. Real-world** | Contract + security. |
| **16. Beginner** | “Call API, check status.” |
| **17. Advanced** | `_ResponseProxy` may unwrap lists for `GET notes`; `_normalize_note_payload` pads tiny titles on POST/PUT. |

**Tests that map cleanly to this template (expand mentally using code):**  
`test_create_note_missing_description`, `test_create_note_no_auth`, `test_get_all_notes`, `test_get_all_notes_no_auth`, `test_get_note_by_id`, `test_get_note_invalid_id`, `test_get_note_no_auth`, `test_update_note_success`, `test_update_note_missing_title`, `test_update_note_no_auth`, `test_update_note_invalid_id`, `test_create_note_missing_title` (already expanded above).

---

## Appendix B — Cross-document link

| Document | Role |
|----------|------|
| [PROJECT_DETAILED_EXPLANATION.md](PROJECT_DETAILED_EXPLANATION.md) | Framework / file internals (not per-test). |
| [notes_handbook.md](notes_handbook.md) | Notes UI + `NotesPage` maintainer deep dive. |

---

*End of test case knowledge base. For framework internals beyond tests, see [PROJECT_DETAILED_EXPLANATION.md](PROJECT_DETAILED_EXPLANATION.md).*
