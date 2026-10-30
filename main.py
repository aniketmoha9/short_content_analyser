#!/usr/bin/env python3
"""
Instagram Video & Reel Analyser CLI (100% Local & Open-Source)
Fetches public Instagram Reels, transcribes speech with local ASR (Nemotron or Whisper),
and performs multimodal technical analysis using local Ollama models.
"""

import sys
import os
import argparse
import time
from pipeline.fetcher import fetch_reel
from pipeline.asr import transcribe_audio
from pipeline.analyzer import analyze_content
from pipeline.reporter import generate_report

def main():
    parser = argparse.ArgumentParser(
        description="100% Open-Source Local Instagram Reel Analyser (Nemotron, Whisper & Ollama)"
    )
    parser.add_argument(
        "url",
        type=str,
        help="Instagram Reel or Video URL (e.g. https://www.instagram.com/p/De9SJQIg9Kv/)"
    )
    parser.add_argument(
        "--asr",
        choices=["nemotron", "whisper"],
        default="nemotron",
        help="Local ASR engine to use (default: nemotron for high-fidelity Hindi/multilingual FastConformer; or whisper for ultra-fast CTranslate2)"
    )
    parser.add_argument(
        "--whisper-size",
        type=str,
        default="base",
        choices=["tiny", "base", "small", "medium", "large-v3"],
        help="Whisper model size if using --asr whisper (default: base)"
    )
    parser.add_argument(
        "--language",
        type=str,
        default="auto",
        help="Language code for ASR (e.g. auto, hi, en, es; default: auto)"
    )
    parser.add_argument(
        "--llm",
        type=str,
        default="nemotron-3.5-bolt:e4b-mxfp8",
        help="Local Ollama model name for multimodal synthesis (default: nemotron-3.5-bolt:e4b-mxfp8)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Directory to save media, frames, transcripts, and reports (default: output)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Interval in seconds between extracted keyframe snapshots (default: 5)"
    )
    
    args = parser.parse_args()
    
    total_start = time.time()
    print("=" * 65)
    print("      INSTAGRAM OPEN-SOURCE REEL ANALYSER PIPELINE      ")
    print("=" * 65)
    print(f"Target URL:    {args.url}")
    print(f"ASR Engine:    {args.asr} (language: {args.language})")
    print(f"Ollama Model:  {args.llm}")
    print(f"Output Dir:    {args.output_dir}")
    print("=" * 65)
    
    # STEP 1: Fetch metadata & download media
    print("\n>>> STEP 1: Fetching Media & Extracting Keyframes")
    metadata = fetch_reel(args.url, output_dir=args.output_dir, frame_interval_seconds=args.interval)
    
    # STEP 2: Transcribe Speech
    print(f"\n>>> STEP 2: Transcribing Audio using {args.asr.upper()}")
    audio_target = metadata.get("speech_wav") or metadata.get("audio_mp3")
    if not audio_target or not os.path.exists(audio_target):
        print("[!] Error: No audio track found to transcribe.")
        sys.exit(1)
        
    asr_result = transcribe_audio(
        audio_path=audio_target,
        engine=args.asr,
        model_size=args.whisper_size,
        language=args.language
    )
    
    # STEP 3: Multimodal Reasoning with Local Ollama
    print(f"\n>>> STEP 3: Multimodal Synthesis & Critique with {args.llm}")
    ai_analysis = analyze_content(
        transcript=asr_result.get("transcript", ""),
        frames_dir=metadata.get("frames_dir", os.path.join(args.output_dir, "frames")),
        metadata=metadata,
        model=args.llm
    )
    
    # STEP 4: Generate Reports
    print("\n>>> STEP 4: Compiling Reports")
    report_file = generate_report(
        metadata=metadata,
        asr_result=asr_result,
        ai_analysis=ai_analysis,
        output_dir=args.output_dir
    )
    
    elapsed = time.time() - total_start
    print("\n" + "=" * 65)
    print(f"[✓] Complete pipeline finished successfully in {elapsed:.2f} seconds!")
    print(f"[✓] View the full Markdown report at: {report_file}")
    print("=" * 65)

if __name__ == "__main__":
    main()
