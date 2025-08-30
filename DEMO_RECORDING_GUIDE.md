# 🎬 Demo Recording Guide

This guide will help you create a professional 60-second demo of your phishing email analyzer.

## 🎯 Demo Script (60 seconds)

### Scene 1: Homepage (0-10 seconds)
- **Action**: Open http://localhost:5000
- **Narration**: "AI-powered phishing detection system combining rule-based analysis with GPT-4o-mini"
- **Visual**: Show clean, professional interface
- **Hover**: Over main heading and upload area

### Scene 2: File Upload (10-20 seconds)  
- **Action**: Click "Choose File" and select `corporate_benefits_scam.eml`
- **Narration**: "Upload suspicious email for dual analysis"
- **Visual**: Show file selection and upload process
- **Action**: Click Submit/Analyze

### Scene 3: Rule-Based Analysis (20-35 seconds)
- **Action**: Show analysis results page
- **Narration**: "Rule-based engine detects multiple threat indicators"
- **Visual**: Highlight risk score, expand evidence sections
- **Focus**: Show detailed evidence breakdown

### Scene 4: AI Analysis (35-50 seconds)
- **Action**: Click AI Analysis tab (if available)
- **Narration**: "GPT-4o-mini provides advanced threat assessment"
- **Visual**: Show AI insights and confidence scores
- **Focus**: Highlight unique AI findings

### Scene 5: Wrap-up (50-60 seconds)
- **Action**: Navigate to analysis history
- **Narration**: "Complete audit trail with professional reporting"
- **Visual**: Show multiple analysis results
- **End**: Return to homepage

## 🎥 Recording Tools

### Windows Options:
1. **OBS Studio** (Recommended - Free)
   - Download: https://obsproject.com/
   - Professional features, high quality
   
2. **Xbox Game Bar** (Built-in)
   - Press `Win + G` to start recording
   - Quick and easy, decent quality

3. **Loom** (Web-based)
   - https://www.loom.com/
   - Easy sharing, automatic cloud upload

### Mac Options:
1. **QuickTime Player** (Built-in)
   - File → New Screen Recording
   - Simple and effective

2. **OBS Studio** (Free)
   - Same as Windows version

### Screen Recording Settings:
- **Resolution**: 1280x720 (720p HD)
- **Frame Rate**: 30 FPS
- **Audio**: Include microphone for narration
- **Format**: MP4 (for best compatibility)

## 📋 Pre-Recording Checklist

### 1. Environment Setup
- [ ] Close unnecessary applications
- [ ] Clean desktop/background
- [ ] Set browser to full screen or clean window
- [ ] Test audio levels
- [ ] Have sample files ready

### 2. Flask App Preparation
- [ ] Start Flask app: `python app_phase2.py`
- [ ] Verify app loads at http://localhost:5000
- [ ] Test upload with one sample file
- [ ] Ensure OpenAI API key is working (for AI analysis)

### 3. Sample Files Ready
Use files from `samples_for_users/`:
- [ ] `corporate_benefits_scam.eml` (Primary demo file)
- [ ] `paypal_security_alert.eml` (Backup option)
- [ ] `crypto_wallet_breach.eml` (High-threat example)

## 🎬 Recording Steps

### Step 1: Start Recording
```bash
# Terminal 1: Start Flask app
cd "C:\Users\Owner\Documents\Projects\Phising_Email_analyzer"
python app_phase2.py

# Terminal 2: Verify it's running
curl http://localhost:5000  # Or open in browser
```

### Step 2: Record Demo
1. **Start screen recording**
2. **Open browser to localhost:5000**
3. **Follow the 60-second script above**
4. **Keep movements smooth and deliberate**
5. **Speak clearly for narration**

### Step 3: Stop Recording
- **Stop recording**
- **Save file as `phishing_analyzer_demo.mp4`**
- **Review the recording**

## 🎨 Post-Production Tips

### Video Editing (Optional):
- **Trim** start/end for clean beginning/ending
- **Add title slide** with project name
- **Add captions** for accessibility
- **Export at 720p** for web optimization

### Recommended Tools:
- **DaVinci Resolve** (Free, professional)
- **OpenShot** (Free, simple)
- **Camtasia** (Paid, user-friendly)

## 🚀 Upload and Sharing

### 1. Loom Upload (Recommended)
1. Go to https://www.loom.com/
2. Upload your video file
3. Get shareable link
4. Copy embed code for README

### 2. YouTube Upload
1. Upload to YouTube
2. Set to "Unlisted" or "Public"
3. Get video ID for embedding
4. Use thumbnail image

### 3. GitHub Integration
Update README.md with:
```markdown
[![Demo Video](thumbnail.png)](https://www.loom.com/share/your-link-here)
```

## 📊 Quality Checklist

After recording, verify:
- [ ] Audio is clear and audible
- [ ] Screen is readable (text not too small)
- [ ] Demo flows smoothly between sections
- [ ] All key features are demonstrated
- [ ] Total time is 45-65 seconds
- [ ] No sensitive information visible
- [ ] Professional appearance

## 🎯 Success Metrics

A successful demo should show:
- [ ] Upload process (user-friendly)
- [ ] Dual analysis approach (rule + AI)
- [ ] Detailed threat detection
- [ ] Professional interface
- [ ] Multiple phishing indicators
- [ ] Evidence-based results

## 🔧 Troubleshooting

### Common Issues:
1. **Flask app won't start**
   - Check OpenAI API key in .env
   - Install missing dependencies
   - Check port 5000 availability

2. **Upload fails**
   - Use provided sample files
   - Check file size (under 25MB)
   - Verify .eml extension

3. **AI analysis doesn't work**
   - Verify OpenAI API key
   - Check internet connection
   - Try rule-based analysis only

### Quick Test:
```bash
python scripts/test_setup.py
```

## 📝 Demo Script Template

Use this narration script:

"This is an AI-powered phishing detection system that combines rule-based analysis with GPT-4o-mini artificial intelligence. 

[Upload file] Let's analyze a suspicious corporate email. The system processes the email through both detection engines.

[Show results] Our rule-based engine identifies multiple threat indicators including authentication failures and urgency tactics, giving this email a high risk score.

[AI tab] The AI analysis provides additional context, identifying subtle social engineering patterns that rules might miss.

[History] The system maintains a complete audit trail, making it perfect for security teams and training purposes.

This demonstrates how advanced AI can enhance traditional cybersecurity tools for better threat detection."

---

Ready to create your demo? Run `python scripts/test_setup.py` to verify everything is working, then start recording!