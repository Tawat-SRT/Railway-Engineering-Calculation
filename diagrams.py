"""Inline SVG engineering illustrations for the railway calculator.

Every function returns a self-contained SVG string (transparent background)
that can be dropped straight into ``st.markdown(..., unsafe_allow_html=True)``.
The drawings are deliberately styled as technical cross-sections and plans —
dimension lines, soil hatching, ballast stipple — so they read like the shop
drawings a permanent-way engineer already works from.
"""

from __future__ import annotations

# --- shared palette -------------------------------------------------------
NAVY = "#0B2341"
MAROON = "#7A0019"
INK = "#182333"
STEEL = "#2B3445"
DIM = "#7A8699"
DIMTX = "#3A4658"
WATER = "#2F6FB0"
WATERFILL = "#CFE2F2"
RAILBG = "#FBFAF7"

FONT = "'Noto Sans Thai','Segoe UI',sans-serif"
MONO = "'Roboto Mono','Consolas',monospace"


def _defs(uid: str) -> str:
    """Reusable arrow markers + hatch/stipple patterns, namespaced by uid."""
    return f"""
  <defs>
    <marker id="arr{uid}" markerWidth="9" markerHeight="9" refX="7.5" refY="3"
            orient="auto" markerUnits="strokeWidth">
      <path d="M0,0 L8,3 L0,6 Z" fill="{DIM}"/>
    </marker>
    <marker id="force{uid}" markerWidth="11" markerHeight="11" refX="8" refY="3.4"
            orient="auto" markerUnits="strokeWidth">
      <path d="M0,0 L9,3.4 L0,6.8 Z" fill="{MAROON}"/>
    </marker>
    <pattern id="soil{uid}" width="11" height="11" patternUnits="userSpaceOnUse"
             patternTransform="rotate(45)">
      <rect width="11" height="11" fill="#EFE7D6"/>
      <line x1="0" y1="0" x2="0" y2="11" stroke="#B79B6B" stroke-width="1"/>
    </pattern>
    <pattern id="rock{uid}" width="14" height="14" patternUnits="userSpaceOnUse">
      <rect width="14" height="14" fill="#E4E1DA"/>
      <circle cx="3" cy="3" r="1.5" fill="#9AA0A6"/>
      <circle cx="10" cy="6" r="1.7" fill="#8A9096"/>
      <circle cx="6" cy="11" r="1.4" fill="#A7ADB3"/>
    </pattern>
    <linearGradient id="sky{uid}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#16335A"/>
      <stop offset="1" stop-color="#0B2341"/>
    </linearGradient>
  </defs>"""


def _dim_h(x1: float, x2: float, y: float, label: str, uid: str, above: bool = False) -> str:
    """Horizontal dimension line with end ticks and centred label."""
    tx = (x1 + x2) / 2
    ty = y - 6 if above else y + 14
    return f"""
  <g stroke="{DIM}" stroke-width="1">
    <line x1="{x1}" y1="{y-5}" x2="{x1}" y2="{y+5}"/>
    <line x1="{x2}" y1="{y-5}" x2="{x2}" y2="{y+5}"/>
    <line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" marker-start="url(#arr{uid})" marker-end="url(#arr{uid})"/>
  </g>
  <text x="{tx}" y="{ty}" font-family="{MONO}" font-size="12.5" fill="{DIMTX}" text-anchor="middle">{label}</text>"""


def _dim_v(y1: float, y2: float, x: float, label: str, uid: str, left: bool = True) -> str:
    """Vertical dimension line with end ticks and rotated label."""
    ty = (y1 + y2) / 2
    tx = x - 8 if left else x + 8
    anchor = "end" if left else "start"
    return f"""
  <g stroke="{DIM}" stroke-width="1">
    <line x1="{x-5}" y1="{y1}" x2="{x+5}" y2="{y1}"/>
    <line x1="{x-5}" y1="{y2}" x2="{x+5}" y2="{y2}"/>
    <line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" marker-start="url(#arr{uid})" marker-end="url(#arr{uid})"/>
  </g>
  <text x="{tx}" y="{ty}" font-family="{MONO}" font-size="12.5" fill="{DIMTX}" text-anchor="{anchor}" dominant-baseline="middle">{label}</text>"""


def _frame(uid: str, body: str, vb: str = "0 0 720 360", h: int = 360) -> str:
    return (
        f'<svg viewBox="{vb}" width="100%" style="max-width:760px;height:auto;display:block;'
        f'margin:.2rem auto 0;font-family:{FONT}" xmlns="http://www.w3.org/2000/svg" role="img">'
        + _defs(uid)
        + body
        + "</svg>"
    )


from math import atan, atan2, cos, degrees, radians, sin, tan


def cant_diagram(ca_mm: float = 75.0, w_mm: float = 1070.0, defic_mm: float | None = None) -> str:
    """Railway super-elevation cross-section, viewed along the track."""
    uid = "cant"
    tilt = radians(12)
    cx, cy = 378, 212
    half = 162
    wh = 100
    dxc, dyc = half * cos(tilt), half * sin(tilt)
    Ax, Ay = cx - dxc, cy + dyc
    Bx, By = cx + dxc, cy - dyc
    Lx, Ly = cx - wh * cos(tilt), cy + wh * sin(tilt)
    Hx, Hy = cx + wh * cos(tilt), cy - wh * sin(tilt)

    def rail(x, y):
        a = tilt
        ux, uy = cos(a), sin(a)
        nx, ny = sin(a), -cos(a)
        return (
            f'<g stroke="{STEEL}" stroke-width="2.4" fill="none" stroke-linecap="round">'
            f'<line x1="{x-7*ux:.1f}" y1="{y-7*uy:.1f}" x2="{x+7*ux:.1f}" y2="{y+7*uy:.1f}"/>'
            f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x+nx*11:.1f}" y2="{y+ny*11:.1f}"/>'
            f'<line x1="{x+nx*11-8*ux:.1f}" y1="{y+ny*11-8*uy:.1f}" x2="{x+nx*11+8*ux:.1f}" y2="{y+ny*11+8*uy:.1f}"/>'
            f'</g>'
        )

    ux, uy = cos(tilt), sin(tilt)
    nx, ny = sin(tilt), -cos(tilt)
    bw, bh = 116, 50
    bx, by = cx + nx * (28 + bh / 2), cy + ny * (28 + bh / 2)
    corners = []
    for sx, sy in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
        px = bx + sx * bw / 2 * ux + sy * bh / 2 * nx
        py = by + sx * bw / 2 * uy + sy * bh / 2 * ny
        corners.append(f"{px:.1f},{py:.1f}")
    body = " ".join(corners)
    gx, gy = bx, by

    cd = ""
    if defic_mm is not None:
        cd = (f'<text x="40" y="300" font-family="{MONO}" font-size="12.5" fill="{MAROON}">'
              f'Cant deficiency  Cd = {defic_mm:.0f} mm</text>')

    body_svg = f"""
  <line x1="40" y1="262" x2="700" y2="262" stroke="{DIM}" stroke-width="1" stroke-dasharray="2 4"/>
  <text x="44" y="257" font-family="{FONT}" font-size="11.5" fill="{DIM}">แนวระดับ (horizontal)</text>

  <polygon points="{Lx:.1f},{Ly:.1f} {Hx:.1f},{Ly:.1f} {Hx:.1f},{Hy:.1f}" fill="{MAROON}" opacity="0.08"/>
  <line x1="{Lx:.1f}" y1="{Ly:.1f}" x2="{Hx:.1f}" y2="{Ly:.1f}" stroke="{DIM}" stroke-width="1" stroke-dasharray="4 3"/>
  <line x1="{Hx:.1f}" y1="{Ly:.1f}" x2="{Hx:.1f}" y2="{Hy:.1f}" stroke="{MAROON}" stroke-width="1.4"/>

  <polygon points="{Ax:.1f},{Ay:.1f} {Bx:.1f},{By:.1f} {Bx+nx*-15:.1f},{By+ny*-15:.1f} {Ax+nx*-15:.1f},{Ay+ny*-15:.1f}" fill="#6B4F2E" stroke="{NAVY}" stroke-width="1"/>

  {rail(Lx, Ly)}
  {rail(Hx, Hy)}

  <polygon points="{body}" fill="{NAVY}" opacity="0.9"/>
  <polygon points="{body}" fill="none" stroke="{NAVY}" stroke-width="1.2"/>
  <text x="{cx:.1f}" y="{cy - 86:.1f}" font-family="{FONT}" font-size="11.5" fill="{NAVY}" text-anchor="middle">ตัวรถ (vehicle)</text>
  <circle cx="{gx:.1f}" cy="{gy:.1f}" r="4.6" fill="#F7D154" stroke="{INK}" stroke-width="1.1"/>
  <text x="{gx + 8:.1f}" y="{gy - 7:.1f}" font-family="{MONO}" font-size="11.5" fill="#FBFAF7">C.G.</text>

  <line x1="{gx:.1f}" y1="{gy:.1f}" x2="{gx:.1f}" y2="237" stroke="{MAROON}" stroke-width="2.6" marker-end="url(#force{uid})"/>
  <text x="{gx + 7:.1f}" y="226" font-family="{MONO}" font-size="12.5" fill="{MAROON}">mg</text>
  <line x1="{gx:.1f}" y1="{gy:.1f}" x2="{gx - 80:.1f}" y2="{gy:.1f}" stroke="{MAROON}" stroke-width="2.6" marker-end="url(#force{uid})"/>
  <text x="{gx - 80:.1f}" y="{gy - 10:.1f}" font-family="{MONO}" font-size="12.5" fill="{MAROON}" text-anchor="middle">Fc = mV²/R</text>

  <path d="M {Lx + 34:.1f},{Ly:.1f} A 34 34 0 0 0 {Lx + 34 * cos(tilt):.1f},{Ly - 34 * sin(tilt):.1f}" fill="none" stroke="{NAVY}" stroke-width="1.2"/>
  <text x="{Lx + 44:.1f}" y="{Ly - 7:.1f}" font-family="{MONO}" font-size="12.5" fill="{NAVY}">θ</text>

  {_dim_v(Hy, Ly, Hx + 32, f"Ca = {ca_mm:.0f} mm", uid, left=False)}
  {_dim_h(Lx, Hx, 252, f"W = {w_mm:.0f} mm", uid)}

  <text x="40" y="26" font-family="{FONT}" font-size="14" font-weight="700" fill="{NAVY}">ภาพตัดขวางค่ายกโค้ง (Super-elevation / Cant)</text>
  <text x="40" y="44" font-family="{MONO}" font-size="11.5" fill="{DIMTX}">Ce = 8.416·V²/R   ·   Ca = 5.611·(V+5)²/R   ·   Cd = Ce − Ca</text>
  {cd}
"""
    return _frame(uid, body_svg, vb="0 0 720 310", h=310)


def embankment_diagram(formation_w_m: float = 6.0, height_m: float = 5.0,
                       slope_m: float = 1.5, base_w_m: float | None = None) -> str:
    """Trapezoidal railway embankment cross-section on a foundation soil."""
    uid = "emb"
    if base_w_m is None:
        base_w_m = formation_w_m + 2 * slope_m * height_m
    gy = 252                       # ground / foundation level
    topy = 116                     # formation level
    bxl, bxr = 150, 570            # base extents
    twl, twr = 286, 434            # formation (top) extents
    body = f"""
  <!-- foundation soil -->
  <rect x="40" y="{gy}" width="660" height="86" fill="url(#soil{uid})" stroke="none"/>
  <line x1="40" y1="{gy}" x2="700" y2="{gy}" stroke="{NAVY}" stroke-width="1.4"/>
  <text x="56" y="{gy+58}" font-family="{FONT}" font-size="12" fill="#6B5634">ดินฐานราก (foundation soil)  c, φ, γ</text>

  <!-- embankment fill -->
  <polygon points="{bxl},{gy} {twl},{topy} {twr},{topy} {bxr},{gy}" fill="url(#soil{uid})" stroke="{NAVY}" stroke-width="1.6"/>
  <text x="360" y="{(gy+topy)//2+22}" font-family="{FONT}" font-size="12.5" fill="#5A4424" text-anchor="middle">ดินถมคันทาง (compacted fill)  γ</text>

  <!-- ballast + sleeper + rails on formation -->
  <polygon points="310,{topy} 410,{topy} 396,{topy-16} 324,{topy-16}" fill="url(#rock{uid})" stroke="{NAVY}" stroke-width="1"/>
  <rect x="322" y="{topy-22}" width="76" height="7" fill="#6B4F2E" stroke="{NAVY}" stroke-width=".8"/>
  <rect x="332" y="{topy-30}" width="5" height="9" fill="{STEEL}"/>
  <rect x="383" y="{topy-30}" width="5" height="9" fill="{STEEL}"/>
  <text x="360" y="{topy-36}" font-family="{FONT}" font-size="11" fill="{NAVY}" text-anchor="middle">ทาง (track)</text>

  <!-- side slope label -->
  <text x="{(bxl+twl)//2-30}" y="{(gy+topy)//2}" font-family="{MONO}" font-size="12.5" fill="{MAROON}" transform="rotate(-48 {(bxl+twl)//2-30} {(gy+topy)//2})">1 : {slope_m:g}</text>
  <text x="{(bxr+twr)//2+30}" y="{(gy+topy)//2}" font-family="{MONO}" font-size="12.5" fill="{MAROON}" transform="rotate(48 {(bxr+twr)//2+30} {(gy+topy)//2})">1 : {slope_m:g}</text>

  <!-- bearing pressure arrows under formation column -->
  <g stroke="{MAROON}" stroke-width="2" marker-end="url(#force{uid})">
    <line x1="330" y1="{gy+6}" x2="330" y2="{gy+30}"/>
    <line x1="360" y1="{gy+6}" x2="360" y2="{gy+30}"/>
    <line x1="390" y1="{gy+6}" x2="390" y2="{gy+30}"/>
  </g>
  <text x="406" y="{gy+26}" font-family="{MONO}" font-size="12" fill="{MAROON}">Pb ≤ qa = qu / FS</text>

  <!-- dimensions -->
  {_dim_h(twl, twr, topy-44, f"ผิวคันทาง {formation_w_m:g} m", uid, above=True)}
  {_dim_v(topy, gy, bxr+54, f"H = {height_m:g} m", uid, left=False)}
  {_dim_h(bxl, bxr, gy+74, f"ฐานคันทาง {base_w_m:g} m", uid)}

  <text x="40" y="26" font-family="{FONT}" font-size="14" font-weight="700" fill="{NAVY}">ภาพตัดขวางคันทางรถไฟ + การรับแรงแบกทานดินฐานราก</text>
  <text x="40" y="44" font-family="{MONO}" font-size="11.5" fill="{DIMTX}">qu = c·Nc + γ·Df·Nq + 0.5·γ·B·Nγ</text>
"""
    return _frame(uid, body, vb="0 0 720 360", h=360)


def ditch_diagram(bottom_m: float = 0.6, side_z: float = 1.0, depth_m: float = 0.6,
                  total_m: float = 0.8, top_m: float | None = None) -> str:
    """Trapezoidal open ditch (drain) cross-section with water and freeboard."""
    uid = "dch"
    topy, boty = 110, 252
    H = boty - topy
    bxl, bxr = 312, 408            # bottom width b
    run = 138                      # horizontal flare across full depth
    txl, txr = bxl - run, bxr + run
    if top_m is None:
        top_m = bottom_m + 2 * side_z * total_m
    # water surface ratio
    wr = max(min(depth_m / total_m, 1.0), 0.0)
    wsy = boty - wr * H
    wrun = run * wr
    wxl, wxr = bxl - wrun, bxr + wrun
    body = f"""
  <!-- ground each side -->
  <line x1="40" y1="{topy}" x2="{txl}" y2="{topy}" stroke="{NAVY}" stroke-width="1.4"/>
  <line x1="{txr}" y1="{topy}" x2="700" y2="{topy}" stroke="{NAVY}" stroke-width="1.4"/>
  <rect x="40" y="{topy}" width="{txl-40}" height="120" fill="url(#soil{uid})"/>
  <rect x="{txr}" y="{topy}" width="{700-txr}" height="120" fill="url(#soil{uid})"/>

  <!-- channel outline -->
  <polygon points="{txl},{topy} {bxl},{boty} {bxr},{boty} {txr},{topy}" fill="#FBFAF7" stroke="{NAVY}" stroke-width="1.8"/>
  <!-- water -->
  <polygon points="{wxl:.1f},{wsy:.1f} {bxl},{boty} {bxr},{boty} {wxr:.1f},{wsy:.1f}" fill="{WATERFILL}" stroke="{WATER}" stroke-width="1.4"/>
  <line x1="{wxl:.1f}" y1="{wsy:.1f}" x2="{wxr:.1f}" y2="{wsy:.1f}" stroke="{WATER}" stroke-width="1.6"/>
  <text x="360" y="{(wsy+boty)/2+4:.0f}" font-family="{FONT}" font-size="12" fill="{WATER}" text-anchor="middle">น้ำ  Q, V</text>

  <!-- side slope label -->
  <text x="{(txl+bxl)//2-8}" y="{(topy+boty)//2}" font-family="{MONO}" font-size="12.5" fill="{MAROON}" transform="rotate(46 {(txl+bxl)//2-8} {(topy+boty)//2})">1 : {side_z:g}</text>
  <text x="{(txr+bxr)//2+8}" y="{(topy+boty)//2}" font-family="{MONO}" font-size="12.5" fill="{MAROON}" transform="rotate(-46 {(txr+bxr)//2+8} {(topy+boty)//2})">1 : {side_z:g}</text>

  <!-- dimensions -->
  {_dim_h(bxl, bxr, boty+16, f"ท้องราง b = {bottom_m:g} m", uid)}
  {_dim_h(txl, txr, topy-10, f"ปากราง T = {top_m:.2f} m", uid, above=True)}
  {_dim_v(wsy, boty, txl-26, f"y = {depth_m:.2f}", uid)}
  {_dim_v(topy, boty, 60, f"h = {total_m:.2f} m", uid)}
  <line x1="{wxr:.1f}" y1="{wsy:.1f}" x2="{txr+30}" y2="{wsy:.1f}" stroke="{DIM}" stroke-width=".8" stroke-dasharray="3 3"/>
  {_dim_v(topy, wsy, txr+34, "freeboard", uid, left=False)}

  <text x="40" y="26" font-family="{FONT}" font-size="14" font-weight="700" fill="{NAVY}">รางระบายน้ำเปิดรูปสี่เหลี่ยมคางหมู (Trapezoidal ditch)</text>
  <text x="40" y="44" font-family="{MONO}" font-size="11.5" fill="{DIMTX}">Q = 0.278·C·I·A   ·   Q = (1/n)·A·R^(2/3)·S^(1/2)</text>
"""
    return _frame(uid, body, vb="0 0 720 300", h=300)


def sleeper_diagram(ballast_h_label: str = "h") -> str:
    """Track cross-section: rail / sleeper / ballast / formation with load spread."""
    uid = "slp"
    body = f"""
  <!-- formation / subgrade -->
  <rect x="40" y="262" width="660" height="74" fill="url(#soil{uid})"/>
  <line x1="40" y1="262" x2="700" y2="262" stroke="{NAVY}" stroke-width="1.4"/>
  <text x="56" y="296" font-family="{FONT}" font-size="12" fill="#6B5634">พื้นทาง (formation / subgrade)</text>

  <!-- ballast -->
  <polygon points="208,262 512,262 470,214 250,214" fill="url(#rock{uid})" stroke="{NAVY}" stroke-width="1.4"/>
  <text x="360" y="244" font-family="{FONT}" font-size="11.5" fill="#5C6166" text-anchor="middle">หินโรยทาง (ballast)</text>

  <!-- sleeper -->
  <rect x="250" y="200" width="220" height="14" rx="2" fill="#6B4F2E" stroke="{NAVY}" stroke-width="1"/>
  <text x="476" y="211" font-family="{FONT}" font-size="11.5" fill="#5A4424">หมอน</text>

  <!-- rails -->
  <g fill="{STEEL}">
    <rect x="300" y="176" width="14" height="6"/><rect x="304" y="182" width="6" height="14"/><rect x="298" y="196" width="18" height="5"/>
    <rect x="406" y="176" width="14" height="6"/><rect x="410" y="182" width="6" height="14"/><rect x="404" y="196" width="18" height="5"/>
  </g>
  <text x="300" y="170" font-family="{FONT}" font-size="11" fill="{NAVY}">ราง</text>

  <!-- wheel loads -->
  <g stroke="{MAROON}" stroke-width="2.6" marker-end="url(#force{uid})">
    <line x1="307" y1="138" x2="307" y2="172"/>
    <line x1="413" y1="138" x2="413" y2="172"/>
  </g>
  <text x="307" y="132" font-family="{MONO}" font-size="12" fill="{MAROON}" text-anchor="middle">P/2</text>
  <text x="413" y="132" font-family="{MONO}" font-size="12" fill="{MAROON}" text-anchor="middle">P/2</text>

  <!-- load spread cone into ballast/subgrade -->
  <path d="M 250,214 L 196,262 M 470,214 L 524,262" stroke="{MAROON}" stroke-width="1" stroke-dasharray="5 4" fill="none"/>
  <path d="M 196,262 Q 360,322 524,262" stroke="{MAROON}" stroke-width="1.4" fill="{MAROON}" fill-opacity="0.06"/>
  <text x="360" y="312" font-family="{MONO}" font-size="11.5" fill="{MAROON}" text-anchor="middle">Pb = 50/(10+h^1.35)·Ps</text>

  {_dim_v(214, 262, 150, f"{ballast_h_label}", uid)}

  <text x="40" y="26" font-family="{FONT}" font-size="14" font-weight="700" fill="{NAVY}">โครงสร้างทาง: ราง–หมอน–หินโรยทาง (Beam on elastic foundation)</text>
  <text x="40" y="44" font-family="{MONO}" font-size="11.5" fill="{DIMTX}">σ = M/Z   ·   M = Q/(4β)   ·   Ps = c·settlement</text>
"""
    return _frame(uid, body, vb="0 0 720 340", h=340)


def turnout_plan_diagram(number: float = 12.0, radius_label: str | None = None,
                         speed_label: str | None = None, theoretical: bool = False) -> str:
    """Plan view of a turnout: stock rails, switch, lead curve and crossing."""
    uid = "tno"
    angle = degrees(2 * atan(0.5 / number))
    toe = (180, 196)
    frog = (610, 132)
    body = f"""
  <!-- main (through) track -->
  <line x1="60" y1="196" x2="720" y2="196" stroke="{STEEL}" stroke-width="2.4"/>
  <line x1="60" y1="208" x2="720" y2="208" stroke="{STEEL}" stroke-width="2.4"/>
  <text x="640" y="226" font-family="{FONT}" font-size="11.5" fill="{DIMTX}">ทางตรงหลัก (through)</text>

  <!-- diverging (turnout) curve -->
  <path d="M {toe[0]},{toe[1]} Q 400,196 {frog[0]},{frog[1]} L 720,108"
        fill="none" stroke="{MAROON}" stroke-width="2.4"/>
  <path d="M {toe[0]},{toe[1]+12} Q 405,208 {frog[0]+4},{frog[1]+11} L 722,119"
        fill="none" stroke="{MAROON}" stroke-width="2.4" opacity="0.75"/>

  <!-- switch (points) -->
  <circle cx="{toe[0]}" cy="{toe[1]}" r="4" fill="{NAVY}"/>
  <text x="{toe[0]-6}" y="{toe[1]+30}" font-family="{FONT}" font-size="11.5" fill="{NAVY}">ลิ้นประแจ (switch)</text>

  <!-- crossing / frog -->
  <circle cx="{frog[0]}" cy="{frog[1]}" r="4" fill="{NAVY}"/>
  <text x="{frog[0]-6}" y="{frog[1]-12}" font-family="{FONT}" font-size="11.5" fill="{NAVY}">ตะเฆ้ (crossing) 1:{number:g}</text>

  <!-- crossing angle -->
  <path d="M {frog[0]-58},196 A 58 58 0 0 0 {frog[0]-58*cos(radians(angle)):.0f},{196-58*sin(radians(angle)):.0f}"
        fill="none" stroke="{NAVY}" stroke-width="1.2"/>
  <text x="{frog[0]-78}" y="186" font-family="{MONO}" font-size="12" fill="{NAVY}">θ={angle:.2f}°</text>

  <!-- lead dimension -->
  {_dim_h(toe[0], frog[0], 250, "Lead", uid)}

  <text x="40" y="26" font-family="{FONT}" font-size="14" font-weight="700" fill="{NAVY}">แปลนประแจ (Turnout)  θ = 2·atan(0.5/N)</text>
"""
    extra = ""
    if radius_label:
        extra += f'<text x="430" y="150" font-family="{MONO}" font-size="12" fill="{MAROON}">R = {radius_label}</text>'
    if speed_label:
        extra += f'<text x="430" y="168" font-family="{MONO}" font-size="12" fill="{MAROON}">V = {speed_label}</text>'
    if theoretical:
        extra += f'<text x="40" y="44" font-family="{MONO}" font-size="11.5" fill="{DIMTX}">Lead₀ = R·sinθ + C·cosθ</text>'
    return _frame(uid, body + extra, vb="0 0 760 270", h=270)


def transition_plan_diagram(delta_deg: float = 20.0, R_label: str = "R",
                            Ls_label: str = "Ls") -> str:
    """Schematic plan of straight–spiral–curve–spiral–straight alignment."""
    uid = "trc"
    O = (430, 338)
    R = 150
    d = radians(delta_deg)
    # arc from SC (left) to CS (right), symmetric about vertical through O
    a0 = radians(90) + d / 2     # SC angle
    a1 = radians(90) - d / 2     # CS angle
    SC = (O[0] + R * cos(a0), O[1] - R * sin(a0))
    CS = (O[0] + R * cos(a1), O[1] - R * sin(a1))
    # tangent directions at SC (perpendicular to radius)
    # incoming tangent heads right-up toward SC; approximate TS and tangents
    TS = (SC[0] - 150, SC[1] + 150 * tan(d / 2) * 0 + 36)
    ST = (CS[0] + 150, CS[1] + 36)
    PIx = O[0]
    PIy = SC[1] - 70
    body = f"""
  <!-- incoming tangent + entry spiral -->
  <line x1="70" y1="{SC[1]+60:.0f}" x2="{TS[0]:.0f}" y2="{TS[1]:.0f}" stroke="{NAVY}" stroke-width="2.2"/>
  <path d="M {TS[0]:.0f},{TS[1]:.0f} Q {(TS[0]+SC[0])/2:.0f},{(TS[1]+SC[1])/2-6:.0f} {SC[0]:.0f},{SC[1]:.0f}" fill="none" stroke="{MAROON}" stroke-width="2.4"/>
  <!-- circular arc -->
  <path d="M {SC[0]:.0f},{SC[1]:.0f} A {R} {R} 0 0 1 {CS[0]:.0f},{CS[1]:.0f}" fill="none" stroke="{NAVY}" stroke-width="2.6"/>
  <!-- exit spiral + tangent -->
  <path d="M {CS[0]:.0f},{CS[1]:.0f} Q {(CS[0]+ST[0])/2:.0f},{(CS[1]+ST[1])/2-6:.0f} {ST[0]:.0f},{ST[1]:.0f}" fill="none" stroke="{MAROON}" stroke-width="2.4"/>
  <line x1="{ST[0]:.0f}" y1="{ST[1]:.0f}" x2="690" y2="{ST[1]+60:.0f}" stroke="{NAVY}" stroke-width="2.2"/>

  <!-- radius lines to centre -->
  <line x1="{O[0]}" y1="{O[1]}" x2="{SC[0]:.0f}" y2="{SC[1]:.0f}" stroke="{DIM}" stroke-width="1" stroke-dasharray="4 3"/>
  <line x1="{O[0]}" y1="{O[1]}" x2="{CS[0]:.0f}" y2="{CS[1]:.0f}" stroke="{DIM}" stroke-width="1" stroke-dasharray="4 3"/>
  <circle cx="{O[0]}" cy="{O[1]}" r="3.5" fill="{DIM}"/>
  <text x="{O[0]+6}" y="{O[1]+4}" font-family="{MONO}" font-size="12" fill="{DIMTX}">O</text>
  <text x="{(O[0]+SC[0])/2-30:.0f}" y="{(O[1]+SC[1])/2:.0f}" font-family="{MONO}" font-size="12" fill="{DIMTX}">{R_label}</text>

  <!-- PI + tangents -->
  <line x1="{TS[0]:.0f}" y1="{TS[1]:.0f}" x2="{PIx}" y2="{PIy:.0f}" stroke="{DIM}" stroke-width="1" stroke-dasharray="2 4"/>
  <line x1="{ST[0]:.0f}" y1="{ST[1]:.0f}" x2="{PIx}" y2="{PIy:.0f}" stroke="{DIM}" stroke-width="1" stroke-dasharray="2 4"/>
  <circle cx="{PIx}" cy="{PIy:.0f}" r="3.5" fill="{NAVY}"/>
  <text x="{PIx-6}" y="{PIy-8:.0f}" font-family="{MONO}" font-size="12" fill="{NAVY}">PI · Δ={delta_deg:g}°</text>

  <!-- station points -->
  <g font-family="{MONO}" font-size="11.5" fill="{MAROON}">
    <circle cx="{TS[0]:.0f}" cy="{TS[1]:.0f}" r="3" fill="{MAROON}"/><text x="{TS[0]-22:.0f}" y="{TS[1]+16:.0f}">TS</text>
    <circle cx="{SC[0]:.0f}" cy="{SC[1]:.0f}" r="3" fill="{MAROON}"/><text x="{SC[0]-18:.0f}" y="{SC[1]-8:.0f}">SC</text>
    <circle cx="{CS[0]:.0f}" cy="{CS[1]:.0f}" r="3" fill="{MAROON}"/><text x="{CS[0]+6:.0f}" y="{CS[1]-8:.0f}">CS</text>
    <circle cx="{ST[0]:.0f}" cy="{ST[1]:.0f}" r="3" fill="{MAROON}"/><text x="{ST[0]+6:.0f}" y="{ST[1]+16:.0f}">ST</text>
  </g>

  <text x="40" y="26" font-family="{FONT}" font-size="14" font-weight="700" fill="{NAVY}">แปลนโค้งต่อและโค้งกลม (Transition + Circular curve)</text>
  <text x="40" y="44" font-family="{MONO}" font-size="11.5" fill="{DIMTX}">Ls = 0.01·V·Ca   ·   Shift = Ls²/(24R)   ·   TS → SC → CS → ST</text>
"""
    return _frame(uid, body, vb="0 0 760 332", h=332)


def widening_plan_diagram(number: float = 12.0, distance_label: str = "D") -> str:
    """Plan of a crossover used to widen / shift between two parallel tracks."""
    uid = "wid"
    body = f"""
  <!-- track A (upper) -->
  <line x1="60" y1="70" x2="720" y2="70" stroke="{STEEL}" stroke-width="2.4"/>
  <line x1="60" y1="80" x2="720" y2="80" stroke="{STEEL}" stroke-width="2.4"/>
  <text x="64" y="60" font-family="{FONT}" font-size="11.5" fill="{DIMTX}">แนวทางที่ 1</text>
  <!-- track B (lower) -->
  <line x1="60" y1="186" x2="720" y2="186" stroke="{STEEL}" stroke-width="2.4"/>
  <line x1="60" y1="196" x2="720" y2="196" stroke="{STEEL}" stroke-width="2.4"/>
  <text x="64" y="216" font-family="{FONT}" font-size="11.5" fill="{DIMTX}">แนวทางที่ 2</text>

  <!-- crossover -->
  <path d="M 250,80 Q 330,80 380,128 T 510,186" fill="none" stroke="{MAROON}" stroke-width="2.6"/>
  <line x1="380" y1="128" x2="382" y2="138" stroke="{MAROON}" stroke-width="1"/>

  <circle cx="250" cy="80" r="4" fill="{NAVY}"/><text x="232" y="100" font-family="{FONT}" font-size="11" fill="{NAVY}">ประแจ 1:{number:g}</text>
  <circle cx="510" cy="186" r="4" fill="{NAVY}"/><text x="492" y="176" font-family="{FONT}" font-size="11" fill="{NAVY}">ประแจ 1:{number:g}</text>

  <!-- distance between tracks -->
  {_dim_v(80, 186, 110, distance_label, uid)}
  <!-- diagonal straight note -->
  <text x="396" y="150" font-family="{MONO}" font-size="11.5" fill="{MAROON}">ทางตรงระหว่างประแจ ≥ 0.2V</text>

  <text x="40" y="26" font-family="{FONT}" font-size="14" font-weight="700" fill="{NAVY}">แปลนการขยายขนาดทาง (Crossover / track shift)</text>
"""
    return _frame(uid, body, vb="0 0 760 240", h=240)


def overview_hero() -> str:
    """Stylised perspective of railway track for the guidance page header."""
    uid = "hero"
    body = f"""
  <rect x="0" y="0" width="760" height="260" fill="url(#sky{uid})"/>
  <!-- ground -->
  <polygon points="0,150 760,150 760,260 0,260" fill="#0E2A4D"/>
  <!-- vanishing rails -->
  <polygon points="372,150 388,150 540,260 300,260" fill="#16335A"/>
  <line x1="372" y1="150" x2="300" y2="260" stroke="#C9D4E4" stroke-width="3"/>
  <line x1="388" y1="150" x2="540" y2="260" stroke="#C9D4E4" stroke-width="3"/>
  <!-- sleepers in perspective -->
  <g stroke="#7A0019" stroke-linecap="round">
    <line x1="360" y1="166" x2="400" y2="166" stroke-width="2"/>
    <line x1="352" y1="182" x2="410" y2="182" stroke-width="2.6"/>
    <line x1="342" y1="202" x2="422" y2="202" stroke-width="3.2"/>
    <line x1="330" y1="226" x2="436" y2="226" stroke-width="4"/>
    <line x1="315" y1="252" x2="452" y2="252" stroke-width="5"/>
  </g>
  <!-- sun / horizon glow -->
  <circle cx="380" cy="150" r="46" fill="#F7D154" opacity="0.16"/>
  <text x="40" y="62" font-family="{FONT}" font-size="22" font-weight="700" fill="#FBFAF7">เครื่องมือคำนวณงานทางรถไฟ</text>
  <text x="42" y="90" font-family="{FONT}" font-size="13.5" fill="#C9D4E4">Railway Engineering Calculator · กองบำรุงทางถาวร</text>
"""
    return _frame(uid, body, vb="0 0 760 260", h=260)
