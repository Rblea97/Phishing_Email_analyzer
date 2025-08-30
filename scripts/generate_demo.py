"""
Demo Generation Script for Phishing Email Analyzer
Automates recording of 60-second demo video and GIF creation using Playwright
"""

import os
import sys
import time
import asyncio
import subprocess
import signal
from pathlib import Path
from playwright.async_api import async_playwright
from PIL import Image
import logging

# Add parent directory to path to import Flask app
sys.path.append(str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DemoGenerator:
    def __init__(self):
        self.flask_process = None
        self.app_url = "http://localhost:5000"
        self.demo_dir = Path(__file__).parent.parent / "demo_assets"
        self.demo_dir.mkdir(exist_ok=True)
        
        # Demo timing (in milliseconds)
        self.scenes = {
            "homepage": 3000,      # 3s - Show homepage
            "upload": 4000,        # 4s - Upload process
            "rule_analysis": 15000, # 15s - Rule-based results
            "ai_analysis": 15000,   # 15s - AI analysis tab
            "history": 8000,       # 8s - Analysis history
            "wrap_up": 2000        # 2s - Final wrap-up
        }
        
    async def start_flask_app(self):
        """Start Flask application in background"""
        logger.info("Starting Flask application...")
        
        # Start Flask app as subprocess
        env = os.environ.copy()
        env['FLASK_ENV'] = 'development'
        
        self.flask_process = subprocess.Popen([
            sys.executable, "app_phase2.py"
        ], cwd=Path(__file__).parent.parent, env=env)
        
        # Wait for app to start
        await asyncio.sleep(5)
        
        # Test if app is responding
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(self.app_url) as response:
                    if response.status == 200:
                        logger.info("Flask app started successfully")
                        return True
        except Exception as e:
            logger.error(f"Failed to start Flask app: {e}")
            return False
        
        return False
    
    def stop_flask_app(self):
        """Stop Flask application"""
        if self.flask_process:
            logger.info("Stopping Flask application...")
            self.flask_process.terminate()
            self.flask_process.wait()
    
    async def record_demo(self):
        """Record the complete demo using Playwright"""
        async with async_playwright() as p:
            # Launch browser with video recording
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                record_video_dir=str(self.demo_dir),
                record_video_size={'width': 1280, 'height': 720}
            )
            
            page = await context.new_page()
            
            try:
                await self.record_scene_1_homepage(page)
                await self.record_scene_2_upload(page)
                await self.record_scene_3_rule_analysis(page)
                await self.record_scene_4_ai_analysis(page)
                await self.record_scene_5_history(page)
                
                logger.info("Demo recording completed")
                
            except Exception as e:
                logger.error(f"Demo recording failed: {e}")
                
            finally:
                await context.close()
                await browser.close()
    
    async def record_scene_1_homepage(self, page):
        """Scene 1: Show homepage and introduce the tool"""
        logger.info("Recording Scene 1: Homepage")
        
        await page.goto(self.app_url)
        await page.wait_for_load_state('networkidle')
        
        # Take screenshot of homepage
        await page.screenshot(path=str(self.demo_dir / "01_homepage.png"))
        
        # Show the upload interface
        await page.hover('.display-6')
        await asyncio.sleep(1500)
        
        await page.hover('.card')
        await asyncio.sleep(1500)
    
    async def record_scene_2_upload(self, page):
        """Scene 2: Upload a phishing email"""
        logger.info("Recording Scene 2: File Upload")
        
        # Upload sample phishing email
        sample_file = Path(__file__).parent.parent / "demo_samples" / "corporate_phishing.eml"
        
        # Click the choose file button
        await page.click('button:has-text("Choose File")')
        await asyncio.sleep(500)
        
        # Set the file
        file_input = page.locator('input[type="file"]')
        await file_input.set_input_files(str(sample_file))
        
        await asyncio.sleep(1000)
        
        # Take screenshot of file selected
        await page.screenshot(path=str(self.demo_dir / "02_file_selected.png"))
        
        # Submit form
        submit_btn = page.locator('input[type="submit"], button[type="submit"]')
        await submit_btn.click()
        
        await asyncio.sleep(3000)
    
    async def record_scene_3_rule_analysis(self, page):
        """Scene 3: Show rule-based analysis results"""
        logger.info("Recording Scene 3: Rule-Based Analysis")
        
        # Wait for analysis to complete - look for common elements
        try:
            await page.wait_for_selector('h1, h2, .card, .alert', timeout=30000)
        except:
            logger.error("Analysis page did not load properly")
            return
        
        # Take screenshot of analysis results
        await page.screenshot(path=str(self.demo_dir / "03_analysis_results.png"))
        
        # Highlight risk score area
        risk_elements = page.locator('.badge, .alert, .text-danger, .text-warning, .text-success')
        if await risk_elements.count() > 0:
            await risk_elements.first.hover()
            await asyncio.sleep(2000)
        
        # Look for expandable sections
        collapsible = page.locator('.collapse, .accordion, [data-bs-toggle]')
        count = await collapsible.count()
        
        for i in range(min(3, count)):  # Show first 3 expandable items
            try:
                await collapsible.nth(i).click()
                await asyncio.sleep(1500)
            except:
                continue
        
        # Scroll to show more content
        await page.evaluate("window.scrollTo(0, 400)")
        await asyncio.sleep(2000)
    
    async def record_scene_4_ai_analysis(self, page):
        """Scene 4: Switch to AI analysis tab"""
        logger.info("Recording Scene 4: AI Analysis")
        
        # Look for AI tab or AI-related content
        ai_tab = page.locator('[data-tab="ai"], [href*="ai"], .nav-link:has-text("AI")')
        if await ai_tab.count() > 0:
            await ai_tab.first.click()
            await asyncio.sleep(2000)
        
        # Take screenshot of AI analysis
        await page.screenshot(path=str(self.demo_dir / "04_ai_analysis.png"))
        
        # Highlight AI-related content
        ai_content = page.locator('.ai-analysis, .gpt, [class*="ai"]')
        if await ai_content.count() > 0:
            await ai_content.first.hover()
            await asyncio.sleep(3000)
        
        # Show confidence scores or analysis details
        score_elements = page.locator('.confidence, .score, .percentage, .badge')
        if await score_elements.count() > 0:
            await score_elements.first.hover()
            await asyncio.sleep(2000)
        
        # Scroll through content
        await page.evaluate("window.scrollTo(0, 300)")
        await asyncio.sleep(2000)
    
    async def record_scene_5_history(self, page):
        """Scene 5: Show analysis history"""
        logger.info("Recording Scene 5: Analysis History")
        
        # Navigate to history page
        history_links = page.locator('a[href="/analyses"], a[href*="history"], .nav-link:has-text("History"), .nav-link:has-text("Analyses")')
        if await history_links.count() > 0:
            await history_links.first.click()
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(2000)
        
        # Take screenshot of history page
        await page.screenshot(path=str(self.demo_dir / "05_history.png"))
        
        # Show table or list content
        content_areas = page.locator('.table, .list-group, .card, .row')
        if await content_areas.count() > 0:
            await content_areas.first.hover()
            await asyncio.sleep(3000)
        
        # Show statistics if available
        stats_elements = page.locator('.stats, .metrics, .badge, .alert-info')
        if await stats_elements.count() > 0:
            await stats_elements.first.hover()
            await asyncio.sleep(2000)
    
    def create_gif_from_video(self, video_path):
        """Convert video to optimized GIF"""
        logger.info("Creating animated GIF from video...")
        
        gif_path = self.demo_dir / "demo.gif"
        
        # Use FFmpeg to extract frames and create GIF
        cmd = [
            'ffmpeg', '-i', str(video_path),
            '-vf', 'fps=10,scale=640:360:flags=lanczos,palettegen=reserve_transparent=0',
            '-y', str(self.demo_dir / 'palette.png')
        ]
        subprocess.run(cmd, check=True)
        
        cmd = [
            'ffmpeg', '-i', str(video_path), '-i', str(self.demo_dir / 'palette.png'),
            '-filter_complex', 'fps=10,scale=640:360:flags=lanczos[x];[x][1:v]paletteuse',
            '-y', str(gif_path)
        ]
        subprocess.run(cmd, check=True)
        
        # Clean up palette file
        (self.demo_dir / 'palette.png').unlink()
        
        logger.info(f"GIF created: {gif_path}")
        return gif_path
    
    async def generate_demo(self):
        """Main method to generate complete demo"""
        try:
            # Start Flask app
            if not await self.start_flask_app():
                logger.error("Failed to start Flask application")
                return False
            
            # Record demo
            await self.record_demo()
            
            # Find the recorded video
            video_files = list(self.demo_dir.glob("*.webm"))
            if not video_files:
                logger.error("No video file found after recording")
                return False
            
            video_path = video_files[0]
            logger.info(f"Demo video recorded: {video_path}")
            
            # Create GIF
            # gif_path = self.create_gif_from_video(video_path)
            
            logger.info("Demo generation completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Demo generation failed: {e}")
            return False
            
        finally:
            self.stop_flask_app()

async def main():
    """Main entry point"""
    demo_gen = DemoGenerator()
    success = await demo_gen.generate_demo()
    
    if success:
        print("✅ Demo generated successfully!")
        print(f"📁 Assets saved to: {demo_gen.demo_dir}")
    else:
        print("❌ Demo generation failed")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())