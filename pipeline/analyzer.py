"""
Local Multimodal Reasoning & Synthesis Module
Communicates with local Ollama instance (Nemotron / Bonsai).
"""

import os
import glob
import json
import base64
import urllib.request
from typing import Dict, Any, List, Optional

OLLAMA_API = "http://localhost:11434/api/generate"

def query_ollama(prompt: str, model: str = "nemotron-3.5-bolt:e4b-mxfp8", images_b64: Optional[List[str]] = None) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    if images_b64:
        payload["images"] = images_b64
        
    req = urllib.request.Request(
        OLLAMA_API,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        return res.get("response", "").strip()

def analyze_content(
    transcript: str,
    frames_dir: str,
    metadata: Dict[str, Any],
    model: str = "nemotron-3.5-bolt:e4b-mxfp8"
) -> Dict[str, Any]:
    print(f"[*] Running multimodal reasoning using local model '{model}'...")
    
    # 1. Inspect first frame (Hook Analysis)
    first_frame = os.path.join(frames_dir, "frame_001.jpg")
    hook_analysis = ""
    if os.path.exists(first_frame):
        print("[*] Analyzing hook & visual card (Frame 1)...")
        with open(first_frame, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        hook_prompt = (
            "Analyze this opening video frame from a tech Instagram Reel. "
            "1. Transcribe the on-screen text verbatim. "
            "2. Identify the target audience, emotional trigger, and retention hook."
        )
        hook_analysis = query_ollama(hook_prompt, model=model, images_b64=[b64])
        
    # 2. Inspect a key architecture diagram frame (e.g. around the 70% mark of the video)
    all_frames = sorted(glob.glob(os.path.join(frames_dir, "frame_*.jpg")))
    diagram_analysis = ""
    if len(all_frames) > 5:
        # Select frame around 70% mark (e.g. frame 18 of 25)
        target_idx = int(len(all_frames) * 0.7)
        diag_frame = all_frames[target_idx]
        print(f"[*] Analyzing technical diagram from {os.path.basename(diag_frame)}...")
        with open(diag_frame, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        diag_prompt = (
            "Explain the technical architecture diagram shown in this slide. "
            "What distributed computing technique or system design is illustrated, "
            "what problem does it solve, and how does it function?"
        )
        diagram_analysis = query_ollama(diag_prompt, model=model, images_b64=[b64])

    # 3. Comprehensive synthesis combining transcript + metadata
    print("[*] Generating comprehensive technical synthesis & critique...")
    meta_summary = (
        f"Creator: @{metadata.get('username')}, Followers: {metadata.get('followers')}, "
        f"Duration: {metadata.get('video_duration_seconds')}s, Comments: {metadata.get('comment_count')}"
    )
    synthesis_prompt = f"""
You are an expert AI Systems Architect reviewing a viral tech video.

POST CONTEXT:
{meta_summary}

VERBATIM TRANSCRIPT:
\"\"\"{transcript}\"\"\"

Please provide a detailed, well-structured breakdown:
1. Executive Summary (Concise overview of the reel's core narrative)
2. The Engineering Problem (Detail the computational bottleneck, mathematics, and limitations mentioned)
3. The Proposed System Architecture (Explain the specific solutions proposed and how they work)
4. Critical Engineering Reality Check (Critique the feasibility, realistic implementation hurdles, and whether this is a sound interview answer)
5. Audience & Viral Mechanics (Why this video works well on social media)
"""
    synthesis = query_ollama(synthesis_prompt, model=model)
    
    return {
        "model_used": model,
        "hook_analysis": hook_analysis,
        "diagram_analysis": diagram_analysis,
        "synthesis": synthesis
    }
