@echo off
REM run_stability_10x.bat
REM Runs the FULL suite (75 tests: 25 UI + 50 API) 10 times.
REM
REM STRATEGY — split UI and API per iteration:
REM   UI  tests: -n 4  (stable — limits simultaneous browser sessions on ad-heavy site)
REM   API tests: -n 8  (fast   — pure HTTP, no browser, no session risk)
REM   Both run per iteration before moving to the next run.
REM
REM This gives ~10-12 min per iteration instead of ~29 min.
REM Total 10x estimate: ~100-120 min instead of ~290 min.
REM
REM Reports:
REM   reports\ui_stab_<N>.html     — UI report per run
REM   reports\api_stab_<N>.html    — API report per run
REM   reports\FULL_stability_log.txt
REM   reports\FULL_stability_summary.md

setlocal enabledelayedexpansion

if not exist reports mkdir reports

set LOGFILE=reports\FULL_stability_log.txt
set SUMMARYMD=reports\FULL_stability_summary.md
echo FULL stability log started > %LOGFILE%

set TOTAL_PASSES=0
set TOTAL_FAILS=0

for /L %%i in (1,1,10) do (
  echo.
  echo ============================================
  echo  Run %%i / 10
  echo ============================================

  REM ── UI pass: -n 4 for session stability ──────────────────────────────
  echo [%%i] Running UI tests ^(-n 4^)...
  for /f "usebackq delims=" %%T in (`powershell -NoProfile -Command "$sw=[Diagnostics.Stopwatch]::StartNew(); python -m pytest tests\ui -c pytest_stability.ini --override-ini='addopts=-n 4' --html=reports\ui_stab_%%i.html --self-contained-html -q; $code=$LASTEXITCODE; $sw.Stop(); Write-Output ($code.ToString() + '|' + [int]$sw.Elapsed.TotalSeconds)"`) do (
    set UI_LINE=%%T
  )
  for /f "tokens=1,2 delims=|" %%A in ("!UI_LINE!") do (
    set UI_EXIT=%%A
    set UI_TIME=%%B
  )

  REM ── API pass: -n 8 for maximum speed ─────────────────────────────────
  echo [%%i] Running API tests ^(-n 8^)...
  for /f "usebackq delims=" %%T in (`powershell -NoProfile -Command "$sw=[Diagnostics.Stopwatch]::StartNew(); python -m pytest tests\api -c pytest_stability.ini --override-ini='addopts=-n 8' --html=reports\api_stab_%%i.html --self-contained-html -q; $code=$LASTEXITCODE; $sw.Stop(); Write-Output ($code.ToString() + '|' + [int]$sw.Elapsed.TotalSeconds)"`) do (
    set API_LINE=%%T
  )
  for /f "tokens=1,2 delims=|" %%A in ("!API_LINE!") do (
    set API_EXIT=%%A
    set API_TIME=%%B
  )

  REM ── Evaluate combined result ──────────────────────────────────────────
  for /f "usebackq delims=" %%D in (`powershell -NoProfile -Command "Get-Date -Format 'yyyy-MM-dd HH:mm'"`) do set NOW=%%D

  set RUN_STATUS=PASSED
  if "!UI_EXIT!" NEQ "0" set RUN_STATUS=FAILED
  if "!API_EXIT!" NEQ "0" set RUN_STATUS=FAILED

  if "!RUN_STATUS!"=="PASSED" (
    set /A TOTAL_PASSES=!TOTAL_PASSES!+1
    set COUNTS=75/75
  ) else (
    set /A TOTAL_FAILS=!TOTAL_FAILS!+1
    set COUNTS=?/75
  )

  set /A ITER_TIME=!UI_TIME!+!API_TIME!

  echo Run %%i: !RUN_STATUS! - !COUNTS! tests ^| !NOW! ^| UI: !UI_TIME!s  API: !API_TIME!s  Total: !ITER_TIME!s>> %LOGFILE%
  echo [%%i] !RUN_STATUS! — UI !UI_TIME!s + API !API_TIME!s = !ITER_TIME!s total
)

echo.
set OVERALL=UNSTABLE
if "!TOTAL_FAILS!"=="0" set OVERALL=STABLE

echo ============================================
echo  STABILITY SUMMARY  ^(FULL — 75 tests x 10^)
echo  Passed Runs : !TOTAL_PASSES! / 10
echo  Failed Runs : !TOTAL_FAILS! / 10
echo  Overall     : !OVERALL!
echo ============================================

python utilities\generate_stability_report.py %LOGFILE% %SUMMARYMD%

endlocal
exit /b 0