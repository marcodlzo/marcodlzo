"""Builds assets/banner-light.svg and assets/banner-dark.svg.

An editor-style card: marco.yml on the left, a 1-bit dithered scene on the right.
The scene is a procedurally drawn Baguio sunset (pines, ridges, fog, hillside
lights). Drop a photo at assets/source/portrait.png to dither that instead.

Run from the repo root:  python scripts/banner.py
Needs: numpy, Pillow
"""

from pathlib import Path
import math
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageOps

sys.path.insert(0, str(Path(__file__).parent))
from theme import DARK, DOTS, LIGHT, MONO  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

W, H = 960, 520
PITCH = 2.0
CELL = 1.6
SCENE_X, SCENE_Y = 620, 118
COLS, ROWS = 146, 166

YAML = [
    (0, "profile", None),
    (1, "name", ["Marco Delizo"]),
    (1, "role", ["Software & AI Engineer"]),
    (1, "base", ["Baguio City, Philippines"]),
    (1, "school", ["Saint Louis University, BS CS '27"]),
    (1, "now", ["Backend AI Engineer Intern @ FlyRank AI"]),
    (1, "philosophy", ["explainable, end to end"]),
    (0, "stack", None),
    (1, "languages", ["TypeScript", "Python", "JavaScript", "C++"]),
    (1, "web", ["Next.js", "React", "Tailwind", "Node.js"]),
    (1, "backend", ["FastAPI", "Express", "PostgreSQL"]),
    (1, "ai_ml", ["PyTorch", "XGBoost", "SHAP", "Grad-CAM"]),
    (0, "off_screen", None),
    (1, "hobbies", ["hiking", "lifting", "coffee"]),
    (0, "contact", None),
    (1, "portfolio", ["marcodlzo.vercel.app"]),
    (1, "linkedin", ["/in/marcodelizo"]),
]


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# --------------------------------------------------------------------------- scene

def _pine(draw, x, base, height, fill, rng):
    """Benguet pine silhouette: thin trunk, irregular tiers that widen downward."""
    trunk_w = max(2, height * 0.035)
    draw.rectangle([x - trunk_w / 2, base - height * 0.98, x + trunk_w / 2, base], fill=fill)
    tiers = 6 + int(height / 120)
    top = base - height
    for i in range(tiers):
        f = (i + 1) / tiers
        apex = top + height * 0.82 * (i / tiers)
        bottom = apex + height * (0.16 + 0.05 * rng.random())
        half = height * (0.06 + 0.17 * f) * (0.8 + 0.4 * rng.random())
        jag = []
        steps = 7
        for k in range(steps + 1):
            t = k / steps
            jag.append((x - half * t + rng.uniform(-1, 1) * half * 0.12,
                        apex + (bottom - apex) * t + rng.uniform(-1, 1) * 3))
        for k in range(steps, -1, -1):
            t = k / steps
            jag.append((x + half * t + rng.uniform(-1, 1) * half * 0.12,
                        apex + (bottom - apex) * t + rng.uniform(-1, 1) * 3))
        draw.polygon(jag, fill=fill)


def baguio_scene(cols: int, rows: int, s: int = 4) -> Image.Image:
    rng = random.Random(1540)  # Baguio's elevation, for a stable seed
    w, h = cols * s, rows * s
    yy, xx = np.mgrid[0:h, 0:w].astype(float)

    # Sky: dusky at the top, glowing toward the horizon.
    px = 0.26 + 0.5 * np.clip(yy / (0.6 * h), 0, 1)

    # Striped synthwave sun with a soft halo.
    cx, cy, r = 0.5 * w, 0.37 * h, 0.27 * w
    d = np.hypot(xx - cx, yy - cy)
    px = px + 0.22 * np.exp(-(((d - r) / (0.06 * w)) ** 2)) * (d > r)
    sun = d < r
    rel = (yy - cy) / r
    gaps = np.zeros_like(sun)
    for center, half in ((0.05, 0.035), (0.24, 0.05), (0.42, 0.065), (0.6, 0.08), (0.78, 0.095)):
        gaps |= np.abs(rel - center) < half
    px = np.where(sun, np.where(gaps, 0.18, 1.0), px)

    xs = np.arange(w)
    far = 0.555 * h + 0.035 * h * np.sin(xs / w * 2 * math.pi * 1.3 + 0.5) \
        + 0.018 * h * np.sin(xs / w * 2 * math.pi * 3.7 + 1.2)
    px = np.where(yy > far[None, :], 0.62, px)

    # Mountain fog sitting between the ridges.
    fog = np.exp(-(((yy - 0.655 * h) / (0.028 * h)) ** 2))
    px = px + (0.97 - px) * 0.8 * fog

    mid = 0.69 * h + 0.04 * h * np.sin(xs / w * 2 * math.pi * 0.9 + 2.1) \
        + 0.014 * h * np.sin(xs / w * 2 * math.pi * 4.3)
    below_mid = yy > mid[None, :]
    px = np.where(below_mid, 0.46, px)

    # A little grain keeps the dither from banding on smooth gradients.
    noise = np.random.default_rng(1540).normal(0, 0.035, px.shape)
    px = px + noise * ((px > 0.15) & (px < 0.98))
    img = Image.fromarray(np.clip(px * 255, 0, 255).astype(np.uint8), "L")
    draw = ImageDraw.Draw(img)

    # Small pines along the mid ridge.
    x = rng.uniform(0, 10) * s
    while x < w:
        base = float(np.interp(x, xs, mid)) + s
        ht = rng.uniform(0.028, 0.05) * h
        draw.polygon([(x, base - ht), (x - ht * 0.28, base), (x + ht * 0.28, base)], fill=int(0.3 * 255))
        x += rng.uniform(7, 15) * s

    # Hillside houses: lit windows scattered down the slope.
    for _ in range(46):
        hx = rng.uniform(0.32, 0.98) * w
        ridge = float(np.interp(hx, xs, mid))
        hy = rng.uniform(ridge + 0.03 * h, 0.86 * h)
        bw, bh = rng.choice([(3, 2), (2, 2), (4, 2)])
        draw.rectangle([hx, hy, hx + bw * s - 1, hy + bh * s - 1], fill=int(0.9 * 255))

    # Foreground ground and big pines.
    ground = [(0, h)]
    for gx in range(0, w + 1, s * 4):
        ground.append((gx, 0.9 * h + 0.025 * h * math.sin(gx / w * 2 * math.pi * 1.1 + 0.7)))
    ground.append((w, h))
    draw.polygon(ground, fill=0)

    for fx, frac in ((0.11, 0.64), (0.25, 0.40), (0.77, 0.33), (0.9, 0.55)):
        _pine(draw, fx * w, h, frac * h, 0, rng)

    return img.resize((cols, rows), Image.LANCZOS)


def portrait_scene(path: Path, cols: int, rows: int) -> Image.Image:
    img = Image.open(path).convert("L")
    img = ImageOps.fit(img, (cols, rows), Image.LANCZOS, centering=(0.5, 0.35))
    return ImageOps.autocontrast(img, cutoff=2)


def dither_path(gray: Image.Image) -> str:
    bits = np.array(gray.convert("1"), dtype=bool)  # Floyd-Steinberg
    parts = []
    for j in range(bits.shape[0]):
        row = ~bits[j]
        i = 0
        while i < row.size:
            if row[i]:
                start = i
                while i < row.size and row[i]:
                    i += 1
                run = i - start
                x = SCENE_X + start * PITCH
                y = SCENE_Y + j * PITCH
                wdt = (run - 1) * PITCH + CELL
                parts.append(f"M{x:g} {y:g}h{wdt:g}v{CELL:g}h-{wdt:g}z")
            else:
                i += 1
    return "".join(parts)


# --------------------------------------------------------------------------- svg

def code_lines(c) -> list[str]:
    out = []
    y = 130
    for n, (level, key, values) in enumerate(YAML, start=1):
        out.append(f'<text x="66" y="{y}" text-anchor="end" fill="{c["gutter"]}">{n}</text>')
        if level == 0:
            out.append(f'<text x="82" y="{y}" fill="{c["section"]}" font-weight="700">{esc(key)}<tspan fill="{c["sep"]}">:</tspan></text>')
        else:
            spans = [f'<tspan fill="{c["key"]}">{esc(key)}</tspan><tspan fill="{c["sep"]}">: </tspan>']
            for i, v in enumerate(values):
                if i:
                    spans.append(f'<tspan fill="{c["sep"]}"> · </tspan>')
                spans.append(f'<tspan fill="{c["value"]}">{esc(v)}</tspan>')
            out.append(f'<text x="100" y="{y}" xml:space="preserve">{"".join(spans)}</text>')
        y += 20
    return out


def build(c, dots_path: str, label: str) -> str:
    d1, d2, d3 = DOTS
    bx0, by0, bx1, by1 = SCENE_X - 6, SCENE_Y - 6, SCENE_X + COLS * PITCH + 4, SCENE_Y + ROWS * PITCH + 4
    corners = (
        f"M{bx0} {by0 + 14}V{by0}H{bx0 + 14}"
        f"M{bx1 - 14} {by0}H{bx1}V{by0 + 14}"
        f"M{bx0} {by1 - 14}V{by1}H{bx0 + 14}"
        f"M{bx1 - 14} {by1}H{bx1}V{by1 - 14}"
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">
  <title id="t">Marco Delizo · Software &amp; AI Engineer</title>
  <desc id="d">{label}</desc>
  <style>
    text {{ font-family: {MONO}; }}
    .code text {{ font-size: 13.5px; }}
    @keyframes blink {{ 0%, 49% {{ opacity: 1 }} 50%, 100% {{ opacity: 0 }} }}
    .cursor {{ animation: blink 1.1s steps(1) infinite; }}
  </style>
  <rect x="10" y="10" width="940" height="500" rx="16" fill="{c["window"]}" stroke="{c["window_stroke"]}" stroke-width="1.5"/>
  <circle cx="36" cy="35" r="5.5" fill="{d1}"/>
  <circle cx="55" cy="35" r="5.5" fill="{d2}"/>
  <circle cx="74" cy="35" r="5.5" fill="{d3}"/>
  <text x="480" y="40" text-anchor="middle" font-size="13" fill="{c["title"]}">nvim ~/marco.yml</text>
  <path d="M10 58H950" stroke="{c["window_stroke"]}"/>

  <rect x="28" y="74" width="556" height="418" rx="10" fill="{c["panel"]}" stroke="{c["panel_stroke"]}"/>
  <text x="46" y="95" font-size="13" font-weight="700" fill="{c["section"]}">marco.yml<tspan font-weight="400" fill="{c["muted"]}" font-size="11.5"> [yaml]</tspan></text>
  <rect x="462" y="83" width="108" height="20" rx="10" fill="{c["pill_bg"]}"/>
  <text x="516" y="97" text-anchor="middle" font-size="11.5" font-weight="700" fill="{c["pill_fg"]}">@marcodlzo</text>
  <path d="M28 106H584" stroke="{c["panel_stroke"]}"/>
  <rect class="cursor" x="82" y="436" width="8.2" height="18" fill="{c["key"]}" opacity="0.85"/>
  <g class="code">
    {chr(10).join("    " + ln for ln in code_lines(c)).strip()}
  </g>
  <path d="M28 462H584" stroke="{c["panel_stroke"]}"/>
  <rect x="40" y="469" width="66" height="17" rx="4" fill="{c["chip_bg"]}"/>
  <text x="73" y="481.5" text-anchor="middle" font-size="10.5" font-weight="700" fill="{c["chip_fg"]}">NORMAL</text>
  <text x="118" y="482" font-size="12" font-weight="700" fill="{c["value"]}">marco.yml</text>
  <text x="330" y="482" text-anchor="middle" font-size="11" fill="{c["muted"]}">[utf-8]</text>
  <text x="572" y="482" text-anchor="end" font-size="11" fill="{c["muted"]}">17L · 100% · 17:1</text>

  <rect x="600" y="74" width="332" height="418" rx="10" fill="{c["panel"]}" stroke="{c["panel_stroke"]}"/>
  <text x="616" y="95" font-size="12.5" font-weight="700" letter-spacing="1" fill="{c["section"]}">PINE.CITY</text>
  <text x="916" y="95" text-anchor="end" font-size="11" fill="{c["muted"]}">{COLS}×{ROWS} / 1-BIT</text>
  <path d="M600 106H932" stroke="{c["panel_stroke"]}"/>
  <path d="{corners}" fill="none" stroke="{c["gutter"]}" stroke-width="1.5"/>
  <path fill="{c["ink"]}" d="{dots_path}"/>
  <path d="M600 462H932" stroke="{c["panel_stroke"]}"/>
  <text x="616" y="482" font-size="10.5" fill="{c["muted"]}">16.41°N 120.59°E · 1,540 M ASL</text>
  <text x="916" y="482" text-anchor="end" font-size="10.5" fill="{c["muted"]}">FS/DITHER</text>
</svg>
'''


def main() -> None:
    portrait = ASSETS / "source" / "portrait.png"
    if portrait.exists():
        gray = portrait_scene(portrait, COLS, ROWS)
        label = "Editor-style card with Marco's profile in YAML and a 1-bit dithered portrait."
    else:
        gray = baguio_scene(COLS, ROWS)
        label = "Editor-style card with Marco's profile in YAML and a 1-bit dithered Baguio sunset over pine trees."
    dots = dither_path(gray)
    ASSETS.mkdir(exist_ok=True)
    for name, c in (("light", LIGHT), ("dark", DARK)):
        out = ASSETS / f"banner-{name}.svg"
        out.write_text(build(c, dots, label), encoding="utf-8")
        print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
