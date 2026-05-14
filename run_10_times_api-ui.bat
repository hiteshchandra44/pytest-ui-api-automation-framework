@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo      STARTING 10x API + UI STABILITY RUN
echo ==========================================

REM Create folders
if not exist logs mkdir logs
if not exist reports mkdir reports
if not exist reports\api mkdir reports\api
if not exist reports\ui mkdir reports\ui

REM Summary files
set API_SUMMARY=reports\api\api_10x_summary.txt
set UI_SUMMARY=reports\ui\ui_10x_summary.txt
set FINAL_SUMMARY=reports\final_stability_summary.txt

echo API 10x Stability Summary > %API_SUMMARY%
echo ========================================== >> %API_SUMMARY%

echo UI 10x Stability Summary > %UI_SUMMARY%
echo ========================================== >> %UI_SUMMARY%

echo Final Stability Summary > %FINAL_SUMMARY%
echo ========================================== >> %FINAL_SUMMARY%

REM ====================================================
REM API TESTS
REM ====================================================

echo.
echo ==========================================
echo            API TESTS - 10 RUNS
echo ==========================================

for /L %%i in (1,1,10) do (

    echo.
    echo --------------------------------------
    echo API RUN %%i / 10
    echo --------------------------------------

    REM Timestamp generation
    for /f %%a in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd_HH-mm-ss"') do set DTS=%%a

    set REPORT=reports\api\api_run_%%i_!DTS!.html
    set LOG=logs\api_run_%%i_!DTS!.log

    python -m pytest -c pytest_api.ini -n 8 ^
    --html=!REPORT! ^
    --self-contained-html ^
    > !LOG! 2>&1

    if errorlevel 1 (
        echo RUN %%i : FAILED >> %API_SUMMARY%
        echo API RUN %%i FAILED
    ) else (
        echo RUN %%i : PASSED >> %API_SUMMARY%
        echo API RUN %%i PASSED
    )
)

REM ====================================================
REM UI TESTS
REM ====================================================

echo.
echo ==========================================
echo             UI TESTS - 10 RUNS
echo ==========================================

for /L %%i in (1,1,10) do (

    echo.
    echo --------------------------------------
    echo UI RUN %%i / 10
    echo --------------------------------------

    REM Timestamp generation
    for /f %%a in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd_HH-mm-ss"') do set DTS=%%a

    set REPORT=reports\ui\ui_run_%%i_!DTS!.html
    set LOG=logs\ui_run_%%i_!DTS!.log

    python -m pytest -c pytest_ui.ini -n 4 ^
    --html=!REPORT! ^
    --self-contained-html ^
    > !LOG! 2>&1

    if errorlevel 1 (
        echo RUN %%i : FAILED >> %UI_SUMMARY%
        echo UI RUN %%i FAILED
    ) else (
        echo RUN %%i : PASSED >> %UI_SUMMARY%
        echo UI RUN %%i PASSED
    )
)

REM ====================================================
REM FINAL COMBINED SUMMARY
REM ====================================================

echo. >> %FINAL_SUMMARY%
echo API RESULTS >> %FINAL_SUMMARY%
echo ========================================== >> %FINAL_SUMMARY%
type %API_SUMMARY% >> %FINAL_SUMMARY%

echo. >> %FINAL_SUMMARY%
echo UI RESULTS >> %FINAL_SUMMARY%
echo ========================================== >> %FINAL_SUMMARY%
type %UI_SUMMARY% >> %FINAL_SUMMARY%

echo.
echo ==========================================
echo          ALL 10x RUNS COMPLETED
echo ==========================================
echo.
echo Reports Folder  : reports\
echo Logs Folder     : logs\
echo Final Summary   : %FINAL_SUMMARY%

pause