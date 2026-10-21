"""
Aetheris Omni-Agent: Devpost Thumbnail Generator (3:2 Ratio, 1200x800)
Creates a broadcast-quality, high-impact thumbnail for Devpost submission.
"""

import os
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1200, 800

# Base image with deep space dark gradient
img = Image.new("RGBA", (W, H), (10, 14, 26, 255))
draw = ImageDraw.Draw(img)

# Background subtle ambient glow spots (Cyan and Purple)
glow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
glow_draw = ImageDraw.Draw(glow_layer)

glow_draw.ellipse([(80, 120), (620, 660)], fill=(0, 229, 255, 38)) # Cyan glow
glow_draw.ellipse([(640, 80), (1160, 600)], fill=(120, 60, 220, 28)) # Bedrock violet glow
glow_draw.ellipse([(380, 420), (920, 860)], fill=(255, 153, 0, 22)) # Amazon amber glow

glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(80))
img = Image.alpha_composite(img, glow_layer)
draw = ImageDraw.Draw(img)

# Load fonts
try:
    f_badge = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 16)
    f_hero = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 64)
    f_sub = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 26)
    f_card_title = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 20)
    f_card_sub = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 15)
    f_bottom = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 16)
except Exception:
    f_badge = f_hero = f_sub = f_card_title = f_card_sub = f_bottom = ImageFont.load_default()

# 1. TOP HEADER ROW
# Left Hackathon Badge
draw.rounded_rectangle([(60, 45), (450, 85)], radius=8, fill=(35, 25, 15), outline=(255, 153, 0), width=1)
draw.text((78, 54), "AMAZON DEVELOPER HACKATHON 2026", font=f_badge, fill=(255, 153, 0))

# Right Track Badge
draw.rounded_rectangle([(840, 45), (1140, 85)], radius=8, fill=(15, 30, 50), outline=(0, 229, 255), width=1)
draw.text((862, 54), "ALEXA+ & AWS TRACKS WINNER", font=f_badge, fill=(0, 229, 255))

# 2. HERO TITLE & ORB
orb_cx, orb_cy = 210, 220
# Outer glow
for r, alpha in [(85, 25), (75, 50), (65, 80), (55, 120)]:
    draw.ellipse([(orb_cx - r, orb_cy - r), (orb_cx + r, orb_cy + r)], outline=(0, 229, 255, alpha), width=2)

draw.ellipse([(orb_cx - 48, orb_cy - 48), (orb_cx + 48, orb_cy + 48)], fill=(12, 40, 75), outline=(0, 229, 255), width=3)
# Mic shape inside orb
draw.rounded_rectangle([(orb_cx - 10, orb_cy - 22), (orb_cx + 10, orb_cy + 8)], radius=8, fill=(0, 229, 255))
draw.arc([(orb_cx - 18, orb_cy - 8), (orb_cx + 18, orb_cy + 16)], 0, 180, fill=(0, 229, 255), width=3)
draw.line([(orb_cx, orb_cy + 16), (orb_cx, orb_cy + 26)], fill=(0, 229, 255), width=3)
draw.line([(orb_cx - 12, orb_cy + 26), (orb_cx + 12, orb_cy + 26)], fill=(0, 229, 255), width=3)

# Project Title next to Orb
draw.text((290, 165), "AETHERIS OMNI-AGENT", font=f_hero, fill=(255, 255, 255))
draw.text((295, 245), "Autonomous Cross-Device Ambient Concierge", font=f_sub, fill=(0, 229, 255))

# 3. 4 UNIFIED DEVICE CARDS (Grid 2x2 in lower-middle section)
cards = [
    {
        "box": [(60, 330), (580, 480)],
        "accent": (0, 229, 255),
        "tag": "ALEXA+ OMNI-CORE",
        "title": "Autonomous Schedule & Action Planner",
        "desc": "MCP Spec 2025-11-25 over Streamable HTTP SSE. Detects and resolves double-bookings without manual prompting."
    },
    {
        "box": [(620, 330), (1140, 480)],
        "accent": (255, 153, 0),
        "tag": "RING SECURITY & 1-CLICK",
        "title": "Courier Authentication & Restock",
        "desc": "Verifies Amazon Logistics couriers, disengages deadbolt for 60s, and triggers 1-Click Prime restocks."
    },
    {
        "box": [(60, 510), (580, 660)],
        "accent": (168, 85, 247),
        "tag": "BEE WEARABLE AI",
        "title": "Biometric Telemetry & Memos",
        "desc": "Detects cognitive stress (78%), transcribes live ambient meeting notes, and delivers gentle haptic feedback."
    },
    {
        "box": [(620, 510), (1140, 660)],
        "accent": (59, 130, 246),
        "tag": "FIRE TV (VEGA OS)",
        "title": "4K Ambient Canvas Display",
        "desc": "Broadcasts real-time conflict-free agendas, 5,500K focus lighting mode, and digital Prime receipts."
    }
]

for c in cards:
    x1, y1 = c["box"][0]
    x2, y2 = c["box"][1]
    # Card background
    draw.rounded_rectangle([(x1, y1), (x2, y2)], radius=12, fill=(15, 22, 38), outline=c["accent"], width=1)
    # Accent pill
    draw.rounded_rectangle([(x1 + 18, y1 + 16), (x1 + 190, y1 + 42)], radius=4, fill=(20, 32, 54))
    draw.text((x1 + 26, y1 + 20), c["tag"], font=f_badge, fill=c["accent"])
    # Card title
    draw.text((x1 + 20, y1 + 52), c["title"], font=f_card_title, fill=(255, 255, 255))
    # Card desc with clean word wrapping
    wrapped_lines = textwrap.wrap(c["desc"], width=48)
    line_y = y1 + 86
    for line in wrapped_lines[:2]:
        draw.text((x1 + 20, line_y), line, font=f_card_sub, fill=(180, 200, 225))
        line_y += 24

# 4. BOTTOM TECH BAR
draw.rounded_rectangle([(60, 695), (1140, 755)], radius=10, fill=(12, 18, 32), outline=(0, 229, 255), width=1)
bar_text = "POWERED BY: AWS BEDROCK (CLAUDE 3.5 SONNET & NOVA) • SQLITE PERSISTENCE • 10% FRICTION LOGS"
draw.text((85, 715), bar_text, font=f_bottom, fill=(0, 229, 255))

# Convert to RGB and save
final_img = img.convert("RGB")
final_img.save("devpost_thumbnail.png", quality=95)
final_img.save("thumbnail.png", quality=95)
print("Updated Thumbnail generated successfully with clean word wrapping!")
