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
    
    caption = metadata.get("caption", "")
    username = metadata.get("username", "creator")
    title = metadata.get("title", caption)
    
    # 1. Inspect first frame (Hook Analysis)
    first_frame = os.path.join(frames_dir, "frame_001.jpg")
    hook_analysis = ""
    if os.path.exists(first_frame):
        print("[*] Analyzing hook & visual card (Frame 1)...")
        with open(first_frame, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        hook_prompt = (
            "Analyze this opening video frame from a short-form video (Reel / Short). "
            "1. Transcribe the on-screen text verbatim. "
            "2. Identify the target audience, emotional trigger, visual hierarchy, and the retention hook."
        )
        hook_analysis = query_ollama(hook_prompt, model=model, images_b64=[b64])
        
    # 2. Inspect a key visual frame (around the 65-70% mark of the video)
    all_frames = sorted(glob.glob(os.path.join(frames_dir, "frame_*.jpg")))
    diagram_analysis = ""
    if len(all_frames) > 3:
        target_idx = int(len(all_frames) * 0.65)
        diag_frame = all_frames[target_idx]
        print(f"[*] Analyzing key content visual from {os.path.basename(diag_frame)}...")
        with open(diag_frame, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        diag_prompt = (
            "Analyze the visual content in this key frame. "
            "If it is a technical architecture slide or diagram, explain the components, system design, and data flow. "
            "If it is a physical demonstration, recipe, or real-world subject, describe what is shown, the technique or ingredients/elements, and how it is visually presented."
        )
        diagram_analysis = query_ollama(diag_prompt, model=model, images_b64=[b64])

    # 3. Comprehensive synthesis combining transcript + metadata + visual domain
    print("[*] Generating comprehensive content synthesis & critique...")
    meta_summary = (
        f"Platform: {metadata.get('platform', 'Short-form')}, Title/Caption: {caption}, "
        f"Creator: @{username}, Followers: {metadata.get('followers')}, "
        f"Duration: {metadata.get('video_duration_seconds')}s, Comments: {metadata.get('comment_count')}"
    )
    synthesis_prompt = f"""
You are an expert media, content, and subject-matter analyst reviewing a viral short-form video (Instagram Reel or YouTube Short).

POST CONTEXT:
{meta_summary}

VERBATIM TRANSCRIPT:
\"\"\"{transcript}\"\"\"

Please provide an in-depth, structured breakdown tailored to the actual subject of the video (whether it is technical, culinary, lifestyle, or educational):
1. Executive Summary: Concise overview of what this video is actually about, its central message, and creator approach.
2. Core Subject Breakdown: Explain the core concepts, techniques, or demonstration shown (e.g. system architecture if tech, ingredients/methods if cooking, practical tips if educational).
3. Soundness & Quality Assessment: Evaluate the accuracy, practicality, and real-world feasibility of what was presented.
4. Audience & Viral Mechanics: Explain why this content engages viewers (hook-hold-payoff structure, audio choice, on-screen text, relatability, and discussion triggers).
"""
    synthesis = query_ollama(synthesis_prompt, model=model)
    
    return {
        "model_used": model,
        "hook_analysis": hook_analysis,
        "diagram_analysis": diagram_analysis,
        "synthesis": synthesis
    }
