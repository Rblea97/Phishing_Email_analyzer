#!/usr/bin/env python3
"""
Simple demo script that tests the Flask app and creates documentation
"""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path

def main():
    """Run a simple demo test"""
    print("Simple Demo Test for Phishing Email Analyzer")
    print("=" * 50)
    
    base_dir = Path(__file__).parent.parent
    
    # Test 1: Check sample files
    demo_samples = base_dir / "demo_samples"
    user_samples = base_dir / "samples_for_users"
    
    sample_files = list(demo_samples.glob("*.eml"))
    user_files = list(user_samples.glob("*.eml"))
    
    print(f"\n1. Sample Files Check:")
    print(f"   Demo samples: {len(sample_files)} files")
    print(f"   User samples: {len(user_files)} files")
    
    if sample_files:
        print("   Sample files available:")
        for f in sample_files[:3]:  # Show first 3
            print(f"   - {f.name}")
        if len(sample_files) > 3:
            print(f"   ... and {len(sample_files) - 3} more")
    
    # Test 2: Check Flask app file
    flask_app = base_dir / "app_phase2.py"
    if flask_app.exists():
        print(f"\n2. Flask App: [OK] Found at {flask_app}")
    else:
        print(f"\n2. Flask App: [ERROR] Not found")
        return False
    
    # Test 3: Check requirements
    requirements = base_dir / "requirements.txt"
    if requirements.exists():
        print(f"3. Requirements: [OK] Found")
        
        # Check if key dependencies are listed
        req_text = requirements.read_text()
        has_flask = "Flask" in req_text
        has_openai = "openai" in req_text
        
        print(f"   - Flask: {'[OK]' if has_flask else '[ERROR]'}")
        print(f"   - OpenAI: {'[OK]' if has_openai else '[ERROR]'}")
    else:
        print(f"3. Requirements: [ERROR] Not found")
    
    # Test 4: Manual demo instructions
    print(f"\n4. Manual Demo Instructions:")
    print(f"   To create a live demo manually:")
    print(f"   1. Start Flask app: python app_phase2.py")
    print(f"   2. Open browser to: http://localhost:5000")
    print(f"   3. Upload a sample file from samples_for_users/")
    print(f"   4. Record your screen using:")
    print(f"      - OBS Studio (free)")
    print(f"      - Loom (web-based)")
    print(f"      - Windows Game Bar (Win+G)")
    print(f"      - QuickTime Player (Mac)")
    
    # Test 5: Try to start Flask app briefly
    print(f"\n5. Flask App Test:")
    print(f"   Testing if Flask app can start...")
    
    try:
        # Try to start Flask app for 5 seconds
        process = subprocess.Popen([
            sys.executable, str(flask_app)
        ], cwd=str(base_dir))
        
        # Wait a moment for startup
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is None:
            print("   [OK] Flask app started successfully")
            print("   [OK] Ready for manual demo recording")
            
            # Ask if user wants to open browser
            try:
                response = input("\n   Open browser to localhost:5000? (y/n): ").lower()
                if response.startswith('y'):
                    webbrowser.open('http://localhost:5000')
                    print("   Browser opened - you can now record your demo!")
                    
                input("\n   Press Enter when done recording...")
            except KeyboardInterrupt:
                pass
            
            # Clean shutdown
            process.terminate()
            time.sleep(1)
            if process.poll() is None:
                process.kill()
        else:
            print("   [ERROR] Flask app failed to start")
            return False
            
    except Exception as e:
        print(f"   [ERROR] Error testing Flask app: {e}")
        return False
    
    print(f"\n" + "=" * 50)
    print("Demo test completed successfully!")
    print("\nNext steps for live demo:")
    print("1. Use manual recording with screen capture software")
    print("2. Upload to Loom/YouTube for sharing")
    print("3. Update README with demo link")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)