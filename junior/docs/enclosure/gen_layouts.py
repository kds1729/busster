"""Generate the Busster Junior enclosure drawing (SVG drawn to scale, 1 cm = 10 units).

Run with plain Python 3; writes enclosure.html next to this file. See ../enclosure.md.
VARIANTS holds the chosen 5" layout; REJECTED keeps the 7" variant for reference.
"""
import math

S = 10  # svg units per cm

# ---- shared numbers (cm) ----
BAND = 1.5          # flat band at top of back
FRONT_H = 2.0
WIDTH = 48.0
MARGIN = 3.0        # switch centre to side edge
FRONT_OFF = 4.0     # switch centre up from the front edge
UP8 = 10.0          # switch 8 up from the front edge
LED_UP = 2.5        # LED pair above switch centre
FOOT_R = 3.0        # 6 cm "foot zone" circle
DISP_TOP = 2.0      # window top below the band line

VARIANTS = [
    dict(key="5 inch", title='5" display, 20 cm deep plate (chosen)',
         slope=18.5, back_h=8.0, floor=19.0,
         disp_w=11.0, disp_h=6.7, mod_w=12.1, mod_h=7.6, act_w=10.8, act_h=6.5,
         panel='5" 800x480', boards="Sunton ESP32-8048S050C"),
]
REJECTED = [
    dict(key="7 inch", title='7" display, 22 cm deep plate',
         slope=20.5, back_h=8.5, floor=21.0,
         disp_w=15.6, disp_h=8.8, mod_w=16.5, mod_h=10.0, act_w=15.4, act_h=8.6,
         panel='7" 800x480', boards="Makerfabs MaTouch 7 or Sunton ESP32-8048S070"),
    dict(key="5 inch", title='5" display, 20 cm deep plate',
         slope=18.5, back_h=8.0, floor=19.0,
         disp_w=11.0, disp_h=6.7, mod_w=12.1, mod_h=7.6, act_w=10.8, act_h=6.5,
         panel='5" 800x480', boards="Makerfabs MaTouch 5 or Sunton ESP32-8048S050"),
]


def c(v):
    return round(v * S, 2)


def switch(x, y, label):
    return (
        f'<circle class="foot" cx="{c(x)}" cy="{c(y)}" r="{c(FOOT_R)}"/>'
        f'<circle class="sw" cx="{c(x)}" cy="{c(y)}" r="{c(0.6)}"/>'
        f'<text class="swlabel" x="{c(x)}" y="{c(y + 1.9)}">{label}</text>'
    )


def leds(x, y):
    return f'<circle class="led rgb" cx="{c(x)}" cy="{c(y - LED_UP)}" r="{c(0.25)}"/>'


def song(x, y, glyph):
    return (
        f'<circle class="sw song" cx="{c(x)}" cy="{c(y)}" r="{c(0.6)}"/>'
        f'<text class="swlabel" x="{c(x)}" y="{c(y + 1.9)}">{glyph}</text>'
    )


def display(x, y, v):
    cx, cy = x + v["disp_w"] / 2, y + v["disp_h"] / 2
    return (
        f'<rect class="module" x="{c(cx - v["mod_w"] / 2)}" y="{c(cy - v["mod_h"] / 2)}" width="{c(v["mod_w"])}" height="{c(v["mod_h"])}"/>'
        f'<rect class="disp" x="{c(x)}" y="{c(y)}" width="{c(v["disp_w"])}" height="{c(v["disp_h"])}"/>'
        f'<text class="disptext" x="{c(cx)}" y="{c(cy + 0.35)}">{v["panel"]}</text>'
        f'<text class="note" x="{c(cx)}" y="{c(cy + 1.5)}" text-anchor="middle">window {v["disp_w"]:g} x {v["disp_h"]:g}</text>'
        f'<text class="note" x="{c(cx)}" y="{c(cy + 2.4)}" text-anchor="middle">module {v["mod_w"]:g} x {v["mod_h"]:g}</text>'
    )


def dim_h(x1, x2, y, text, above=True):
    ty = y - 0.7 if above else y + 1.2
    return (
        f'<line class="dim" x1="{c(x1)}" y1="{c(y)}" x2="{c(x2)}" y2="{c(y)}"/>'
        f'<line class="dim" x1="{c(x1)}" y1="{c(y - 0.4)}" x2="{c(x1)}" y2="{c(y + 0.4)}"/>'
        f'<line class="dim" x1="{c(x2)}" y1="{c(y - 0.4)}" x2="{c(x2)}" y2="{c(y + 0.4)}"/>'
        f'<text class="dimtext" x="{c((x1 + x2) / 2)}" y="{c(ty)}">{text}</text>'
    )


def dim_v(x, y1, y2, text):
    return (
        f'<line class="dim" x1="{c(x)}" y1="{c(y1)}" x2="{c(x)}" y2="{c(y2)}"/>'
        f'<line class="dim" x1="{c(x - 0.4)}" y1="{c(y1)}" x2="{c(x + 0.4)}" y2="{c(y1)}"/>'
        f'<line class="dim" x1="{c(x - 0.4)}" y1="{c(y2)}" x2="{c(x + 0.4)}" y2="{c(y2)}"/>'
        f'<text class="dimtext" transform="translate({c(x - 0.5)} {c((y1 + y2) / 2)}) rotate(-90)">{text}</text>'
    )


def plate(width, depth, body):
    pad_l, pad_r, pad_t, pad_b = 3.5, 1.0, 3.0, 2.5
    vb = f"{c(-pad_l)} {c(-pad_t)} {c(width + pad_l + pad_r)} {c(depth + pad_t + pad_b)}"
    parts = [
        '<defs><linearGradient id="rgb" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="var(--red)"/><stop offset=".5" stop-color="var(--green)"/><stop offset="1" stop-color="var(--blue)"/></linearGradient></defs>',
        f'<rect class="plate" x="0" y="0" width="{c(width)}" height="{c(depth)}"/>',
        f'<line class="bend" x1="0" y1="{c(BAND)}" x2="{c(width)}" y2="{c(BAND)}"/>',
        f'<text class="note" x="{c(0.4)}" y="{c(BAND - 0.4)}">flat band {BAND:g} cm (bend line below)</text>',
        f'<text class="note" x="{c(width - 0.4)}" y="{c(depth - 0.5)}" text-anchor="end">front edge</text>',
        body,
        dim_h(0, width, -1.0, f"{width:g} cm"),
        dim_v(-1.5, 0, depth, f"{depth:g} cm"),
    ]
    return f'<svg viewBox="{vb}" xmlns="http://www.w3.org/2000/svg" role="img">{"".join(parts)}</svg>'


def arc_points(depth):
    ax, ay = MARGIN, depth - FRONT_OFF
    bx, by = WIDTH - MARGIN, depth - UP8
    dx, dy = bx - ax, ay - by
    R = (dx * dx + dy * dy) / (2 * dy)
    phi = math.asin(dx / R)
    pts = [(ax + R * math.sin(phi * i / 7), ay - R * (1 - math.cos(phi * i / 7))) for i in range(8)]
    chord = 2 * R * math.sin(phi / 14)
    return pts, R, phi, chord


def layout_svg(v):
    depth = BAND + v["slope"]
    pts, R, phi, chord = arc_points(depth)
    ax, ay = pts[0]
    bx, by = pts[7]
    b = [f'<path class="arc" d="M {c(ax)} {c(ay)} A {c(R)} {c(R)} 0 0 0 {c(bx)} {c(by)}"/>']
    for i, (x, y) in enumerate(pts):
        b.append(switch(x, y, str(i + 1)))
        b.append(leds(x, y))
    disp_x = pts[2][0]
    disp_y = BAND + DISP_TOP
    sy = disp_y + v["disp_h"] / 2
    b.append(display(disp_x, disp_y, v))
    b.append(song(3.5, sy, "&#9660;"))
    b.append(song(9.5, sy, "&#9650;"))
    b.append(dim_h(0, MARGIN, depth + 1.2, f"{MARGIN:g}", above=False))
    b.append(dim_v(WIDTH - 1.2, by, depth, f"{UP8:g}"))
    b.append(dim_v(WIDTH - 2.4, ay, depth, f"{FRONT_OFF:g}"))
    # clearance between the module's bottom edge and the nearest LED hole above a switch under it
    mod_bottom = sy + v["mod_h"] / 2
    mod_right = disp_x + v["disp_w"] / 2 + v["mod_w"] / 2
    clear = min(y - LED_UP - 0.25 - mod_bottom for (x, y) in pts if x - 0.25 < mod_right + 0.3)
    return plate(WIDTH, depth, "".join(b)), pts, R, phi, chord, disp_x, depth, clear


def profile_svg(v):
    """Hood profile: back, band, slope, front. Open bottom; sits on a wood base with wood end cheeks."""
    H = v["back_h"]
    floor = v["floor"]
    ang = math.atan2(H - FRONT_H, floor - BAND)
    slope_len = math.hypot(floor - BAND, H - FRONT_H)
    BASE_T = 1.8  # wood base thickness, indicative

    def P(x, y):
        return f"{c(x)},{c(H - y)}"

    outline = " ".join(P(x, y) for x, y in [(0, 0), (0, H), (BAND, H), (floor, FRONT_H), (floor, 0)])
    prof = (
        f'<rect class="wood" x="{c(-1.0)}" y="{c(H)}" width="{c(floor + 2.0)}" height="{c(BASE_T)}"/>'
        f'<polyline class="prof" points="{outline}"/>'
        + dim_v(-1.2, 0, H, f"back {H:g}")
        + dim_v(floor + 1.2, H - FRONT_H, H, f"{FRONT_H:g}")
        + dim_h(0, floor, -2.4, f"hood {floor:g} cm deep")
        + f'<text class="note" x="{c(BAND + 1.0)}" y="{c(1.4)}" transform="rotate({math.degrees(ang):.1f} {c(BAND)} 0)">slope {slope_len:.1f} cm at {math.degrees(ang):.0f}&#176;</text>'
        + f'<text class="note" x="{c(0.2)}" y="{c(-0.4)}">band {BAND:g}</text>'
        + f'<text class="note" x="{c(floor / 2)}" y="{c(H + BASE_T + 1.0)}" text-anchor="middle">wood base plate, open underneath for access; wood end cheeks close the sides</text>'
        + f'<text class="note" x="{c(floor - 0.2)}" y="{c(H + BASE_T + 2.2)}" text-anchor="end">player side &#8594;</text>'
    )
    vb = f"{c(-3)} {c(-4)} {c(floor + 6)} {c(H + BASE_T + 7.5)}"
    return f'<svg viewBox="{vb}" xmlns="http://www.w3.org/2000/svg" role="img">{prof}</svg>', slope_len, math.degrees(ang)


LEGEND = '<div class="legend"><span class="lf">6 cm foot zone around each switch</span><span class="lrgb">RGB LED (5 mm addressable)</span><span class="ld">dimension</span></div>'

sections = []
for v in VARIANTS:
    svg, pts, R, phi, chord, disp_x, depth, clear = layout_svg(v)
    prof, slope_len, ang = profile_svg(v)
    rows = "".join(
        f"<tr><td>{i + 1}</td><td>{x:.1f}</td><td>{depth - y:.1f}</td><td>{'' if i == 0 else f'{math.dist(pts[i - 1], pts[i]):.2f}'}</td></tr>"
        for i, (x, y) in enumerate(pts)
    )
    sections.append(f"""
<section>
<div class="eyebrow">{v["key"]}</div>
<h2>{v["title"]}</h2>
{svg}
{LEGEND}
<p>Window {v["disp_w"]:g} x {v["disp_h"]:g} cm for a {v["panel"]} IPS panel ({v["boards"]}), active area {v["act_w"]:g} x {v["act_h"]:g} cm, module about {v["mod_w"]:g} x {v["mod_h"]:g} cm (dashed, to confirm from the board drawing). The window's left edge is on switch 3's centre line, {disp_x:.1f} cm from the left, {DISP_TOP:g} cm below the band. Song switches are level with the window centre. The module clears the nearest LED hole by {clear:.1f} cm.</p>
<div class="two">
<div class="profile">{prof}</div>
<div class="wrap"><table>
<tr><th>Item</th><th>Value</th></tr>
<tr><td>Plate</td><td>{WIDTH:g} x {depth:g} cm</td></tr>
<tr><td>Back / front height</td><td>{v["back_h"]:g} / {FRONT_H:g} cm</td></tr>
<tr><td>Hood depth, back to front edge</td><td>{v["floor"]:g} cm</td></tr>
<tr><td>Flat pattern</td><td>{WIDTH:g} x {v["back_h"] + BAND + v["slope"] + FRONT_H:g} cm, 4 bends, all 90 degrees or less</td></tr>
<tr><td>Slope</td><td>{slope_len:.1f} cm at {ang:.0f} degrees</td></tr>
<tr><td>Switch arc</td><td>radius {R:.0f} cm, neighbours {chord:.1f} cm apart</td></tr>
</table></div>
</div>
<details><summary>Switch coordinates</summary>
<div class="wrap"><table>
<tr><th>Switch</th><th>From left edge</th><th>Up from front</th><th>Distance to previous</th></tr>
{rows}
</table></div>
</details>
</section>""")

html = f"""<title>Busster Junior Enclosure</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* Layout: a drafting sheet. One column; each variant is a full-width drawing with its profile and numbers beneath. */
:root {{
  --bg: #eef0f2; --paper: #fbfbfa; --ink: #1d242c; --muted: #5b6672; --line: #c9ced4;
  --accent: #2f6b99; --dim: #b4543a; --green: #2e9b5a; --blue: #2d7fd6; --red: #c8402f;
  --foot: rgba(47,107,153,.08); --wood: #d9b98a;
  --sans: "IBM Plex Sans", "Helvetica Neue", Arial, sans-serif;
  --mono: "IBM Plex Mono", Menlo, Consolas, monospace;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --bg: #14181d; --paper: #1d2329; --ink: #e4e8ec; --muted: #9aa6b2; --line: #39424c;
  --accent: #7db5e0; --dim: #e0896f; --green: #4fc47e; --blue: #5aa4ee; --red: #ee6a57;
  --foot: rgba(125,181,224,.10); --wood: #6b5435; color-scheme: dark }} }}
:root[data-theme="dark"] {{
  --bg: #14181d; --paper: #1d2329; --ink: #e4e8ec; --muted: #9aa6b2; --line: #39424c;
  --accent: #7db5e0; --dim: #e0896f; --green: #4fc47e; --blue: #5aa4ee; --red: #ee6a57;
  --foot: rgba(125,181,224,.10); --wood: #6b5435; color-scheme: dark }}
body {{ background: var(--bg); color: var(--ink); font-family: var(--sans); line-height: 1.5;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
  padding-block: 24px 48px; }}
main {{ max-width: 1100px; margin: 0 auto; display: grid; gap: 32px; }}
h1 {{ font-size: 1.6rem; font-weight: 600; margin: 0; text-wrap: balance; }}
h2 {{ font-size: 1.1rem; font-weight: 600; margin: 0 0 4px; }}
p {{ max-width: 72ch; margin: 0; }}
.lede {{ color: var(--muted); }}
section {{ background: var(--paper); border: 1px solid var(--line); border-radius: 6px; padding: 20px; display: grid; gap: 14px; }}
.eyebrow {{ font-family: var(--mono); font-size: .75rem; letter-spacing: .08em; text-transform: uppercase; color: var(--accent); }}
svg {{ width: 100%; height: auto; display: block; font-family: var(--mono); }}
.plate {{ fill: var(--paper); stroke: var(--ink); stroke-width: 1.6; }}
.bend {{ stroke: var(--ink); stroke-width: .8; stroke-dasharray: 6 4; }}
.prof {{ fill: none; stroke: var(--ink); stroke-width: 1.6; stroke-linejoin: round; }}
.arc {{ fill: none; stroke: var(--accent); stroke-width: .8; stroke-dasharray: 3 3; }}
.foot {{ fill: var(--foot); stroke: var(--accent); stroke-width: .5; stroke-dasharray: 2 2; }}
.sw {{ fill: var(--paper); stroke: var(--ink); stroke-width: 1.4; }}
.song {{ stroke: var(--accent); }}
.led.rgb {{ fill: url(#rgb); stroke: var(--ink); stroke-width: .3; }}
.swlabel {{ font-size: 11px; text-anchor: middle; fill: var(--ink); }}
.disp {{ fill: none; stroke: var(--ink); stroke-width: 1.2; }}
.module {{ fill: none; stroke: var(--muted); stroke-width: .6; stroke-dasharray: 3 2; }}
.wood {{ fill: var(--wood); stroke: none; }}
.disptext {{ font-size: 10px; text-anchor: middle; fill: var(--muted); }}
.dim {{ stroke: var(--dim); stroke-width: .6; }}
.dimtext {{ font-size: 9px; text-anchor: middle; fill: var(--dim); }}
.note {{ font-size: 8px; fill: var(--muted); }}
.two {{ display: grid; grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr); gap: 20px; align-items: start; }}
@media (max-width: 700px) {{ .two {{ grid-template-columns: 1fr; }} }}
.profile .dimtext {{ font-size: 5.5px; }} .profile .note {{ font-size: 5px; }} .profile .prof {{ stroke-width: 1; }} .profile .dim {{ stroke-width: .4; }}
table {{ border-collapse: collapse; font-size: .9rem; font-variant-numeric: tabular-nums; }}
th, td {{ text-align: left; padding: 4px 14px 4px 0; border-bottom: 1px solid var(--line); vertical-align: top; }}
th {{ font-weight: 500; color: var(--muted); }}
.wrap {{ overflow-x: auto; }}
details summary {{ cursor: pointer; color: var(--muted); font-size: .9rem; }}
details summary:focus-visible {{ outline: 2px solid var(--accent); }}
.legend {{ display: flex; flex-wrap: wrap; gap: 6px 18px; font-size: .85rem; color: var(--muted); }}
.legend span::before {{ content: ""; display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; vertical-align: -1px; }}
.legend .lrgb::before {{ background: conic-gradient(var(--red), var(--green), var(--blue), var(--red)); }}
.legend .lf::before {{ background: var(--foot); border: 1px dashed var(--accent); }}
.legend .ld::before {{ background: var(--dim); border-radius: 0; height: 2px; vertical-align: 3px; }}
</style>
<main>
<div>
<h1>Busster Junior Enclosure</h1>
<p class="lede">The folded-metal hood drawn to scale with the chosen 5 inch display, on a wood base with wood end cheeks. All sizes in centimetres, switch positions are centres. The 7 inch variant on a 22 cm plate was drawn and rejected on 2026-11-15.</p>
</div>
{"".join(sections)}
<section>
<div class="eyebrow">Shared</div>
<div class="wrap"><table>
<tr><th>Item</th><th>Value</th></tr>
<tr><td>Switch to side edge / to front edge</td><td>{MARGIN:g} cm / {FRONT_OFF:g} cm</td></tr>
<tr><td>Switch 8 up from the front</td><td>{UP8:g} cm</td></tr>
<tr><td>LED</td><td>one 5 mm addressable RGB LED (WS2812 type) {LED_UP:g} cm above each switch centre; all on one data line, colour set by the firmware (blue, green, red for the page switch)</td></tr>
<tr><td>Song switches</td><td>side by side at 3.5 and 9.5 cm from the left, level with the window centre</td></tr>
<tr><td>Metal part</td><td>a hood: back, {BAND:g} cm band, slope, {FRONT_H:g} cm front, 4 bends, open underneath. Option 2 in the sketch replaces the two front bends with a 1 cm radius. A closed one-piece wrap with floor flanges was dropped: press-brake shops cannot form a box that closes on itself</td></tr>
<tr><td>Wood parts</td><td>base plate the hood screws down to (carries the feet; the underside stays open for access) and two end cheeks</td></tr>
</table></div>
</section>
</main>
"""

out = __file__.rsplit("/", 1)[0] + "/enclosure.html"
with open(out, "w") as f:
    f.write("<!doctype html>\n<meta charset=\"utf-8\">\n<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n" + html)
for v in VARIANTS:
    svg, pts, R, phi, chord, disp_x, depth, clear = layout_svg(v)
    print(v["key"], f"depth={depth:g} R={R:.1f} chord={chord:.2f} clearance={clear:.2f}")
