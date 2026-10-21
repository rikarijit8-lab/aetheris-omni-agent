"""
Aetheris Omni-Agent: Automated Hackathon Demo Video Generator
Generates a broadcast-quality, 1080p narrated MP4 video walkthrough for judges.
Amazon Developer Hackathon: Build, Ship, Shape 2026
"""

import os
import sys
import time
import io
import subprocess
import urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio.v2 as imageio
import imageio_ffmpeg
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Force UTF-8 stdout
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
OUTPUT_VIDEO = "aetheris_demo_video.mp4"
TEMP_VIDEO = "temp_raw_video.mp4"
TEMP_AUDIO = "final_narration.wav"
FPS = 15  # 15 fps gives great smoothness while keeping encoding fast & compact

SCENES = [
    {
        "id": 1,
        "name": "Architecture Overview",
        "header": "AMAZON DEVELOPER HACKATHON 2026 • BUILD, SHIP, SHAPE",
        "title": "[SCENE 1/6] Executive Overview & Proactive Ambient Architecture",
        "subtitle": "Unified Ambient AI via Amazon MCP Spec 2025-11-25 & AWS Bedrock",
        "badge": "Alexa+ MCP Streamable HTTP",
        "speech": (
            "Welcome judges to Aetheris Omni-Agent, built for the Amazon Developer Hackathon 2026. "
            "While traditional smart home assistants wait for single-turn commands, Aetheris is a proactive, "
            "cross-device intelligence system powered by AWS Bedrock and the new Amazon Model Context Protocol, "
            "MCP Spec 2025-11-25 over Streamable HTTP. It unifies Alexa+, Ring Doorbell, Bee Wearable AI, "
            "and Fire TV into one autonomous orchestra."
        ),
        "steps": [
            {"action": "wait", "sec": 2.0},
            {"action": "tab", "target": "all", "sec": 4.0},
            {"action": "tab", "target": "calendar", "sec": 4.0},
            {"action": "tab", "target": "ring", "sec": 4.0},
            {"action": "tab", "target": "bee", "sec": 4.0},
            {"action": "tab", "target": "all", "sec": 4.0},
        ]
    },
    {
        "id": 2,
        "name": "Calendar Collision Resolution",
        "header": "AMAZON DEVELOPER HACKATHON 2026 • ALEXA+ TRACK",
        "title": "[SCENE 2/6] Autonomous Calendar Conflict Auto-Resolution",
        "subtitle": "MCP Tools: check_schedule_conflicts -> reschedule_event -> render_ambient_canvas",
        "badge": "SQLite Live Persistence",
        "speech": (
            "Watch what happens in a typical morning: our calendar has an overlapping executive conflict. "
            "Alexa+ inspects today's schedule via MCP, detects the time collision, autonomously moves the overlapping "
            "meeting to an open 2:00 PM slot, and immediately broadcasts the updated itinerary to our Fire TV "
            "ambient display in 4K resolution. Zero manual intervention required."
        ),
        "steps": [
            {"action": "scenario", "target": "resolve_calendar_conflict", "sec": 4.0},
            {"action": "scroll_chat", "sec": 4.0},
            {"action": "tab", "target": "calendar", "sec": 8.0},
            {"action": "tab", "target": "firetv", "sec": 6.0},
            {"action": "tab", "target": "calendar", "sec": 4.0},
        ]
    },
    {
        "id": 3,
        "name": "Ring Courier & 1-Click Procurement",
        "header": "AMAZON DEVELOPER HACKATHON 2026 • CROSS-DEVICE ORCHESTRATION",
        "title": "[SCENE 3/6] Ring Courier Verification & Amazon 1-Click Auto-Procurement",
        "subtitle": "Smart Deadbolt 60s Temporary Access & Autonomous Corporate Restock",
        "badge": "Ring Cam + 1-Click",
        "speech": (
            "Next, at our front door: Ring Video Doorbell detects an Amazon Logistics courier with priority supplies. "
            "Aetheris verifies the courier credential, temporarily unlocks our smart deadbolt for 60 seconds with an audit log, "
            "and checks our inventory. Detecting that coffee pods are low, it initiates an Amazon Corporate 1-Click restock order, "
            "restocks inventory, and displays the receipt right on screen."
        ),
        "steps": [
            {"action": "scenario", "target": "courier_delivery_restock", "sec": 4.0},
            {"action": "scroll_chat", "sec": 4.0},
            {"action": "tab", "target": "ring", "sec": 7.0},
            {"action": "tab", "target": "procure", "sec": 7.0},
            {"action": "tab", "target": "all", "sec": 4.0},
        ]
    },
    {
        "id": 4,
        "name": "Bee Wearable AI & Fire TV Ambience",
        "header": "AMAZON DEVELOPER HACKATHON 2026 • AMBIENT COMPUTING",
        "title": "[SCENE 4/6] Bee Wearable AI Biometrics -> Smart Lighting & Fire TV",
        "subtitle": "Cognitive Stress Spike (78%) Proactively Engages 5500K Focus Mode & Haptics",
        "badge": "Bee AI + Vega OS",
        "speech": (
            "Now let's check the Bee Wearable AI on the user's wrist. Bee detects elevated cognitive stress at 78% "
            "and transcribes meeting notes from an executive hallway sync. Aetheris intervenes proactively: it dials the room's "
            "smart lighting to 5,500 Kelvin focus daylight, mutes external chimes, and updates Fire TV with a calming ambient focus canvas."
        ),
        "steps": [
            {"action": "scenario", "target": "bee_stress_focus_ambience", "sec": 4.0},
            {"action": "scroll_chat", "sec": 4.0},
            {"action": "tab", "target": "bee", "sec": 7.0},
            {"action": "tab", "target": "firetv", "sec": 7.0},
            {"action": "tab", "target": "all", "sec": 3.0},
        ]
    },
    {
        "id": 5,
        "name": "MCP Spec 2025-11-25 Protocol Inspector",
        "header": "AMAZON DEVELOPER HACKATHON 2026 • AWS BUILDER & OPEN SOURCE TRACK",
        "title": "[SCENE 5/6] Official MCP Spec 2025-11-25 Protocol Inspector",
        "subtitle": "Streamable HTTP SSE & JSON-RPC 2.0 (tools/list, tools/call, AgentCore)",
        "badge": "MCP Open Standard",
        "speech": (
            "For the developer ecosystem, Aetheris is fully open standard. Here in our real-time Protocol Inspector, "
            "you can verify every JSON-RPC 2.0 packet complying with the MCP 2025-11-25 spec over Streamable HTTP, "
            "connecting Bedrock AgentCore directly to the client with zero latency."
        ),
        "steps": [
            {"action": "inspector_open", "sec": 3.0},
            {"action": "inspector_scroll_1", "sec": 5.0},
            {"action": "inspector_scroll_2", "sec": 5.0},
            {"action": "inspector_scroll_3", "sec": 5.0},
            {"action": "inspector_hold", "sec": 4.0},
        ]
    },
    {
        "id": 6,
        "name": "Grand Finale & Hackathon Submission",
        "header": "AMAZON DEVELOPER HACKATHON 2026 • SUBMISSION SUMMARY",
        "title": "[SCENE 6/6] Grand Finale: The Future of Ambient Intelligence",
        "subtitle": "Repository: github.com/rikarijit8-lab/aetheris-omni-agent | MIT License",
        "badge": "Devpost Ready",
        "speech": (
            "Aetheris Omni-Agent: connecting the living room, the front door, the wrist, and the AWS cloud into the future of "
            "ambient computing. All code, architecture docs, and friction logs are open source on GitHub. Thank you judges!"
        ),
        "steps": [
            {"action": "inspector_close", "sec": 2.0},
            {"action": "tab", "target": "all", "sec": 5.0},
            {"action": "outro_card", "sec": 8.0},
        ]
    }
]

def generate_scene_audio(scene_idx, text):
    """Synthesizes speech to WAV file using PowerShell SpeechSynthesizer and pads with silence."""
    raw_wav = f"raw_scene_{scene_idx}.wav"
    clean_text = text.replace('"', '\\"').replace("'", "")
    ps_content = f"""
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.Rate = 0
$synth.SetOutputToWaveFile('{raw_wav}')
$synth.Speak('{clean_text}')
$synth.Dispose()
"""
    ps_file = f"gen_audio_{scene_idx}.ps1"
    with open(ps_file, "w", encoding="utf-8") as f:
        f.write(ps_content)

    subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", ps_file], check=True)
    if os.path.exists(ps_file):
        os.remove(ps_file)

    # Probe duration
    probe = subprocess.run([FFMPEG_EXE, "-i", raw_wav], capture_output=True, text=True)
    raw_duration = 15.0
    for line in probe.stderr.splitlines():
        if "Duration:" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip().split(":")
            h, m, s = float(parts[0]), float(parts[1]), float(parts[2])
            raw_duration = h * 3600 + m * 60 + s
            break

    # Add 1.5s silence padding to audio
    pad_dur = 1.5
    final_wav = f"scene_{scene_idx}_pad.wav"
    cmd_pad = [
        FFMPEG_EXE, "-y",
        "-i", raw_wav,
        "-af", f"apad=pad_dur={pad_dur}",
        final_wav
    ]
    subprocess.run(cmd_pad, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if os.path.exists(raw_wav):
        os.remove(raw_wav)

    total_duration = raw_duration + pad_dur
    return final_wav, total_duration

def merge_audio_files(wav_files, output_wav):
    """Concatenates multiple WAV files using ffmpeg concat demuxer."""
    list_file = "audio_list.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for w in wav_files:
            f.write(f"file '{os.path.abspath(w)}'\n")

    cmd = [
        FFMPEG_EXE, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_file,
        "-c", "copy",
        output_wav
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if os.path.exists(list_file):
        os.remove(list_file)
    for w in wav_files:
        if os.path.exists(w):
            os.remove(w)

def load_fonts():
    """Loads modern Segoe UI fonts for TV broadcast graphics."""
    try:
        font_header_bold = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 22)
        font_header_sub = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 16)
        font_title_bold = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 21)
        font_sub = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 16)
        font_badge = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 15)
        font_outro_title = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 34)
        font_outro_body = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 20)
        return font_header_bold, font_header_sub, font_title_bold, font_sub, font_badge, font_outro_title, font_outro_body
    except Exception:
        def_font = ImageFont.load_default()
        return def_font, def_font, def_font, def_font, def_font, def_font, def_font

def draw_broadcast_overlays(pil_img, scene, fonts, is_outro=False):
    """Overlays television-grade headers, lower-thirds, and outro cards."""
    # Ensure exact 1920x1080 resolution
    if pil_img.size != (1920, 1080):
        pil_img = pil_img.resize((1920, 1080), Image.Resampling.LANCZOS)

    draw = ImageDraw.Draw(pil_img)
    f_h_bold, f_h_sub, f_t_bold, f_sub, f_badge, f_o_title, f_o_body = fonts

    # 1. TOP HEADER BANNER (48px)
    draw.rectangle([(0, 0), (1920, 48)], fill=(8, 12, 22))
    draw.line([(0, 48), (1920, 48)], fill=(0, 229, 255), width=2)
    draw.text((25, 12), scene["header"], font=f_h_bold, fill=(255, 153, 0)) # Amazon Amber
    draw.text((1260, 15), "AETHERIS OMNI-AGENT • ALEXA+ / AWS BEDROCK / BEE / RING / FIRE TV", font=f_h_sub, fill=(0, 229, 255))

    # 2. BOTTOM LOWER THIRD (108px)
    y_start = 972
    draw.rectangle([(0, y_start), (1920, 1080)], fill=(9, 14, 26))
    draw.line([(0, y_start), (1920, y_start)], fill=(0, 229, 255), width=2)

    # Accent badge
    draw.rounded_rectangle([(30, y_start + 12), (90, y_start + 38)], radius=4, fill=(0, 100, 140))
    draw.text((38, y_start + 15), f"{scene['id']}/6", font=f_badge, fill=(255, 255, 255))

    # Scene Title
    draw.text((105, y_start + 14), scene["title"], font=f_t_bold, fill=(255, 255, 255))

    # Scene Subtitle / Description
    draw.text((32, y_start + 50), scene["subtitle"], font=f_sub, fill=(185, 205, 230))

    # Right side tech badge
    badge_text = scene["badge"]
    draw.rounded_rectangle([(1590, y_start + 24), (1895, y_start + 64)], radius=8, fill=(16, 30, 52), outline=(0, 229, 255), width=1)
    draw.text((1610, y_start + 32), badge_text, font=f_badge, fill=(0, 229, 255))

    # 3. OUTRO CENTER CARD (if outro scene)
    if is_outro:
        # Dim background
        overlay = Image.new("RGBA", (1920, 1080), (10, 15, 28, 210))
        pil_img.paste(overlay, (0, 0), overlay)
        draw = ImageDraw.Draw(pil_img)

        # Center Card
        card_box = [(340, 220), (1580, 800)]
        draw.rounded_rectangle(card_box, radius=16, fill=(14, 20, 36), outline=(0, 229, 255), width=2)

        # Content
        draw.text((400, 260), "AMAZON DEVELOPER HACKATHON 2026: BUILD, SHIP, SHAPE", font=f_h_bold, fill=(255, 153, 0))
        draw.text((400, 310), "Aetheris Omni-Agent", font=f_o_title, fill=(255, 255, 255))
        draw.text((400, 365), "Autonomous Cross-Device Ambient Concierge (Alexa+, Bedrock, Ring, Bee, Fire TV)", font=f_o_body, fill=(0, 229, 255))

        lines = [
            "[+] Amazon Model Context Protocol (MCP Spec 2025-11-25) over Streamable HTTP SSE",
            "[+] Multi-turn AWS Bedrock Converse API with Claude 3.5 Sonnet & Amazon Nova",
            "[+] Live Cross-Device Synchronization: Ring Doorbell, Bee Wearable AI, Fire TV Canvas",
            "[+] SQLite Persistent Memory with 6 Unified Schemas (Schedule, Supplies, Orders, etc.)",
            "[+] 10% Judging Bonus: 5 In-Depth Friction Logs in FRICTION_LOGS.md",
            "[+] Open Source MIT License • GitHub: github.com/rikarijit8-lab/aetheris-omni-agent"
        ]

        y_c = 430
        for l in lines:
            draw.text((400, y_c), l, font=f_sub, fill=(220, 235, 255))
            y_c += 40

    return pil_img

def reset_backend_state():
    """Resets backend database to ensure clean demonstration run."""
    try:
        req = urllib.request.Request("http://localhost:8000/api/reset", method="POST")
        with urllib.request.urlopen(req, timeout=5) as res:
            pass
        print("Backend reset to clean demo state.")
    except Exception as e:
        print(f"Reset note: {e}")

def main():
    print("=" * 70)
    print("🎬 AETHERIS OMNI-AGENT: AUTOMATED HACKATHON DEMO VIDEO BUILDER")
    print("=" * 70)

    # Step 1: Synthesize all voice narration files
    print("\n[1/5] Synthesizing professional spoken narration for all scenes...")
    wav_files = []
    durations = []
    total_audio_time = 0.0

    for i, sc in enumerate(SCENES):
        print(f"  -> Synthesizing Scene {sc['id']}: {sc['name']}...")
        w, dur = generate_scene_audio(sc["id"], sc["speech"])
        wav_files.append(w)
        durations.append(dur)
        total_audio_time += dur
        print(f"     Duration: {dur:.2f}s")

    print(f"\nTotal video runtime: {total_audio_time:.2f}s (~{int(total_audio_time//60)}m {int(total_audio_time%60)}s)")

    # Step 2: Merge audio tracks
    print("\n[2/5] Concatenating audio track into final_narration.wav...")
    merge_audio_files(wav_files, TEMP_AUDIO)
    print("Audio narration track successfully compiled.")

    # Step 3: Initialize Headless Chrome at 1920x1080
    print("\n[3/5] Launching Chrome Headless at 1920x1080...")
    chrome_opts = Options()
    chrome_opts.add_argument("--headless=new")
    chrome_opts.add_argument("--window-size=1920,1080")
    chrome_opts.add_argument("--disable-gpu")
    chrome_opts.add_argument("--hide-scrollbars")
    chrome_opts.add_argument("--disable-infobars")
    chrome_opts.add_argument("--disable-notifications")

    driver = webdriver.Chrome(options=chrome_opts)
    driver.set_window_size(1920, 1080)

    # Reset backend to fresh state
    reset_backend_state()

    driver.get("http://localhost:8000")
    time.sleep(2)

    # Fonts
    fonts = load_fonts()

    # Step 4: Render Video Frames
    print(f"\n[4/5] Recording live scenario walkthrough at {FPS} FPS...")
    video_writer = imageio.get_writer(
        TEMP_VIDEO,
        fps=FPS,
        codec="libx264",
        quality=8,
        pixelformat="yuv420p"
    )

    frame_count = 0

    for sc_idx, sc in enumerate(SCENES):
        scene_dur = durations[sc_idx]
        total_scene_frames = int(scene_dur * FPS)
        print(f"\n>>> Executing Scene {sc['id']}/{len(SCENES)}: {sc['name']} ({total_scene_frames} frames, {scene_dur:.2f}s)...")

        steps = sc.get("steps", [])
        total_step_weight = sum(s.get("sec", 1.0) for s in steps)
        scene_rendered_frames = 0

        for s_idx, st in enumerate(steps):
            act = st.get("action")
            step_sec = st.get("sec", 1.0)
            target = st.get("target")

            # Allocate frames proportional to step time
            if s_idx == len(steps) - 1:
                step_frames = total_scene_frames - scene_rendered_frames
            else:
                step_frames = int(round((step_sec / total_step_weight) * total_scene_frames))

            is_outro = (act == "outro_card")

            # Execute action
            if act == "tab":
                driver.execute_script(f"switchDeviceTab('{target}')")
            elif act == "scenario":
                print(f"    Triggering scenario: {target}...")
                driver.execute_script(f"triggerScenario('{target}')")
                time.sleep(2.0)
            elif act == "scroll_chat":
                driver.execute_script("const c = document.getElementById('conversation-feed'); if (c) c.scrollTop = c.scrollHeight;")
            elif act == "inspector_open":
                driver.execute_script("const d = document.getElementById('inspector-drawer'); if (!d.classList.contains('open')) toggleInspector();")
            elif act == "inspector_scroll_1":
                driver.execute_script("const b = document.getElementById('inspector-logs'); if (b) b.scrollTop = 150;")
            elif act == "inspector_scroll_2":
                driver.execute_script("const b = document.getElementById('inspector-logs'); if (b) b.scrollTop = 350;")
            elif act == "inspector_scroll_3":
                driver.execute_script("const b = document.getElementById('inspector-logs'); if (b) b.scrollTop = 600;")
            elif act == "inspector_close":
                driver.execute_script("const d = document.getElementById('inspector-drawer'); if (d.classList.contains('open')) toggleInspector();")

            time.sleep(0.5)

            # Capture screenshot
            png_bytes = driver.get_screenshot_as_png()
            base_img = Image.open(io.BytesIO(png_bytes)).convert("RGB")

            # Apply broadcast overlay
            overlay_img = draw_broadcast_overlays(base_img, sc, fonts, is_outro=is_outro)
            frame_np = np.array(overlay_img)

            # Write frames for this step duration
            for _ in range(max(1, step_frames)):
                video_writer.append_data(frame_np)
                frame_count += 1
                scene_rendered_frames += 1

        print(f"    Rendered {scene_rendered_frames} frames for Scene {sc['id']}.")

    video_writer.close()
    driver.quit()
    print(f"\nTotal video frames encoded: {frame_count} frames.")

    # Step 5: Mux Video + Audio with FFmpeg
    print(f"\n[5/5] Combining video and audio into {OUTPUT_VIDEO}...")
    mux_cmd = [
        FFMPEG_EXE, "-y",
        "-i", TEMP_VIDEO,
        "-i", TEMP_AUDIO,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        OUTPUT_VIDEO
    ]
    subprocess.run(mux_cmd, check=True)

    # Cleanup temporary files
    if os.path.exists(TEMP_VIDEO):
        os.remove(TEMP_VIDEO)
    if os.path.exists(TEMP_AUDIO):
        os.remove(TEMP_AUDIO)

    # Probe final output video
    print("\n" + "=" * 70)
    print("🎉 DEMO VIDEO CREATION COMPLETE!")
    print(f"📁 File: {os.path.abspath(OUTPUT_VIDEO)}")
    if os.path.exists(OUTPUT_VIDEO):
        size_mb = os.path.getsize(OUTPUT_VIDEO) / (1024 * 1024)
        print(f"📦 Size: {size_mb:.2f} MB")
        probe = subprocess.run([FFMPEG_EXE, "-i", OUTPUT_VIDEO], capture_output=True, text=True)
        for line in probe.stderr.splitlines():
            if "Duration:" in line or "Video:" in line or "Audio:" in line:
                print("   " + line.strip())
    print("=" * 70)

if __name__ == "__main__":
    main()
