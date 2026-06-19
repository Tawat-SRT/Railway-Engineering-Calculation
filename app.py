from __future__ import annotations

from io import BytesIO

import pandas as pd
import streamlit as st

import diagrams as dg
from calculators import (
    RAIL_PROPERTIES,
    cant_calculation,
    drainage_design,
    embankment_design,
    sleeper_track_analysis,
    track_widening,
    transition_curve,
    turnout_geometry,
    turnout_speed,
)

GRAV = 9.80665  # ton/m^2 -> kPa (กก.แรง -> นิวตัน)

st.set_page_config(
    page_title="SRT Railway Calculator",
    page_icon="🛤️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@400;500;600;700&family=Roboto+Mono:wght@500&display=swap');
:root { --navy:#0B2341; --maroon:#7A0019; --cream:#F7F3EA; --ink:#182333; --muted:#667085; }
html, body, [class*="css"] { font-family:'Noto Sans Thai',sans-serif; }
[data-testid="stAppViewContainer"] { background:#fbfaf7; color:var(--ink); }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#0B2341 0%,#0E2C52 100%); border-right:1px solid rgba(255,255,255,.08); }
[data-testid="stSidebar"] * { color:#f8fafc !important; }
[data-testid="stSidebar"] [role="radiogroup"] label { padding:.52rem .65rem; border-radius:7px; transition:background .15s; }
[data-testid="stSidebar"] [role="radiogroup"] label:hover { background:rgba(255,255,255,.06); }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) { background:rgba(122,0,25,.55); box-shadow:inset 3px 0 0 var(--maroon); }
.block-container { padding-top:2.2rem; max-width:1500px; }
h1,h2,h3 { color:var(--navy); letter-spacing:-.02em; }
h1 { font-size:2.15rem !important; margin-bottom:.15rem !important; }
.eyebrow { color:var(--maroon); font-weight:700; letter-spacing:.08em; text-transform:uppercase; font-size:.78rem; }
.subhead { color:var(--muted); font-size:1rem; margin-bottom:1.45rem; }
.rail-rule { height:8px; margin:0 0 1.3rem; background:repeating-linear-gradient(90deg,var(--maroon) 0 54px,transparent 54px 66px); border-top:2px solid var(--navy); }
.section-label { font-size:.77rem; color:var(--muted); font-weight:700; letter-spacing:.06em; text-transform:uppercase; margin:1rem 0 .2rem; }
.ok { color:#146c43; font-weight:700; }
.bad { color:#a61b1b; font-weight:700; }
.formula { font-family:'Roboto Mono',monospace; color:#344054; background:#f1eee8; padding:.7rem .85rem; border-left:3px solid var(--maroon); font-size:.84rem; border-radius:0 5px 5px 0; }
div[data-testid="stMetric"] { border-left:3px solid var(--maroon); padding-left:.85rem; }
div[data-testid="stMetric"] label { color:#667085; }
.stButton>button, .stDownloadButton>button { border-radius:6px; border:1px solid var(--navy); font-weight:650; }
.stDownloadButton>button { background:var(--navy); color:white; }
[data-testid="stNumberInput"] input, [data-testid="stSelectbox"] > div > div { background:white; }
figure.diagram { margin:.2rem 0 1rem; padding:1rem 1.1rem .7rem; background:#fff; border:1px solid #e6e2da; border-radius:12px; box-shadow:0 1px 2px rgba(11,35,65,.05); }
figure.diagram svg { width:100%; height:auto; display:block; }
figure.diagram figcaption { color:var(--muted); font-size:.82rem; margin-top:.5rem; text-align:center; }
.guide-card { background:#fff; border:1px solid #e6e2da; border-left:4px solid var(--maroon); border-radius:10px; padding:.85rem 1rem; margin-bottom:.65rem; }
.guide-card b { color:var(--navy); }
.guide-card span { color:#475467; font-size:.92rem; }
.step { display:flex; gap:.8rem; align-items:flex-start; margin:.55rem 0; }
.step .num { flex:0 0 auto; width:1.9rem; height:1.9rem; border-radius:50%; background:var(--navy); color:#fff; font-weight:700; display:flex; align-items:center; justify-content:center; font-size:.95rem; }
.step .txt { padding-top:.18rem; color:#344054; }
.stTabs [data-baseweb="tab-list"] { gap:.4rem; }
.stTabs [data-baseweb="tab"] { background:#f1eee8; border-radius:8px 8px 0 0; padding:.5rem 1rem; font-weight:600; }
.stTabs [aria-selected="true"] { background:var(--navy); color:#fff !important; }
@media(max-width:768px){ .block-container{padding:1.2rem 1rem;} h1{font-size:1.7rem!important;} }
</style>
""",
    unsafe_allow_html=True,
)


PAGES = {
    "ข้อแนะนำการใช้": "guide",
    "ค่ายกโค้งและความเร็ว": "cant",
    "ความเร็วผ่านประแจ": "turnout_speed",
    "ออกแบบโครงสร้างทางรถไฟและระบายน้ำ": "structure",
    "วิเคราะห์ราง–หมอน–หินโรยทาง": "sleeper",
    "เรขาคณิตประแจ": "turnout_geometry",
    "โค้งต่อและโค้งกลม": "transition",
    "การขยายขนาดทาง": "widening",
}


def heading(title: str, subtitle: str, eyebrow: str = "Railway Engineering Calculator") -> None:
    st.markdown(f'<div class="eyebrow">{eyebrow}</div>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<div class="subhead">{subtitle}</div><div class="rail-rule"></div>', unsafe_allow_html=True)


def figure(svg: str, caption: str = "") -> None:
    cap = f"<figcaption>{caption}</figcaption>" if caption else ""
    st.markdown(f'<figure class="diagram">{svg}{cap}</figure>', unsafe_allow_html=True)


def result_status(label: str, ok: bool, detail: str) -> None:
    cls, text = ("ok", "ผ่านเกณฑ์") if ok else ("bad", "ต้องตรวจสอบ")
    st.markdown(f"**{label}** — <span class='{cls}'>{text}</span> · {detail}", unsafe_allow_html=True)


def excel_download(title: str, inputs: dict, results: dict) -> None:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame({"รายการ": list(inputs), "ค่า": list(inputs.values())}).to_excel(writer, "Input", index=False)
        pd.DataFrame({"ผลลัพธ์": list(results), "ค่า": list(results.values())}).to_excel(writer, "Result", index=False)
        ws = writer.book["Result"]
        ws.freeze_panes = "A2"
        ws.column_dimensions["A"].width = 38
        ws.column_dimensions["B"].width = 22
    st.download_button(
        "ดาวน์โหลดผลคำนวณ Excel",
        output.getvalue(),
        file_name=f"{title}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )


with st.sidebar:
    st.markdown("## SRT · CALC")
    st.caption("เครื่องมือคำนวณงานทางรถไฟ")
    selected = st.radio("หมวดคำนวณ", list(PAGES), label_visibility="collapsed")
    st.markdown("---")
    st.caption("อ้างอิงเกณฑ์ตามมาตรฐานบำรุงทาง (มบท.) และหลักวิศวกรรมทางรถไฟ")
    st.caption("จัดทำระบบ: กองบำรุงทางถาวร")

page = PAGES[selected]


if page == "guide":
    heading("ข้อแนะนำการใช้", "เครื่องมือช่วยคำนวณงานทางรถไฟตามมาตรฐานบำรุงทางและหลักวิศวกรรม เลือกหมวดได้จากแถบด้านซ้าย")
    figure(dg.overview_hero())
    st.markdown("### ขั้นตอนการใช้งาน")
    steps = [
        "เลือกหมวดการคำนวณจากแถบเมนูด้านซ้ายให้ตรงกับงานที่ต้องการ",
        "กรอกค่าพารามิเตอร์ออกแบบ เช่น รัศมีโค้ง ความเร็ว ขนาดราง หรือคุณสมบัติดิน",
        "อ่านผลลัพธ์ ภาพประกอบ และสถานะการตรวจสอบเกณฑ์ที่แสดงทางขวา",
        "ดาวน์โหลดผลคำนวณเป็นไฟล์เพื่อแนบประกอบรายงานหรือตรวจทานต่อ",
    ]
    for i, s in enumerate(steps, 1):
        st.markdown(f'<div class="step"><div class="num">{i}</div><div class="txt">{s}</div></div>', unsafe_allow_html=True)
    st.markdown("### หมวดการคำนวณ")
    cards = [
        ("ค่ายกโค้งและความเร็ว", "ค่ายกสมดุล ค่ายกจริง ส่วนขาด/ส่วนเกิน และช่วงความเร็วสูงสุด–ต่ำสุดที่ยอมให้ผ่านโค้ง"),
        ("ความเร็วผ่านประแจ", "ความเร็วจำกัดผ่านทางเลี้ยวของประแจจากรัศมีและความเร่งด้านข้าง"),
        ("ออกแบบโครงสร้างทางรถไฟและระบายน้ำ", "ออกแบบคันทางและตรวจกำลังรับแรงแบกทาน พร้อมออกแบบรางระบายน้ำเปิดรูปสี่เหลี่ยมคางหมู"),
        ("วิเคราะห์ราง–หมอน–หินโรยทาง", "แรงเค้นในราง แรงถ่ายทอดสู่หมอน และแรงกดบนหินโรยทางกับพื้นทาง"),
        ("เรขาคณิตประแจ", "มุมตะเฆ้ Theoretical lead และองค์ประกอบเรขาคณิตของชุดประแจ"),
        ("โค้งต่อและโค้งกลม", "ความยาวโค้งต่อ ระยะ Shift และ Chainage ของจุด TS–SC–CS–ST"),
        ("การขยายขนาดทาง", "ตรวจระยะทางตรงระหว่างชุดประแจและเรขาคณิตจากมุม 1:N"),
    ]
    for title, body in cards:
        st.markdown(f'<div class="guide-card"><b>{title}</b><br><span>{body}</span></div>', unsafe_allow_html=True)


elif page == "cant":
    heading("ค่ายกโค้งและความเร็ว", "คำนวณค่ายกสมดุล ส่วนขาด/ส่วนเกิน และช่วงความเร็วที่ยอมให้ผ่านโค้ง")
    left, right = st.columns([1, 1.45], gap="large")
    with left:
        radius = st.number_input("รัศมีโค้ง R (ม.)", 100.0, 10000.0, 1600.0, 10.0)
        speed = st.number_input("ความเร็วออกแบบ V (กม./ชม.)", 10.0, 250.0, 120.0, 5.0)
        auto = st.toggle("ใช้ค่ายกจริงที่ระบบแนะนำ", True)
        actual = None if auto else st.number_input("ค่ายกจริง Ca (มม.)", 0.0, 180.0, 55.0, 5.0)
        result = cant_calculation(radius, speed, actual)
        st.markdown('<div class="formula">Ce = 8.416V²/R · Ca = 5.611(V+5)²/R</div>', unsafe_allow_html=True)
    with right:
        figure(
            dg.cant_diagram(result["actual_cant_mm"], 1070, result["cant_deficiency_mm"]),
            "ค่ายกโค้ง (Super-elevation) ยกรางนอกสูงกว่ารางในเป็นระยะ Ca บนระยะศูนย์กลางราง W = 1,070 มม.",
        )
        st.markdown('<div class="section-label">ผลคำนวณ</div>', unsafe_allow_html=True)
        a, b, c = st.columns(3)
        a.metric("ค่ายกสมดุล Ce", f'{result["equilibrium_cant_mm"]:.0f} มม.')
        b.metric("ค่ายกจริง Ca", f'{result["actual_cant_mm"]:.0f} มม.')
        c.metric("ส่วนขาด Cd", f'{result["cant_deficiency_mm"]:.0f} มม.')
        a, b, c = st.columns(3)
        a.metric("ส่วนเกิน", f'{result["cant_excess_mm"]:.0f} มม.')
        b.metric("V สูงสุด", f'{result["vmax_kmh"]:.0f} กม./ชม.')
        c.metric("V ต่ำสุด", f'{result["vmin_kmh"]:.0f} กม./ชม.')
        result_status("ส่วนขาดค่ายก (Cant deficiency)", result["deficiency_ok"], "เกณฑ์ (มบท.) ≤ 50 มม.")
        result_status("ส่วนเกินค่ายก (Cant excess)", result["excess_ok"], "เกณฑ์ (มบท.) ≤ 60 มม.")
        speeds = list(range(20, 181, 5))
        chart = pd.DataFrame({"ความเร็ว (กม./ชม.)": speeds, "ค่ายกสมดุล (มม.)": [8.416 * v**2 / radius for v in speeds]})
        st.line_chart(chart, x="ความเร็ว (กม./ชม.)", y="ค่ายกสมดุล (มม.)", height=230)
        excel_download("cant_calculation", {"R (m)": radius, "V (km/h)": speed}, result)


elif page == "turnout_speed":
    heading("ความเร็วผ่านประแจทางเลี้ยว", "หาความเร็วจำกัดจากรัศมีและความเร่งด้านข้างที่เกิดจากส่วนขาดค่ายก")
    left, right = st.columns([1, 1.35], gap="large")
    with left:
        presets = {"1:8 · R 164.496 m": 164.496, "1:10 · R 185 m": 185.0, "1:12 · R 265 m": 265.0, "1:16 · R 648 m": 648.0, "กำหนดเอง": 300.0}
        preset = st.selectbox("แบบประแจ", presets)
        radius = st.number_input("รัศมีทางเลี้ยว (ม.)", 50.0, 3000.0, presets[preset], 1.0)
        hd = st.number_input("ส่วนขาดค่ายก hd (มม.)", 10.0, 100.0, 50.0, 5.0)
        gauge = st.number_input("ระยะศูนย์กลางราง G (มม.)", 900.0, 1600.0, 1067.0, 1.0)
        result = turnout_speed(radius, hd, gauge)
        st.markdown('<div class="formula">ac = g·hd/G · Vlim = 3.6√(ac·R)</div>', unsafe_allow_html=True)
    with right:
        number_guess = max(8.0, min(16.0, round((radius / 40) ** 0.5 + 6)))
        figure(
            dg.turnout_plan_diagram(number_guess, radius_label=f"R = {radius:.0f} m", speed_label=f"V = {result['design_speed_kmh']:.0f} km/h"),
            "ผังประแจ: ทางตรงผ่าน ทางเลี้ยวรัศมี R ผ่านลิ้นประแจและตะเฆ้ 1:N",
        )
        a, b, c = st.columns(3)
        a.metric("ความเร่งด้านข้าง", f'{result["lateral_acceleration_mps2"]:.3f} m/s²')
        b.metric("V จำกัด", f'{result["limit_speed_kmh"]:.0f} กม./ชม.')
        c.metric("V ออกแบบ", f'{result["design_speed_kmh"]:.0f} กม./ชม.')
        st.info("ความเร็วออกแบบปัดลงทีละ 5 กม./ชม. เพื่อความปลอดภัยในการเดินรถผ่านประแจ")
        excel_download("turnout_speed", {"R (m)": radius, "hd (mm)": hd, "G (mm)": gauge}, result)


elif page == "structure":
    heading("ออกแบบโครงสร้างทางรถไฟและระบายน้ำ", "ออกแบบคันทางพร้อมตรวจกำลังรับแรงแบกทาน และออกแบบรางระบายน้ำเปิดรูปสี่เหลี่ยมคางหมูตามแนวทางรถไฟ")
    tab_emb, tab_ditch = st.tabs(["คันทางและกำลังรับแรงแบกทาน", "รางระบายน้ำเปิด (Ditch)"])

    with tab_emb:
        left, right = st.columns([1, 1.45], gap="large")
        with left:
            st.markdown('<div class="section-label">รูปตัดคันทาง</div>', unsafe_allow_html=True)
            formation_w = st.number_input("ความกว้างหลังคันทาง (ม.)", 4.0, 20.0, 7.0, 0.5)
            height = st.number_input("ความสูงคันทาง H (ม.)", 0.5, 20.0, 5.0, 0.5)
            slope = st.number_input("ลาดข้างคันทาง (H ต่อ 1V)", 0.5, 3.0, 1.5, 0.25)
            fill_gamma = st.number_input("หน่วยน้ำหนักวัสดุถม γ (kN/m³)", 14.0, 24.0, 19.0, 0.5)
            st.markdown('<div class="section-label">ดินฐานรากและแรงกระทำ</div>', unsafe_allow_html=True)
            cohesion = st.number_input("แรงยึดเหนี่ยวดินฐาน c (kPa)", 0.0, 200.0, 20.0, 1.0)
            phi = st.number_input("มุมเสียดทานภายใน φ (องศา)", 0.0, 45.0, 28.0, 1.0)
            sub_gamma = st.number_input("หน่วยน้ำหนักดินฐาน γ (kN/m³)", 14.0, 24.0, 18.0, 0.5)
            embed = st.number_input("ความลึกฝัง Df (ม.)", 0.0, 5.0, 0.5, 0.1)
            bearing_w = st.number_input("ความกว้างฐานรับแรง B (ม.)", 0.5, 10.0, 3.0, 0.5)
            fos = st.number_input("ส่วนปลอดภัย FS", 2.0, 4.0, 3.0, 0.5)
            pb_default = sleeper_track_analysis("BS 100 A", 10, 20, 25, 200, 60, 25, 120)["formation_pressure_ton_m2"] * GRAV
            applied = st.number_input("แรงกดที่พื้นทาง Pb (kPa)", 10.0, 500.0, float(round(pb_default, 1)), 1.0)
            st.caption("ค่า Pb เริ่มต้นแปลงจากแรงกดพื้นทาง (formation pressure) ในหมวดวิเคราะห์ราง–หมอน × 9.81")
            result = embankment_design(formation_w, height, slope, fill_gamma, cohesion, phi, sub_gamma, applied, bearing_w, fos, embed)
        with right:
            figure(
                dg.embankment_diagram(formation_w, height, slope, result["base_width_m"]),
                f"รูปตัดคันทางรูปสี่เหลี่ยมคางหมู ฐานกว้าง {result['base_width_m']:.1f} ม. ลาดข้าง 1:{slope:g} รับโครงสร้างทางด้านบน",
            )
            st.markdown('<div class="section-label">ปริมาณงานดินถม (ต่อความยาว 1 ม.)</div>', unsafe_allow_html=True)
            a, b, c = st.columns(3)
            a.metric("ฐานคันทาง", f'{result["base_width_m"]:.2f} ม.')
            b.metric("พื้นที่หน้าตัด", f'{result["cross_section_area_m2"]:.2f} ม.²')
            c.metric("ปริมาตรถม", f'{result["fill_volume_per_m_m3"]:.2f} ม.³/ม.')
            st.markdown('<div class="section-label">กำลังรับแรงแบกทาน</div>', unsafe_allow_html=True)
            a, b, c = st.columns(3)
            a.metric("qu สูงสุด", f'{result["ultimate_bearing_kpa"]:.1f} kPa')
            b.metric("qa ยอมให้", f'{result["allowable_bearing_kpa"]:.1f} kPa')
            c.metric("Pb ที่กระทำ", f'{result["applied_pressure_kpa"]:.1f} kPa')
            a, b, c = st.columns(3)
            a.metric("Nc", f'{result["Nc"]:.2f}')
            b.metric("Nq", f'{result["Nq"]:.2f}')
            c.metric("Nγ", f'{result["Ngamma"]:.2f}')
            result_status("กำลังรับแรงแบกทาน (Pb ≤ qa)", result["bearing_ok"], f'อัตราการใช้งาน {result["utilisation_ratio"]*100:.0f}% · FS จริง {result["factor_of_safety_actual"]:.2f}')
            st.markdown('<div class="formula">qu = c·Nc + γ·Df·Nq + 0.5·γ·B·Nγ · qa = qu/FS</div>', unsafe_allow_html=True)
            excel_download(
                "embankment_design",
                {"หลังคันทาง (m)": formation_w, "H (m)": height, "ลาดข้าง": slope, "γ ถม": fill_gamma, "c (kPa)": cohesion, "φ (deg)": phi, "γ ฐาน": sub_gamma, "Df (m)": embed, "B (m)": bearing_w, "FS": fos, "Pb (kPa)": applied},
                result,
            )

    with tab_ditch:
        c1, c2, c3 = st.columns(3)
        with c1:
            length = st.number_input("ความยาวพื้นที่รับน้ำ (กม.)", .1, 100.0, 2.0, .1)
            width = st.number_input("ความกว้างพื้นที่รับน้ำ (ม.)", 1.0, 1000.0, 40.0, 1.0)
            intensity = st.number_input("ความเข้มฝน I (มม./ชม.)", 1.0, 500.0, 117.3, 1.0)
            runoff = st.number_input("สัมประสิทธิ์การไหลนอง C", 0.05, 1.0, .37, .01)
        with c2:
            n = st.number_input("Manning n", .005, .2, .03, .005, format="%.3f")
            slope_d = st.number_input("ความลาดชัน S", .0001, .2, .01, .001, format="%.4f")
            bottom = st.number_input("ท้องราง B (ม.)", .1, 20.0, .6, .1)
            z = st.number_input("ลาดข้าง z (H:V)", .0, 10.0, 1.0, .25)
            result = drainage_design(length, width, intensity, runoff, n, slope_d, bottom, z)
        with c3:
            st.metric("อัตราการไหล Q", f'{result["design_discharge_m3s"]:.3f} m³/s')
            st.metric("ความลึกน้ำ y", f'{result["flow_depth_m"]:.2f} ม.')
            st.metric("ความลึกรวม h", f'{result["total_depth_m"]:.2f} ม.')
            st.metric("ความกว้างปากราง T", f'{result["top_width_m"]:.2f} ม.')
            st.metric("ความเร็ว V", f'{result["velocity_mps"]:.2f} m/s')
        figure(
            dg.ditch_diagram(bottom, z, result["flow_depth_m"], result["total_depth_m"], result["top_width_m"]),
            "รางระบายน้ำเปิดรูปสี่เหลี่ยมคางหมู ท้องราง B ลาดข้าง 1:z ความลึกน้ำ y และระยะเผื่อพ้นน้ำ (freeboard)",
        )
        d1, d2 = st.columns([1, 1])
        with d1:
            result_status("ไม่ตกตะกอน", result["sedimentation_ok"], "V ≥ 0.76 m/s")
            result_status("ไม่กัดเซาะ", result["erosion_ok"], "V ≤ 1.52 m/s")
        with d2:
            st.markdown('<div class="formula">Q = 0.278CIA · Q = (1/n)AR^(2/3)S^(1/2)</div>', unsafe_allow_html=True)
        excel_download("ditch_design", {"L (km)": length, "width (m)": width, "I": intensity, "C": runoff, "n": n, "S": slope_d, "B": bottom, "z": z}, result)


elif page == "sleeper":
    heading("วิเคราะห์ราง–หมอน–หินโรยทาง", "ตรวจแรงเค้นในราง แรงถ่ายทอด และแรงกดบนชั้นหินโรยทางกับพื้นทาง")
    c1, c2, c3 = st.columns(3)
    with c1:
        rail = st.selectbox("ขนาดราง", list(RAIL_PROPERTIES), index=list(RAIL_PROPERTIES).index("BS 100 A"))
        ballast_c = st.number_input("สัมประสิทธิ์หินโรยทาง c (กก./ซม.³)", 1.0, 100.0, 10.0, 1.0)
        axle = st.number_input("น้ำหนักกดเพลา P (ตัน)", 1.0, 40.0, 20.0, 1.0)
        speed = st.number_input("ความเร็วสูงสุด (กม./ชม.)", 10.0, 250.0, 120.0, 5.0)
    with c2:
        sw = st.number_input("ความกว้างหมอน b (ซม.)", 10.0, 50.0, 25.0, 1.0)
        sl = st.number_input("ความยาวหมอน l (ซม.)", 100.0, 300.0, 200.0, 5.0)
        spacing = st.number_input("ระยะห่างหมอน a (ซม.)", 30.0, 100.0, 60.0, 5.0)
        thickness = st.number_input("ความหนาหินโรยทาง h (ซม.)", 10.0, 100.0, 25.0, 5.0)
        result = sleeper_track_analysis(rail, ballast_c, axle, sw, sl, spacing, thickness, speed)
    with c3:
        st.metric("แรงเค้นในราง σ", f'{result["rail_stress_ton_cm2"]:.3f} ตัน/ซม.²')
        st.metric("แรงสู่หมอน Prs", f'{result["rail_to_sleeper_ton"]:.2f} ตัน')
        st.metric("แรงกดหินโรยทาง Ps", f'{result["ballast_pressure_ton_m2"]:.2f} ตัน/ม.²')
        st.metric("แรงกดพื้นทาง Pb", f'{result["formation_pressure_ton_m2"]:.2f} ตัน/ม.²')
    figure(
        dg.sleeper_diagram(f"h = {thickness:.0f} ซม."),
        "รูปตัดโครงสร้างทาง: ราง–หมอน–หินโรยทาง–พื้นทาง และการกระจายแรงจากล้อลงสู่ชั้นล่าง",
    )
    s1, s2 = st.columns([1, 1])
    with s1:
        result_status("แรงเค้นราง", result["rail_stress_ok"], "σa = 2.36 ตัน/ซม.²")
        result_status("หินโรยทาง", result["ballast_pressure_ok"], "Psa = 30 ตัน/ม.²")
        result_status("พื้นทาง", result["formation_pressure_ok"], "Pba = 15 ตัน/ม.²")
    with s2:
        excel_download("track_structure", {"rail": rail, "c": ballast_c, "axle": axle, "speed": speed, "b": sw, "l": sl, "spacing": spacing, "h": thickness}, result)


elif page == "turnout_geometry":
    heading("เรขาคณิตประแจ", "คำนวณมุมตะเฆ้ Theoretical lead และความยาวชุดประแจ")
    left, right = st.columns([1, 1.35], gap="large")
    with left:
        number = st.number_input("เบอร์ประแจ 1:N", 4.0, 40.0, 12.0, 1.0)
        straight = st.number_input("ทางตรงก่อนถึงจุด C (มม.)", 0.0, 5000.0, 1000.0, 50.0)
        radius = st.number_input("รัศมีโค้งประแจ (มม.)", 50000.0, 2000000.0, 264500.0, 500.0)
        tail = st.number_input("TNC ถึงท้ายตะเฆ้ e (มม.)", 0.0, 20000.0, 3252.0, 10.0)
        result = turnout_geometry(number, straight, radius, tail)
    with right:
        figure(
            dg.turnout_plan_diagram(number, theoretical=True),
            f"ผังเรขาคณิตประแจ 1:{number:g} มุมตะเฆ้ θ = 2·atan(0.5/N)",
        )
        a, b = st.columns(2)
        a.metric("มุมตะเฆ้", f'{result["crossing_angle_deg"]:.4f}°')
        b.metric("PC–PI", f'{result["tangent_pc_pi_mm"]:,.0f} มม.')
        a.metric("Projection โค้ง", f'{result["curve_projection_mm"]:,.0f} มม.')
        b.metric("Lead เบื้องต้น", f'{result["preliminary_lead_mm"]:,.0f} มม.')
        st.info("Lead เบื้องต้นใช้ตรวจเรขาคณิตขั้นต้น ความยาวชุดประแจจริงต้องใช้มิติ switch panel, closure panel และ crossing panel จากแบบที่อนุมัติ")
        st.markdown('<div class="formula">θ = 2atan(0.5/N) · T = C/sinθ · Lead₀ = Rsinθ + Ccosθ</div>', unsafe_allow_html=True)
        excel_download("turnout_geometry", {"N": number, "C (mm)": straight, "R (mm)": radius, "e (mm)": tail}, result)


elif page == "transition":
    heading("โค้งต่อและโค้งกลม", "คำนวณความยาวโค้งต่อ ระยะ Shift และ Chainage ของ TS–SC–CS–ST")
    left, right = st.columns([1, 1.45], gap="large")
    with left:
        delta = st.number_input("มุมเบี่ยงเบน Δ (องศา)", .1, 179.0, 20.376667, .1, format="%.6f")
        radius = st.number_input("รัศมีโค้ง R (ม.)", 50.0, 10000.0, 600.0, 10.0)
        speed = st.number_input("ความเร็วออกแบบ V (กม./ชม.)", 10.0, 250.0, 80.0, 5.0)
        pi_ch = st.number_input("Chainage PI (ม.)", 0.0, 5000000.0, 700514.123, 10.0, format="%.3f")
        result = transition_curve(delta, radius, speed, pi_ch)
    with right:
        figure(
            dg.transition_plan_diagram(delta),
            "แนวเส้นทาง: ทางตรง–โค้งต่อ (spiral)–โค้งกลม–โค้งต่อ–ทางตรง พร้อมจุด TS · SC · CS · ST",
        )
        a, b, c = st.columns(3)
        a.metric("ค่ายกจริง", f'{result["actual_cant_mm"]:.0f} มม.')
        b.metric("โค้งต่อ Ls", f'{result["transition_length_m"]:.2f} ม.')
        c.metric("Shift", f'{result["shift_m"]:.3f} ม.')
        chainages = pd.DataFrame({"จุด": ["TS", "SC", "CS", "ST"], "Chainage (m)": [result["ts_chainage_m"], result["sc_chainage_m"], result["cs_chainage_m"], result["st_chainage_m"]]})
        st.dataframe(chainages.style.format({"Chainage (m)": "{:,.3f}"}), hide_index=True, use_container_width=True)
        st.markdown('<div class="formula">Ls = 0.01VCa · Shift = Ls²/(24R)</div>', unsafe_allow_html=True)
        excel_download("transition_curve", {"delta": delta, "R": radius, "V": speed, "PI": pi_ch}, result)


elif page == "widening":
    heading("การขยายขนาดทางจากราง", "ตรวจระยะทางตรงระหว่างชุดประแจและเรขาคณิตจากมุม 1:N")
    left, right = st.columns([1, 1.35], gap="large")
    with left:
        number = st.number_input("มุมประแจ 1:N", 4.0, 40.0, 12.0, 1.0)
        track_distance = st.number_input("ระยะระหว่างแนวทาง (ม.)", 2.0, 20.0, 4.4, .1)
        speed = st.number_input("ความเร็ว (กม./ชม.)", 10.0, 200.0, 50.0, 5.0)
        track_width = st.number_input("Track width W (มม.)", 900.0, 2000.0, 1500.0, 10.0)
        hd = st.number_input("Cant deficiency ที่ยอมให้ (มม.)", 10.0, 200.0, 90.0, 5.0)
        result = track_widening(number, track_distance, speed, track_width, hd)
    with right:
        figure(
            dg.widening_plan_diagram(number, f"{track_distance:g} m"),
            "ผังการขยายขนาดทางด้วยชุดประแจสองชุด (crossover) ระหว่างแนวทางขนาน",
        )
        a, b, c = st.columns(3)
        a.metric("รัศมีใช้คำนวณ", f'{result["radius_m"]:.0f} ม.')
        b.metric("ระยะทางตรงที่มี", f'{result["available_straight_m"]:.2f} ม.')
        c.metric("ระยะที่ต้องการ", f'{result["required_straight_m"]:.2f} ม.')
        result_status("เรขาคณิตทางตรง", result["geometry_ok"], "ต้องไม่น้อยกว่า 0.2V")
        st.dataframe(pd.DataFrame({"รายการ": ["มุมประแจ", "Throw", "Tangent", "แนวทแยง"], "ค่า": [f'{result["angle_deg"]:.3f}°', f'{result["throw_m"]:.3f} m', f'{result["tangent_m"]:.3f} m', f'{result["diagonal_m"]:.3f} m']}), hide_index=True, use_container_width=True)
        excel_download("track_widening", {"N": number, "distance": track_distance, "V": speed, "W": track_width, "hd": hd}, result)

st.markdown("---")
st.caption("หมายเหตุ: ผลคำนวณเป็นเครื่องมือช่วยงานวิศวกรรม ต้องตรวจสอบข้อมูลสำรวจ แบบ มาตรฐานฉบับปัจจุบัน และให้วิศวกรผู้รับผิดชอบทบทวนก่อนนำไปใช้จริง")
