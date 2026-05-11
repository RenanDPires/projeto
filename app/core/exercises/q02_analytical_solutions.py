"""Solução completa da Questão 2 - Análise analítica de perdas em tampa circular.

Este módulo implementa a solução analítica das três partes da Questão 2:
a) Equação de difusão e campo H_φ
b) Densidade de corrente induzida J_r
c) Perdas totais

Geometria: Tampa circular com raio interno 'a', raio externo 'b', espessura 'c'
Coordenadas: Cilíndricas (r, φ, z)
"""

import numpy as np
from pydantic import BaseModel
from app.core.electromagnetics.diffusion_equation import (
    calculate_skin_depth,
    magnetic_field_circular_plate,
    induced_current_density_circular_plate,
    calculate_total_losses_circular_plate,
)


class Q2DerivationOutput(BaseModel):
    """Saída estruturada das deduções da Questão 2."""

    # Parte (a) - Equação de difusão e H_φ
    skin_depth_m: float  # δ [m]
    omega_rad_s: float  # ω = 2πf [rad/s]
    propagation_constant_real: float  # Re(p) [1/m]
    propagation_constant_imag: float  # Im(p) [1/m]

    # Geometria
    outer_radius_mm: float  # b [mm]
    inner_radius_mm: float  # a [mm]
    thickness_mm: float  # c [mm]
    plate_area_mm2: float  # π(b² - a²) [mm²]

    # Propriedades do material
    permeability_rel: float  # μ_r
    conductivity_s_per_m: float  # σ [S/m]
    frequency_hz: float  # f [Hz]
    current_rms_a: float  # I [A_rms]

    # Resultados em r = b (superfície externa)
    h_field_at_outer_radius_a_per_m: float  # |H_φ(b)| [A/m]

    # Parte (b) - Densidade de corrente
    max_current_density_a_per_m2: float  # max(|J_r|) [A/m²]
    avg_current_density_a_per_m2: float  # média de |J_r| [A/m²]

    # Parte (c) - Perdas totais
    total_losses_w: float  # P [W]
    losses_per_unit_area_w_per_mm2: float  # P / (π(b²-a²)) [W/mm²]
    losses_per_unit_volume_w_per_mm3: float  # P / (π(b²-a²)c) [W/mm³]

    # Notas adicionais
    notes: list[str] = []


def solve_question_02(
    outer_diameter_mm: float,
    inner_diameter_mm: float,
    thickness_mm: float,
    current_a_rms: float,
    frequency_hz: float,
    permeability_rel: float,
    conductivity_s_per_m: float,
) -> Q2DerivationOutput:
    """Resolve a Questão 2 - Análise analítica de perdas na tampa circular.

    Args:
        outer_diameter_mm: Diâmetro externo [mm]
        inner_diameter_mm: Diâmetro interno [mm]
        thickness_mm: Espessura [mm]
        current_a_rms: Corrente RMS [A]
        frequency_hz: Frequência [Hz]
        permeability_rel: Permeabilidade relativa μ_r
        conductivity_s_per_m: Condutividade [S/m]

    Returns:
        Q2DerivationOutput com todos os resultados das três partes
    """
    # Conversões
    outer_radius_m = outer_diameter_mm / 2.0 * 1e-3
    inner_radius_m = inner_diameter_mm / 2.0 * 1e-3
    thickness_m = thickness_mm * 1e-3

    # Permeabilidade absoluta
    mu0 = 4.0 * np.pi * 1e-7  # [H/m]
    mu = permeability_rel * mu0

    # Frequência angular
    omega = 2.0 * np.pi * frequency_hz

    # ─────────────────────────────────────────────────────────────────────────
    # PARTE (a): Equação de difusão e campo H_φ
    # ─────────────────────────────────────────────────────────────────────────

    # Profundidade de penetração
    skin_depth_m = calculate_skin_depth(omega, mu, conductivity_s_per_m)

    # Constante de propagação complexa p = (1+j)/δ
    p_complex = (1.0 + 1.0j) / skin_depth_m
    p_real = np.real(p_complex)
    p_imag = np.imag(p_complex)

    # Campo magnético na superfície externa
    h_field_at_boundary = current_a_rms / (2.0 * np.pi * outer_radius_m)

    # ─────────────────────────────────────────────────────────────────────────
    # PARTE (b): Densidade de corrente induzida J_r
    # ─────────────────────────────────────────────────────────────────────────

    # Calcular campos sobre todo o raio
    n_radii = 200
    r_radii = np.linspace(inner_radius_m, outer_radius_m, n_radii)

    _, h_magnitude, _ = magnetic_field_circular_plate(
        r_radii,
        outer_radius_m,
        inner_radius_m,
        current_a_rms,
        frequency_hz,
        mu,
        conductivity_s_per_m,
    )

    j_magnitude = induced_current_density_circular_plate(
        r_radii, h_magnitude, frequency_hz, conductivity_s_per_m
    )

    max_current_density = np.max(j_magnitude)
    avg_current_density = np.mean(j_magnitude)

    # ─────────────────────────────────────────────────────────────────────────
    # PARTE (c): Perdas totais
    # ─────────────────────────────────────────────────────────────────────────

    losses_dict = calculate_total_losses_circular_plate(
        outer_radius_m,
        inner_radius_m,
        thickness_m,
        current_a_rms,
        frequency_hz,
        mu,
        conductivity_s_per_m,
    )

    total_losses_w = losses_dict["total_loss_w"]

    # Áreas e volumes
    plate_area_m2 = np.pi * (outer_radius_m**2 - inner_radius_m**2)
    plate_volume_m3 = plate_area_m2 * thickness_m

    losses_per_area_w_per_mm2 = (
        total_losses_w / (plate_area_m2 * 1e6) if plate_area_m2 > 0 else 0.0
    )
    losses_per_volume_w_per_mm3 = (
        total_losses_w / (plate_volume_m3 * 1e9) if plate_volume_m3 > 0 else 0.0
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Notas e observações
    # ─────────────────────────────────────────────────────────────────────────

    notes = [
        f"Profundidade de penetração δ = {skin_depth_m*1e3:.3f} mm",
        f"Razão espessura/skin: c/δ = {thickness_m/skin_depth_m:.2f}",
        f"Campo H_φ na superfície externa (r=b): {h_field_at_boundary:.2f} A/m",
        f"Frequência de operação: {frequency_hz:.1f} Hz",
        f"Material: μ_r={permeability_rel:.0f}, σ={conductivity_s_per_m:.2e} S/m",
    ]

    if thickness_m > 3 * skin_depth_m:
        notes.append(
            "⚠️ Espessura >> profundidade de penetração: campo penetra pouco"
        )
    elif thickness_m < skin_depth_m / 3:
        notes.append("⚠️ Espessura << profundidade de penetração: campo penetra uniformemente")

    return Q2DerivationOutput(
        skin_depth_m=skin_depth_m,
        omega_rad_s=omega,
        propagation_constant_real=p_real,
        propagation_constant_imag=p_imag,
        outer_radius_mm=outer_diameter_mm / 2.0,
        inner_radius_mm=inner_diameter_mm / 2.0,
        thickness_mm=thickness_mm,
        plate_area_mm2=plate_area_m2 * 1e6,
        permeability_rel=permeability_rel,
        conductivity_s_per_m=conductivity_s_per_m,
        frequency_hz=frequency_hz,
        current_rms_a=current_a_rms,
        h_field_at_outer_radius_a_per_m=h_field_at_boundary,
        max_current_density_a_per_m2=max_current_density,
        avg_current_density_a_per_m2=avg_current_density,
        total_losses_w=total_losses_w,
        losses_per_unit_area_w_per_mm2=losses_per_area_w_per_mm2,
        losses_per_unit_volume_w_per_mm3=losses_per_volume_w_per_mm3,
        notes=notes,
    )


def compare_q1_vs_q2_methods(
    outer_diameter_mm: float,
    inner_diameter_mm: float,
    thickness_mm: float,
    current_a_rms: float,
    frequency_hz: float,
    permeability_rel: float,
    conductivity_s_per_m: float,
) -> dict:
    """Compara os resultados analíticos (Q2) com os numéricos (Q1).

    Args:
        Mesmos parâmetros de solve_question_02

    Returns:
        Dict com comparação entre métodos
    """
    q2_result = solve_question_02(
        outer_diameter_mm,
        inner_diameter_mm,
        thickness_mm,
        current_a_rms,
        frequency_hz,
        permeability_rel,
        conductivity_s_per_m,
    )

    # Aqui poderíamos importar e comparar com resultados de Q1
    # Por enquanto, retornamos apenas os resultados de Q2

    return {
        "q2_analytical": q2_result.model_dump(),
        "comparison_notes": [
            "Método Q2: Solução analítica da equação de difusão em coords. cilíndricas",
            "Método Q1: Integração numérica de Biot-Savart em geometria 3D retangular",
            "Observação: Geometrias diferentes → resultados podem não ser diretamente comparáveis",
        ],
    }
