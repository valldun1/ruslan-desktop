#!/usr/bin/env python3
"""Generate app_icon.png (1024x1024) — shield on black, green glow."""

from PIL import Image, ImageDraw, ImageFilter, ImageChops
import math

SIZE = 1024
OUT = "/Users/valen/Desktop/ruslan-desktop/assets/app_icon.png"

def create_icon():
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img)

    cx, cy = SIZE // 2, SIZE // 2

    # ---- Shield shape ----
    # We'll build a shield polygon
    w, h = 640, 640  # shield bounding box
    x0, y0 = cx - w // 2, cy - h // 2 + 30

    # Shield path points (normalized 0..1)
    pts_rel = [
        (0.5, 0.0),    # top center
        (1.0, 0.0),    # top right
        (1.0, 0.45),   # mid right
        (0.85, 0.55),  # curve right
        (0.5, 1.0),    # bottom point
        (0.15, 0.55),  # curve left
        (0.0, 0.45),   # mid left
        (0.0, 0.0),    # top left
    ]

    shield_pts = []
    for rx, ry in pts_rel:
        px = int(x0 + rx * w)
        py = int(y0 + ry * h)
        shield_pts.append((px, py))

    # ---- Glow layer ----
    glow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)

    # Draw larger shield semi-transparent green
    scale = 0.08  # 8% larger
    glow_pts = []
    for rx, ry in pts_rel:
        # Expand from center
        px = int(cx + (x0 + rx * w - cx) * (1 + scale))
        py = int(cy + (y0 + ry * h - cy) * (1 + scale))
        glow_pts.append((px, py))

    # Multiple glow layers with different opacities
    for i, (r, g, b, a) in enumerate([
        (0, 255, 100, 80),   # outer glow
        (0, 255, 120, 60),
        (0, 255, 80, 100),
    ]):
        gdraw.polygon(glow_pts, fill=(r, g, b, a))

    # Blur glow
    glow = glow.filter(ImageFilter.GaussianBlur(radius=40))

    # Composite glow onto main
    img = Image.alpha_composite(img, glow)

    # ---- Shield body ----
    draw = ImageDraw.Draw(img)

    # Dark gradient fill — draw multiple layers
    for i in range(3):
        offset = i * 2
        shrunk_pts = []
        for rx, ry in pts_rel:
            px = int(cx + (x0 + rx * w - cx) * (1 - offset / w))
            py = int(cy + (y0 + ry * h - cy) * (1 - offset / h))
            shrunk_pts.append((px, py))

        shade = 30 + i * 20
        draw.polygon(shrunk_pts, fill=(shade, shade + 10, shade + 5, 220))

    # Main shield fill — dark metallic
    draw.polygon(shield_pts, fill=(25, 28, 26, 230))

    # Inner lighter shield
    inset = 20
    inner_pts = []
    for rx, ry in pts_rel:
        px = int(x0 + rx * w + (1 if rx > 0.5 else -1) * inset if 0 < rx < 1 else x0 + rx * w)
        py = int(y0 + ry * h + (1 if ry > 0.5 else -1) * inset if 0 < ry < 1 else y0 + ry * h)
        if rx == 0.5 and ry == 0.0:
            inner_pts.append((cx, y0 + 10))
        elif rx == 0.5 and ry == 1.0:
            inner_pts.append((cx, y0 + h - 10))
        else:
            inner_pts.append((px, py))

    # Actually let me just use a simpler approach
    # Redraw with a proper inner shield
    # Clear the shield area first
    inner_w, inner_h = w - 60, h - 60
    inner_x0 = cx - inner_w // 2
    inner_y0 = y0 + 30

    inner_pts = []
    for rx, ry in pts_rel:
        px = int(inner_x0 + rx * inner_w)
        py = int(inner_y0 + ry * inner_h)
        inner_pts.append((px, py))

    draw.polygon(inner_pts, fill=(40, 45, 42, 230))

    # ---- Green glow emblem ----
    # Central "R" or a glowing diamond/eye
    # Draw a stylized glowing diamond in center
    gem_size = 160
    gem = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    gdraw2 = ImageDraw.Draw(gem)

    # Diamond shape
    d_pts = [
        (cx, cy - gem_size // 2),
        (cx + gem_size // 2, cy),
        (cx, cy + gem_size // 2),
        (cx - gem_size // 2, cy),
    ]
    gdraw2.polygon(d_pts, fill=(0, 255, 100, 200))
    # Inner diamond
    inner_d = [
        (cx, cy - gem_size // 4),
        (cx + gem_size // 4, cy),
        (cx, cy + gem_size // 4),
        (cx - gem_size // 4, cy),
    ]
    gdraw2.polygon(inner_d, fill=(180, 255, 200, 220))

    # Glow around diamond
    gem_glow = gem.filter(ImageFilter.GaussianBlur(radius=25))
    img = Image.alpha_composite(img, gem_glow)
    img = Image.alpha_composite(img, gem)

    # ---- Subtle scanline/highlight ----
    # Top highlight on shield
    highlight = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    hdraw = ImageDraw.Draw(highlight)

    # Thin bright arc near top of shield
    h_pts = []
    for rx, ry in pts_rel:
        px = int(inner_x0 + rx * inner_w)
        py = int(inner_y0 + ry * inner_h)
        h_pts.append((px, py))

    # Draw a partial top highlight
    for i in range(3, 7):
        p1 = shield_pts[i]
        p2 = shield_pts[(i + 1) % len(shield_pts)]
        draw.line([p1, p2], fill=(100, 255, 150, 60), width=2)

    img.save(OUT, "PNG")
    print(f"Icon saved to {OUT}")

if __name__ == "__main__":
    create_icon()
