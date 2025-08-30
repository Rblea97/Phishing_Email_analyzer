# README Demo Section Template

Once you have recorded and uploaded your demo, replace the demo section in README.md with this:

```markdown
## 🎬 Live Demo

### 60-Second Demo Video
> **Watch the full phishing detection process in action**

[![Phishing Detection Demo](https://img.youtube.com/vi/YOUR_VIDEO_ID/maxresdefault.jpg)](https://www.loom.com/share/YOUR_LOOM_LINK)

*Click to watch: Upload → Analysis → Results in 60 seconds*

### Quick Preview (Animated GIF)
![Demo Preview](demo.gif)

**What you'll see in the demo:**
- Upload a phishing email sample
- Dual analysis (Rule-based + AI) processing 
- Detailed threat scoring and evidence
- Professional results dashboard
- Analysis history tracking

## 🧪 Try It Yourself

### Sample Phishing Emails
We've created 8 realistic phishing email samples for testing:

📧 **[Download Sample Files](samples_for_users/)** - Ready-to-test phishing examples

**Available Samples:**
- Corporate HR benefits scam
- PayPal security alert fraud  
- Amazon delivery issue scam
- Microsoft account warning
- Cryptocurrency wallet breach
- IRS tax refund fraud
- Business invoice scam
- Dating site romance scam

### Quick Start Demo
Want to record your own demo? Use our automated setup:

```bash
# Windows
.\start_demo_recording.bat

# Manual setup
python app_phase2.py
# Open http://localhost:5000 in browser
# Upload a sample file and record!
```

**Demo Recording Resources:**
- 📋 [Complete Recording Guide](DEMO_RECORDING_GUIDE.md)
- 🎨 [GIF Creation Guide](scripts/create_gif_guide.md)  
- ⚡ Quick test: `python scripts/test_setup.py`
```

## Upload Platforms and Instructions

### Option 1: Loom (Recommended - Easy sharing)

1. **Record or Upload**:
   - Go to https://www.loom.com/
   - Sign up for free account
   - Upload your demo video OR record directly in browser

2. **Get Share Link**:
   - After upload, click "Share" 
   - Copy the link (format: https://www.loom.com/share/abc123xyz)
   - Copy embed code if needed

3. **Update README**:
   ```markdown
   [![Demo Video](https://cdn.loom.com/sessions/thumbnails/YOUR_ID-with-play.gif)](https://www.loom.com/share/YOUR_LOOM_ID)
   ```

### Option 2: YouTube

1. **Upload Video**:
   - Go to YouTube Studio
   - Upload your demo video
   - Set visibility to "Unlisted" (accessible via link only)
   - Add title: "AI-Powered Phishing Detection System - Demo"

2. **Get Video ID**:
   - From URL like: https://youtu.be/ABC123XYZ
   - Video ID is: ABC123XYZ

3. **Update README**:
   ```markdown
   [![Demo Video](https://img.youtube.com/vi/YOUR_VIDEO_ID/maxresdefault.jpg)](https://youtu.be/YOUR_VIDEO_ID)
   ```

### Option 3: GitHub Releases (For GIF only)

1. **Create Release**:
   - Go to your GitHub repo
   - Releases → Create a new release
   - Upload demo.gif as an asset

2. **Use in README**:
   ```markdown
   ![Demo](https://github.com/Rblea97/Phishing_Email_analyzer/releases/download/v1.0.0/demo.gif)
   ```

## 🎯 Your Next Action Steps:

1. **📹 Record Demo**: 
   - Run `.\start_demo_recording.bat` 
   - Follow the 60-second script in the guide
   - Use OBS Studio, Loom, or built-in screen recording

2. **🎨 Create GIF**: 
   - Use EZGIF.com to convert best 10-15 seconds
   - Target: 640x360, 10 FPS, under 3MB
   - Save as `demo.gif` in project root

3. **🚀 Upload Video**:
   - Choose Loom for easy sharing
   - Get the shareable link
   - Optional: Also upload to YouTube

4. **📝 Update README**:
   - Replace placeholder links with your actual links
   - Test that video embeds work
   - Commit and push changes

5. **🎉 Share**:
   - Your GitHub README now has a professional demo
   - Share the repository link to showcase your work

## 📊 Success Checklist

Your demo is ready when you have:
- [ ] 60-second demo video recorded
- [ ] Video uploaded to Loom or YouTube
- [ ] Animated GIF created (10-15 seconds)
- [ ] README updated with actual links
- [ ] All links tested and working
- [ ] Sample files available for download
- [ ] Recording guides available for others

---

**Ready to record?** Run the test setup and then start recording:
```bash
python scripts/test_setup.py
.\start_demo_recording.bat
```