"""Regenerate the art for the Cafés de Colombia 2026 post.

    /usr/bin/python3 blog-src/features/feria-cafes-colombia-2026/generate-art.py

Needs Pillow and numpy. Reads geo.json (Colombia/Venezuela borders and rivers extracted from
Natural Earth, public domain) and writes:
  - assets/blog/feria-cafes-colombia-2026/relief-800.webp / relief-1600.webp   shaded relief base map
  - blog-src/features/feria-cafes-colombia-2026/hero-map.svg   overlay: route, plane, labels, coffee farms
  - blog-src/features/feria-cafes-colombia-2026/map.svg        small Colombia map for the regions widget
"""
import json, math, pathlib, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = pathlib.Path(__file__).parent
ROOT = HERE.parents[2]
ASSETS = ROOT / "assets/blog/feria-cafes-colombia-2026"
GEO = json.loads((HERE / "geo.json").read_text())
random.seed(11); rng = np.random.default_rng(11)

def f(v): return f"{v:.1f}".rstrip("0").rstrip(".")

# ---------------- hero map frame ----------------
W, H = 800, 1000                       # viewBox, portrait 4:5
LAT0, LAT1 = 3.4, 8.6
LON0, LON1 = -75.37, -71.21
def P(lon, lat): return ((lon - LON0) / (LON1 - LON0) * W, (LAT1 - lat) / (LAT1 - LAT0) * H)

# ---------------- relief raster ----------------
S = 2
RW, RH = W * S, H * S
xs = np.linspace(LON0, LON1, RW); ys = np.linspace(LAT1, LAT0, RH)
LON, LAT = np.meshgrid(xs, ys)

def dist_to_polyline(pts):
    d = np.full(LON.shape, 1e9)
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        dx, dy = x2 - x1, y2 - y1
        t = np.clip(((LON - x1) * dx + (LAT - y1) * dy) / (dx * dx + dy * dy), 0, 1)
        d = np.minimum(d, np.hypot(LON - (x1 + t * dx), LAT - (y1 + t * dy)))
    return d

ranges = [  # (axis, peak, half-width in degrees)
    ([(-74.7, 3.2), (-74.25, 4.1), (-73.95, 4.8), (-73.5, 5.45), (-73.0, 6.0), (-72.45, 6.55), (-72.5, 7.15), (-72.75, 7.7), (-72.95, 8.35), (-72.9, 9.0)], 0.92, 0.40),
    ([(-72.55, 7.55), (-72.0, 7.95), (-71.5, 8.35), (-70.9, 8.75)], 0.85, 0.30),                     # Andes de Mérida
    ([(-75.75, 3.2), (-75.5, 4.4), (-75.4, 5.3), (-75.35, 6.2), (-75.55, 7.2)], 0.95, 0.36),           # Cordillera Central
    ([(-74.25, 7.4), (-74.05, 8.2)], 0.45, 0.22),                                                      # Serranía de San Lucas
]
# smooth union of the ranges (a hard max leaves a visible crease where two ranges meet)
K = 14.0
elev = np.log(sum(np.exp(K * peak * np.exp(-(dist_to_polyline(pts) / w) ** 2)) for pts, peak, w in ranges)) / K
elev = np.clip(elev - math.log(len(ranges)) / K, 0, None)
for lon, lat, amp, r in [(-72.33, 6.45, 0.32, 0.16), (-74.2, 3.95, 0.12, 0.2), (-73.0, 7.2, 0.08, 0.25)]:
    elev += amp * np.exp(-((LON - lon) ** 2 + (LAT - lat) ** 2) / r ** 2)

def fractal(octaves=8, base=5, persistence=0.58):
    out = np.zeros((RH, RW), dtype=np.float32)
    for o in range(octaves):
        n = base * 2 ** o
        g = rng.random((int(n * 1.25) + 2, n + 2)).astype(np.float32)
        img = Image.fromarray((g * 255).astype(np.uint8)).resize((RW, RH), Image.BICUBIC)
        out += (np.asarray(img, dtype=np.float32) / 255 - 0.5) * persistence ** o
    return out
noise = fractal()
ridged = 1 - np.abs(fractal(octaves=7, base=9, persistence=0.55)) * 2.2   # sharp crests and valleys
elev = elev + noise * (0.04 + 0.30 * elev) + (ridged - 0.5) * 0.42 * elev ** 1.2
elev = np.clip(elev, 0, 1.35)

gy, gx = np.gradient(elev * 70)
az, alt = math.radians(315), math.radians(42)
slope = np.arctan(np.hypot(gx, gy)); aspect = np.arctan2(-gx, gy)
shade = np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect)
shade = np.clip(0.55 + 0.75 * (shade - 0.45), 0.45, 1.25)

stops = [(0.0, (182, 214, 150)), (0.18, (160, 202, 128)), (0.42, (122, 176, 100)), (0.66, (96, 148, 82)),
         (0.88, (112, 136, 88)), (1.08, (150, 148, 118)), (1.2, (196, 190, 170)), (1.3, (246, 245, 240))]
ks = [s[0] for s in stops]
rgb = np.stack([np.interp(elev, ks, [s[1][c] for s in stops]) for c in range(3)], -1)
llanos = np.clip((LON + 73.3) / 0.6, 0, 1) * np.clip((6.9 - LAT) / 0.8, 0, 1) * np.clip(1 - elev / 0.35, 0, 1)
rgb = rgb * (1 - llanos[..., None] * 0.55) + np.array([205, 214, 150]) * llanos[..., None] * 0.55
rgb = np.clip(rgb * shade[..., None], 0, 255)

def poly_mask(name):
    m = Image.new("L", (RW, RH), 0); d = ImageDraw.Draw(m)
    for ring in GEO[name]:
        d.polygon([(P(x, y)[0] * S, P(x, y)[1] * S) for x, y in ring], fill=255)
    return np.asarray(m.filter(ImageFilter.GaussianBlur(1.2)), dtype=np.float32)[..., None] / 255
ven = poly_mask("VEN")
grey = rgb.mean(-1, keepdims=True)
neighbour = (rgb * 0.35 + grey * 0.65) * 0.55 + np.array([233, 235, 226]) * 0.45
rgb = rgb * (1 - ven) + neighbour * ven

base = Image.fromarray(rgb.astype(np.uint8))
base.save(ASSETS / "relief-1600.webp", "WEBP", quality=74, method=6)
base.resize((W, H), Image.LANCZOS).save(ASSETS / "relief-800.webp", "WEBP", quality=76, method=6)

# ---------------- overlay SVG ----------------
def path_of(coords):
    pts = [P(x, y) for x, y in coords]
    return "M" + " L".join(f"{f(x)},{f(y)}" for x, y in pts)

rivers = "".join(f'<path d="{path_of(line)}"/>' for line in GEO["rivers"])
border = "".join(f'<path d="{path_of(ring)}"/>' for ring in GEO["VEN"])

CITIES = {"Cúcuta": (-72.5078, 7.8939), "Bogotá": (-74.0721, 4.7110), "Pamplona": (-72.648, 7.3754),
          "Bucaramanga": (-73.1227, 7.1193), "Tunja": (-73.3678, 5.5353), "Ragonvalia": (-72.4767, 7.5775)}
cx, cy = P(*CITIES["Cúcuta"]); bx, by = P(*CITIES["Bogotá"])
rx, ry = P(*CITIES["Ragonvalia"])
origin_label = (f'<g class="town origin"><circle cx="{f(rx)}" cy="{f(ry)}" r="4.5"/>'
                f'<text x="{f(rx + 10)}" y="{f(ry + 5)}" font-size="15">Ragonvalia</text></g>')
route = f"M{f(cx)},{f(cy)} C{f(cx - 40)},{f(cy + 260)} {f(bx + 170)},{f(by - 300)} {f(bx)},{f(by)}"

def town(name, anchor="start", dx=9, dy=4, size=17):
    x, y = P(*CITIES[name])
    tx = x + (dx if anchor == "start" else -dx)
    return (f'<g class="town"><circle cx="{f(x)}" cy="{f(y)}" r="4.5"/>'
            f'<text x="{f(tx)}" y="{f(y + dy)}" text-anchor="{anchor}" font-size="{size}">{name}</text></g>')

def pin(name, code, side):
    x, y = P(*CITIES[name])
    lx = x + (18 if side == "right" else -18); anchor = "start" if side == "right" else "end"
    rect_x = lx - (0 if side == "right" else 132)
    return (f'<g class="pin"><ellipse cx="{f(x)}" cy="{f(y + 2)}" rx="10" ry="4" fill="#000" opacity=".25"/>'
            f'<path transform="translate({f(x)} {f(y)})" d="M0 0 C-11 -13 -13 -20 -13 -26 A13 13 0 1 1 13 -26 C13 -20 11 -13 0 0Z" fill="#D7261E" stroke="#fff" stroke-width="2.5"/>'
            f'<circle cx="{f(x)}" cy="{f(y - 26)}" r="4.6" fill="#fff"/></g>'
            f'<g class="pin-label"><rect x="{f(rect_x)}" y="{f(y - 48)}" width="132" height="36" rx="18" fill="rgba(0,16,46,.88)"/>'
            f'<text x="{f(rect_x + 66)}" y="{f(y - 24)}" text-anchor="middle" font-size="17" font-weight="600" fill="#fff">{name} <tspan fill="#F4B544">{code}</tspan></text></g>')

PLANE = ("M30 0 C30 -2 28 -3.2 24 -3.2 L12 -3.2 L-2 -22 L-8 -22 L2 -3.2 L-18 -3.2 L-25 -10 L-29 -10 L-25 -3 "
         "L-27 0 L-25 3 L-29 10 L-25 10 L-18 3.2 L2 3.2 L-8 22 L-2 22 L12 3.2 L24 3.2 C28 3.2 30 2 30 0Z")

# coffee farm strip
FY = 862
def hill(px, py, half, depth, x): t = (x - px) / half; return py + min(1.0, t * t) * depth
hills = [dict(px=170, py=FY, half=300, depth=150), dict(px=620, py=FY + 8, half=320, depth=150)]
def strip_y(x): return min(hill(h["px"], h["py"], h["half"], h["depth"], x) for h in hills)
strip_d = "M-10,1010 " + " ".join(f"L{x},{f(strip_y(x))}" for x in range(-10, 821, 20)) + " L810,1010 Z"
bushes = []
for h in hills:
    for r in range(4):
        x = h["px"] - h["half"] * 0.95; s = 0.42 + r * 0.1
        while x < h["px"] + h["half"] * 0.95:
            y = hill(h["px"], h["py"], h["half"], h["depth"], x) + 20 + r * 24
            if y < 1000 and strip_y(x) + 12 < y:
                bushes.append((x + random.uniform(-4, 4), y, s))
            x += 30 * s
bushes.sort(key=lambda b: b[1])
front = [(30, 1012, 1.5), (175, 1016, 1.25), (640, 1016, 1.3), (785, 1012, 1.55)]
def bush(x, y, s, sway=False):
    if sway:
        return f'<g transform="translate({f(x)} {f(y)}) scale({f(s)})"><use href="#bush" class="sway"/></g>'
    return f'<use href="#bush" transform="translate({f(x)} {f(y)}) scale({f(s)})"/>'
house = ('<g transform="translate(395 892)"><rect x="-34" y="-30" width="68" height="34" fill="#FBF6EC" stroke="#8C6A4A" stroke-width="2"/>'
         '<path d="M-42 -28 L0 -56 L42 -28 Z" fill="#B5442B" stroke="#7C2E1D" stroke-width="2"/>'
         '<rect x="-8" y="-16" width="16" height="20" fill="#7C4A2A"/><rect x="-26" y="-20" width="11" height="10" fill="#7FB6D9"/>'
         '<rect x="15" y="-20" width="11" height="10" fill="#7FB6D9"/></g>')

svg = f'''<svg class="fx-map-overlay" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">
  <defs>
    <symbol id="bush" overflow="visible">
      <ellipse cx="0" cy="2" rx="24" ry="5" fill="#1D3A1E" opacity=".35"/>
      <rect x="-2" y="-14" width="4" height="16" rx="2" fill="#5B3A22"/>
      <circle cx="-15" cy="-22" r="15" fill="#2C6332"/><circle cx="15" cy="-22" r="15" fill="#2C6332"/>
      <circle cx="0" cy="-34" r="18" fill="#357A3B"/><circle cx="-9" cy="-46" r="12" fill="#3F8A44"/><circle cx="10" cy="-45" r="11" fill="#3F8A44"/>
      <circle cx="-14" cy="-26" r="3.4" fill="#C8302A"/><circle cx="-6" cy="-19" r="3" fill="#E04B3A"/><circle cx="7" cy="-28" r="3.4" fill="#C8302A"/>
      <circle cx="16" cy="-19" r="3" fill="#E04B3A"/><circle cx="2" cy="-41" r="3" fill="#C8302A"/><circle cx="-4" cy="-31" r="2.6" fill="#F0B13B"/>
    </symbol>
    <linearGradient id="fxFarmSky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".55" stop-color="#F6EFD9" stop-opacity=".85"/><stop offset="1" stop-color="#F6EFD9"/></linearGradient>
    <linearGradient id="fxFarmHill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5E9650"/><stop offset="1" stop-color="#2F5A2E"/></linearGradient>
    <path id="fxRoute" d="{route}"/>
    <mask id="fxTrail" maskUnits="userSpaceOnUse">
      <use href="#fxRoute" fill="none" stroke="#fff" stroke-width="16" stroke-linecap="round" pathLength="100" stroke-dasharray="100" stroke-dashoffset="100">
        <animate attributeName="stroke-dashoffset" values="100;100;0;0;0" keyTimes="0;.08;.76;.94;1" dur="10s" repeatCount="indefinite"/>
      </use>
    </mask>
  </defs>
  <g class="rivers">{rivers}</g>
  <g class="border">{border}</g>
  <text class="region-label" x="{f(P(-71.95, 7.05)[0])}" y="{f(P(-71.95, 7.05)[1])}" text-anchor="middle">VENEZUELA</text>
  <text class="range-label" transform="translate({f(P(-73.55, 5.95)[0])} {f(P(-73.55, 5.95)[1])}) rotate(-52)" text-anchor="middle">Cordillera Oriental</text>
  {town("Pamplona", "start")}{town("Bucaramanga", "end", dx=10)}{town("Tunja", "start")}
  {origin_label}
  <use href="#fxRoute" class="trail-ghost"/>
  <use href="#fxRoute" class="trail" mask="url(#fxTrail)"/>
  <g class="fx-plane" opacity="0">
    <g class="plane-body">
      <path d="{PLANE}" transform="translate(6 10)" fill="#00102E" opacity=".22"/>
      <path d="{PLANE}" fill="#fff" stroke="#00102E" stroke-width="2" stroke-linejoin="round"/>
      <path d="M-25 -3 L-27 0 L-25 3 M14 -3 L14 3" stroke="#D7261E" stroke-width="2" fill="none"/>
      <animateTransform attributeName="transform" type="scale" values="1.25;1.25;1.7;1.7;1.25;1.25" keyTimes="0;.08;.24;.6;.76;1" dur="10s" repeatCount="indefinite"/>
    </g>
    <animateMotion id="fxLoop" dur="10s" repeatCount="indefinite" rotate="auto" keyPoints="0;0;1;1;1" keyTimes="0;.08;.76;.94;1" calcMode="linear"><mpath href="#fxRoute"/></animateMotion>
    <animate attributeName="opacity" values="0;1;1;1;0;0" keyTimes="0;.05;.76;.86;.93;1" dur="10s" repeatCount="indefinite"/>
  </g>
  {pin("Cúcuta", "CUC", "right")}
  {pin("Bogotá", "BOG", "right")}
  <g class="farms">
    <rect x="0" y="{FY - 120}" width="{W}" height="{H - FY + 120}" fill="url(#fxFarmSky)"/>
    <path d="{strip_d}" fill="url(#fxFarmHill)"/>
    {"".join(bush(x, y, s) for x, y, s in bushes)}
    {house}
    <g class="fx-front">{"".join(bush(x, y, s, True) for x, y, s in front)}</g>
  </g>
</svg>'''
(HERE / "hero-map.svg").write_text(svg, encoding="utf-8")

# ---------------- regions map (whole country) ----------------
ring = max(GEO["COL"], key=len)
lons = [p[0] for p in ring]; lats = [p[1] for p in ring]
kx = math.cos(math.radians(sum(lats) / len(lats)))
minx, maxx, miny, maxy = min(lons) * kx, max(lons) * kx, min(lats), max(lats)
MW = 520; sc = MW / (maxx - minx); MH = (maxy - miny) * sc; pad = 20
def Q(lon, lat): return (pad + (lon * kx - minx) * sc, pad + (maxy - lat) * sc)
outline = "M" + " L".join(f"{f(x)},{f(y)}" for x, y in (Q(*p) for p in ring)) + " Z"
places = {"nds": (-72.90, 8.05), "antioquia": (-75.75, 6.35), "caldas": (-75.45, 5.12), "risaralda": (-75.95, 4.95),
          "bogota": (-74.07, 4.71), "huila": (-75.75, 2.35)}
pts = {k: Q(*v) for k, v in places.items()}
(mx1, my1), (mx2, my2) = pts["nds"], pts["bogota"]
dots = "".join(f'<g class="map-dot" data-region="{k}" transform="translate({f(x)} {f(y)})"><circle class="halo" r="16"/><circle class="core" r="7"/></g>'
               for k, (x, y) in pts.items())
(HERE / "map.svg").write_text(f'''<svg class="fx-map-svg" viewBox="0 0 {f(MW + pad * 2)} {f(MH + pad * 2)}" aria-hidden="true" focusable="false">
  <path d="{outline}" class="map-land"/>
  <path d="M{f(mx1)},{f(my1)} Q{f((mx1 + mx2) / 2 + 40)},{f((my1 + my2) / 2 - 10)} {f(mx2)},{f(my2)}" class="map-route"/>
  {dots}
</svg>''', encoding="utf-8")
print("relief:", (ASSETS / "relief-800.webp").stat().st_size // 1024, "KB /", (ASSETS / "relief-1600.webp").stat().st_size // 1024,
      "KB | overlay:", len(svg) // 1024, "KB | bushes:", len(bushes))
