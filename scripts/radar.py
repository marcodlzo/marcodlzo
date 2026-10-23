"""Draws the radar charts in assets/ from assets/radar.json.

Writes assets/radar-<id>-light.svg and assets/radar-<id>-dark.svg for each chart.
Pure standard library, so the GitHub Action needs no installs.

Run from the repo root:  python scripts/radar.py
"""

from pathlib import Path
import json
import math
import sys

sys.path.insert(0, str(Path(__file__).parent))
from theme import DARK, LIGHT, MONO  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

W, H = 480, 362
CX, CY, R = 240, 210, 104


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def point(i: int, n: int, frac: float) -> tuple[float, float]:
    a = -math.pi / 2 + 2 * math.pi * i / n
    return CX + R * frac * math.cos(a), CY + R * frac * math.sin(a)


def poly(points) -> str:
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


def build(chart: dict, c: dict) -> str:
    axes = chart["axes"]
    n = len(axes)
    if n < 3:
        raise ValueError(f"chart {chart['id']!r} needs at least 3 axes")

    rings = "\n".join(
        f'    <polygon points="{poly(point(i, n, k / 5) for i in range(n))}" fill="none" stroke="{c["grid"]}"/>'
        for k in range(1, 6)
    )
    spokes = "\n".join(
        f'    <line x1="{CX}" y1="{CY}" x2="{x:.1f}" y2="{y:.1f}" stroke="{c["grid"]}"/>'
        for x, y in (point(i, n, 1) for i in range(n))
    )

    vals = [max(0, min(100, a["value"])) / 100 for a in axes]
    shape = poly(point(i, n, v) for i, v in enumerate(vals))
    dots = "\n".join(
        f'    <circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{c["dot"]}" stroke="{c["window"]}" stroke-width="1.5"/>'
        for x, y in (point(i, n, v) for i, v in enumerate(vals))
    )

    labels = []
    for i, a in enumerate(axes):
        x, y = point(i, n, 1.17)
        dx = x - CX
        anchor = "middle" if abs(dx) < 12 else ("start" if dx > 0 else "end")
        if y < CY - R * 0.9:
            y -= 6
        # Keep long labels inside the card (approx. monospace glyph widths).
        width = len(a["label"]) * 7.6 + 6 + len(str(int(a["value"]))) * 6.7
        if anchor == "start":
            x = min(x, W - 16 - width)
        elif anchor == "end":
            x = max(x, 16 + width)
        labels.append(
            f'    <text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" font-size="12.5" fill="{c["label"]}">'
            f'{esc(a["label"])}<tspan dx="6" fill="{c["muted"]}" font-size="11">{int(a["value"])}</tspan></text>'
        )
    labels_svg = "\n".join(labels)
    title = esc(chart["title"])

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t">
  <title id="t">{title} radar, self-rated 0 to 100: {esc(", ".join(f"{a['label']} {a['value']}" for a in axes))}</title>
  <style>
    text {{ font-family: {MONO}; }}
    @keyframes grow {{ from {{ transform: scale(0.15); opacity: 0 }} to {{ transform: scale(1); opacity: 1 }} }}
    .shape {{ transform-origin: {CX}px {CY}px; animation: grow 1.1s cubic-bezier(.2,.8,.2,1) both; }}
  </style>
  <rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14" fill="{c["window"]}" stroke="{c["window_stroke"]}" stroke-width="1.5"/>
  <text x="22" y="34" font-size="14" font-weight="700" fill="{c["section"]}">❯ {title}</text>
  <text x="{W - 22}" y="34" text-anchor="end" font-size="11" fill="{c["muted"]}">self-rated · 0-100</text>
  <g>
{rings}
{spokes}
  </g>
  <g class="shape">
    <polygon points="{shape}" fill="{c["fill"]}" fill-opacity="0.28" stroke="{c["key"]}" stroke-width="2" stroke-linejoin="round"/>
{dots}
  </g>
{labels_svg}
</svg>
'''


def main() -> None:
    data = json.loads((ASSETS / "radar.json").read_text(encoding="utf-8"))
    for chart in data["charts"]:
        for name, c in (("light", LIGHT), ("dark", DARK)):
            out = ASSETS / f"radar-{chart['id']}-{name}.svg"
            out.write_text(build(chart, c), encoding="utf-8")
            print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
