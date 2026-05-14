"""Solução Analítica da Questão 4 - Condutores Retangulares de Cobre

Equação de difusão:  d²H/dx² = γ²H,  γ = √(jωμσ) = (1+j)/δ
Solução geral:       H(x) = C1 cosh(γx) + C2 sinh(γx)
Densidade corrente:  J(x) = -dH/dx

Três casos com H0 = campo na superfície, condutor de -b ≤ x ≤ b:

  (a) H(-b) = H0, H(+b) = H0   → C2 = 0 → Ha = H0 cosh(γx)/cosh(γb)
  (b) H(-b) = H0, H(+b) = -H0  → C1 = 0 → Hb = -H0 sinh(γx)/sinh(γb)
  (c) H(-b) = H0, H(+b) = 0    → Hc = (Ha + Hb)/2

Perdas (integração analítica com γ complexo, Δ = b/δ):
  P_a = H0²/(σδ) × [sinh(2Δ) - sin(2Δ)] / [cosh(2Δ) + cos(2Δ)]
  P_b = H0²/(σδ) × [sinh(2Δ) + sin(2Δ)] / [cosh(2Δ) - cos(2Δ)]
  P_c = (P_a + P_b) / 4
"""

import numpy as np
from pydantic import BaseModel


class Q4RectangularConductor(BaseModel):
    """Modelo de saída para análise de condutor retangular."""
    
    # Geometria
    half_width_b_cm: float  # b em cm (meia largura)
    half_width_b_m: float  # b em m
    full_width_2b_cm: float  # 2b em cm
    
    # Material e operação
    conductivity_s_per_m: float  # σ [S/m]
    frequency_hz: float  # f [Hz]
    permeability_mu0_h_per_m: float  # μ₀ [H/m]
    surface_field_h0_a_per_m: float  # H₀ [A/m]
    
    # Parâmetros derivados
    omega_rad_s: float  # ω = 2πf [rad/s]
    skin_depth_m: float  # δ [m]
    skin_depth_mm: float  # δ [mm]
    skin_depth_ratio_b_over_delta: float  # b/δ (razão)
    
    # Variante (a): H(-b)=H0, H(+b)=H0 → simétrico
    variant_a_power_loss_w_per_m2: float
    variant_a_factor: float  # [sinh(2Δ)-sin(2Δ)]/[cosh(2Δ)+cos(2Δ)]
    
    # Variante (b): H(-b)=H0, H(+b)=-H0 → antissimétrico
    variant_b_power_loss_w_per_m2: float
    variant_b_factor: float  # [sinh(2Δ)+sin(2Δ)]/[cosh(2Δ)-cos(2Δ)]
    
    # Variante (c): H(-b)=H0, H(+b)=0 → assimétrico = (a+b)/4
    variant_c_power_loss_w_per_m2: float
    
    # Campos e correntes induzidas
    max_current_density_var_a_a_per_m2: float  # Máximo de |J_x| em variante (a)
    max_current_density_var_b_a_per_m2: float  # Máximo de |J_x| em variante (b)
    max_current_density_var_c_a_per_m2: float  # Máximo de |J_x| em variante (c)
    
    # Comparações
    power_loss_ratio_a_to_b: float  # P_a / P_b
    power_loss_ratio_c_to_b: float  # P_c / P_b
    
    # Notas
    notes: list[str] = []


def solve_question_04_rectangular_conductors(
    half_width_b_cm: float,
    surface_magnetic_field_h0_a_per_m: float,
    conductivity_s_per_m: float,
    frequency_hz: float,
    permeability_rel: float = 1.0,
) -> Q4RectangularConductor:
    """Resolve a Questão 4 - Análise de condutores retangulares de cobre.
    
    Calcula campo magnético, densidade de corrente e perdas para as 3 variantes
    de geometria usando as referências Del Vecchio (2010) e Kulkarni (2013).
    
    Args:
        half_width_b_cm: Meia largura do condutor [cm]
        surface_magnetic_field_h0_a_per_m: Campo magnético na superfície [A/m]
        conductivity_s_per_m: Condutividade do cobre [S/m]
        frequency_hz: Frequência de operação [Hz]
        permeability_rel: Permeabilidade relativa (1.0 para cobre não-magnético)
    
    Returns:
        Q4RectangularConductor com todos os resultados
    """
    
    # Conversões
    b_m = half_width_b_cm / 100.0  # cm → m
    b_cm = half_width_b_cm
    
    # Constantes
    mu0 = 4.0 * np.pi * 1e-7  # [H/m]
    mu = permeability_rel * mu0
    omega = 2.0 * np.pi * frequency_hz
    
    # ─────────────────────────────────────────────────────────────────────────
    # Profundidade de penetração (skin depth)
    # δ = √(1 / (π f μ σ))  ≡  √(2 / (ω μ σ))
    # ─────────────────────────────────────────────────────────────────────────
    delta_m = np.sqrt(1.0 / (np.pi * frequency_hz * mu * conductivity_s_per_m))
    delta_mm = delta_m * 1e3
    
    # Razão adimensional Δ = b/δ
    Delta = b_m / delta_m
    two_Delta = 2.0 * Delta

    # ─────────────────────────────────────────────────────────────────────────
    # Fator base  H0² / (σ δ)
    # ─────────────────────────────────────────────────────────────────────────
    base = (surface_magnetic_field_h0_a_per_m ** 2) / (conductivity_s_per_m * delta_m)

    # ─────────────────────────────────────────────────────────────────────────
    # VARIANTE (a): H(-b) = H0, H(+b) = H0  →  simétrico
    # Ha(x) = H0 cosh(γx) / cosh(γb)
    # Ja(x) = -γ H0 sinh(γx) / cosh(γb)
    # P_a = H0²/(σδ) × [sinh(2Δ) - sin(2Δ)] / [cosh(2Δ) + cos(2Δ)]
    # ─────────────────────────────────────────────────────────────────────────
    factor_a = (np.sinh(two_Delta) - np.sin(two_Delta)) / (np.cosh(two_Delta) + np.cos(two_Delta))
    p_a_w_per_m2 = base * factor_a

    # ─────────────────────────────────────────────────────────────────────────
    # VARIANTE (b): H(-b) = H0, H(+b) = -H0  →  antissimétrico
    # Hb(x) = -H0 sinh(γx) / sinh(γb)
    # Jb(x) =  γ H0 cosh(γx) / sinh(γb)
    # P_b = H0²/(σδ) × [sinh(2Δ) + sin(2Δ)] / [cosh(2Δ) - cos(2Δ)]
    # ─────────────────────────────────────────────────────────────────────────
    factor_b = (np.sinh(two_Delta) + np.sin(two_Delta)) / (np.cosh(two_Delta) - np.cos(two_Delta))
    p_b_w_per_m2 = base * factor_b

    # ─────────────────────────────────────────────────────────────────────────
    # VARIANTE (c): H(-b) = H0, H(+b) = 0  →  assimétrico
    # Hc = (Ha + Hb) / 2  →  P_c = (P_a + P_b) / 4
    # ─────────────────────────────────────────────────────────────────────────
    p_c_w_per_m2 = (p_a_w_per_m2 + p_b_w_per_m2) / 4.0

    # ─────────────────────────────────────────────────────────────────────────
    # Densidades de corrente máximas (x = ±b, módulo)
    # γ = (1+j)/δ  →  |γ| = √2 / δ
    # ─────────────────────────────────────────────────────────────────────────
    gamma_mag = np.sqrt(2.0) / delta_m
    # |sinh(γb)| = √[(cosh(2Δ)-cos(2Δ))/2], |cosh(γb)| = √[(cosh(2Δ)+cos(2Δ))/2]
    mod_sinh_gb = np.sqrt((np.cosh(two_Delta) - np.cos(two_Delta)) / 2.0)
    mod_cosh_gb = np.sqrt((np.cosh(two_Delta) + np.cos(two_Delta)) / 2.0)
    j_max_a_a_per_m2 = gamma_mag * surface_magnetic_field_h0_a_per_m * mod_sinh_gb / mod_cosh_gb
    j_max_b_a_per_m2 = gamma_mag * surface_magnetic_field_h0_a_per_m / mod_sinh_gb
    j_max_c_a_per_m2 = (j_max_a_a_per_m2 + j_max_b_a_per_m2) / 2.0

    # ─────────────────────────────────────────────────────────────────────────
    # Notas físicas
    # ─────────────────────────────────────────────────────────────────────────
    notes = []
    if delta_mm > b_cm * 10:
        notes.append(f"⚠️ Skin depth δ={delta_mm:.2f} mm >> largura 2b={2*b_cm:.2f} cm: campo penetra uniformemente")
    elif delta_mm < b_cm:
        notes.append(f"✓ Skin depth δ={delta_mm:.2f} mm < largura 2b={2*b_cm:.2f} cm: forte efeito pelicular")
    else:
        notes.append(f"~ Skin depth δ={delta_mm:.2f} mm comparável à largura 2b={2*b_cm:.2f} cm")

    notes.append(f"Δ = b/δ = {Delta:.4f}")
    notes.append(f"P_a/P_b = {p_a_w_per_m2/p_b_w_per_m2:.4f}")
    notes.append(f"P_c/P_b = {p_c_w_per_m2/p_b_w_per_m2:.4f}")
    notes.append(f"Material: σ={conductivity_s_per_m:.2e} S/m, μ_r={permeability_rel}")
    notes.append(f"Operação: f={frequency_hz} Hz, H₀={surface_magnetic_field_h0_a_per_m} A/m")
    
    return Q4RectangularConductor(
        half_width_b_cm=b_cm,
        half_width_b_m=b_m,
        full_width_2b_cm=2*b_cm,
        conductivity_s_per_m=conductivity_s_per_m,
        frequency_hz=frequency_hz,
        permeability_mu0_h_per_m=mu0,
        surface_field_h0_a_per_m=surface_magnetic_field_h0_a_per_m,
        omega_rad_s=omega,
        skin_depth_m=delta_m,
        skin_depth_mm=delta_mm,
        skin_depth_ratio_b_over_delta=Delta,
        variant_a_power_loss_w_per_m2=p_a_w_per_m2,
        variant_a_factor=factor_a,
        variant_b_power_loss_w_per_m2=p_b_w_per_m2,
        variant_b_factor=factor_b,
        variant_c_power_loss_w_per_m2=p_c_w_per_m2,
        max_current_density_var_a_a_per_m2=j_max_a_a_per_m2,
        max_current_density_var_b_a_per_m2=j_max_b_a_per_m2,
        max_current_density_var_c_a_per_m2=j_max_c_a_per_m2,
        power_loss_ratio_a_to_b=p_a_w_per_m2 / p_b_w_per_m2,
        power_loss_ratio_c_to_b=p_c_w_per_m2 / p_b_w_per_m2,
        notes=notes,
    )


if __name__ == "__main__":
    # Dados da questão 4
    result = solve_question_04_rectangular_conductors(
        half_width_b_cm=2.5,
        surface_magnetic_field_h0_a_per_m=6.0,
        conductivity_s_per_m=5.8e7,
        frequency_hz=60.0,
        permeability_rel=1.0,
    )
    
    print("=" * 70)
    print("QUESTÃO 4 - CONDUTORES RETANGULARES DE COBRE")
    print("=" * 70)
    print()
    print(f"Profundidade de penetração: δ = {result.skin_depth_mm:.4f} mm")
    print(f"Razão: b/δ = {result.skin_depth_ratio_b_over_delta:.4f}")
    print()
    print("VARIANTE (a) - Campo em ambas as superfícies:")
    print(f"  Fator tanh(b/δ) = {result.variant_a_hyperbolic_factor:.6f}")
    print(f"  Perdas: P_a = {result.variant_a_power_loss_w_per_m2:.4e} W/m²")
    print(f"  Corrente máxima: J_max = {result.max_current_density_var_a_a_per_m2:.4e} A/m²")
    print()
    print("VARIANTE (b) - Campo em uma superfície:")
    print(f"  Perdas: P_b = {result.variant_b_power_loss_w_per_m2:.4e} W/m²")
    print(f"  Corrente máxima: J_max = {result.max_current_density_var_b_a_per_m2:.4e} A/m²")
    print()
    print("VARIANTE (c) - Espaço finito (sanduíche):")
    print(f"  Fator 1/tanh(b/δ) = {result.variant_c_hyperbolic_factor:.6f}")
    print(f"  Perdas: P_c = {result.variant_c_power_loss_w_per_m2:.4e} W/m²")
    print(f"  Corrente máxima: J_max = {result.max_current_density_var_c_a_per_m2:.4e} A/m²")
    print()
    print("COMPARAÇÕES:")
    print(f"  P_a / P_b = {result.power_loss_ratio_a_to_b:.6f}")
    print(f"  P_c / P_b = {result.power_loss_ratio_c_to_b:.6f}")
    print()
    print("NOTAS:")
    for note in result.notes:
        print(f"  • {note}")
    print()
    print("=" * 70)
