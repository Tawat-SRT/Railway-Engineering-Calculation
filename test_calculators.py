import unittest

from calculators import (
    bearing_capacity_factors,
    cant_calculation,
    drainage_design,
    embankment_design,
    sleeper_track_analysis,
    turnout_speed,
    track_widening,
)


class CalculatorWorkbookParityTests(unittest.TestCase):
    def test_turnout_speed_matches_workbook(self):
        result = turnout_speed(265, 50, 1067)
        self.assertEqual(result["design_speed_kmh"], 40)

    def test_drainage_matches_workbook(self):
        result = drainage_design(2, 40, 117.3, 0.37, 0.03, 0.01, 0.6, 1)
        self.assertAlmostEqual(result["design_discharge_m3s"], 0.96523824, places=8)
        self.assertTrue(0.55 < result["flow_depth_m"] < 0.65)

    def test_sleeper_matches_workbook(self):
        result = sleeper_track_analysis("BS 100 A", 10, 20, 25, 200, 60, 25, 120)
        self.assertAlmostEqual(result["rail_stress_ton_cm2"], 1.72775, places=3)
        self.assertAlmostEqual(result["formation_pressure_ton_m2"], 12.4373, places=2)

    def test_cant_example(self):
        result = cant_calculation(1600, 120, 55)
        self.assertEqual(result["equilibrium_cant_mm"], 75)
        self.assertEqual(result["vmax_kmh"], 140)

    def test_track_widening_matches_workbook(self):
        result = track_widening(12, 4.4, 50, 1500, 90)
        self.assertEqual(result["radius_m"], 330)
        self.assertAlmostEqual(result["available_straight_m"], 25.5306, places=2)

    def test_bearing_capacity_factors_textbook(self):
        f = bearing_capacity_factors(30)
        self.assertAlmostEqual(f["Nc"], 30.14, places=1)
        self.assertAlmostEqual(f["Nq"], 18.40, places=1)
        self.assertAlmostEqual(f["Ngamma"], 22.40, places=1)
        f0 = bearing_capacity_factors(0)
        self.assertEqual(f0["Nc"], 5.14)
        self.assertEqual(f0["Nq"], 1.0)

    def test_embankment_geometry_and_bearing(self):
        result = embankment_design(
            formation_width_m=6.0,
            embankment_height_m=5.0,
            side_slope_h_per_v=1.5,
            fill_unit_weight_knm3=18.0,
            subgrade_cohesion_kpa=20.0,
            subgrade_friction_deg=28.0,
            subgrade_unit_weight_knm3=18.0,
            applied_formation_pressure_kpa=122.0,
            bearing_width_m=2.0,
            factor_of_safety=3.0,
        )
        self.assertAlmostEqual(result["base_width_m"], 21.0, places=3)
        self.assertAlmostEqual(result["cross_section_area_m2"], 67.5, places=3)
        self.assertTrue(result["allowable_bearing_kpa"] > 122.0)
        self.assertTrue(result["bearing_ok"])


if __name__ == "__main__":
    unittest.main()
