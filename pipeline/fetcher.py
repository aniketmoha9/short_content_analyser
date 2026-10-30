"""
Media Fetcher: Bypasses Instagram login-walls, extracts metadata,
downloads the raw video stream, and extracts audio and keyframes via FFmpeg.
"""

import os
import sys
import re
import json
import subprocess
from typing import Dict, Any, Optional

def get_ffmpeg_path() -> str:
    """Returns local FFmpeg binary path."""
    venv_ffmpeg = os.path.join(sys.prefix, "bin", "ffmpeg")
    if os.path.exists(venv_ffmpeg):
        return venv_ffmpeg
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return "ffmpeg"

def fetch_reel(url: str, output_dir: str = "output", frame_interval_seconds: int = 5) -> Dict[str, Any]:
    os.makedirs(output_dir, exist_ok=True)
    frames_dir = os.path.join(output_dir, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    
    clean_url = url.split("?")[0].rstrip("/")
    embed_url = f"{clean_url}/embed/captioned/"
    
    print(f"[*] Fetching embed payload: {embed_url}")
    curl_cmd = ["curl", "-s", "-L", embed_url]
    res = subprocess.run(curl_cmd, capture_output=True, text=True)
    html = res.stdout
    
    # Save embed HTML
    with open(os.path.join(output_dir, "embed.html"), "w", encoding="utf-8") as f:
        f.write(html)
        
    # Extract direct video URL
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
    print(f"[✓] Metadata saved: creator=@{username}, duration={duration}s, comments={comments}")

    video_path = os.path.join(output_dir, "reel.mp4")
    speech_wav = os.path.join(output_dir, "speech.wav")
    audio_mp3 = os.path.join(output_dir, "audio.mp3")
    
    if not video_url:
        print("[!] Warning: Could not find direct video_url in embed payload.")
        return metadata

    # Download raw video
    print(f"[*] Downloading raw video stream ({video_path})...")
    subprocess.run(["curl", "-s", "-L", video_url, "-o", video_path], check=True)
    video_size_mb = os.path.getsize(video_path) / (1024 * 1024)
    print(f"[✓] Video downloaded ({video_size_mb:.2f} MB)")
    
    ffmpeg_bin = get_ffmpeg_path()
    
    # 1. Extract 16kHz mono WAV (ideal for ASR engines)
    print(f"[*] Converting audio to 16kHz mono WAV ({speech_wav})...")
    subprocess.run([
        ffmpeg_bin, "-i", video_path,
        "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
        speech_wav, "-y"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # 2. Extract MP3 (lightweight audio preview)
    subprocess.run([
        ffmpeg_bin, "-i", video_path,
        "-vn", "-c:a", "mp3",
        audio_mp3, "-y"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # 3. Extract keyframe snapshots every N seconds
    print(f"[*] Extracting keyframes every {frame_interval_seconds}s to {frames_dir}/...")
    subprocess.run([
        ffmpeg_bin, "-i", video_path,
        "-vf", f"fps=1/{frame_interval_seconds}",
        os.path.join(frames_dir, "frame_%03d.jpg"),
        "-y"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    num_frames = len([f for f in os.listdir(frames_dir) if f.endswith(".jpg")])
    print(f"[✓] Extracted {num_frames} keyframe snapshots.")
    
    metadata["video_path"] = video_path
    metadata["speech_wav"] = speech_wav
    metadata["audio_mp3"] = audio_mp3
    metadata["frames_dir"] = frames_dir
    metadata["frame_count"] = num_frames
    
    return metadata
