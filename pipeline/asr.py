"""
Automatic Speech Recognition (ASR) Module
Supports:
1. NVIDIA Nemotron 3.5 ASR (FastConformer-RNNT on Apple Silicon Metal via MLX)
2. Faster-Whisper (OpenAI Whisper via CTranslate2 int8)
"""

import os
import time
import json
from typing import Dict, Any

def transcribe_with_nemotron(audio_wav: str, language: str = "auto") -> Dict[str, Any]:
    print("[*] Running NVIDIA Nemotron-3.5-ASR (Apple Silicon Metal)...")
    from mlx_audio.stt import load
    
    t0 = time.time()
    model = load("mlx-community/nemotron-3.5-asr-streaming-0.6b")
    load_time = time.time() - t0
    
    t1 = time.time()
    kwargs = {}
    if language != "auto":
        kwargs["language"] = language
        
    result = model.generate(audio_wav, **kwargs)
    infer_time = time.time() - t1
    text = result.text.strip() if hasattr(result, "text") else str(result).strip()
    
    print(f"[✓] Nemotron ASR transcribed in {infer_time:.2f}s (Load: {load_time:.2f}s)")
    return {
        "engine": "nvidia/nemotron-3.5-asr-streaming-0.6b",
        "backend": "MLX (Metal GPU)",
        "infer_time_seconds": round(infer_time, 2),
        "transcript": text
    }

def transcribe_with_whisper(audio_file: str, model_size: str = "base") -> Dict[str, Any]:
    print(f"[*] Running Faster-Whisper ({model_size} model on CPU/int8)...")
    from faster_whisper import WhisperModel
    
    t0 = time.time()
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    load_time = time.time() - t0
    
    t1 = time.time()
    segments, info = model.transcribe(audio_file, beam_size=5, vad_filter=True)
    
    segment_data = []
    text_pieces = []
    for s in segments:
        text_pieces.append(s.text.strip())
        segment_data.append({
            "start": round(s.start, 2),
            "end": round(s.end, 2),
            "text": s.text.strip()
        })
        
    infer_time = time.time() - t1
    full_text = " ".join(text_pieces)
    
    print(f"[✓] Faster-Whisper transcribed in {infer_time:.2f}s (Language: {info.language})")
    return {
        "engine": f"faster-whisper-{model_size}",
        "backend": "CTranslate2 (int8)",
        "detected_language": info.language,
        "language_confidence": round(info.language_probability, 4),
        "infer_time_seconds": round(infer_time, 2),
        "transcript": full_text,
        "segments": segment_data
    }

def transcribe_audio(audio_path: str, engine: str = "nemotron", model_size: str = "base", language: str = "auto") -> Dict[str, Any]:
    if engine.lower() in ["nemotron", "nemo", "nvidia"]:
        return transcribe_with_nemotron(audio_path, language=language)
    elif engine.lower() in ["whisper", "faster-whisper"]:
        return transcribe_with_whisper(audio_path, model_size=model_size)
    else:
        raise ValueError(f"Unknown ASR engine '{engine}'. Choose 'nemotron' or 'whisper'.")
