#!/usr/bin/env python3
"""
Quick script to update README with your YouTube link
"""

def update_youtube_link():
    """Update the README with YouTube link"""
    print("YouTube Link Updater")
    print("=" * 30)
    
    # Get YouTube URL from user
    youtube_url = input("\nPaste your YouTube URL (e.g., https://youtu.be/ABC123XYZ): ").strip()
    
    if not youtube_url:
        print("No URL provided. Exiting.")
        return
    
    # Extract video ID
    if "youtu.be/" in youtube_url:
        video_id = youtube_url.split("youtu.be/")[-1]
    elif "youtube.com/watch?v=" in youtube_url:
        video_id = youtube_url.split("v=")[-1].split("&")[0]
    else:
        print("Invalid YouTube URL format. Please use youtu.be/ID or youtube.com/watch?v=ID")
        return
    
    print(f"Extracted video ID: {video_id}")
    
    # Read current README
    readme_path = "README.md"
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update the placeholder links
    old_video_line = '[![Phishing Detection Demo](https://img.youtube.com/vi/demo_placeholder/maxresdefault.jpg)](https://www.loom.com/share/your-demo-link-here)'
    new_video_line = f'[![Phishing Detection Demo](https://img.youtube.com/vi/{video_id}/maxresdefault.jpg)](https://youtu.be/{video_id})'
    
    if old_video_line in content:
        content = content.replace(old_video_line, new_video_line)
        
        # Write back to file
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"\n✅ README updated successfully!")
        print(f"📹 Video: https://youtu.be/{video_id}")
        print(f"🖼️  Thumbnail: https://img.youtube.com/vi/{video_id}/maxresdefault.jpg")
        print(f"\nNext steps:")
        print("1. Check that your video is public or unlisted")
        print("2. Test the links work by opening README.md")
        print("3. Commit and push to GitHub")
        
    else:
        print("❌ Could not find placeholder text in README. You may need to update manually.")

if __name__ == "__main__":
    update_youtube_link()