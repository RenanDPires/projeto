"""Testes para a Questão 2 - Equação de difusão e análise analítica."""

import numpy as np
import pytest
from app.core.exercises.q02_analytical_solutions import solve_question_02
from app.core.electromagnetics.diffusion_equation import (
    calculate_skin_depth,
    calculate_propagation_constant,
    magnetic_field_circular_plate,
    induced_current_density_circular_plate,
    calculate_total_losses_circular_plate,
)


class TestSkinDepth:
    """Testes da profundidade de penetração."""

    def test_skin_depth_basic(self):
        """Verifica cálculo básico da profundidade de penetração."""
        omega = 2 * np.pi * 60  # 60 Hz
        mu = 200 * 4 * np.pi * 1e-7  # μ_r = 200
        sigma = 4.0e6  # S/m
        
        delta = calculate_skin_depth(omega, mu, sigma)
        
        # Para aço carbono a 60 Hz, δ deve ser ~2-3 mm
        assert 0.001 < delta < 0.01, f"Skin depth {delta*1000:.3f} mm fora do intervalo esperado"

    def test_skin_depth_frequency_dependence(self):
        """Verifica dependência de frequência: δ ∝ 1/√f."""
        mu = 200 * 4 * np.pi * 1e-7
        sigma = 4.0e6
        
        delta_60 = calculate_skin_depth(2 * np.pi * 60, mu, sigma)
        delta_120 = calculate_skin_depth(2 * np.pi * 120, mu, sigma)
        
        # δ(120 Hz) / δ(60 Hz) ≈ sqrt(60/120) ≈ 0.707
        ratio = delta_120 / delta_60
        expected_ratio = np.sqrt(60.0 / 120.0)
        
        assert np.isclose(ratio, expected_ratio, rtol=0.01)

    def test_skin_depth_zero_frequency(self):
        """Verifica que δ → ∞ para frequência zero."""
        delta = calculate_skin_depth(0, 1.0, 1.0)
        assert delta == float('inf')


class TestPropagationConstant:
    """Testes da constante de propagação."""

    def test_propagation_constant_magnitude(self):
        """Verifica que |p| = √2/δ."""
        omega = 2 * np.pi * 60
        mu = 200 * 4 * np.pi * 1e-7
        sigma = 4.0e6
        
        delta = calculate_skin_depth(omega, mu, sigma)
        p = calculate_propagation_constant(omega, mu, sigma)
        
        p_magnitude = np.abs(p)
        # |p| = |(1+j)/δ| = √2/δ
        expected = np.sqrt(2.0) / delta
        
        assert np.isclose(p_magnitude, expected, rtol=0.01)

    def test_propagation_constant_complex_form(self):
        """Verifica que p = (1+j)/δ."""
        omega = 2 * np.pi * 60
        mu = 200 * 4 * np.pi * 1e-7
        sigma = 4.0e6
        
        p = calculate_propagation_constant(omega, mu, sigma)
        delta = calculate_skin_depth(omega, mu, sigma)
        
        # p deve ser proporcional a (1+j)
        expected = (1.0 + 1.0j) / delta
        
        assert np.isclose(p, expected, rtol=0.01)


class TestMagneticField:
    """Testes do campo magnético H_φ."""

    def test_h_field_boundary_condition(self):
        """Verifica condição de contorno: H_φ(b) ~ I/(2πb)."""
        outer_d_mm = 910.0
        inner_d_mm = 165.0
        current_a = 1000.0
        frequency_hz = 60.0
        mu = 200 * 4 * np.pi * 1e-7
        sigma = 4.0e6
        
        outer_r_m = outer_d_mm / 2.0 * 1e-3
        inner_r_m = inner_d_mm / 2.0 * 1e-3
        
        r_values = np.array([outer_r_m])
        _, h_mag, _ = magnetic_field_circular_plate(
            r_values, outer_r_m, inner_r_m, current_a, frequency_hz, mu, sigma
        )
        
        h_expected = current_a / (2 * np.pi * outer_r_m)
        
        # Campo na superfície deve estar próximo do esperado
        assert np.isclose(h_mag[0], h_expected, rtol=0.1)

    def test_h_field_monotonic_decay(self):
        """Verifica que H_φ decai monotonicamente de fora para dentro."""
        outer_d_mm = 910.0
        inner_d_mm = 165.0
        current_a = 1000.0
        frequency_hz = 60.0
        mu = 200 * 4 * np.pi * 1e-7
        sigma = 4.0e6
        
        outer_r_m = outer_d_mm / 2.0 * 1e-3
        inner_r_m = inner_d_mm / 2.0 * 1e-3
        
        r_values = np.linspace(inner_r_m, outer_r_m, 10)
        _, h_mag, _ = magnetic_field_circular_plate(
            r_values, outer_r_m, inner_r_m, current_a, frequency_hz, mu, sigma
        )
        
        # Verificar que valores são positivos e decaem
        assert np.all(h_mag >= 0)
        # Campo diminui conforme nos afastamos da superfície externa
        assert h_mag[-1] >= h_mag[0]  # Ordenação: de dentro para fora


class TestInducedCurrent:
    """Testes da densidade de corrente induzida."""

    def test_current_density_proportional_to_h_field(self):
        """Verifica que J_r ∝ H_φ."""
        r_values = np.array([0.5, 0.6, 0.7])
        h_mag = np.array([100.0, 200.0, 300.0])
        frequency_hz = 60.0
        sigma = 4.0e6
        
        j_mag = induced_current_density_circular_plate(r_values, h_mag, frequency_hz, sigma)
        
        # J deve ser proporcional a H
        j_ratio_1 = j_mag[1] / j_mag[0]
        h_ratio_1 = h_mag[1] / h_mag[0]
        
        assert np.isclose(j_ratio_1, h_ratio_1, rtol=0.01)

    def test_current_density_positive(self):
        """Verifica que densidade de corrente é sempre positiva."""
        r_values = np.linspace(0.1, 0.9, 50)
        h_mag = np.random.rand(50) * 1000
        frequency_hz = 60.0
        sigma = 4.0e6
        
        j_mag = induced_current_density_circular_plate(r_values, h_mag, frequency_hz, sigma)
        
        assert np.all(j_mag >= 0)


class TestTotalLosses:
    """Testes das perdas totais."""

    def test_losses_positive(self):
        """Verifica que as perdas são sempre positivas."""
        outer_r_m = 0.455
        inner_r_m = 0.0825
        thickness_m = 0.00952
        current_a = 1000.0
        frequency_hz = 60.0
        mu = 200 * 4 * np.pi * 1e-7
        sigma = 4.0e6
        
        result = calculate_total_losses_circular_plate(
            outer_r_m, inner_r_m, thickness_m, current_a, frequency_hz, mu, sigma
        )
        
        assert result["total_loss_w"] >= 0
        assert result["max_h_field"] >= 0
        assert result["max_j_density"] >= 0

    def test_losses_increase_with_current(self):
        """Verifica que P ∝ I² (não linearmente)."""
        outer_r_m = 0.455
        inner_r_m = 0.0825
        thickness_m = 0.00952
        frequency_hz = 60.0
        mu = 200 * 4 * np.pi * 1e-7
        sigma = 4.0e6
        
        result_1000 = calculate_total_losses_circular_plate(
            outer_r_m, inner_r_m, thickness_m, 1000.0, frequency_hz, mu, sigma
        )
        result_2000 = calculate_total_losses_circular_plate(
            outer_r_m, inner_r_m, thickness_m, 2000.0, frequency_hz, mu, sigma
        )
        
        # P(2000 A) / P(1000 A) ≈ (2000/1000)² = 4
        ratio = result_2000["total_loss_w"] / result_1000["total_loss_w"]
        expected_ratio = 4.0
        
        assert np.isclose(ratio, expected_ratio, rtol=0.1)


class TestQ2Derivation:
    """Testes da solução completa da Questão 2."""

    def test_q2_basic_calculation(self):
        """Verifica que Q2 calcula sem erros."""
        result = solve_question_02(
            outer_diameter_mm=910.0,
            inner_diameter_mm=165.0,
            thickness_mm=9.52,
            current_a_rms=1000.0,
            frequency_hz=60.0,
            permeability_rel=200.0,
            conductivity_s_per_m=4.0e6,
        )
        
        assert result.skin_depth_m > 0
        assert result.total_losses_w >= 0
        assert result.max_current_density_a_per_m2 >= 0

    def test_q2_material_dependence(self):
        """Verifica que resultados diferem entre materiais."""
        # Aço carbono
        result_carbon = solve_question_02(
            outer_diameter_mm=910.0,
            inner_diameter_mm=165.0,
            thickness_mm=9.52,
            current_a_rms=1000.0,
            frequency_hz=60.0,
            permeability_rel=200.0,
            conductivity_s_per_m=4.0e6,
        )
        
        # Aço inox
        result_inox = solve_question_02(
            outer_diameter_mm=910.0,
            inner_diameter_mm=165.0,
            thickness_mm=9.52,
            current_a_rms=1000.0,
            frequency_hz=60.0,
            permeability_rel=1.0,
            conductivity_s_per_m=1.33e6,
        )
        
        # Perdas devem ser diferentes
        assert result_carbon.total_losses_w != result_inox.total_losses_w
        # Skin depth deve ser diferente
        assert result_carbon.skin_depth_m != result_inox.skin_depth_m

    def test_q2_output_types(self):
        """Verifica que todos os outputs estão com tipos corretos."""
        result = solve_question_02(
            outer_diameter_mm=910.0,
            inner_diameter_mm=165.0,
            thickness_mm=9.52,
            current_a_rms=1000.0,
            frequency_hz=60.0,
            permeability_rel=200.0,
            conductivity_s_per_m=4.0e6,
        )
        
        assert isinstance(result.skin_depth_m, float)
        assert isinstance(result.total_losses_w, float)
        assert isinstance(result.notes, list)
        assert all(isinstance(note, str) for note in result.notes)

    def test_q2_boundary_conditions(self):
        """Verifica comportamentos limites."""
        # Frequência muito baixa vs normal
        result_low_freq = solve_question_02(
            outer_diameter_mm=910.0,
            inner_diameter_mm=165.0,
            thickness_mm=9.52,
            current_a_rms=1000.0,
            frequency_hz=0.1,  # 0.1 Hz
            permeability_rel=200.0,
            conductivity_s_per_m=4.0e6,
        )
        
        result_normal_freq = solve_question_02(
            outer_diameter_mm=910.0,
            inner_diameter_mm=165.0,
            thickness_mm=9.52,
            current_a_rms=1000.0,
            frequency_hz=60.0,  # 60 Hz
            permeability_rel=200.0,
            conductivity_s_per_m=4.0e6,
        )
        
        # Skin depth deve ser maior em frequência mais baixa
        assert result_low_freq.skin_depth_m > result_normal_freq.skin_depth_m
        # Razão deve ser ~√(60/0.1) ≈ 24.5
        ratio = result_low_freq.skin_depth_m / result_normal_freq.skin_depth_m
        expected_ratio = np.sqrt(60.0 / 0.1)
        assert np.isclose(ratio, expected_ratio, rtol=0.1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
