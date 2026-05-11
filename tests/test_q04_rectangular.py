"""Testes para a Questão 4 - Condutores Retangulares de Cobre."""

import numpy as np
import pytest
from app.core.exercises.q04_rectangular_conductors import (
    solve_question_04_rectangular_conductors,
)


class TestQ4ParameterDerivation:
    """Testes dos parâmetros derivados básicos."""

    def test_skin_depth_calculation(self):
        """Verifica cálculo da profundidade de penetração para cobre a 60 Hz."""
        result = solve_question_04_rectangular_conductors(
            half_width_b_cm=2.5,
            surface_magnetic_field_h0_a_per_m=6.0,
            conductivity_s_per_m=5.8e7,
            frequency_hz=60.0,
            permeability_rel=1.0,
        )
        
        # Para cobre a 60 Hz, δ deve estar entre 5-15 mm
        assert 0.005 < result.skin_depth_m < 0.015
        assert 5 < result.skin_depth_mm < 15

    def test_omega_calculation(self):
        """Verifica que ω = 2πf."""
        frequency_hz = 50.0
        result = solve_question_04_rectangular_conductors(
            half_width_b_cm=2.5,
            surface_magnetic_field_h0_a_per_m=6.0,
            conductivity_s_per_m=5.8e7,
            frequency_hz=frequency_hz,
            permeability_rel=1.0,
        )
        
        expected_omega = 2 * np.pi * frequency_hz
        assert np.isclose(result.omega_rad_s, expected_omega, rtol=0.001)

    def test_skin_depth_frequency_dependence(self):
        """Verifica que δ ∝ 1/√f."""
        result_60 = solve_question_04_rectangular_conductors(
            half_width_b_cm=2.5,
            surface_magnetic_field_h0_a_per_m=6.0,
            conductivity_s_per_m=5.8e7,
            frequency_hz=60.0,
            permeability_rel=1.0,
        )
        
        result_240 = solve_question_04_rectangular_conductors(
            half_width_b_cm=2.5,
            surface_magnetic_field_h0_a_per_m=6.0,
            conductivity_s_per_m=5.8e7,
            frequency_hz=240.0,
            permeability_rel=1.0,
        )
        
        # δ(240 Hz) / δ(60 Hz) = √(60/240) = 0.5
        ratio = result_240.skin_depth_m / result_60.skin_depth_m
        expected_ratio = np.sqrt(60.0 / 240.0)
        
        assert np.isclose(ratio, expected_ratio, rtol=0.01)


class TestVariantACalculations:
    """Testes para Variante (a) - Campo em ambas as superfícies."""

    def test_tanh_factor_range(self):
        """Verifica que tanh(b/δ) está sempre entre 0 e 1."""
        result = solve_question_04_rectangular_conductors(
            half_width_b_cm=2.5,
            surface_magnetic_field_h0_a_per_m=6.0,
            conductivity_s_per_m=5.8e7,
            frequency_hz=60.0,
            permeability_rel=1.0,
        )
        
        assert 0 < result.variant_a_hyperbolic_factor < 1.0

    def test_variant_a_power_loss_positive(self):
        """Verifica que perdas de variante (a) são positivas."""
        result = solve_question_04_rectangular_conductors(
            half_width_b_cm=2.5,
            surface_magnetic_field_h0_a_per_m=6.0,
            conductivity_s_per_m=5.8e7,
            frequency_hz=60.0,
            permeability_rel=1.0,
        )
        
        assert result.variant_a_power_loss_w_per_m2 > 0

    def test_variant_a_power_loss_proportional_to_h0_squared(self):
        """Verifica que P_a ∝ H₀²."""
        result_h6 = solve_question_04_rectangular_conductors(
            half_width_b_cm=2.5,
            surface_magnetic_field_h0_a_per_m=6.0,
            conductivity_s_per_m=5.8e7,
            frequency_hz=60.0,
            permeability_rel=1.0,
        )
        
        result_h12 = solve_question_04_rectangular_conductors(
            half_width_b_cm=2.5,
            surface_magnetic_field_h0_a_per_m=12.0,
            conductivity_s_per_m=5.8e7,
            frequency_hz=60.0,
            permeability_rel=1.0,
        )
        
        # P(12 A/m) / P(6 A/m) ≈ (12/6)² = 4
        ratio = result_h12.variant_a_power_loss_w_per_m2 / result_h6.variant_a_power_loss_w_per_m2
        expected_ratio = 4.0
        
        assert np.isclose(ratio, expected_ratio, rtol=0.01)


class TestVariantBCalculations:
    """Testes para Variante (b) - Campo em uma superfície (semi-espaço)."""

    def test_variant_b_power_loss_positive(self):
        """Verifica que perdas de variante (b) são positivas."""
        result = solve_question_04_rectangular_conductors(
            half_width_b_cm=2.5,
            surface_magnetic_field_h0_a_per_m=6.0,
            conductivity_s_per_m=5.8e7,
            frequency_hz=60.0,
            permeability_rel=1.0,
        )
        
        assert result.variant_b_power_loss_w_per_m2 > 0

    def test_variant_b_reference_case(self):
        """Verifica variante (b) com dados da questão."""
        result = solve_question_04_rectangular_conductors(
            half_width_b_cm=2.5,
            surface_magnetic_field_h0_a_per_m=6.0,
            conductivity_s_per_m=5.8e7,
            frequency_hz=60.0,
            permeability_rel=1.0,
        )
        
        # Para estes dados, P_b deve estar em ordem de ~7e-5 W/m²
        assert result.variant_b_power_loss_w_per_m2 > 1e-5
        assert result.variant_b_power_loss_w_per_m2 < 1e-3


class TestVariantCCalculations:
    """Testes para Variante (c) - Espaço finito (sanduíche)."""

    def test_coth_factor_range(self):
        """Verifica que coth(b/δ) > 1."""
        result = solve_question_04_rectangular_conductors(
            half_width_b_cm=2.5,
            surface_magnetic_field_h0_a_per_m=6.0,
            conductivity_s_per_m=5.8e7,
            frequency_hz=60.0,
            permeability_rel=1.0,
        )
        
        assert result.variant_c_hyperbolic_factor > 1.0

    def test_variant_c_power_loss_positive(self):
        """Verifica que perdas de variante (c) são positivas."""
        result = solve_question_04_rectangular_conductors(
            half_width_b_cm=2.5,
            surface_magnetic_field_h0_a_per_m=6.0,
            conductivity_s_per_m=5.8e7,
            frequency_hz=60.0,
            permeability_rel=1.0,
        )
        
        assert result.variant_c_power_loss_w_per_m2 > 0


class TestComparativeBehavior:
    """Testes de comportamento comparativo entre variantes."""

    def test_variant_relationship_tanh_plus_coth(self):
        """Verifica que tanh(x) · coth(x) = 1."""
        result = solve_question_04_rectangular_conductors(
            half_width_b_cm=2.5,
            surface_magnetic_field_h0_a_per_m=6.0,
            conductivity_s_per_m=5.8e7,
            frequency_hz=60.0,
            permeability_rel=1.0,
        )
        
        product = result.variant_a_hyperbolic_factor * result.variant_c_hyperbolic_factor
        assert np.isclose(product, 1.0, rtol=0.001)

    def test_power_loss_ratios_consistent(self):
        """Verifica que as razões de perdas estão consistentes."""
        result = solve_question_04_rectangular_conductors(
            half_width_b_cm=2.5,
            surface_magnetic_field_h0_a_per_m=6.0,
            conductivity_s_per_m=5.8e7,
            frequency_hz=60.0,
            permeability_rel=1.0,
        )
        
        # Razões devem ser positivas
        assert result.power_loss_ratio_a_to_b > 0
        assert result.power_loss_ratio_c_to_b > 0
        
        # Razão a/b deve ser igual a tanh(b/δ)
        assert np.isclose(
            result.power_loss_ratio_a_to_b,
            result.variant_a_hyperbolic_factor,
            rtol=0.001
        )
        
        # Razão c/b deve ser igual a coth(b/δ)
        assert np.isclose(
            result.power_loss_ratio_c_to_b,
            result.variant_c_hyperbolic_factor,
            rtol=0.001
        )

    def test_variant_b_baseline(self):
        """Verifica que variante (b) é o caso base (P_b = 1.0 em escala relativa)."""
        result = solve_question_04_rectangular_conductors(
            half_width_b_cm=2.5,
            surface_magnetic_field_h0_a_per_m=6.0,
            conductivity_s_per_m=5.8e7,
            frequency_hz=60.0,
            permeability_rel=1.0,
        )
        
        # Variante (b) é sempre usada como referência (razão = 1.0)
        # Verificar indiretamente através de P_b
        p_b_from_formula = (result.surface_field_h0_a_per_m ** 2) / (
            result.conductivity_s_per_m * result.skin_depth_m
        )
        
        assert np.isclose(
            result.variant_b_power_loss_w_per_m2,
            p_b_from_formula,
            rtol=0.001
        )


class TestCurrentDensity:
    """Testes da densidade de corrente induzida."""

    def test_current_density_positive(self):
        """Verifica que densidades de corrente são sempre positivas."""
        result = solve_question_04_rectangular_conductors(
            half_width_b_cm=2.5,
            surface_magnetic_field_h0_a_per_m=6.0,
            conductivity_s_per_m=5.8e7,
            frequency_hz=60.0,
            permeability_rel=1.0,
        )
        
        assert result.max_current_density_var_a_a_per_m2 > 0
        assert result.max_current_density_var_b_a_per_m2 > 0
        assert result.max_current_density_var_c_a_per_m2 > 0

    def test_current_density_physical_range(self):
        """Verifica que densidades de corrente estão em intervalo físico."""
        result = solve_question_04_rectangular_conductors(
            half_width_b_cm=2.5,
            surface_magnetic_field_h0_a_per_m=6.0,
            conductivity_s_per_m=5.8e7,
            frequency_hz=60.0,
            permeability_rel=1.0,
        )
        
        # Para cobre com H₀=6 A/m, esperar J ~ 10^4 a 10^6 A/m²
        for j_val in [
            result.max_current_density_var_a_a_per_m2,
            result.max_current_density_var_b_a_per_m2,
            result.max_current_density_var_c_a_per_m2
        ]:
            assert 1e3 < j_val < 1e8


class TestModelConsistency:
    """Testes de consistência do modelo."""

    def test_output_model_types(self):
        """Verifica que todos os outputs têm tipos corretos."""
        result = solve_question_04_rectangular_conductors(
            half_width_b_cm=2.5,
            surface_magnetic_field_h0_a_per_m=6.0,
            conductivity_s_per_m=5.8e7,
            frequency_hz=60.0,
            permeability_rel=1.0,
        )
        
        assert isinstance(result.skin_depth_m, float)
        assert isinstance(result.variant_a_power_loss_w_per_m2, float)
        assert isinstance(result.notes, list)
        assert all(isinstance(note, str) for note in result.notes)

    def test_geometry_parameters_consistent(self):
        """Verifica consistência de parâmetros geométricos."""
        half_width = 2.5
        result = solve_question_04_rectangular_conductors(
            half_width_b_cm=half_width,
            surface_magnetic_field_h0_a_per_m=6.0,
            conductivity_s_per_m=5.8e7,
            frequency_hz=60.0,
            permeability_rel=1.0,
        )
        
        assert result.half_width_b_cm == half_width
        assert np.isclose(result.half_width_b_m, half_width / 100.0)
        assert np.isclose(result.full_width_2b_cm, 2 * half_width)

    def test_reference_data_reproducibility(self):
        """Verifica reprodutibilidade com dados da questão."""
        # Dados: H₀=6.0 A/m, σ=5.8e7 S/m, b=2.5 cm, f=60 Hz
        result = solve_question_04_rectangular_conductors(
            half_width_b_cm=2.5,
            surface_magnetic_field_h0_a_per_m=6.0,
            conductivity_s_per_m=5.8e7,
            frequency_hz=60.0,
            permeability_rel=1.0,
        )
        
        # Executar novamente
        result2 = solve_question_04_rectangular_conductors(
            half_width_b_cm=2.5,
            surface_magnetic_field_h0_a_per_m=6.0,
            conductivity_s_per_m=5.8e7,
            frequency_hz=60.0,
            permeability_rel=1.0,
        )
        
        # Devem ser idênticos
        assert result.variant_a_power_loss_w_per_m2 == result2.variant_a_power_loss_w_per_m2
        assert result.variant_b_power_loss_w_per_m2 == result2.variant_b_power_loss_w_per_m2
        assert result.variant_c_power_loss_w_per_m2 == result2.variant_c_power_loss_w_per_m2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
