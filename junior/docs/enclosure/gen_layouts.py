"""Generate the Busster Junior enclosure drawing (SVG drawn to scale, 1 cm = 10 units).

Run with plain Python 3; writes enclosure.html next to this file. See ../enclosure.md.

Construction (2026-11-16): one aluminium sheet with a single bend (back + sloped
control face) resting on four wooden wedge ribs, with a decorative wooden front
rail and a rigid base. Four thumb screws into threaded inserts in the two outer
ribs hold it down; the whole electronics assembly lifts out with the metal.
"""
import math

S = 10  # svg units per cm

# ---- shared numbers (cm) ----
WIDTH = 52.0        # 48 for the switches plus 2 cm each side so switch 1 and 8 clear the outer ribs
BACK_H = 8.0        # back height, which is also the rib height at the back
BAND = 0.0          # no flat band: the back bends straight into the slope
FRONT_H = 2.0       # rib height at the front
DEPTH = 19.0        # footprint depth, back face to the panel's front edge
SLOPE = math.hypot(DEPTH - BAND, BACK_H - FRONT_H)  # sloped face, measured along the slope
SLOPE_DEG = math.degrees(math.atan2(BACK_H - FRONT_H, DEPTH - BAND))
BEND_DEG = 90 + SLOPE_DEG  # bend angle between the back and the sloped face
MARGIN = 5.0        # switch centre to side edge: outer rib (3.8) + switch body (0.9) + clearance
FRONT_OFF = 4.0     # switch centre up from the front edge
UP8 = 10.0          # switch 8 up from the front edge
LED_UP = 2.5        # LED above switch centre
FOOT_R = 3.0        # 6 cm "foot zone" circle
DISP_TOP = 2.0      # window top below the bend line
RIB_T_OUTER = 3.8   # outer ribs: two laminated 3/4" pieces
RIB_T_INNER = 1.9   # inner ribs: one 3/4" piece
RAIL_T = 0.6        # decorative front rail (1/4" stock) under the panel's front edge; the ribs stop behind it
BASE_T = 1.27       # base thickness: 1/2" Baltic birch
ANCHOR_FRONT = 2.0  # thumb screws up from the front edge, behind the rail and in the rib
ANCHOR_BACK = 16.5  # thumb screws up from the front edge
SW_BODY_R = 0.9     # footswitch body radius below the panel, plus a little
SONG_X = (MARGIN + 0.5, MARGIN + 6.5)  # song down / up switches from the left edge

DISPLAY = dict(
    disp_w=11.0, disp_h=6.7, mod_w=12.1, mod_h=7.6, act_w=10.8, act_h=6.5,
    panel='5" 800x480', boards="Sunton ESP32-8048S050C",
)


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


def anchor(x, y):
    return (
        f'<circle class="anchor" cx="{c(x)}" cy="{c(y)}" r="{c(0.6)}"/>'
        f'<line class="anchorx" x1="{c(x - 0.4)}" y1="{c(y)}" x2="{c(x + 0.4)}" y2="{c(y)}"/>'
        f'<line class="anchorx" x1="{c(x)}" y1="{c(y - 0.4)}" x2="{c(x)}" y2="{c(y + 0.4)}"/>'
    )


def rib_strip(x0, t, depth, label):
    return (
        f'<rect class="rib" x="{c(x0)}" y="0" width="{c(t)}" height="{c(depth)}"/>'
        f'<text class="note" transform="translate({c(x0 + t / 2 + 0.3)} {c(depth / 2 + 2.0)}) rotate(-90)">{label}</text>'
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
        body,
        f'<text class="note" x="{c(0.4)}" y="{c(-0.3)}">bend line: the {BACK_H:g} cm back continues below it, same sheet</text>',
        f'<text class="note" x="{c(width - 0.4)}" y="{c(depth - 0.5)}" text-anchor="end">front edge</text>',
        dim_h(0, width, -1.4, f"{width:g} cm"),
        dim_v(-1.5, 0, depth, f"{depth:.1f} cm"),
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


def ribs_for(pts):
    """(left edge, thickness) of each rib. Outer ribs flush with the panel ends;
    inner ribs centred midway between switches 2-3 and 5-6, clear of the display module."""
    m23 = (pts[1][0] + pts[2][0]) / 2
    m56 = (pts[4][0] + pts[5][0]) / 2
    return [(0.0, RIB_T_OUTER), (m23 - RIB_T_INNER / 2, RIB_T_INNER),
            (m56 - RIB_T_INNER / 2, RIB_T_INNER), (WIDTH - RIB_T_OUTER, RIB_T_OUTER)]


def layout_svg(v):
    depth = SLOPE
    pts, R, phi, chord = arc_points(depth)
    ribs = ribs_for(pts)
    ax, ay = pts[0]
    bx, by = pts[7]
    b = []
    for i, (x0, t) in enumerate(ribs):
        b.append(rib_strip(x0, t, depth - RAIL_T, f"rib {i + 1} ({t:g})"))
    b.append(f'<rect class="rib" x="0" y="{c(depth - RAIL_T)}" width="{c(WIDTH)}" height="{c(RAIL_T)}"/>')
    b.append(f'<path class="arc" d="M {c(ax)} {c(ay)} A {c(R)} {c(R)} 0 0 0 {c(bx)} {c(by)}"/>')
    for i, (x, y) in enumerate(pts):
        b.append(switch(x, y, str(i + 1)))
        b.append(leds(x, y))
    disp_x = pts[2][0]
    disp_y = DISP_TOP
    sy = disp_y + v["disp_h"] / 2
    b.append(display(disp_x, disp_y, v))
    b.append(song(SONG_X[0], sy, "&#9660;"))
    b.append(song(SONG_X[1], sy, "&#9650;"))
    lc, rc = RIB_T_OUTER / 2, WIDTH - RIB_T_OUTER / 2
    anchors = [(lc, depth - ANCHOR_FRONT), (lc, depth - ANCHOR_BACK),
               (rc, depth - ANCHOR_FRONT), (rc, depth - ANCHOR_BACK)]
    for x, y in anchors:
        b.append(anchor(x, y))
    b.append(dim_h(0, MARGIN, depth + 1.2, f"{MARGIN:g}", above=False))
    b.append(dim_v(WIDTH - 1.2, by, depth, f"{UP8:g}"))
    b.append(dim_v(WIDTH - 2.4, ay, depth, f"{FRONT_OFF:g}"))
    # clearances: module edge to nearest LED hole, and module edge to the nearest rib face
    mod_bottom = sy + v["mod_h"] / 2
    mod_cx = disp_x + v["disp_w"] / 2
    mod_left, mod_right = mod_cx - v["mod_w"] / 2, mod_cx + v["mod_w"] / 2
    clear_led = min(y - LED_UP - 0.25 - mod_bottom for (x, y) in pts if x - 0.25 < mod_right + 0.3)
    clear_rib = min(mod_left - (ribs[1][0] + ribs[1][1]), ribs[2][0] - mod_right)
    clear_sw = MARGIN - RIB_T_OUTER - SW_BODY_R
    spans = [ribs[i + 1][0] - (ribs[i][0] + ribs[i][1]) for i in range(3)]
    return dict(svg=plate(WIDTH, depth, "".join(b)), pts=pts, R=R, chord=chord, disp_x=disp_x,
                depth=depth, clear_led=clear_led, clear_rib=clear_rib, clear_sw=clear_sw, ribs=ribs, anchors=anchors, spans=spans)


def profile_svg():
    """Section through the box: base, rib, back angle, panel, front rail."""
    H = BACK_H
    ang = math.atan2(H - FRONT_H, DEPTH - BAND)
    slope_len = math.hypot(DEPTH - BAND, H - FRONT_H)
    T = 0.2  # metal thickness as drawn

    def P(x, y):
        return f"{c(x)},{c(H - y)}"

    rib_len = DEPTH - RAIL_T
    h_rib_front = H - (H - FRONT_H) * (rib_len - BAND) / (DEPTH - BAND)
    rib = " ".join(P(x, y) for x, y in [(0, 0), (0, H), (BAND, H), (rib_len, h_rib_front), (rib_len, 0)])
    ux, uy = (DEPTH - BAND) / slope_len, (H - FRONT_H) / slope_len   # along the slope, downward
    nx, ny = uy, ux                                                   # outward normal (up)
    sheet = " ".join(P(x, y) for x, y in [
        (-T, 0), (-T, H + ny * T), (DEPTH + nx * T, FRONT_H + ny * T), (DEPTH, FRONT_H), (0, H), (0, 0)])
    rail_top = FRONT_H + ny * T
    rail = '<polygon class="wood" points="' + " ".join(P(x, y) for x, y in [(rib_len, 0), (rib_len, h_rib_front), (DEPTH, FRONT_H), (DEPTH, 0)]) + '"/>'  # on the base, under the panel
    screws = ""
    for up in (ANCHOR_FRONT, ANCHOR_BACK):
        d = SLOPE - up
        x, y = BAND + ux * d, H - uy * d
        screws += f'<line class="screw" x1="{c(x + nx * 0.9)}" y1="{c(H - (y + ny * 0.9))}" x2="{c(x - nx * 2.0)}" y2="{c(H - (y - ny * 2.0))}"/>'
    base_screws = "".join(
        f'<line class="screw" x1="{c(x)}" y1="{c(H + BASE_T + 0.3)}" x2="{c(x)}" y2="{c(H - 1.4)}"/>' for x in (4.0, 13.0))
    prof = (
        f'<rect class="base" x="{c(-T)}" y="{c(H)}" width="{c(DEPTH + T)}" height="{c(BASE_T)}"/>'
        f'<polygon class="wood" points="{rib}"/>'
        + rail
        + f'<polygon class="metal" points="{sheet}"/>'
        + screws + base_screws
        + dim_v(-1.6, 0, H, f"back {H:g}")
        + dim_v(DEPTH + 1.2, H - FRONT_H, H, f"{FRONT_H:g}")
        + dim_h(0, DEPTH, -2.6, f"base {DEPTH:g} cm deep: ribs {DEPTH - RAIL_T:g} + rail {RAIL_T:g} under the panel's front edge")
        + f'<text class="note" x="{c(BAND + 1.0)}" y="{c(1.6)}" transform="rotate({math.degrees(ang):.1f} {c(BAND)} 0)">sloped face {slope_len:.1f} at {math.degrees(ang):.0f}&#176; on the rib; thumb screws {ANCHOR_FRONT:g} and {ANCHOR_BACK:g} from the front</text>'
        + f'<text class="note" x="{c(0.2)}" y="{c(-0.5)}">one bend, {BEND_DEG:.0f}&#176;</text>'
        + f'<text class="note" x="{c(DEPTH + 0.4)}" y="{c(H - 0.6)}">rail</text>'
        + f'<text class="note" x="{c(DEPTH / 2)}" y="{c(H + BASE_T + 1.2)}" text-anchor="middle">base: 1/2\" Baltic birch, sealed; ribs glued and screwed to it from below, rail glued</text>'
        + f'<text class="note" x="{c(DEPTH - 0.2)}" y="{c(H + BASE_T + 2.4)}" text-anchor="end">player side &#8594;</text>'
        + f'<text class="note" x="{c(-2.6)}" y="{c(H)}" text-anchor="start" transform="rotate(-90 {c(-2.6)} {c(H)})">back, jacks</text>'
    )
    vb = f"{c(-4.5)} {c(-4)} {c(DEPTH + 9.5)} {c(H + BASE_T + 7.5)}"
    return f'<svg viewBox="{vb}" xmlns="http://www.w3.org/2000/svg" role="img">{prof}</svg>', slope_len, math.degrees(ang)


LEGEND = ('<div class="legend"><span class="lf">6 cm foot zone around each switch</span>'
          '<span class="lrgb">RGB LED (5 mm addressable)</span>'
          '<span class="lw">wood rib under the panel</span>'
          '<span class="la">thumb screw into a threaded insert</span>'
          '<span class="ld">dimension</span></div>')

v = DISPLAY
L = layout_svg(v)
prof, slope_len, ang = profile_svg()
pts, ribs, anchors = L["pts"], L["ribs"], L["anchors"]
depth = L["depth"]
rows = "".join(
    f"<tr><td>{i + 1}</td><td>{x:.1f}</td><td>{depth - y:.1f}</td><td>{'' if i == 0 else f'{math.dist(pts[i - 1], pts[i]):.2f}'}</td></tr>"
    for i, (x, y) in enumerate(pts)
)
rib_rows = "".join(
    f"<tr><td>rib {i + 1}</td><td>{t:g}</td><td>{x0:.1f} to {x0 + t:.1f}</td><td>{x0 + t / 2:.2f}</td></tr>"
    for i, (x0, t) in enumerate(ribs)
)
anchor_rows = "".join(
    f"<tr><td>{n}</td><td>{x:.1f}</td><td>{depth - y:.1f}</td></tr>"
    for n, (x, y) in zip(("front left", "back left", "front right", "back right"), anchors)
)

html = f"""<title>Busster Junior Enclosure</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* Layout: a drafting sheet. One column; the panel drawing, then the section and the numbers beneath. */
:root {{
  --bg: #eef0f2; --paper: #fbfbfa; --ink: #1d242c; --muted: #5b6672; --line: #c9ced4;
  --accent: #2f6b99; --dim: #b4543a; --green: #2e9b5a; --blue: #2d7fd6; --red: #c8402f;
  --foot: rgba(47,107,153,.08); --wood: #d9b98a; --woodline: #a67c4a; --metal: #8d97a1; --base: #c4c9ce;
  --sans: "IBM Plex Sans", "Helvetica Neue", Arial, sans-serif;
  --mono: "IBM Plex Mono", Menlo, Consolas, monospace;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --bg: #14181d; --paper: #1d2329; --ink: #e4e8ec; --muted: #9aa6b2; --line: #39424c;
  --accent: #7db5e0; --dim: #e0896f; --green: #4fc47e; --blue: #5aa4ee; --red: #ee6a57;
  --foot: rgba(125,181,224,.10); --wood: #6b5435; --woodline: #a67c4a; --metal: #aab3bc; --base: #3a434c; color-scheme: dark }} }}
:root[data-theme="dark"] {{
  --bg: #14181d; --paper: #1d2329; --ink: #e4e8ec; --muted: #9aa6b2; --line: #39424c;
  --accent: #7db5e0; --dim: #e0896f; --green: #4fc47e; --blue: #5aa4ee; --red: #ee6a57;
  --foot: rgba(125,181,224,.10); --wood: #6b5435; --woodline: #a67c4a; --metal: #aab3bc; --base: #3a434c; color-scheme: dark }}
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
.rib {{ fill: var(--wood); fill-opacity: .45; stroke: var(--woodline); stroke-width: .5; stroke-dasharray: 3 2; }}
.arc {{ fill: none; stroke: var(--accent); stroke-width: .8; stroke-dasharray: 3 3; }}
.foot {{ fill: var(--foot); stroke: var(--accent); stroke-width: .5; stroke-dasharray: 2 2; }}
.sw {{ fill: var(--paper); stroke: var(--ink); stroke-width: 1.4; }}
.song {{ stroke: var(--accent); }}
.led.rgb {{ fill: url(#rgb); stroke: var(--ink); stroke-width: .3; }}
.swlabel {{ font-size: 11px; text-anchor: middle; fill: var(--ink); }}
.disp {{ fill: none; stroke: var(--ink); stroke-width: 1.2; }}
.module {{ fill: none; stroke: var(--muted); stroke-width: .6; stroke-dasharray: 3 2; }}
.anchor {{ fill: var(--paper); stroke: var(--dim); stroke-width: 1.2; }}
.anchorx {{ stroke: var(--dim); stroke-width: .8; }}
.wood {{ fill: var(--wood); stroke: var(--woodline); stroke-width: .5; }}
.metal {{ fill: var(--metal); stroke: var(--ink); stroke-width: .5; }}
.base {{ fill: var(--base); stroke: var(--ink); stroke-width: .5; }}
.screw {{ stroke: var(--dim); stroke-width: 1.4; stroke-linecap: round; }}
.disptext {{ font-size: 10px; text-anchor: middle; fill: var(--muted); }}
.dim {{ stroke: var(--dim); stroke-width: .6; }}
.dimtext {{ font-size: 9px; text-anchor: middle; fill: var(--dim); }}
.note {{ font-size: 8px; fill: var(--muted); }}
.two {{ display: grid; grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr); gap: 20px; align-items: start; }}
@media (max-width: 700px) {{ .two {{ grid-template-columns: 1fr; }} }}
.profile .dimtext {{ font-size: 5.5px; }} .profile .note {{ font-size: 5px; }} .profile .dim {{ stroke-width: .4; }} .profile .screw {{ stroke-width: .9; }}
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
.legend .lw::before {{ background: var(--wood); border-radius: 0; }}
.legend .la::before {{ background: var(--paper); border: 2px solid var(--dim); }}
.legend .ld::before {{ background: var(--dim); border-radius: 0; height: 2px; vertical-align: 3px; }}
</style>
<main>
<div>
<h1>Busster Junior Enclosure</h1>
<p class="lede">One aluminium sheet with a single bend, back and sloped control face, on four wooden wedge ribs, with a decorative wooden front rail and a plywood base. Drawn to scale; all sizes in centimetres, switch positions are hole centres. The wood under the sheet is shown dashed.</p>
</div>
<section>
<div class="eyebrow">Sloped face</div>
<h2>Sloped face {WIDTH:g} x {depth:.1f} cm, {v["panel"]} display</h2>
{L["svg"]}
{LEGEND}
<p>Window {v["disp_w"]:g} x {v["disp_h"]:g} cm for a {v["panel"]} IPS panel ({v["boards"]}), active area {v["act_w"]:g} x {v["act_h"]:g} cm, module about {v["mod_w"]:g} x {v["mod_h"]:g} cm (dashed, to confirm from the board drawing). The window's left edge is on switch 3's centre line, {L["disp_x"]:.1f} cm from the left, {DISP_TOP:g} cm below the bend. Song switches are level with the window centre. The module clears the nearest LED hole by {L["clear_led"]:.1f} cm and the nearest rib by {L["clear_rib"]:.1f} cm. Switches 1 and 8 are {MARGIN:g} cm from the panel ends, which leaves {L["clear_sw"]:.1f} cm between the switch body and the outer rib; that is why the panel is {WIDTH:g} wide rather than 48. The circuit board bolts to the inside of the back next to the jacks, so every electrical part is on the sheet and lifts out with it; wiring to the switches runs through holes in the inner ribs.</p>
<div class="two">
<div class="profile">{prof}</div>
<div class="wrap"><table>
<tr><th>Part</th><th>Size</th></tr>
<tr><td>Chassis (aluminium, one bend)</td><td>sloped face {WIDTH:g} x {depth:.1f}, back {WIDTH:g} x {BACK_H:g}; flat pattern {WIDTH:g} x {BACK_H + depth:.1f}, bent {BEND_DEG:.0f}&#176;</td></tr>
<tr><td>Outer ribs (wood, 2, laminated)</td><td>{DEPTH - RAIL_T:g} long, {BACK_H:g} at the back, stopping behind the rail; {RIB_T_OUTER:g} thick; top back corner chamfered for the bend radius</td></tr>
<tr><td>Inner ribs (wood, 2)</td><td>same profile, {RIB_T_INNER:g} thick (one 1/2" ply layer if laser cut), placed between switches and clear of the display module</td></tr>
<tr><td>Front rail (wood, decorative, 1/4")</td><td>{WIDTH:g} long, {RAIL_T:g} thick, on the base under the panel's front edge, top bevelled to the slope, {FRONT_H:g} high at the front</td></tr>
<tr><td>Base (1/2" Baltic birch, sealed)</td><td>{WIDTH:g} x {DEPTH:g} cm, ribs glued and screwed from below, rail glued</td></tr>
<tr><td>Slope</td><td>{slope_len:.1f} cm at {ang:.1f} degrees</td></tr>
<tr><td>Switch arc</td><td>radius {L["R"]:.0f} cm, neighbours {L["chord"]:.1f} cm apart</td></tr>
<tr><td>Panel spans between ribs</td><td>{", ".join(f"{s:.1f}" for s in L["spans"])} cm</td></tr>
</table></div>
</div>
<details><summary>Switch coordinates</summary>
<div class="wrap"><table>
<tr><th>Switch</th><th>From left edge</th><th>Up from front</th><th>Distance to previous</th></tr>
{rows}
</table></div>
</details>
<details><summary>Rib and thumb screw positions</summary>
<div class="wrap"><table>
<tr><th>Rib</th><th>Thickness</th><th>From left edge</th><th>Centre</th></tr>
{rib_rows}
</table></div>
<div class="wrap"><table>
<tr><th>Thumb screw</th><th>From left edge</th><th>Up from front</th></tr>
{anchor_rows}
</table></div>
</details>
</section>
<section>
<div class="eyebrow">Shared</div>
<div class="wrap"><table>
<tr><th>Item</th><th>Value</th></tr>
<tr><td>Switch to side edge / to front edge</td><td>{MARGIN:g} cm / {FRONT_OFF:g} cm</td></tr>
<tr><td>Switch 8 up from the front</td><td>{UP8:g} cm</td></tr>
<tr><td>LED</td><td>one 5 mm addressable RGB LED (WS2812 type) {LED_UP:g} cm above each switch centre; all on one data line, colour set by the firmware (blue, green, red for the page switch)</td></tr>
<tr><td>Song switches</td><td>side by side at {SONG_X[0]:g} and {SONG_X[1]:g} cm from the left, level with the window centre</td></tr>
<tr><td>Hold-down</td><td>four flat-head knurled thumb screws (M4) into brass threaded inserts in the sloped top of the two outer ribs; the chassis, with every electrical part on it, lifts out without tools</td></tr>
<tr><td>Metal</td><td>one aluminium sheet, bare, sanded matte, bent once between the back and the sloped face; no seam for a spill to enter. The ribs carry the load, so 1.5 to 2 mm is enough. The back carries the power, USB and MIDI jacks and the circuit board</td></tr>
<tr><td>Grounding</td><td>the sheet is signal ground, bonded at one point: a crimped ring terminal with an internal-tooth star washer under the MIDI jack nut</td></tr>
<tr><td>History</td><td>a closed one-piece wrap, a four-bend hood, and a flat panel with a separate back angle were each dropped on 2026-11-15/16: the first two for bending limits at cut-and-bend shops, the last for the seam between the two parts</td></tr>
</table></div>
</section>
</main>
"""

out = __file__.rsplit("/", 1)[0] + "/enclosure.html"
with open(out, "w") as f:
    f.write("<!doctype html>\n<meta charset=\"utf-8\">\n<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n" + html)
print(f"width={WIDTH:g} depth={depth:.2f} slope_deg={SLOPE_DEG:.1f} bend={BEND_DEG:.1f} R={L['R']:.1f} chord={L['chord']:.2f} clear_led={L['clear_led']:.2f} clear_rib={L['clear_rib']:.2f} clear_sw={L['clear_sw']:.2f}")
print("ribs", [(round(x0, 2), t) for x0, t in ribs], "spans", [round(s, 1) for s in L["spans"]])
print("anchors", [(round(x, 2), round(depth - y, 1)) for x, y in anchors])
print("switches", [(round(x, 1), round(depth - y, 1)) for x, y in pts])
