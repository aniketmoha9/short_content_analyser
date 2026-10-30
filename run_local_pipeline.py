"""
Complete 100% Local Open-Source Instagram Reel Pipeline
Components:
- Downloader & Extractor: analyze_reel.py (curl + ffmpeg)
- ASR Transcriber: transcribe_whisper.py (faster-whisper)
- Multimodal Reasoning & Synthesis: analyze_with_nemotron.py (Nemotron on Ollama)
"""

import sys
import os
import json
from analyze_reel import extract_reel_data
from transcribe_whisper import transcribe_audio
from analyze_with_nemotron import query_nemotron

def run_pipeline(url: str, whisper_model: str = "base"):
    output_dir = "output"
    print("=" * 60)
    print(f"STEP 1: Fetching Reel Media from {url}")
    print("=" * 60)
    meta = extract_reel_data(url, output_dir=output_dir)
    
    audio_path = os.path.join(output_dir, "audio.mp3")
    transcript = ""
    if os.path.exists(audio_path):
        print("\n" + "=" * 60)
        print(f"STEP 2: Transcribing Audio with faster-whisper ({whisper_model})")
        print("=" * 60)
        transcript = transcribe_audio(audio_path, model_size=whisper_model)
        
    print("\n" + "=" * 60)
    print("STEP 3: Running Deep Analysis with Local Nemotron (Ollama)")
    print("=" * 60)
    
    # Send transcript + hook frame to Nemotron
    import base64
    first_frame = os.path.join(output_dir, "frames", "frame_001.jpg")
    img_b64 = None
    if os.path.exists(first_frame):
        with open(first_frame, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")
            
    prompt = f"""
Here is the audio transcript of an Instagram tech reel:
\"\"\"{transcript}\"\"\"

And attached is the opening title card frame.

Please provide:
1. A concise executive summary of the reel.
2. The core technical bottleneck discussed and the proposed engineering solution.
3. An evaluation of the content effectiveness and audience hook.
"""
    images = [img_b64] if img_b64 else None
    response = query_nemotron(prompt, images_b64=images)
    
    print("\n--- Nemotron Executive Synthesis ---")
    print(response)
    
    final_output = {
        "url": url,
        "metadata": meta,
        "whisper_transcript": transcript,
        "nemotron_synthesis": response
    }
    
    final_path = os.path.join(output_dir, "final_local_report.json")
    with open(final_path, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2)
    print(f"\n[✓] Pipeline finished! Full report saved to {final_path}")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "https://www.instagram.com/p/De9SJQIg9Kv/"
    run_pipeline(target)
