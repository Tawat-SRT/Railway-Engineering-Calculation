"""Pure railway engineering calculation functions derived from the source workbook."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import atan, cos, exp, floor, pi, radians, sin, sqrt, tan

import numpy as np


RAIL_PROPERTIES = {
    "50 RSR": {"I": 550.30, "Z": 98.30, "area": 3203.00, "mass": 24.80},
    "BS 60 R": {"I": 680.85, "Z": 115.98, "area": 3798.92, "mass": 29.882},
    "60 ASCE": {"I": 607.70, "Z": 108.75, "area": 3825.80, "mass": 29.76},
    "70 ASCE": {"I": 819.97, "Z": 137.58, "area": 4393.54, "mass": 34.49},
    "BS 70 R": {"I": 922.79, "Z": 143.06, "area": 4437.41, "mass": 34.72},
    "BS 70 A": {"I": 911.96, "Z": 145.96, "area": 4438.69, "mass": 34.84},
    "BS 80 A": {"I": 1209.15, "Z": 178.29, "area": 5070.95, "mass": 39.80},
    "BS 100 A": {"I": 1961.00, "Z": 252.42, "area": 6392.61, "mass": 50.182},
    "54E1": {"I": 2338.00, "Z": 278.70, "area": 6977.00, "mass": 54.77},
    "60E1": {"I": 3038.00, "Z": 333.60, "area": 7670.00, "mass": 60.21},
}


def string_lining_calculation(
    original_versines: list[float],
    revised_versines: list[float],
    baseline_offset_mm: float = 500,
) -> dict:
    """Calculate string-lining throws using the cumulative summation method in the workbook.

    Columns follow the source workbook:
    difference = original - revised
    cumulative difference = previous cumulative + difference
    half throw = previous half throw + previous cumulative difference
    throw = 2 * half throw
    rail-to-centre = baseline - throw
    """
    if len(original_versines) != len(revised_versines):
        raise ValueError("Original and revised versine lists must have equal length")
    if not original_versines:
        raise ValueError("At least one station is required")

    rows = []
    previous_cumulative = 0.0
    previous_half_throw = 0.0
    for index, (original, revised) in enumerate(zip(original_versines, revised_versines), start=1):
        original = float(original)
        revised = float(revised)
        difference = original - revised
        cumulative = previous_cumulative + difference
        half_throw = previous_half_throw + previous_cumulative
        throw = 2 * half_throw
        rows.append(
            {
                "station": index,
                "original_versine_mm": original,
                "revised_versine_mm": revised,
                "difference_mm": difference,
                "cumulative_difference_mm": cumulative,
                "half_throw_mm": half_throw,
                "throw_mm": throw,
                "rail_to_centre_mm": baseline_offset_mm - throw,
            }
        )
        previous_cumulative = cumulative
        previous_half_throw = half_throw

    sum_original = sum(float(v) for v in original_versines)
    sum_revised = sum(float(v) for v in revised_versines)
    max_abs_throw = max(abs(row["throw_mm"]) for row in rows)
    return {
        "rows": rows,
        "sum_original_mm": sum_original,
        "sum_revised_mm": sum_revised,
        "sum_difference_mm": sum_original - sum_revised,
        "final_cumulative_difference_mm": rows[-1]["cumulative_difference_mm"],
        "final_half_throw_mm": rows[-1]["half_throw_mm"],
        "max_abs_throw_mm": max_abs_throw,
        "sum_balanced": abs(sum_original - sum_revised) < 1e-9,
        "cumulative_closed": abs(rows[-1]["cumulative_difference_mm"]) < 1e-9,
        "throw_closed": abs(rows[-1]["half_throw_mm"]) < 1e-9,
        "end_versines_zero": abs(float(revised_versines[0])) < 1e-9
        and abs(float(revised_versines[-1])) < 1e-9,
        "throw_within_working_range": max_abs_throw <= 120,
        "throw_within_document_limit": max_abs_throw <= 200,
    }


def theoretical_versine_profile(
    straight_before_pins: int,
    entry_transition_pins: int,
    circular_pins: int,
    exit_transition_pins: int,
    straight_after_pins: int,
    maximum_versine_mm: float,
) -> list[float]:
    """Create a rounded arithmetic-progression profile as an editable starting point."""
    profile = [0.0] * max(straight_before_pins, 0)
    if entry_transition_pins > 0:
        profile.extend(
            round(maximum_versine_mm * i / entry_transition_pins)
            for i in range(1, entry_transition_pins + 1)
        )
    profile.extend([round(maximum_versine_mm)] * max(circular_pins, 0))
    if exit_transition_pins > 0:
        profile.extend(
            round(maximum_versine_mm * (exit_transition_pins - i) / exit_transition_pins)
            for i in range(1, exit_transition_pins + 1)
        )
    profile.extend([0.0] * max(straight_after_pins, 0))
    return [float(v) for v in profile]


def improve_string_lining_versines(
    original_versines: list[float],
    current_revised_versines: list[float],
    maximum_throw_mm: float = 120,
) -> dict:
    """Improve revised versines while enforcing the two string-lining closure equations.

    The solution is the smallest least-squares correction to the current revised
    profile. If its throw exceeds the selected working limit, the profile is
    progressively blended toward the measured versines and projected again.
    End versines are fixed at zero throughout.
    """
    old = np.asarray(original_versines, dtype=float)
    current = np.asarray(current_revised_versines, dtype=float)
    if old.shape != current.shape or old.ndim != 1:
        raise ValueError("Original and revised versines must be equal one-dimensional lists")
    if len(old) < 4:
        raise ValueError("At least four stations are required for automatic improvement")

    n = len(old)
    weights = np.arange(n - 1, -1, -1, dtype=float)
    interior = np.arange(1, n - 1)
    a = np.vstack([np.ones(len(interior)), weights[interior]])
    b = np.array([old.sum(), np.dot(weights, old)], dtype=float)
    gram_inverse = np.linalg.pinv(a @ a.T)

    def project(base: np.ndarray) -> np.ndarray:
        candidate = base.copy()
        candidate[0] = 0.0
        candidate[-1] = 0.0
        x = candidate[interior]
        x = x + a.T @ gram_inverse @ (b - a @ x)
        candidate[interior] = x
        return candidate

    # A low-throw closure reference: retain measured versines except for the
    # two stations next to the ends, which absorb the endpoint corrections.
    closure_difference = np.zeros(n, dtype=float)
    closure_difference[0] = old[0]
    closure_difference[-1] = old[-1]
    closure_difference[1] = (old[-1] - (n - 2) * old[0]) / (n - 3)
    closure_difference[-2] = -(old[0] + old[-1]) - closure_difference[1]
    closure_reference = old - closure_difference

    selected = project(current)
    blend_used = 0.0
    selected_result = string_lining_calculation(old.tolist(), selected.tolist())
    if selected_result["max_abs_throw_mm"] > maximum_throw_mm:
        for blend in np.linspace(0.01, 1.0, 100):
            base = (1 - blend) * current + blend * closure_reference
            candidate = project(base)
            candidate_result = string_lining_calculation(old.tolist(), candidate.tolist())
            selected = candidate
            selected_result = candidate_result
            blend_used = float(blend)
            if candidate_result["max_abs_throw_mm"] <= maximum_throw_mm:
                break

    selected[np.abs(selected) < 1e-10] = 0.0
    return {
        "revised_versines": selected.tolist(),
        "blend_used": blend_used,
        "maximum_throw_mm": selected_result["max_abs_throw_mm"],
        "sum_closed": selected_result["sum_balanced"],
        "moment_closed": selected_result["throw_closed"],
    }


def round_to(value: float, increment: float = 5.0) -> float:
    return round(value / increment) * increment


def floor_to(value: float, increment: float = 5.0) -> float:
    return floor(value / increment) * increment


def cant_calculation(radius_m: float, speed_kmh: float, actual_cant_mm: float | None = None) -> dict:
    coefficient = 8.416  # workbook constant for 1,070 mm rail-centre distance
    equilibrium = round_to(coefficient * speed_kmh**2 / radius_m, 5)
    recommended = round_to(min(5.611 * (speed_kmh + 5) ** 2 / radius_m, 90), 5)
    actual = recommended if actual_cant_mm is None else actual_cant_mm
    deficiency = max(equilibrium - actual, 0)
    excess = max(actual - equilibrium, 0)
    minimum_cant = round_to(equilibrium - 50, 5)
    vmax = round_to(sqrt(max(actual + 50, 0) * radius_m / coefficient), 5)
    vmin = round_to(sqrt(max(actual - 60, 0) * radius_m / coefficient), 5)
    return {
        "equilibrium_cant_mm": equilibrium,
        "recommended_cant_mm": recommended,
        "actual_cant_mm": actual,
        "cant_deficiency_mm": deficiency,
        "cant_excess_mm": excess,
        "minimum_cant_mm": minimum_cant,
        "vmax_kmh": vmax,
        "vmin_kmh": vmin,
        "deficiency_ok": deficiency <= 50,
        "excess_ok": excess <= 60,
    }


def turnout_speed(radius_m: float, cant_deficiency_mm: float = 50, gauge_mm: float = 1067) -> dict:
    lateral_acceleration = 9.81 * cant_deficiency_mm / gauge_mm
    limit = sqrt(lateral_acceleration * radius_m) * 3.6
    rounded_limit = round(limit)
    return {
        "lateral_acceleration_mps2": lateral_acceleration,
        "limit_speed_kmh": rounded_limit,
        "design_speed_kmh": floor_to(rounded_limit, 5),
    }


def drainage_design(
    length_km: float,
    catchment_width_m: float,
    intensity_mm_hr: float,
    runoff_coefficient: float,
    manning_n: float,
    slope: float,
    bottom_width_m: float,
    side_slope_z: float,
    freeboard_ratio: float = 0.2,
) -> dict:
    area_m2 = length_km * 1000 * catchment_width_m
    discharge = 0.278 * runoff_coefficient * intensity_mm_hr * area_m2 * 1e-6

    def capacity(depth: float) -> float:
        flow_area = depth * (bottom_width_m + side_slope_z * depth)
        wetted = bottom_width_m + 2 * depth * sqrt(1 + side_slope_z**2)
        hydraulic_radius = flow_area / wetted
        return (1 / manning_n) * flow_area * hydraulic_radius ** (2 / 3) * sqrt(slope)

    low, high = 0.0001, 0.2
    while capacity(high) < discharge and high < 20:
        high *= 2
    for _ in range(100):
        mid = (low + high) / 2
        if capacity(mid) < discharge:
            low = mid
        else:
            high = mid
    depth = high
    flow_area = depth * (bottom_width_m + side_slope_z * depth)
    velocity = discharge / flow_area
    freeboard = max(round(depth * freeboard_ratio, 1), 0.1)
    total_depth = depth + freeboard
    top_width = bottom_width_m + 2 * side_slope_z * total_depth
    return {
        "catchment_area_m2": area_m2,
        "design_discharge_m3s": discharge,
        "flow_depth_m": depth,
        "flow_area_m2": flow_area,
        "velocity_mps": velocity,
        "freeboard_m": freeboard,
        "total_depth_m": total_depth,
        "top_width_m": top_width,
        "sedimentation_ok": velocity >= 0.76,
        "erosion_ok": velocity <= 1.52,
    }


def sleeper_track_analysis(
    rail_name: str,
    ballast_coefficient: float,
    axle_load_ton: float,
    sleeper_width_cm: float,
    sleeper_length_cm: float,
    sleeper_spacing_cm: float,
    ballast_thickness_cm: float,
    speed_kmh: float,
    sleeper_factor: float = 1.0,
    elastic_modulus_kg_cm2: float = 2.1e6,
) -> dict:
    rail = RAIL_PROPERTIES[rail_name]
    dynamic_wheel_load = 0.5 * axle_load_ton * (1 + speed_kmh / 100)
    bearing_area = sleeper_width_cm * sleeper_length_cm / 2
    u = (4 * elastic_modulus_kg_cm2 * rail["I"] * sleeper_spacing_cm / ballast_coefficient / bearing_area) ** 0.25
    beta = 1 / u
    rail_moment = dynamic_wheel_load / (4 * beta)
    rail_stress = rail_moment / rail["Z"]
    transfer_factor = 1 - exp(-beta * sleeper_spacing_cm / 2) * cos(radians(beta * sleeper_spacing_cm / 2))
    rail_to_sleeper = dynamic_wheel_load * transfer_factor
    under_sleeper = axle_load_ton / 2 * (1 + 0.6 * speed_kmh / 100) * transfer_factor
    settlement = sleeper_factor * 2 * under_sleeper * 1000 / sleeper_width_cm / sleeper_length_cm / ballast_coefficient
    ballast_pressure = ballast_coefficient * settlement * 10
    formation_pressure = 50 / (10 + ballast_thickness_cm**1.35) * ballast_pressure
    return {
        "dynamic_wheel_load_ton": dynamic_wheel_load,
        "bearing_area_cm2": bearing_area,
        "u_cm": u,
        "beta_per_cm": beta,
        "rail_moment_ton_cm": rail_moment,
        "rail_stress_ton_cm2": rail_stress,
        "rail_to_sleeper_ton": rail_to_sleeper,
        "under_sleeper_ton": under_sleeper,
        "ballast_settlement_cm": settlement,
        "ballast_pressure_ton_m2": ballast_pressure,
        "formation_pressure_ton_m2": formation_pressure,
        "rail_stress_ok": rail_stress <= 2.36,
        "ballast_pressure_ok": ballast_pressure <= 30,
        "formation_pressure_ok": formation_pressure <= 15,
    }


def turnout_geometry(number: float, straight_before_mm: float, radius_mm: float, frog_tail_mm: float) -> dict:
    angle_rad = 2 * atan(0.5 / number)
    angle_deg = angle_rad * 180 / pi
    tangent_pc_pi = straight_before_mm / sin(angle_rad)
    curve_projection = radius_mm * sin(angle_rad)
    straight_projection = straight_before_mm * cos(angle_rad)
    preliminary_lead = curve_projection + straight_projection
    return {
        "crossing_angle_rad": angle_rad,
        "crossing_angle_deg": angle_deg,
        "tangent_pc_pi_mm": tangent_pc_pi,
        "curve_projection_mm": curve_projection,
        "straight_projection_mm": straight_projection,
        "preliminary_lead_mm": preliminary_lead,
        "lead_plus_frog_tail_mm": preliminary_lead + frog_tail_mm,
    }


def transition_curve(delta_deg: float, radius_m: float, speed_kmh: float, pi_chainage_m: float) -> dict:
    actual_cant = round_to(5.5587 * (speed_kmh + 5) ** 2 / radius_m, 5)
    transition_length = round_to(0.01 * speed_kmh * actual_cant, 5)
    shift = transition_length**2 / (24 * radius_m)
    tangent = (radius_m + shift) * tan(radians(delta_deg) / 2) + transition_length / 2
    total_arc = radius_m * radians(delta_deg)
    circular_arc = total_arc - transition_length
    return {
        "actual_cant_mm": actual_cant,
        "transition_length_m": transition_length,
        "shift_m": shift,
        "tangent_length_m": tangent,
        "total_arc_m": total_arc,
        "circular_arc_m": circular_arc,
        "ts_chainage_m": pi_chainage_m - tangent,
        "sc_chainage_m": pi_chainage_m - tangent + transition_length,
        "cs_chainage_m": pi_chainage_m - tangent + transition_length + circular_arc,
        "st_chainage_m": pi_chainage_m - tangent + 2 * transition_length + circular_arc,
    }


def track_widening(
    turnout_number: float,
    distance_between_tracks_m: float,
    speed_kmh: float,
    track_width_mm: float = 1500,
    allowable_cant_deficiency_mm: float = 90,
) -> dict:
    angle = atan(1 / turnout_number)
    radius_raw = (track_width_mm / 9.8) * (speed_kmh / 3.6) ** 2 / allowable_cant_deficiency_mm
    radius = (floor(radius_raw / 10) + 1) * 10
    throw = (radius + 1.435 / 2) * (1 - cos(angle))
    tangent = radius * tan(angle / 2)
    diagonal = distance_between_tracks_m / sin(angle)
    available_straight = diagonal - 2 * tangent
    required_straight = 0.2 * speed_kmh
    return {
        "angle_deg": angle * 180 / pi,
        "radius_m": radius,
        "throw_m": throw,
        "tangent_m": tangent,
        "diagonal_m": diagonal,
        "available_straight_m": available_straight,
        "required_straight_m": required_straight,
        "geometry_ok": available_straight >= required_straight,
    }
