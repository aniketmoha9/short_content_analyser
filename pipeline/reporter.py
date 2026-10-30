"""
Report Generator Module: Formats extracted data, transcripts,
and local AI synthesis into human-readable Markdown and structured JSON.
"""

import os
import json
from typing import Dict, Any

def generate_report(
    metadata: Dict[str, Any],
    asr_result: Dict[str, Any],
    ai_analysis: Dict[str, Any],
    output_dir: str = "output"
) -> str:
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Save complete raw JSON
    combined_data = {
        "metadata": metadata,
        "asr": asr_result,
        "ai_analysis": ai_analysis
    }
    json_path = os.path.join(output_dir, "analysis_report.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(combined_data, f, indent=2, ensure_ascii=False)
        
    # 2. Render publication-grade Markdown
    username = metadata.get("username", "unknown")
    duration = metadata.get("video_duration_seconds", "N/A")
    followers = metadata.get("followers", "N/A")
    comments = metadata.get("comment_count", "N/A")
    url = metadata.get("url", "")
    caption = metadata.get("caption", "")
    asr_engine = asr_result.get("engine", "")
    asr_time = asr_result.get("infer_time_seconds", "")
    transcript = asr_result.get("transcript", "")
    llm_model = ai_analysis.get("model_used", "")
    
    hook_sec = ai_analysis.get("hook_analysis", "")
    diag_sec = ai_analysis.get("diagram_analysis", "")
    synth_sec = ai_analysis.get("synthesis", "")
    
    followers_str = f"{followers:,}" if isinstance(followers, int) else str(followers)
    
    is_yt = "youtube" in url or "youtu.be" in url
    creator_display = f"[@{username}](https://www.youtube.com/@{username})" if is_yt else f"[@{username}](https://www.instagram.com/{username}/)"
    platform_name = "YouTube Short" if is_yt else "Instagram Reel"
    
    md_content = f"""# Short-Form Video Intelligence Report ({platform_name})

Generated locally via 100% open-source models (**{asr_engine}** + **{llm_model}**).

---

## 1. Post & Creator Overview

| Metric / Attribute | Value |
| :--- | :--- |
| **Platform** | {platform_name} |
| **Creator** | {creator_display} |
| **Followers / Subscribers** | {followers_str} |
| **Duration** | {duration} seconds |
| **Comments Count** | {comments} |
| **Source URL** | [{url}]({url}) |
| **Caption** | `{caption}` |

---

## 2. Audio Transcript & Speech Recognition

* **ASR Model Used:** `{asr_engine}` ({asr_result.get("backend", "Local")})
* **Transcription Time:** {asr_time} seconds

> {transcript}

---

## 3. Visual Hook & Audience Targeting (Frame 1)

{hook_sec}

---

## 4. Technical Architecture Diagram Breakdown

{diag_sec}

---

## 5. Comprehensive Systems Synthesis & Critique

{synth_sec}

---

*Report generated with zero cloud API dependencies on local hardware.*
"""

    md_path = os.path.join(output_dir, "analysis_report.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
        
    print(f"\n[✓] Generated reports:")
    print(f"    - Markdown: {md_path}")
    print(f"    - JSON:     {json_path}")
    return md_path
