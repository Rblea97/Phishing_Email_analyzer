#!/usr/bin/env python3
"""
Test demo generation without recording - just validate the setup
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.generate_demo import DemoGenerator

async def test_demo_setup():
    """Test the demo setup without actually recording"""
    print("🧪 Testing demo setup...\n")
    
    demo_gen = DemoGenerator()
    
    # Test 1: Check sample files exist
    demo_samples = Path(__file__).parent.parent / "demo_samples"
    sample_files = list(demo_samples.glob("*.eml"))
    
    if sample_files:
        print(f"✅ Found {len(sample_files)} sample email files:")
        for file in sample_files:
            print(f"   📧 {file.name}")
    else:
        print("❌ No sample email files found")
        return False
    
    # Test 2: Check Flask app can start
    print(f"\n🔄 Testing Flask app startup...")
    try:
        if await demo_gen.start_flask_app():
            print("✅ Flask app started successfully")
            demo_gen.stop_flask_app()
        else:
            print("❌ Flask app failed to start")
            return False
    except Exception as e:
        print(f"❌ Flask app test failed: {e}")
        return False
    
    # Test 3: Check demo directory
    if demo_gen.demo_dir.exists():
        print(f"✅ Demo assets directory ready: {demo_gen.demo_dir}")
    else:
        print(f"🔄 Created demo assets directory: {demo_gen.demo_dir}")
        demo_gen.demo_dir.mkdir(exist_ok=True)
    
    print("\n🎉 Demo setup test completed successfully!")
    print("\nReady to generate demo with: python scripts/generate_demo.py")
    
    return True

async def main():
    """Main test function"""
    try:
        success = await test_demo_setup()
        return success
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)