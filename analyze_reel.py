"""
Instagram Reel Fetcher & Analyser
Fetches public Instagram Reels metadata, downloads video & audio, and extracts key frames.
"""

import sys
import os
import re
import json
import urllib.request
import subprocess

def fetch_with_curl(url: str) -> str:
    res = subprocess.run(["curl", "-s", "-L", url], capture_output=True, text=True)
    return res.stdout

def download_file_curl(url: str, dest_path: str):
    subprocess.run(["curl", "-s", "-L", url, "-o", dest_path], check=True)

def extract_reel_data(url: str, output_dir: str = "output"):
    os.makedirs(output_dir, exist_ok=True)
    
    clean_url = url.split("?")[0].rstrip("/")
    embed_url = f"{clean_url}/embed/captioned/"
    
    print(f"[*] Fetching embed metadata from: {embed_url}")
    html = fetch_with_curl(embed_url)
        
    with open(os.path.join(output_dir, "embed.html"), "w", encoding="utf-8") as f:
        f.write(html)
        
    # Parse video URL
    idx = html.find("video_url")
    video_url = None
    if idx != -1:
        start = html.find("https:", idx)
        end = html.find(".mp4", start) + 4
        end_q = html.find('\\"', end)
        if end_q == -1:
            end_q = html.find('"', end)
        raw_url = html[start:end_q]
        video_url = raw_url.replace("\\/", "/").replace("\\\\/", "/").replace('\\"', "").replace("\\", "")
        
    # Extract metadata fields
    def search_field(pattern, default=None):
        m = re.search(pattern, html)
        return m.group(1) if m else default

    caption = search_field(r'edge_media_to_caption.*?text\\?":\\?"(.*?)\\')
    duration = search_field(r'video_duration\\?":([0-9.]+)')
    comments = search_field(r'edge_media_to_comment.*?count\\?":(\d+)')
    likes = search_field(r'edge_liked_by.*?count\\?":(\d+)')
    username = search_field(r'owner.*?username\\?":\\?"([^"]+?)\\')
    followers = search_field(r'edge_followed_by.*?count\\?":(\d+)')
    
    metadata = {
        "url": url,
        "username": username,
        "followers": int(followers) if followers else None,
        "caption": caption,
        "video_duration_seconds": float(duration) if duration else None,
        "comment_count": int(comments) if comments else None,
        "like_count": int(likes) if likes else None,
        "video_url": video_url
    }
    
    meta_path = os.path.join(output_dir, "metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"[✓] Metadata saved to {meta_path}")

    # Download Video if found
    video_path = os.path.join(output_dir, "reel.mp4")
    if video_url:
        print(f"[*] Downloading video to {video_path}...")
        download_file_curl(video_url, video_path)
        print(f"[✓] Video downloaded ({os.path.getsize(video_path) / (1024*1024):.2f} MB)")
        
        # Check ffmpeg availability
        ffmpeg_bin = os.path.join(sys.prefix, "bin", "ffmpeg")
        if not os.path.exists(ffmpeg_bin):
            ffmpeg_bin = "ffmpeg"
            
        # Extract audio
        audio_path = os.path.join(output_dir, "audio.mp3")
        print(f"[*] Extracting audio to {audio_path}...")
        subprocess.run([ffmpeg_bin, "-i", video_path, "-vn", "-c:a", "mp3", audio_path, "-y"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(audio_path):
            print(f"[✓] Audio extracted ({os.path.getsize(audio_path) / (1024*1024):.2f} MB)")
            
        # Extract keyframes (1 frame every 5s)
        frames_dir = os.path.join(output_dir, "frames")
        os.makedirs(frames_dir, exist_ok=True)
        print(f"[*] Extracting keyframes to {frames_dir}/...")
        subprocess.run([ffmpeg_bin, "-i", video_path, "-vf", "fps=1/5", os.path.join(frames_dir, "frame_%03d.jpg"), "-y"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        num_frames = len(os.listdir(frames_dir))
        print(f"[✓] Extracted {num_frames} frames.")

    return metadata

if __name__ == "__main__":
    target_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.instagram.com/p/De9SJQIg9Kv/"
    extract_reel_data(target_url)
