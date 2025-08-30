@echo off
echo.
echo ========================================
echo   PHISHING ANALYZER DEMO SETUP
echo ========================================
echo.

echo [1] Starting Flask application...
echo    URL: http://localhost:5000
echo.

cd /d "%~dp0"
start "Flask App" python app_phase2.py

echo [2] Waiting for app to start...
timeout /t 5 /nobreak > nul

echo [3] Opening browser...
start "" "http://localhost:5000"

echo [4] Opening sample files folder...
start "" "samples_for_users"

echo.
echo ========================================
echo   READY FOR DEMO RECORDING!
echo ========================================
echo.
echo NEXT STEPS:
echo 1. Start your screen recording software
echo 2. Follow the script in DEMO_RECORDING_GUIDE.md
echo 3. Upload a sample file and demonstrate features
echo 4. Record for 60 seconds total
echo.
echo SAMPLE FILES TO USE:
echo - corporate_benefits_scam.eml  (Primary)
echo - paypal_security_alert.eml    (Backup)
echo - crypto_wallet_breach.eml     (High-threat)
echo.
echo When done recording:
echo - Stop Flask app with Ctrl+C
echo - Upload video to Loom or YouTube
echo - Update README with demo link
echo.
pause