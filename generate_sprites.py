#!/usr/bin/env python3
"""
Generate 6 PNG sprites (128×128) for character Руслан.
Cyberpunk style: green #00ff88 on black #0a0a0a.
Uses only ImageDraw — lines, arcs, polygons.
"""

import os
import math
from PIL import Image, ImageDraw

GREEN = "#00ff88"
BLACK = "#0a0a0a"
SIZE = 128
OUT_DIR = os.path.expanduser("~/Desktop/ruslan-desktop/assets/sprites")

os.makedirs(OUT_DIR, exist_ok=True)


def new_canvas():
    img = Image.new("RGBA", (SIZE, SIZE), BLACK)
    draw = ImageDraw.Draw(img)
    return img, draw


def save(suffix, img):
    path = os.path.join(OUT_DIR, f"{suffix}.png")
    img.save(path)
    print(f"  ✓ {path}")


# ──────────────────────────────────────────────
# 1. idle.png — Shield in center, green outline
# ──────────────────────────────────────────────
def make_idle():
    img, draw = new_canvas()
    cx, cy = SIZE // 2, SIZE // 2
    w, h = 56, 64

    # Shield polygon: top flat, curved sides, point at bottom
    # Classic shield shape
    pts = [
        (cx - w // 2, cy - h // 2),  # top-left
        (cx + w // 2, cy - h // 2),  # top-right
        (cx + w // 2, cy - 4),       # right upper
        (cx + 2,     cy + h // 2),   # right bottom point
        (cx - 2,     cy + h // 2),   # left bottom point
        (cx - w // 2, cy - 4),       # left upper
    ]
    draw.polygon(pts, outline=GREEN, width=3)

    # Inner accent lines (cyberpunk style)
    draw.line((cx - w // 4, cy - h // 4, cx + w // 4, cy - h // 4), fill=GREEN, width=2)
    draw.line((cx - w // 4, cy - h // 4, cx - w // 4, cy + h // 4), fill=GREEN, width=1)
    draw.line((cx + w // 4, cy - h // 4, cx + w // 4, cy + h // 4), fill=GREEN, width=1)

    # Small glow dots at corners
    for dx, dy in [(-w//2, -h//2), (w//2, -h//2)]:
        draw.ellipse(
            (cx + dx - 3, cy + dy - 3, cx + dx + 3, cy + dy + 3),
            fill=GREEN,
        )

    save("idle", img)


# ──────────────────────────────────────────────
# 2. thinking.png — Stylised brain / gear
# ──────────────────────────────────────────────
def make_thinking():
    img, draw = new_canvas()
    cx, cy = SIZE // 2, SIZE // 2
    r = 36

    # Outer gear ring — draw individual teeth
    num_teeth = 10
    for i in range(num_teeth):
        angle = (2 * math.pi / num_teeth) * i - math.pi / 2
        angle_deg = math.degrees(angle)
        # Tooth as small rectangle rotated around center
        tx = cx + r * math.cos(angle)
        ty = cy + r * math.sin(angle)
        tw, th = 8, 16
        # Points of tooth rectangle
        tooth_pts = [
            (tx - tw // 2, ty - th // 2),
            (tx + tw // 2, ty - th // 2),
            (tx + tw // 2, ty + th // 2),
            (tx - tw // 2, ty + th // 2),
        ]
        # Rotate tooth points around center
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        rotated = []
        for px, py in tooth_pts:
            dx, dy = px - cx, py - cy
            rx = cx + dx * cos_a - dy * sin_a
            ry = cy + dx * sin_a + dy * cos_a
            rotated.append((rx, ry))
        draw.polygon(rotated, outline=GREEN, width=2)

    # Inner gear circle
    draw.ellipse(
        (cx - r + 6, cy - r + 6, cx + r - 6, cy + r - 6),
        outline=GREEN, width=3,
    )

    # Brain hemisphere curves inside gear (squiggly centre line)
    # Left hemisphere
    for t in range(0, 180, 15):
        a = math.radians(t)
        r_inner = 12
        x1 = cx + r_inner * math.cos(a)
        y1 = cy + r_inner * math.sin(a)
        x2 = cx + r_inner * 1.6 * math.cos(a + 0.3)
        y2 = cy + r_inner * 1.4 * math.sin(a + 0.3)
        draw.line((x1, y1, x2, y2), fill=GREEN, width=1)

    # Centre dot
    draw.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), fill=GREEN)

    save("thinking", img)


# ──────────────────────────────────────────────
# 3. speaking.png — Sound waves
# ──────────────────────────────────────────────
def make_speaking():
    img, draw = new_canvas()
    cx, cy = SIZE // 2, SIZE // 2

    # Speaker / mouth dot at left
    draw.ellipse((cx - 36, cy - 10, cx - 20, cy + 10), fill=GREEN)

    # Sound wave arcs emanating to the right
    for i, radius in enumerate([18, 30, 44, 58]):
        x0 = cx - 8
        y0 = cy - radius
        x1 = cx - 8 + radius * 2
        y1 = cy + radius
        # Arc from -60 to +60 degrees (rightward opening)
        draw.arc((x0, y0, x1, y1), start=-70, end=70, fill=GREEN, width=3 - i // 2)

    # Frequency lines going outward (digital feel)
    for angle_deg, length in [(15, 16), (35, 10), (-15, 16), (-35, 10)]:
        a = math.radians(angle_deg)
        x1 = cx + 30 * math.cos(a)
        y1 = cy + 30 * math.sin(a)
        x2 = cx + (30 + length) * math.cos(a)
        y2 = cy + (30 + length) * math.sin(a)
        draw.line((x1, y1, x2, y2), fill=GREEN, width=2)

    # Small dots along waves (cyberpunk glitch accents)
    for r, ao in [(22, 0), (36, 15), (50, -10)]:
        a = math.radians(ao)
        px = cx - 8 + r * math.cos(a)
        py = cy + r * math.sin(a)
        draw.ellipse((px - 2, py - 2, px + 2, py + 2), fill=GREEN)

    save("speaking", img)


# ──────────────────────────────────────────────
# 4. happy.png — Stars / sparkles
# ──────────────────────────────────────────────
def make_happy():
    img, draw = new_canvas()
    cx, cy = SIZE // 2, SIZE // 2

    def star(cx, cy, outer_r, inner_r, points, rotation=0):
        """Draw a star polygon with given number of points."""
        pts = []
        for i in range(points * 2):
            angle = rotation + (math.pi / points) * i
            r = outer_r if i % 2 == 0 else inner_r
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            pts.append((x, y))
        return pts

    # Big central star
    big = star(cx, cy, 30, 14, 5, -math.pi / 2)
    draw.polygon(big, outline=GREEN, width=2)

    # Small stars around
    for angle_deg, size in [(0, 6), (72, 8), (144, 5), (216, 7), (288, 6)]:
        a = math.radians(angle_deg)
        sx = cx + 44 * math.cos(a)
        sy = cy + 44 * math.sin(a)
        sm = star(sx, sy, size, size * 0.4, 4, a + math.pi / 4)
        draw.polygon(sm, outline=GREEN, width=2)

    # Sparkle lines (glint rays)
    for angle_deg in [0, 45, 90, 135, 180, 225, 270, 315]:
        a = math.radians(angle_deg)
        x1 = cx + 12 * math.cos(a)
        y1 = cy + 12 * math.sin(a)
        x2 = cx + 36 * math.cos(a)
        y2 = cy + 36 * math.sin(a)
        draw.line((x1, y1, x2, y2), fill=GREEN, width=1)

    # Corner spark dots
    for dx, dy in [(-48, -48), (48, -48), (-48, 48), (48, 48)]:
        dot = star(cx + dx, cy + dy, 6, 2, 4, math.pi / 4)
        draw.polygon(dot, outline=GREEN, width=1)

    save("happy", img)


# ──────────────────────────────────────────────
# 5. sad.png — Drooping / wilted shield
# ──────────────────────────────────────────────
def make_sad():
    img, draw = new_canvas()
    cx, cy = SIZE // 2, SIZE // 2

    # Drooping shield — same shield but sagging and cracked
    w, h = 52, 58

    pts = [
        (cx - w // 2 + 4,  cy - h // 2 - 2),   # top-left (pulled down)
        (cx + w // 2 - 4,  cy - h // 2 - 2),   # top-right (pulled down)
        (cx + w // 2 + 2,  cy - 8),             # right upper (bulging out)
        (cx + 6,           cy + h // 2 + 6),    # right bottom (drooping)
        (cx - 6,           cy + h // 2 + 6),    # left bottom (drooping)
        (cx - w // 2 - 2,  cy - 8),             # left upper (bulging out)
    ]
    draw.polygon(pts, outline=GREEN, width=3)

    # Crack lines across the shield
    draw.line((cx - 20, cy - 16, cx + 10, cy + 20), fill=GREEN, width=2)
    draw.line((cx + 10, cy + 20, cx + 18, cy + 12), fill=GREEN, width=2)
    draw.line((cx - 20, cy - 16, cx - 28, cy - 8), fill=GREEN, width=2)

    # Drip / tear drops below shield
    for dx in [-16, 0, 16]:
        tx = cx + dx
        ty = cy + h // 2 + 12
        # Tear shape: small oval
        draw.ellipse((tx - 3, ty, tx + 3, ty + 8), fill=GREEN, outline=None)
        draw.line((tx, ty, tx, ty + 12), fill=GREEN, width=2)

    # Sad "eyes" — two dashes angled down
    draw.line((cx - 18, cy - 14, cx - 8, cy - 8), fill=GREEN, width=3)
    draw.line((cx + 18, cy - 14, cx + 8, cy - 8), fill=GREEN, width=3)

    save("sad", img)


# ──────────────────────────────────────────────
# 6. working.png — Wrench / tools
# ──────────────────────────────────────────────
def make_working():
    img, draw = new_canvas()
    cx, cy = SIZE // 2, SIZE // 2

    # Wrench (spanner) — drawn as polygons
    # Handle: vertical rectangle
    handle_w, handle_h = 8, 52
    draw.rectangle(
        (cx - handle_w // 2, cy + 4, cx + handle_w // 2, cy + 4 + handle_h),
        outline=GREEN, width=2,
    )

    # Handle grip lines
    for i in range(3):
        y = cy + 12 + i * 14
        draw.line((cx - 5, y, cx + 5, y), fill=GREEN, width=2)

    # Wrench head: C-shaped jaw at top
    # Outer contour of the head
    head_r = 22
    draw.arc(
        (cx - head_r, cy - head_r, cx + head_r, cy + head_r),
        start=-120, end=120, fill=GREEN, width=4,
    )

    # Inner jaw opening
    draw.arc(
        (cx - 8, cy - head_r + 8, cx + 8, cy + 8),
        start=-130, end=130, fill=BLACK, width=3,
    )

    # Jaw teeth (small polygons)
    for angle_deg in [-100, -60, -20, 20, 60, 100]:
        a = math.radians(angle_deg)
        rx = cx + head_r * math.cos(a)
        ry = cy + head_r * math.sin(a)
        draw.ellipse((rx - 3, ry - 3, rx + 3, ry + 3), fill=GREEN)

    # Small gear tool next to wrench
    gx, gy = cx + 30, cy + 20
    draw.ellipse((gx - 10, gy - 10, gx + 10, gy + 10), outline=GREEN, width=2)
    for angle_deg in [0, 60, 120, 180, 240, 300]:
        a = math.radians(angle_deg)
        tx = gx + 12 * math.cos(a)
        ty = gy + 12 * math.sin(a)
        bx = gx + 16 * math.cos(a)
        by = gy + 16 * math.sin(a)
        draw.line((tx, ty, bx, by), fill=GREEN, width=3)

    # Spark particles
    for ox, oy in [(-30, -34), (20, -40), (38, -10), (-22, 30)]:
        draw.line(
            (cx + ox, cy + oy, cx + ox + 6, cy + oy - 6),
            fill=GREEN, width=2,
        )
        draw.ellipse(
            (cx + ox + 4, cy + oy - 4, cx + ox + 8, cy + oy),
            fill=GREEN,
        )

    save("working", img)


# ──────────────────────────────────────────────
if __name__ == "__main__":
    print("Generating Руслан sprites 128×128 (cyberpunk style)…\n")
    print(f"Output: {OUT_DIR}/\n")

    make_idle()
    make_thinking()
    make_speaking()
    make_happy()
    make_sad()
    make_working()

    print("\nDone — all 6 sprites generated.")
