"""
Instagram Reel Analyzer using local Nemotron on Ollama
100% local and open-source inference on Apple Silicon.
"""

import os
import sys
import glob
import json
import base64
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "nemotron-3.5-bolt:e4b-mxfp8"

def query_nemotron(prompt: str, images_b64: list = None) -> str:
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }
    if images_b64:
        payload["images"] = images_b64
        
    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        return res.get("response", "")

def analyze_reel_locally(output_dir: str = "output"):
    meta_path = os.path.join(output_dir, "metadata.json")
    frames_dir = os.path.join(output_dir, "frames")
    
    metadata = {}
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
            
    print(f"[*] Analyzing Reel with local Nemotron ({MODEL_NAME})...")
    
    # 1. Analyze the Hook (First Frame)
    first_frame = os.path.join(frames_dir, "frame_001.jpg")
    hook_analysis = ""
    if os.path.exists(first_frame):
        print("[*] Analyzing Hook & Title Card (Frame 1)...")
        with open(first_frame, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        hook_analysis = query_nemotron(
            "Analyze this opening frame of a tech Instagram Reel. "
            "1. Transcribe all text verbatim. "
            "2. Identify the target audience, hook tactic, and topic.",
            [b64]
        )
        print("\n--- Hook Analysis ---")
        print(hook_analysis)

    # 2. Analyze the Technical Solution Slide (Frame 18 - Ring Attention)
    sol_frame = os.path.join(frames_dir, "frame_018.jpg")
    arch_analysis = ""
    if os.path.exists(sol_frame):
        print("\n[*] Analyzing Technical Architecture (Frame 18)...")
        with open(sol_frame, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        arch_analysis = query_nemotron(
            "Explain the technical architecture diagram in this slide. "
            "What distributed computing technique is used and how does it solve LLM inference memory bottlenecks?",
            [b64]
        )
        print("\n--- Architecture Analysis ---")
        print(arch_analysis)

    # 3. Overall Summary
    full_report = {
        "model": MODEL_NAME,
        "metadata": metadata,
        "hook_analysis": hook_analysis,
        "architecture_analysis": arch_analysis
    }
    
    report_path = os.path.join(output_dir, "nemotron_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=2)
    print(f"\n[✓] Complete local Nemotron report saved to {report_path}")

if __name__ == "__main__":
    analyze_reel_locally()
