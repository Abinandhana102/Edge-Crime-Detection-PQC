@echo off
chcp 65001 >nul
title Edge AI Crime Detection and Quantum-Safe Evidence Management Framework

:MENU
cls
echo ===============================================================================
echo   [*] EDGE AI CRIME DETECTION AND QUANTUM-SAFE EVIDENCE MANAGEMENT FRAMEWORK
echo   [*] NIST FIPS 203 ML-KEM-768 + AES-256-GCM + SHA-256 INTEGRITY
echo ===============================================================================
echo.
echo   [1] Start Police Command HQ Server (http://localhost:8000)
echo   [2] Run Interactive End-to-End Demo Pipeline (run_demo.py)
echo   [3] Open Client / Store Camera Portal (http://localhost:8000/user)
echo   [4] Launch Edge AI Surveillance Worker - Demo CCTV Mode (run_edge_ai.py)
echo   [5] Launch Edge AI Surveillance Worker - Physical Webcam Mode
echo   [6] Launch BOTH Server and Edge AI Worker (Dual Windows)
echo   [7] Launch Edge AI on Custom Video File (sample_videos)
echo   [8] Run Full Automated Pytest Verification Suite (17 Tests)
echo   [9] Install / Check Dependencies (requirements.txt)
echo   [C] Clear Incident Logs & Recorded Evidence (clear_logs.py)
echo   [0] Exit
echo.
echo ===============================================================================
set /p choice="Enter your choice (0-9, C): "

if "%choice%"=="1" goto START_SERVER
if "%choice%"=="2" goto RUN_DEMO
if "%choice%"=="3" goto OPEN_USER_PORTAL
if "%choice%"=="4" goto RUN_EDGE_DEMO
if "%choice%"=="5" goto RUN_EDGE_WEBCAM
if "%choice%"=="6" goto START_ALL
if "%choice%"=="7" goto RUN_CUSTOM_VIDEO
if "%choice%"=="8" goto RUN_TESTS
if "%choice%"=="9" goto INSTALL_DEPS
if /i "%choice%"=="C" goto CLEAR_LOGS
if "%choice%"=="0" goto EXIT

echo Invalid choice. Please try again.
pause
goto MENU

:START_SERVER
cls
echo ===============================================================================
echo   Starting Police Command HQ Server...
echo   URL: http://localhost:8000
echo   Admin:   admin   / PoliceSecure2026!
echo   Officer: officer / OfficerPass2026!
echo ===============================================================================
echo.
python run_server.py
pause
goto MENU

:RUN_DEMO
cls
echo ===============================================================================
echo   Running Interactive End-to-End Demonstration Scenario...
echo ===============================================================================
echo.
python run_demo.py
echo.
pause
goto MENU

:OPEN_USER_PORTAL
cls
echo ===============================================================================
echo   Opening Client / Store Camera Portal in browser...
echo   URL: http://localhost:8000/user
echo   Default User: user / UserSecure2026!
echo ===============================================================================
start "" "http://localhost:8000/user"
timeout /t 2 >nul
goto MENU

:RUN_EDGE_DEMO
cls
echo ===============================================================================
echo   Launching Edge AI Surveillance Worker in Demo CCTV Simulation Mode...
echo ===============================================================================
echo.
python run_edge_ai.py --source demo --camera CAM-01
pause
goto MENU

:RUN_EDGE_WEBCAM
cls
echo ===============================================================================
echo   Launching Edge AI Surveillance Worker in Physical Webcam Mode...
echo ===============================================================================
echo.
python run_edge_ai.py --source webcam --camera CAM-01
pause
goto MENU

:START_ALL
cls
echo ===============================================================================
echo   Launching Police Command HQ Server and Edge AI Worker in separate windows...
echo ===============================================================================
start "Police Command HQ Server" cmd /k "python run_server.py"
timeout /t 3 /nobreak >nul
start "Edge AI Surveillance Worker" cmd /k "python run_edge_ai.py --source demo --camera CAM-01"
echo.
echo Both services started! Open http://localhost:8000 in your browser.
echo.
pause
goto MENU

:RUN_CUSTOM_VIDEO
cls
echo ===============================================================================
echo   Launching Edge AI Surveillance Worker on Custom Video...
echo   Place your video files in: sample_videos\
echo ===============================================================================
echo.
echo Available videos in sample_videos:
dir /b sample_videos\*.mp4 sample_videos\*.avi sample_videos\*.mkv 2>nul
echo.
set /p vidname="Enter video filename inside sample_videos folder (e.g. crime.mp4): "
if "%vidname%"=="" (
    echo No video entered. Returning to menu...
    timeout /t 2 >nul
    goto MENU
)
if exist "sample_videos\%vidname%" (
    python run_edge_ai.py --source "sample_videos\%vidname%" --camera CAM-01
) else if exist "%vidname%" (
    python run_edge_ai.py --source "%vidname%" --camera CAM-01
) else (
    echo File not found! Please check the filename.
    pause
)
goto MENU

:RUN_TESTS
cls
echo ===============================================================================
echo   Running Full Pytest Test Suite...
echo ===============================================================================
echo.
pytest tests/ -v
echo.
pause
goto MENU

:INSTALL_DEPS
cls
echo ===============================================================================
echo   Installing / Verifying Dependencies...
echo ===============================================================================
echo.
pip install -r requirements.txt
echo.
pause
goto MENU

:CLEAR_LOGS
cls
echo ===============================================================================
echo   Clear Security Incident Logs and Encrypted Evidence Files
echo ===============================================================================
echo.
echo   [1] Clear ALL incident logs and evidence files
echo   [2] Clear ONLY User / Store camera incidents (CAM-USR-*)
echo   [3] Keep latest 5 incidents and clear older ones
echo   [4] Cancel and return to main menu
echo.
set /p clr_choice="Enter your choice (1-4): "
if "%clr_choice%"=="1" python clear_logs.py
if "%clr_choice%"=="2" python clear_logs.py --user
if "%clr_choice%"=="3" python clear_logs.py --keep 5
if "%clr_choice%"=="4" goto MENU
echo.
pause
goto MENU

:EXIT
echo.
echo Thank you for using Edge AI and Quantum-Safe Evidence Management System.
timeout /t 2 >nul
exit
