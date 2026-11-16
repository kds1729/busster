"""Write the cut files for the enclosure: chassis flat pattern, rib profile, base.

Run with plain Python 3 from anywhere; writes dxf/*.dxf and dxf/preview.html next
to this file. Every position comes from gen_layouts.py so the DXFs cannot drift
from the drawing. DXF is R12 ASCII in millimetres: LINE and CIRCLE entities only,
which every cut-and-bend shop's uploader reads.

Layers: CUT (through cuts), BEND (bend line, not a cut), PLACEHOLDER (circuit
board standoff holes, to confirm once the board is designed).
"""
import contextlib
import io
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
with contextlib.redirect_stdout(io.StringIO()):
    import gen_layouts as G  # noqa: E402  (regenerates enclosure.html, harmlessly)

MM = 10.0  # the drawing is in cm

# ---- hole sizes (mm) ----
FOOTSWITCH_HOLE = 12.5   # 12 mm bushing footswitch
LED_HOLE = 5.2           # 5 mm LED, press fit (6.4 if using a plastic LED holder)
THUMB_SCREW_HOLE = 4.5   # M4 clearance
DIN_HOLE = 16.0          # 5-pin DIN panel jack body
DIN_SCREW_HOLE = 3.2     # its two mounting screws, 22 mm apart (check the jack's datasheet)
DC_JACK_HOLE = 8.0       # 5.5 x 2.1 mm panel-mount barrel jack (some need 11 mm)
USB_SCREW_HOLE = 3.2     # panel-mount USB-C pass-through: two screws 18 mm apart plus a cutout
USB_CUTOUT = (10.0, 4.0)
BOARD_HOLE = 3.2         # M3 standoffs for the circuit board, 50 x 40 pattern
FEET_HOLE = 4.5          # rubber feet, M4
BASE_SEAL = "sealed on all faces and edges"
RIB_SCREW_HOLE = 4.5     # screws up through the base into the ribs
RIB_CHAMFER = 3.0        # top back corner of the rib, clears the inside bend radius


class Dxf:
    def __init__(self):
        self.ents = []

    def line(self, x1, y1, x2, y2, layer="CUT"):
        self.ents.append(f"0\nLINE\n8\n{layer}\n10\n{x1:.3f}\n20\n{y1:.3f}\n30\n0\n11\n{x2:.3f}\n21\n{y2:.3f}\n31\n0\n")

    def circle(self, x, y, d, layer="CUT"):
        self.ents.append(f"0\nCIRCLE\n8\n{layer}\n10\n{x:.3f}\n20\n{y:.3f}\n30\n0\n40\n{d / 2:.3f}\n")

    def rect(self, x, y, w, h, layer="CUT"):
        self.poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], layer)

    def poly(self, pts, layer="CUT"):
        for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
            self.line(x1, y1, x2, y2, layer)

    def write(self, path):
        layers = "".join(
            f"0\nLAYER\n2\n{name}\n70\n0\n62\n{color}\n6\nCONTINUOUS\n"
            for name, color in (("CUT", 7), ("BEND", 1), ("PLACEHOLDER", 3)))
        with open(path, "w") as f:
            f.write("0\nSECTION\n2\nHEADER\n9\n$INSUNITS\n70\n4\n0\nENDSEC\n")
            f.write(f"0\nSECTION\n2\nTABLES\n0\nTABLE\n2\nLAYER\n70\n3\n{layers}0\nENDTAB\n0\nENDSEC\n")
            f.write("0\nSECTION\n2\nENTITIES\n" + "".join(self.ents) + "0\nENDSEC\n0\nEOF\n")


# ---- geometry from the drawing (mm) ----
W = G.WIDTH * MM
BACK = G.BACK_H * MM
FACE = G.SLOPE * MM
FLAT_H = BACK + FACE
pts, R, phi, chord = G.arc_points(G.SLOPE)
ribs = G.ribs_for(pts)


def face_xy(x_cm, up_cm):
    """Flat-pattern coordinates of a point on the sloped face given 'from left' and 'up from front'."""
    return x_cm * MM, FLAT_H - up_cm * MM


def chassis():
    d = Dxf()
    d.rect(0, 0, W, FLAT_H)
    d.line(0, BACK, W, BACK, "BEND")
    for x, y in pts:                      # footswitches and LEDs
        up = G.SLOPE - y
        d.circle(*face_xy(x, up), FOOTSWITCH_HOLE)
        d.circle(*face_xy(x, up + G.LED_UP), LED_HOLE)
    sy_up = G.SLOPE - (G.DISP_TOP + G.DISPLAY["disp_h"] / 2)
    for sx in G.SONG_X:                   # song switches
        d.circle(*face_xy(sx, sy_up), FOOTSWITCH_HOLE)
    wx, wy = face_xy(pts[2][0], G.SLOPE - G.DISP_TOP)   # corner nearest the bend; the rect grows toward the front
    d.rect(wx, wy, G.DISPLAY["disp_w"] * MM, G.DISPLAY["disp_h"] * MM)   # display window
    for x, y in G.layout_svg(G.DISPLAY)["anchors"]:                      # thumb screws
        d.circle(*face_xy(x, G.SLOPE - y), THUMB_SCREW_HOLE)
    # Back: jacks on the decided line (G.JACKS, in cm from the left edge; y up from the base top)
    yb = G.JACK_Y * MM
    for label, x, hole in G.JACKS:
        x *= MM
        if "DIN" in label:
            d.circle(x, yb, DIN_HOLE)
            d.circle(x - 11, yb, DIN_SCREW_HOLE)
            d.circle(x + 11, yb, DIN_SCREW_HOLE)
        elif "USB" in label:
            d.rect(x - USB_CUTOUT[0] / 2, yb - USB_CUTOUT[1] / 2, *USB_CUTOUT)
            d.circle(x - 9, yb, USB_SCREW_HOLE)
            d.circle(x + 9, yb, USB_SCREW_HOLE)
        else:
            d.circle(x, yb, DC_JACK_HOLE)
    # Circuit board standoffs inside the back, left bay: placeholder until the board is designed
    bd = G.BOARD
    for sx in (-1, 1):
        for sy in (-1, 1):
            d.circle((bd["cx"] + sx * bd["hole_dx"] / 2) * MM, (bd["cy"] + sy * bd["hole_dy"] / 2) * MM, BOARD_HOLE, "PLACEHOLDER")
    return d


def rib():
    rib_len = (G.DEPTH - G.RAIL_T) * MM
    h_front = BACK - (BACK - G.FRONT_H * MM) * (rib_len / (G.DEPTH * MM))
    drop = (BACK - h_front) / rib_len          # slope as a ratio
    d = Dxf()
    d.poly([(0, 0), (0, BACK - RIB_CHAMFER), (RIB_CHAMFER, BACK - RIB_CHAMFER * drop), (rib_len, h_front), (rib_len, 0)])
    return d, rib_len, h_front


def base():
    D = G.DEPTH * MM
    d = Dxf()
    d.rect(0, 0, W, D)
    for x in (15, W - 15):
        for y in (15, D - 15):
            d.circle(x, y, FEET_HOLE)
    for x0, t in ribs:                     # three screws per rib, on its centre line
        cx = (x0 + t / 2) * MM
        for y in (35, 95, 155):
            d.circle(cx, y, RIB_SCREW_HOLE)
    return d


def svg_of(d, w, h, title):
    out = []
    for e in d.ents:
        f = e.split("\n")
        layer = f[f.index("8") + 1]
        if f[1] == "LINE":
            x1, y1, x2, y2 = (float(f[f.index(k) + 1]) for k in ("10", "20", "11", "21"))
            out.append(f'<line class="{layer}" x1="{x1}" y1="{h - y1}" x2="{x2}" y2="{h - y2}"/>')
        else:
            x, y, r = (float(f[f.index(k) + 1]) for k in ("10", "20", "40"))
            out.append(f'<circle class="{layer}" cx="{x}" cy="{h - y}" r="{r}"/>')
    return (f'<figure><figcaption>{title}</figcaption><svg viewBox="-10 -10 {w + 20} {h + 20}" xmlns="http://www.w3.org/2000/svg" role="img">'
            + "".join(out) + "</svg></figure>")


out_dir = os.path.join(HERE, "dxf")
os.makedirs(out_dir, exist_ok=True)
ch = chassis()
ch.write(os.path.join(out_dir, "chassis.dxf"))
rb, rib_len, h_front = rib()
rb.write(os.path.join(out_dir, "rib.dxf"))
bs = base()
bs.write(os.path.join(out_dir, "base.dxf"))

html = f"""<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Busster Junior Cut Files</title>
<style>
:root {{ --bg: #eef0f2; --paper: #fbfbfa; --ink: #1d242c; --muted: #5b6672; --cut: #1d242c; --bend: #b4543a; --ph: #2e9b5a; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg: #14181d; --paper: #1d2329; --ink: #e4e8ec; --muted: #9aa6b2; --cut: #e4e8ec; --bend: #e0896f; --ph: #4fc47e; color-scheme: dark }} }}
:root[data-theme="dark"] {{ --bg: #14181d; --paper: #1d2329; --ink: #e4e8ec; --muted: #9aa6b2; --cut: #e4e8ec; --bend: #e0896f; --ph: #4fc47e; color-scheme: dark }}
body {{ background: var(--bg); color: var(--ink); font-family: "IBM Plex Sans", "Helvetica Neue", Arial, sans-serif; line-height: 1.5; padding: 24px 16px 48px; }}
main {{ max-width: 1100px; margin: 0 auto; display: grid; gap: 24px; }}
h1 {{ font-size: 1.5rem; margin: 0; }} p {{ max-width: 72ch; margin: 0; color: var(--muted); }}
figure {{ margin: 0; background: var(--paper); border-radius: 6px; padding: 16px; }}
figcaption {{ font-size: .9rem; color: var(--muted); margin-bottom: 8px; }}
svg {{ width: 100%; height: auto; display: block; }}
line, circle {{ fill: none; stroke-width: 1.2; vector-effect: non-scaling-stroke; }}
.CUT {{ stroke: var(--cut); }} .BEND {{ stroke: var(--bend); stroke-dasharray: 8 6; }} .PLACEHOLDER {{ stroke: var(--ph); stroke-dasharray: 3 3; }}
.legend span {{ margin-right: 18px; }} .legend i {{ display: inline-block; width: 22px; border-top: 2px solid; vertical-align: middle; margin-right: 6px; }}
</style>
<main>
<div><h1>Busster Junior Cut Files</h1>
<p>What the three DXF files contain, rendered from the files themselves. Millimetres. Black is a through cut, the dashed orange line is the bend (not a cut), green dashed holes are placeholders for the circuit board standoffs, to be confirmed once the board is designed.</p>
<p class="legend"><span><i style="border-color: var(--cut)"></i>CUT</span><span><i style="border-color: var(--bend); border-top-style: dashed"></i>BEND</span><span><i style="border-color: var(--ph); border-top-style: dashed"></i>PLACEHOLDER</span></p></div>
{svg_of(ch, W, FLAT_H, f"chassis.dxf: flat pattern {W:.0f} x {FLAT_H:.1f} mm, 1.5 or 2 mm 5052 aluminium, one bend of {G.BEND_DEG:.1f} degrees along the dashed line (back below it, sloped face above it, bent so the back goes down). Quantity 1.")}
{svg_of(rb, rib_len, BACK, f"rib.dxf: {rib_len:.0f} x {BACK:.0f} mm wedge, {h_front:.1f} mm high at the front, 3 mm chamfer at the top back corner. 1/2 inch Baltic birch, quantity 8: three glued up for each outer rib, one for each inner rib.")}
{svg_of(bs, W, G.DEPTH * MM, f"base.dxf: {W:.0f} x {G.DEPTH * MM:.0f} mm, 1/2 inch Baltic birch, quantity 1, {BASE_SEAL}. Four feet holes in the corners and three screw holes on each rib centre line.")}
</main>
"""
with open(os.path.join(out_dir, "preview.html"), "w") as f:
    f.write(html)
print(f"chassis {W:.0f} x {FLAT_H:.1f} mm, {len(ch.ents)} entities; rib {rib_len:.0f} x {BACK:.0f} ({h_front:.1f} front), {len(rb.ents)}; base {len(bs.ents)}")
