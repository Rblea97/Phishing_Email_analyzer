# 🎨 Creating Animated GIF from Demo Video

## Option 1: Online Tools (Easiest)

### 1. EZGIF (Recommended)
- Go to https://ezgif.com/video-to-gif
- Upload your demo video
- Settings:
  - Size: 640x360 (for GitHub)
  - Frame rate: 10 FPS
  - Start/End time: Select best 10-15 seconds
- Download optimized GIF

### 2. CloudConvert
- Go to https://cloudconvert.com/mp4-to-gif
- Upload video
- Advanced settings:
  - Width: 640px
  - Quality: Medium
  - FPS: 10
- Convert and download

## Option 2: Local Tools

### Windows - FFmpeg (If installed)
```bash
# Install FFmpeg first from https://ffmpeg.org/
# Then run:
ffmpeg -i your_demo_video.mp4 -vf "fps=10,scale=640:360:flags=lanczos" -t 15 demo.gif
```

### Mac - GIF Brewery (App Store)
- Import your video
- Set dimensions to 640x360
- Set frame rate to 10 FPS
- Select 10-15 second segment
- Export as GIF

### Cross-platform - GIMP (Free)
1. Open GIMP
2. File → Open as Layers → Select video frames
3. Image → Scale Image → 640x360
4. File → Export As → demo.gif
5. Check "As Animation"

## 📏 Recommended GIF Settings

- **Dimensions**: 640x360 pixels (16:9 aspect ratio)
- **Duration**: 10-15 seconds (looping)
- **Frame Rate**: 8-12 FPS
- **File Size**: Under 3MB (GitHub limit is 25MB, but smaller is better)
- **Quality**: Medium (balance between size and clarity)

## 🎬 Best GIF Segments to Extract

Choose one of these segments from your 60-second demo:

### Option A: Upload Process (10 seconds)
- Show file selection
- Upload button click
- Brief loading/processing
- Results appearing

### Option B: Results Highlight (12 seconds)
- Risk score display
- Evidence sections expanding
- Tab switching (rule-based to AI)
- Key findings highlighted

### Option C: Complete Workflow (15 seconds)
- Quick upload
- Analysis processing
- Results overview
- History page glimpse

## 📝 Quick Creation Steps

1. **Record your 60-second demo**
2. **Identify the best 10-15 second segment**
3. **Use EZGIF.com for quick conversion**:
   - Upload video
   - Set start time (e.g., 15 seconds in)
   - Set duration (e.g., 12 seconds)
   - Size: 640x360
   - FPS: 10
   - Download optimized GIF
4. **Save as `demo.gif` in project root**
5. **Update README.md**:
   ```markdown
   ![Demo Preview](demo.gif)
   ```

## 🔧 Optimization Tips

### Reduce File Size:
- **Lower FPS**: 8-10 instead of 30
- **Smaller dimensions**: 480x270 if needed
- **Shorter duration**: 8-12 seconds
- **Fewer colors**: Most tools auto-optimize

### Improve Quality:
- **Clean background**: Solid colors compress better
- **Avoid rapid movement**: Smooth transitions
- **High contrast text**: Easier to read when compressed
- **Stable browser window**: Consistent framing

## 📊 Testing Your GIF

Before using in README:
- [ ] File size under 5MB (preferably under 2MB)
- [ ] Text is readable at small sizes
- [ ] Loops smoothly
- [ ] Shows key functionality clearly
- [ ] Loads quickly in browser

## 🚀 README Integration

Once you have your GIF:

```markdown
## 🎬 Quick Demo

![Phishing Analyzer Demo](demo.gif)

*60-second demo showing upload, analysis, and results*

### Full Demo Video
[![Watch Full Demo](demo-thumbnail.png)](https://www.loom.com/share/your-link)
```

## 💡 Pro Tips

1. **Create multiple GIFs**: One for upload, one for results
2. **Add captions**: Brief text overlays in video editing
3. **Use consistent timing**: 3-5 seconds per major action
4. **Test on mobile**: Ensure readability on small screens
5. **Version control**: Keep original video for re-editing

---

**Ready to create your GIF?**
1. Record your demo using the guide
2. Use EZGIF.com for quick conversion
3. Test the result
4. Add to your README