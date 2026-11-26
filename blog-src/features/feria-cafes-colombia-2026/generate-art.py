# Regenerate banner.svg and map.svg:  /usr/bin/python3 blog-src/features/feria-cafes-colombia-2026/generate-art.py blog-src/features/feria-cafes-colombia-2026 blog-src/features/feria-cafes-colombia-2026/colombia.geo.json
"""Generates the banner (flight CUC -> BOG over coffee mountains) and the Colombia map SVG fragments."""
import json, math, pathlib, random, sys

out_dir = pathlib.Path(sys.argv[1]); out_dir.mkdir(parents=True, exist_ok=True)
geo = json.load(open(sys.argv[2]))
random.seed(7)
W, H = 1600, 640

def f(v): return f"{v:.1f}".rstrip("0").rstrip(".")

# ---------- terrain helpers ----------
def ridge(points, base=H + 2):
    """Smooth closed silhouette through (x, y) peaks using quadratic midpoints."""
    d = f"M{f(points[0][0])},{f(base)} L{f(points[0][0])},{f(points[0][1])}"
    for i in range(1, len(points)):
        x0, y0 = points[i - 1]; x1, y1 = points[i]
        d += f" Q{f(x0)},{f(y0)} {f((x0 + x1) / 2)},{f((y0 + y1) / 2)}"
    d += f" T{f(points[-1][0])},{f(points[-1][1])} L{f(points[-1][0])},{f(base)} Z"
    return d

def hill_y(x, px, py, half, depth):
    t = (x - px) / half
    return py + min(1.0, t * t) * depth

far = [(-40, 330), (120, 270), (260, 320), (420, 240), (560, 300), (720, 215), (880, 285),
       (1040, 225), (1190, 290), (1340, 230), (1480, 300), (1640, 250)]
mid = [(-40, 420), (140, 360), (300, 410), (470, 345), (640, 420), (800, 380), (960, 430),
       (1130, 360), (1290, 405), (1450, 350), (1640, 410)]

# near hills: two big coffee slopes + valley
HILLS = [dict(px=330, py=420, half=470, depth=330), dict(px=1260, py=430, half=470, depth=320)]
def near_y(x):
    return min(hill_y(x, **h) for h in HILLS)
near_pts = [(x, near_y(x)) for x in range(-40, 1661, 40)]
near_d = "M-40,642 " + " ".join(f"L{x},{f(y)}" for x, y in near_pts) + " L1660,642 Z"

# ---------- coffee bushes along contour rows ----------
def rows_for(h, rows, spacing, scale0, scale_step, x_jitter=6):
    uses = []
    for r in range(rows):
        dy = 26 + r * 30
        s = scale0 + r * scale_step
        x = h["px"] - h["half"] * 0.95
        while x < h["px"] + h["half"] * 0.95:
            y = hill_y(x, **h) + dy
            if y < H - 8 and near_y(x) + 14 < y:
                uses.append((x + random.uniform(-x_jitter, x_jitter), y, s))
            x += spacing * s
    return uses

bushes = []
for h in HILLS:
    bushes += rows_for(h, rows=7, spacing=34, scale0=0.55, scale_step=0.12)
bushes.sort(key=lambda b: b[1])
# exaggerated foreground bushes (these sway)
front = [(70, 640, 2.6), (250, 650, 2.2), (1350, 650, 2.3), (1540, 640, 2.7), (760, 668, 1.8), (930, 672, 1.7)]

def use(x, y, s, cls=""):
    if cls:  # animated: keep placement on a wrapper so the CSS transform only rotates
        return f'<g transform="translate({f(x)} {f(y)}) scale({f(s)})"><use href="#bush" class="{cls}"/></g>'
    return f'<use href="#bush" transform="translate({f(x)} {f(y)}) scale({f(s)})"/>'

# ---------- route ----------
CUC, BOG = (520, 318), (1090, 352)
route_d = f"M{CUC[0]},{CUC[1]} C 640,130 960,120 {BOG[0]},{BOG[1]}"

def pin(x, y, label, code, anchor):
    return f'''<g class="pin" transform="translate({x} {y})">
      <ellipse cx="0" cy="2" rx="11" ry="4" fill="#000" opacity=".18"/>
      <path d="M0 0 C-12 -14 -14 -22 -14 -28 A14 14 0 1 1 14 -28 C14 -22 12 -14 0 0Z" fill="#C8941A" stroke="#fff" stroke-width="2.5"/>
      <circle cx="0" cy="-28" r="5" fill="#fff"/>
    </g>
    <g class="pin-label" transform="translate({x} {y - 62})">
      <rect x="-75" y="-20" width="150" height="38" rx="19" fill="rgba(0,16,46,.85)"/>
      <text x="0" y="5" text-anchor="middle" font-family="Jost, system-ui, sans-serif" font-size="17" font-weight="600" fill="#fff" letter-spacing=".5">{label} <tspan fill="#F4B544">{code}</tspan></text>
    </g>'''

clouds = [(80, 110, 1.0), (420, 70, .75), (760, 150, .9), (1100, 80, 1.15), (1420, 140, .8)]
def cloud(x, y, s):
    return (f'<g transform="translate({x} {y}) scale({s})" opacity=".95">'
            '<ellipse cx="0" cy="0" rx="70" ry="24" fill="#fff"/><ellipse cx="-30" cy="-14" rx="34" ry="26" fill="#fff"/>'
            '<ellipse cx="22" cy="-20" rx="40" ry="32" fill="#fff"/><ellipse cx="55" cy="-4" rx="30" ry="20" fill="#fff"/></g>')
cloud_set = "".join(cloud(*c) for c in clouds)

banner = f'''<svg class="fx-banner-svg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMax slice" aria-hidden="true" focusable="false">
  <defs>
    <linearGradient id="fxSky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#BFE0EE"/><stop offset=".55" stop-color="#E9EFE3"/><stop offset="1" stop-color="#F6E3BE"/>
    </linearGradient>
    <radialGradient id="fxSun" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#FFF6D8"/><stop offset=".45" stop-color="#FCE3A1" stop-opacity=".85"/><stop offset="1" stop-color="#FCE3A1" stop-opacity="0"/></radialGradient>
    <linearGradient id="fxFar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#9DB9B0"/><stop offset="1" stop-color="#B9CDBF"/></linearGradient>
    <linearGradient id="fxMid" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#6F9B6A"/><stop offset="1" stop-color="#86AA77"/></linearGradient>
    <linearGradient id="fxNear" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4E8346"/><stop offset="1" stop-color="#2F5A2E"/></linearGradient>
    <symbol id="bush" overflow="visible">
      <ellipse cx="0" cy="2" rx="24" ry="5" fill="#1D3A1E" opacity=".35"/>
      <rect x="-2" y="-14" width="4" height="16" rx="2" fill="#5B3A22"/>
      <circle cx="-15" cy="-22" r="15" fill="#2C6332"/><circle cx="15" cy="-22" r="15" fill="#2C6332"/>
      <circle cx="0" cy="-34" r="18" fill="#357A3B"/><circle cx="-9" cy="-46" r="12" fill="#3F8A44"/><circle cx="10" cy="-45" r="11" fill="#3F8A44"/>
      <circle cx="-14" cy="-26" r="3.4" fill="#C8302A"/><circle cx="-6" cy="-19" r="3" fill="#E04B3A"/><circle cx="7" cy="-28" r="3.4" fill="#C8302A"/>
      <circle cx="16" cy="-19" r="3" fill="#E04B3A"/><circle cx="2" cy="-41" r="3" fill="#C8302A"/><circle cx="-4" cy="-31" r="2.6" fill="#F0B13B"/>
    </symbol>
    <path id="fxRoute" d="{route_d}"/>
    <mask id="fxRouteMask" maskUnits="userSpaceOnUse">
      <use href="#fxRoute" fill="none" stroke="#fff" stroke-width="14" stroke-linecap="round" pathLength="100" stroke-dasharray="100" stroke-dashoffset="100">
        <animate attributeName="stroke-dashoffset" values="100;100;0;0;0" keyTimes="0;.1;.78;.92;1" dur="12s" repeatCount="indefinite"/>
      </use>
    </mask>
  </defs>
  <rect width="{W}" height="{H}" fill="url(#fxSky)"/>
  <circle cx="1270" cy="150" r="150" fill="url(#fxSun)"/><circle cx="1270" cy="150" r="48" fill="#FFF3CF"/>
  <g class="fx-clouds"><g>{cloud_set}</g><g transform="translate({W} 0)">{cloud_set}</g></g>
  <path class="fx-layer fx-far" d="{ridge(far)}" fill="url(#fxFar)"/>
  <path class="fx-layer fx-mid" d="{ridge(mid)}" fill="url(#fxMid)"/>
  <g class="fx-layer fx-near">
    <path d="{near_d}" fill="url(#fxNear)"/>
    {"".join(use(x, y, s) for x, y, s in bushes)}
  </g>
  <use href="#fxRoute" fill="none" stroke="#fff" stroke-width="3" stroke-dasharray="2 12" stroke-linecap="round" opacity=".55"/>
  <use href="#fxRoute" fill="none" stroke="#fff" stroke-width="4.5" stroke-dasharray="2 12" stroke-linecap="round" mask="url(#fxRouteMask)"/>
  <g class="fx-plane" opacity="0">
    <g transform="scale(1.15)">
      <path d="M-24 0 L-14 -3 L-4 -3 L6 -20 L13 -20 L8 -3 L22 -3 C28 -3 30 0 30 0 C30 0 28 3 22 3 L8 3 L13 20 L6 20 L-4 3 L-14 3 Z" fill="#fff" stroke="#00102E" stroke-width="2" stroke-linejoin="round"/>
      <path d="M-24 0 L-30 -9 L-25 -9 L-17 -2 Z M-24 0 L-30 9 L-25 9 L-17 2 Z" fill="#C8941A" stroke="#00102E" stroke-width="1.5" stroke-linejoin="round"/>
    </g>
    <animateMotion dur="12s" repeatCount="indefinite" rotate="auto" keyPoints="0;0;1;1;1" keyTimes="0;.1;.78;.92;1" calcMode="linear"><mpath href="#fxRoute"/></animateMotion>
    <animate attributeName="opacity" values="0;1;1;1;0;0" keyTimes="0;.06;.78;.88;.94;1" dur="12s" repeatCount="indefinite"/>
  </g>
  {pin(*CUC, "Cúcuta", "CUC", "end")}
  {pin(*BOG, "Bogotá", "BOG", "start")}
  <g class="fx-front">{"".join(use(x, y, s, "sway") for x, y, s in front)}</g>
</svg>'''

# ---------- map ----------
ring = geo["features"][0]["geometry"]["coordinates"][0]
lons = [p[0] for p in ring]; lats = [p[1] for p in ring]
lat0 = sum(lats) / len(lats); kx = math.cos(math.radians(lat0))
minx, maxx = min(lons) * kx, max(lons) * kx; miny, maxy = min(lats), max(lats)
MW = 520; scale = MW / (maxx - minx); MH = (maxy - miny) * scale
pad = 20
def proj(lon, lat): return (pad + (lon * kx - minx) * scale, pad + (maxy - lat) * scale)
outline = "M" + " L".join(f"{f(x)},{f(y)}" for x, y in (proj(*p) for p in ring)) + " Z"
places = {"nds": (-72.90, 8.05), "antioquia": (-75.75, 6.35), "caldas": (-75.45, 5.12), "risaralda": (-75.95, 4.95), "bogota": (-74.07, 4.71)}
pts = {k: proj(*v) for k, v in places.items()}
mx1, my1 = pts["nds"]; mx2, my2 = pts["bogota"]
cx, cy = (mx1 + mx2) / 2 + 40, (my1 + my2) / 2 - 10
dots = "".join(
    f'<g class="map-dot" data-region="{k}" transform="translate({f(x)} {f(y)})"><circle class="halo" r="16"/><circle class="core" r="7"/></g>'
    for k, (x, y) in pts.items())
mapsvg = f'''<svg class="fx-map-svg" viewBox="0 0 {f(MW + pad * 2)} {f(MH + pad * 2)}" aria-hidden="true" focusable="false">
  <path d="{outline}" class="map-land"/>
  <path d="M{f(mx1)},{f(my1)} Q{f(cx)},{f(cy)} {f(mx2)},{f(my2)}" class="map-route"/>
  {dots}
</svg>'''

(out_dir / "banner.svg").write_text(banner, encoding="utf-8")
(out_dir / "map.svg").write_text(mapsvg, encoding="utf-8")
print("bushes:", len(bushes), "front:", len(front), "| banner KB:", len(banner) // 1024, "| map KB:", len(mapsvg) // 1024)
print({k: (round(x), round(y)) for k, (x, y) in pts.items()}, "map size", round(MW + 2 * pad), round(MH + 2 * pad))
