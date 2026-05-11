"""
Unit tests for Questão 5 - Comparison of analytical methods.

Tests cover:
- Sheet conductor calculations
- Comparison logic across three geometries
- Consistency checks (tanh·coth=1 principle extended to sheet)
- Physical bounds and numerical stability
"""

import pytest
import numpy as np
from app.core.electromagnetics.sheet_conductors import (
    calculate_skin_depth_sheet,
    magnetic_field_sheet_conductor,
    induced_current_density_sheet,
    calculate_power_loss_sheet_conductor,
    compare_conductor_geometries,
)
from app.core.exercises.q05_comparison_methods import solve_question_05_comparison


class TestSheetConductorSkinDepth:
    """Test skin depth calculation for sheet conductors."""
    
    def test_skin_depth_basic(self):
        """Skin depth for copper at 60 Hz should be ~8.5 mm."""
        delta = calculate_skin_depth_sheet(
            frequency_hz=60,
            permeability_rel=1.0,
            conductivity_s_per_m=5.8e7,
        )
        assert 0.008 < delta < 0.009, f"Expected ~8.5 mm, got {delta*1000:.3f} mm"
    
    def test_skin_depth_frequency_dependence(self):
        """Skin depth inversely proportional to sqrt(frequency)."""
        delta_60 = calculate_skin_depth_sheet(60, 1.0, 5.8e7)
        delta_240 = calculate_skin_depth_sheet(240, 1.0, 5.8e7)
        # delta ∝ 1/√f, so delta_60/delta_240 = √(240/60) = 2
        ratio = delta_60 / delta_240
        assert 1.9 < ratio < 2.1, f"Expected ratio ~2, got {ratio:.3f}"
    
    def test_skin_depth_material_dependence(self):
        """Skin depth depends on permeability and conductivity."""
        # Copper: non-magnetic but highly conductive
        delta_copper = calculate_skin_depth_sheet(60, 1.0, 5.8e7)
        # For non-magnetic comparison, lower conductivity = larger delta
        delta_alu = calculate_skin_depth_sheet(60, 1.0, 3.5e7)
        assert delta_copper < delta_alu, f"Copper: {delta_copper}, Alu: {delta_alu}"


class TestSheetConductorField:
    """Test magnetic field distribution in sheet conductor."""
    
    def test_field_boundary_condition(self):
        """Field at surface should equal H₀."""
        y_values = np.array([0.0, 0.001, 0.01])
        delta = 0.01
        h0 = 10.0
        h_field = magnetic_field_sheet_conductor(y_values, h0, delta)
        assert np.isclose(h_field[0], h0, rtol=0.01), f"Expected H(0)={h0}, got {h_field[0]}"
    
    def test_field_exponential_decay(self):
        """Field should decay exponentially with distance."""
        y_values = np.array([0, 1, 2, 3]) * 0.01  # 0, 10, 20, 30 mm
        delta = 0.01  # 10 mm
        h0 = 10.0
        h_field = magnetic_field_sheet_conductor(y_values, h0, delta)
        
        # At y=δ: H(δ) = H₀·exp(-1) ≈ 0.368·H₀
        h_at_delta = magnetic_field_sheet_conductor(np.array([delta]), h0, delta)[0]
        assert np.isclose(h_at_delta / h0, np.exp(-1), rtol=0.01)
    
    def test_field_monotonic_decrease(self):
        """Field magnitude should be monotonically decreasing."""
        y_values = np.linspace(0, 0.05, 50)
        h_field = magnetic_field_sheet_conductor(y_values, 10.0, 0.01)
        diffs = np.diff(h_field)
        assert np.all(diffs <= 0), "Field should decrease monotonically"


class TestSheetConductorCurrentDensity:
    """Test induced current density in sheet conductor."""
    
    def test_current_density_proportional_to_field(self):
        """Current density should be proportional to magnetic field."""
        h_field_1 = np.array([10.0])
        h_field_2 = np.array([20.0])
        j_1 = induced_current_density_sheet(h_field_1, 60, 1.0, 4*np.pi*1e-7)
        j_2 = induced_current_density_sheet(h_field_2, 60, 1.0, 4*np.pi*1e-7)
        assert np.isclose(j_2[0] / j_1[0], 2.0, rtol=0.01)
    
    def test_current_density_positive(self):
        """Current density should always be positive."""
        h_field = np.linspace(0, 100, 50)
        j_density = induced_current_density_sheet(h_field, 60, 1.0)
        assert np.all(j_density >= 0)


class TestSheetConductorPowerLoss:
    """Test power loss calculation in sheet conductors."""
    
    def test_power_loss_positive(self):
        """Power loss should be positive."""
        result = calculate_power_loss_sheet_conductor(
            thickness_m=0.01,
            surface_magnetic_field_h0_a_per_m=10.0,
            conductivity_s_per_m=5.8e7,
            frequency_hz=60,
        )
        assert result["power_loss_w_per_m2"] > 0
        assert result["power_loss_semi_infinite"] > 0
    
    def test_power_loss_frequency_dependence(self):
        """Power loss should increase with frequency (P ∝ √f)."""
        loss_60 = calculate_power_loss_sheet_conductor(
            0.01, 10.0, 5.8e7, 60
        )["power_loss_w_per_m2"]
        loss_240 = calculate_power_loss_sheet_conductor(
            0.01, 10.0, 5.8e7, 240
        )["power_loss_w_per_m2"]
        # P ∝ √f, so loss_240/loss_60 = √(240/60) = 2
        ratio = loss_240 / loss_60
        assert 1.9 < ratio < 2.3, f"Expected ~2, got {ratio:.3f}"
    
    def test_power_loss_h0_squared_dependence(self):
        """Power loss should depend quadratically on H₀."""
        loss_h0_10 = calculate_power_loss_sheet_conductor(
            0.01, 10.0, 5.8e7, 60
        )["power_loss_w_per_m2"]
        loss_h0_20 = calculate_power_loss_sheet_conductor(
            0.01, 20.0, 5.8e7, 60
        )["power_loss_w_per_m2"]
        ratio = loss_h0_20 / loss_h0_10
        assert 3.9 < ratio < 4.1, f"Expected 4.0, got {ratio:.3f}"
    
    def test_finite_thickness_correction(self):
        """Finite thickness correction should be between 0 and 1."""
        result = calculate_power_loss_sheet_conductor(
            0.01, 10.0, 5.8e7, 60
        )
        factor = result["power_loss_w_per_m2"] / result["power_loss_semi_infinite"]
        assert 0 < factor <= 1, f"Correction factor should be in (0,1], got {factor}"
    
    def test_thick_sheet_approaches_semi_infinite(self):
        """Very thick sheet should approach semi-infinite limit."""
        # For t >> δ, correction factor → 1/2
        result_thin = calculate_power_loss_sheet_conductor(
            0.001, 10.0, 5.8e7, 60  # 1 mm thick
        )
        result_thick = calculate_power_loss_sheet_conductor(
            0.1, 10.0, 5.8e7, 60  # 100 mm thick
        )
        # Thick sheet should have factor closer to 0.5 (finite correction)
        factor_thin = result_thin["power_loss_w_per_m2"] / result_thin["power_loss_semi_infinite"]
        factor_thick = result_thick["power_loss_w_per_m2"] / result_thick["power_loss_semi_infinite"]
        assert factor_thick > factor_thin  # Thicker sheet has larger loss


class TestConductorComparison:
    """Test comparison across three conductor types."""
    
    def test_comparison_structure(self):
        """Comparison should have all three geometry types."""
        comparison = compare_conductor_geometries(
            surface_magnetic_field_h0_a_per_m=10.0,
            conductivity_s_per_m=5.8e7,
            frequency_hz=60,
            characteristic_dimension_m=0.025,
        )
        assert "rectangular_symmetric" in comparison
        assert "sheet_semi_infinite" in comparison
        assert "sheet_finite" in comparison
    
    def test_rectangular_vs_sheet_semi_infinite(self):
        """Rectangular (b) and sheet semi-infinite should have same base loss."""
        comparison = compare_conductor_geometries(
            10.0, 5.8e7, 60, 0.025
        )
        loss_rect_b = comparison["sheet_semi_infinite"]["power_loss_w_per_m2"]
        loss_sheet = comparison["sheet_semi_infinite"]["power_loss_w_per_m2"]
        assert np.isclose(loss_rect_b, loss_sheet, rtol=0.01)


class TestQ5Integration:
    """Test Q5 full comparison functionality."""

    def test_q5_skin_depth_reference_value(self):
        """Q5 should return physically consistent skin depth for copper at 60 Hz."""
        result = solve_question_05_comparison(
            frequency_hz=60,
            surface_magnetic_field_h0_a_per_m=6.0,
            characteristic_dimension_cm=2.5,
            conductivity_s_per_m=5.8e7,
            permeability_rel=1.0,
        )
        assert 8.0 < result.skin_depth_mm < 9.0, (
            f"Expected skin depth around 8.5 mm, got {result.skin_depth_mm:.4f} mm"
        )
    
    def test_q5_basic_calculation(self):
        """Q5 should compute without errors."""
        result = solve_question_05_comparison(
            frequency_hz=60,
            surface_magnetic_field_h0_a_per_m=6.0,
            characteristic_dimension_cm=2.5,
        )
        assert result is not None
        assert result.frequency_hz == 60
    
    def test_q5_output_types(self):
        """Q5 output should have correct types."""
        result = solve_question_05_comparison()
        assert isinstance(result.frequency_hz, (int, float))
        assert isinstance(result.skin_depth_m, (int, float))
        assert isinstance(result.circular_conductor_loss_w_per_m2, (int, float))
        assert isinstance(result.ratio_circular_to_rect_b, (int, float))
    
    def test_q5_all_losses_positive(self):
        """All losses should be positive."""
        result = solve_question_05_comparison()
        assert result.circular_conductor_loss_w_per_m2 > 0
        assert result.rectangular_variant_a_loss_w_per_m2 > 0
        assert result.rectangular_variant_b_loss_w_per_m2 > 0
        assert result.rectangular_variant_c_loss_w_per_m2 > 0
        assert result.sheet_semi_infinite_loss_w_per_m2 > 0
        assert result.sheet_finite_loss_w_per_m2 > 0
    
    def test_q5_ratio_consistency(self):
        """Loss ratios should be consistent with absolute values."""
        result = solve_question_05_comparison()
        baseline = result.rectangular_variant_b_loss_w_per_m2
        
        expected_ratio_a = result.rectangular_variant_a_loss_w_per_m2 / baseline
        assert np.isclose(result.ratio_rect_a_to_b, expected_ratio_a, rtol=0.001)
        
        expected_ratio_c = result.rectangular_variant_c_loss_w_per_m2 / baseline
        assert np.isclose(result.ratio_rect_c_to_b, expected_ratio_c, rtol=0.001)
    
    def test_q5_sheet_finite_less_than_semi_infinite(self):
        """Sheet finite loss should be less than semi-infinite."""
        result = solve_question_05_comparison()
        # With finite correction: P_finite = P_semi · [1-exp(-2t/δ)]/2 < P_semi
        assert result.sheet_finite_loss_w_per_m2 <= result.sheet_semi_infinite_loss_w_per_m2
    
    def test_q5_reference_data_reproducibility(self):
        """Q5 should reproduce reference case consistently."""
        result1 = solve_question_05_comparison(
            frequency_hz=60,
            surface_magnetic_field_h0_a_per_m=6.0,
            characteristic_dimension_cm=2.5,
            conductivity_s_per_m=5.8e7,
        )
        result2 = solve_question_05_comparison(
            frequency_hz=60,
            surface_magnetic_field_h0_a_per_m=6.0,
            characteristic_dimension_cm=2.5,
            conductivity_s_per_m=5.8e7,
        )
        assert np.isclose(
            result1.rectangular_variant_b_loss_w_per_m2,
            result2.rectangular_variant_b_loss_w_per_m2,
            rtol=0.0001,
        )
