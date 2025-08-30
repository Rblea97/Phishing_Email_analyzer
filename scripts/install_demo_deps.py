#!/usr/bin/env python3
"""
Install dependencies for demo generation
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"Running: {description}...")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"SUCCESS: {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: {description} failed:")
        print(f"   Error: {e}")
        if e.stdout:
            print(f"   Output: {e.stdout}")
        if e.stderr:
            print(f"   Error output: {e.stderr}")
        return False

def main():
    """Install demo dependencies"""
    print("Installing demo generation dependencies...\n")
    
    # Install Python dependencies
    success = run_command([
        sys.executable, "-m", "pip", "install", 
        "playwright==1.40.0", 
        "pillow>=10.0.0",
        "aiohttp>=3.8.0"
    ], "Installing Python packages")
    
    if not success:
        print("ERROR: Failed to install Python dependencies")
        return False
    
    # Install Playwright browsers
    success = run_command([
        sys.executable, "-m", "playwright", "install", "chromium"
    ], "Installing Playwright browsers")
    
    if not success:
        print("ERROR: Failed to install Playwright browsers")
        return False
    
    # Check if FFmpeg is available (optional for GIF creation)
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, capture_output=True)
        print("SUCCESS: FFmpeg found - GIF creation will be available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("WARNING: FFmpeg not found - GIF creation may not work")
        print("   Install FFmpeg from https://ffmpeg.org/ for best results")
    
    print("\nDemo dependencies installed successfully!")
    print("\nNext steps:")
    print("1. Ensure your OpenAI API key is set in .env")
    print("2. Start the Flask app: python app_phase2.py")
    print("3. Run demo generation: python scripts/generate_demo.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)