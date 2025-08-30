@echo off
echo.
echo ========================
echo  LIVE DEMO GENERATOR
echo ========================
echo.
echo This script will generate a live demo of the phishing email analyzer.
echo.

echo [1/4] Installing demo dependencies...
python scripts\install_demo_deps.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [2/4] Testing setup...
python scripts\test_demo.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Setup test failed
    pause
    exit /b 1
)

echo.
echo [3/4] Creating user sample files...
python scripts\create_user_samples.py

echo.
echo [4/4] Ready to generate demo!
echo.
echo INSTRUCTIONS:
echo 1. Make sure your OpenAI API key is set in .env file
echo 2. Press any key to start the automated demo recording
echo 3. The script will start Flask, open browser, and record the demo
echo 4. Generated assets will be saved to demo_assets/ folder
echo.
pause

echo Starting demo generation...
python scripts\generate_demo.py

echo.
echo Demo generation completed!
echo Check the demo_assets/ folder for your video and screenshots.
echo.
pause