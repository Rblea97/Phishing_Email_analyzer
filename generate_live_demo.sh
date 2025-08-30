#!/bin/bash

echo
echo "========================"
echo " LIVE DEMO GENERATOR"
echo "========================"
echo

echo "This script will generate a live demo of the phishing email analyzer."
echo

echo "[1/4] Installing demo dependencies..."
python3 scripts/install_demo_deps.py
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi

echo
echo "[2/4] Testing setup..."
python3 scripts/test_demo.py
if [ $? -ne 0 ]; then
    echo "ERROR: Setup test failed"
    exit 1
fi

echo
echo "[3/4] Creating user sample files..."
python3 scripts/create_user_samples.py

echo
echo "[4/4] Ready to generate demo!"
echo
echo "INSTRUCTIONS:"
echo "1. Make sure your OpenAI API key is set in .env file"
echo "2. Press Enter to start the automated demo recording"
echo "3. The script will start Flask, open browser, and record the demo"
echo "4. Generated assets will be saved to demo_assets/ folder"
echo
read -p "Press Enter to continue..."

echo "Starting demo generation..."
python3 scripts/generate_demo.py

echo
echo "Demo generation completed!"
echo "Check the demo_assets/ folder for your video and screenshots."
echo