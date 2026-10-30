"""
Local Audio Transcriber using nvidia/nemotron-3.5-asr-streaming-0.6b via MLX
100% open-source NVIDIA FastConformer-RNNT running locally on Apple Silicon Metal
"""

import sys
import os
import time
import json

def transcribe_with_nemotron_asr(audio_path: str = "output/speech.wav", language: str = "auto"):
    if not os.path.exists(audio_path):
        print(f"Error: audio file {audio_path} not found.")
        sys.exit(1)

    print(f"[*] Initializing NVIDIA Nemotron-3.5-ASR-Streaming-0.6B on Apple Silicon...")
    from mlx_audio.stt import load
    
    t0 = time.time()
    model = load("mlx-community/nemotron-3.5-asr-streaming-0.6b")
    load_time = time.time() - t0
    print(f"[✓] Model loaded in {load_time:.2f} seconds.")
    
    print(f"[*] Transcribing {audio_path} (language={language})...")
    t1 = time.time()
    kwargs = {}
    if language != "auto":
        kwargs["language"] = language
        
    result = model.generate(audio_path, **kwargs)
    infer_time = time.time() - t1
    
    text = result.text if hasattr(result, "text") else str(result)
    print(f"\n[✓] Transcription finished in {infer_time:.2f} seconds.")
    print("=" * 60)
    print("NVIDIA Nemotron 3.5 ASR Transcript:")
    print("=" * 60)
    print(text.strip())
    print("=" * 60)
    
    output_dir = os.path.dirname(audio_path) or "output"
    txt_path = os.path.join(output_dir, "nemotron_asr_transcript.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text.strip())
        
    json_path = os.path.join(output_dir, "nemotron_asr_transcript.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "model": "nvidia/nemotron-3.5-asr-streaming-0.6b",
            "audio_file": audio_path,
            "infer_time_seconds": round(infer_time, 2),
            "transcript": text.strip()
        }, f, indent=2)
        
    print(f"[✓] Saved to {txt_path} and {json_path}")
    return text.strip()

if __name__ == "__main__":
    audio_file = sys.argv[1] if len(sys.argv) > 1 else "output/speech.wav"
    lang = sys.argv[2] if len(sys.argv) > 2 else "auto"
    transcribe_with_nemotron_asr(audio_file, lang)
