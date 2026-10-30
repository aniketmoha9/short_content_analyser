"""
Local Audio Transcriber using faster-whisper
100% open-source local automatic speech recognition (ASR)
"""

import sys
import os
import json
import time

def transcribe_audio(audio_path: str = "output/audio.mp3", model_size: str = "base"):
    if not os.path.exists(audio_path):
        print(f"Error: audio file {audio_path} not found.")
        sys.exit(1)
        
    print(f"[*] Loading faster-whisper model: '{model_size}'...")
    from faster_whisper import WhisperModel
    
    start_time = time.time()
    # On Apple Silicon / macOS CPU with int8 quantization
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    load_time = time.time() - start_time
    print(f"[✓] Model loaded in {load_time:.2f} seconds.")
    
    print(f"[*] Transcribing {audio_path}...")
    transcribe_start = time.time()
    segments, info = model.transcribe(
        audio_path,
        beam_size=5,
        vad_filter=True  # Voice activity detection to trim silence
    )
    
    print(f"[✓] Detected language: '{info.language}' (confidence: {info.language_probability:.2%})")
    print(f"[✓] Audio duration: {info.duration:.2f} seconds\n")
    
    segment_list = []
    text_pieces = []
    
    for seg in segments:
        line = f"[{seg.start:05.2f}s -> {seg.end:05.2f}s] {seg.text.strip()}"
        print(line)
        segment_list.append({
            "start": round(seg.start, 2),
            "end": round(seg.end, 2),
            "text": seg.text.strip()
        })
        text_pieces.append(seg.text.strip())
        
    total_time = time.time() - transcribe_start
    full_text = " ".join(text_pieces)
    
    output_dir = os.path.dirname(audio_path) or "output"
    
    # Save text
    txt_path = os.path.join(output_dir, "whisper_transcript.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(full_text)
        
    # Save structured JSON
    json_path = os.path.join(output_dir, "whisper_transcript.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "model": model_size,
            "language": info.language,
            "language_confidence": info.language_probability,
            "duration_seconds": info.duration,
            "transcription_time_seconds": round(total_time, 2),
            "segments": segment_list,
            "full_text": full_text
        }, f, indent=2)
        
    print(f"\n[✓] Transcription finished in {total_time:.2f} seconds.")
    print(f"[✓] Saved transcript to {txt_path} and {json_path}")
    return full_text

if __name__ == "__main__":
    audio_file = sys.argv[1] if len(sys.argv) > 1 else "output/audio.mp3"
    size = sys.argv[2] if len(sys.argv) > 2 else "base"
    transcribe_audio(audio_file, size)
