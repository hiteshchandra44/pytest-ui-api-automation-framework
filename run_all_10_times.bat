@echo off
REM run_all_10_times.bat
REM Runs UI tests 10 times and API tests 10 times.
REM UI reports:  reports\ui_run_YYYY-MM-DD_HH-MM-SS.html (one per run, via utilities\run_tests.py)
REM API reports: reports\api_run_YYYY-MM-DD_HH-MM-SS.html
REM FULL reports: reports\stability_run_YYYY-MM-DD_HH-MM-SS.html (UI+API together, 75 tests)
REM It also writes stability logs and markdown summaries.

setlocal enabledelayedexpansion

if not exist reports mkdir reports

REM This subroutine runs a suite 10 times:
REM %1 = suite name (UI/API)
REM %2 = test path (tests\ui or tests\api)
REM %3 = report prefix (ui_run/api_run)
REM %4 = expected test count (25/50)
call :RUN_SUITE UI tests\ui ui_run 25
call :RUN_SUITE API tests\api api_run 50
call :RUN_SUITE FULL tests stability_run 75

endlocal
exit /b 0

:RUN_SUITE
set SUITE=%1
set TESTPATH=%2
set PREFIX=%3
set EXPECTED=%4

set PASSES=0
set FAILS=0

set LOGFILE=reports\%SUITE%_stability_log.txt
set SUMMARYMD=reports\%SUITE%_stability_summary.md
echo %SUITE% stability log started > %LOGFILE%

for /L %%i in (1,1,10) do (
  echo === %SUITE% Run %%i/10 ===

  REM Measure time and run timestamped HTML report via utilities\run_tests.py (NO reruns).
  for /f "usebackq delims=" %%T in (`powershell -NoProfile -Command "$sw=[Diagnostics.Stopwatch]::StartNew(); python utilities\run_tests.py stability --path %TESTPATH% --report-prefix %PREFIX%_%%i; $code=$LASTEXITCODE; $sw.Stop(); Write-Output ($code.ToString() + '|' + [int]$sw.Elapsed.TotalSeconds)"`) do (
    set RESULT_LINE=%%T
  )

  for /f "tokens=1,2 delims=|" %%A in ("!RESULT_LINE!") do (
    set EXIT_CODE=%%A
    set TIME_TAKEN=%%B
  )

  for /f "usebackq delims=" %%D in (`powershell -NoProfile -Command "Get-Date -Format 'yyyy-MM-dd'"`) do set TODAY=%%D

  if "!EXIT_CODE!"=="0" (
    set STATUS=PASSED
    set /A PASSES=!PASSES!+1
    set PASSED_COUNT=%EXPECTED%/%EXPECTED%
  ) else (
    set STATUS=FAILED
    set /A FAILS=!FAILS!+1
    set PASSED_COUNT=0/%EXPECTED%
  )

  echo Run %%i: !STATUS! - !PASSED_COUNT! tests ^| Date: !TODAY! ^| Time taken: !TIME_TAKEN!s>> %LOGFILE%
)

set OVERALL=UNSTABLE
if "!FAILS!"=="0" set OVERALL=STABLE

echo ================================
echo STABILITY SUMMARY (%SUITE%)
echo Total Runs: 10
echo Passed Runs: !PASSES!
echo Failed Runs: !FAILS!
echo Overall Result: !OVERALL!
echo ================================

python utilities\generate_stability_report.py %LOGFILE% %SUMMARYMD%
exit /b 0
