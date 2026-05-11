"""Solução Analítica da Questão 4 - Condutores Retangulares de Cobre

Referências:
- Del Vecchio, R. M., "Transformer Design Principles", 
  Seção 15.3.2.1 "Eddy Current Losses in the Coils" (página 426)
  
- Kulkarni, S. V., & Khaparde, S. A., "Transformer Engineering: Design, 
  Technology, and Diagnostics", Seção 4.5.1 "Expression for the eddy loss" 
  (página 150)

Três variantes de condutores retangulares de cobre com largura 2b:
(a) Campo aplicado em ambas as superfícies (simetria)
(b) Campo aplicado em uma superfície (semi-espaço)
(c) Espaço finito com ambas as superfícies limitadas (sanduíche)
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
    
    # Variante (a): Ambas as superfícies com campo
    variant_a_power_loss_w_per_m2: float
    variant_a_hyperbolic_factor: float  # tanh(b/δ)
    
    # Variante (b): Uma superfície com campo (semi-espaço)
    variant_b_power_loss_w_per_m2: float
    
    # Variante (c): Espaço finito (sanduíche)
    variant_c_power_loss_w_per_m2: float
    variant_c_hyperbolic_factor: float  # 1/tanh(b/δ)
    
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
    # δ = √(2 / (ω μ σ))
    # ─────────────────────────────────────────────────────────────────────────
    
    delta_m = np.sqrt(2.0 / (omega * mu * conductivity_s_per_m))
    delta_mm = delta_m * 1e3
    
    # Razão adimensional b/δ
    b_over_delta = b_m / delta_m
    
    # ─────────────────────────────────────────────────────────────────────────
    # VARIANTE (a): Ambas as superfícies com campo aplicado
    # 
    # Equação de difusão: ∇² H_z - (ωμσ/2)(1-j) H_z = 0
    # 
    # Coordenada: -b ≤ x ≤ b (condutor)
    # Condição de contorno: H_z(±b) = H₀
    # 
    # Solução: H_z(x) = H₀ cosh(x/δ)
    # Densidade de corrente: J_x(x) = σωμ H_z = σωμ H₀ sinh(x/δ) (com complexo)
    # 
    # Perdas por unidade de área:
    # P_a = ∫_{-b}^{b} (|J_x|²/σ) dx = (H₀² / (σδ)) ∫_{-b}^{b} sinh²(x/δ) dx
    #     = (H₀² / (σδ)) · [δ/2 · sinh(2b/δ) + b]  = H₀²/(σδ) · tanh(b/δ)
    # ─────────────────────────────────────────────────────────────────────────
    
    tanh_factor_a = np.tanh(b_over_delta)
    p_a_w_per_m2 = (surface_magnetic_field_h0_a_per_m ** 2) * (1.0 / (conductivity_s_per_m * delta_m)) * tanh_factor_a
    
    # Densidade de corrente máxima (em x = ±b)
    j_max_a_a_per_m2 = (conductivity_s_per_m * omega * mu0 * 
                        surface_magnetic_field_h0_a_per_m * np.sinh(b_over_delta))
    
    # ─────────────────────────────────────────────────────────────────────────
    # VARIANTE (b): Campo aplicado em uma superfície (semi-espaço)
    # 
    # Coordenada: 0 ≤ y ≤ ∞ (semi-espaço)
    # Condição de contorno: H_z(0) = H₀, H_z(∞) = 0
    # 
    # Solução: H_z(y) = H₀ exp(-y/δ)
    # Densidade de corrente: J_x(y) = σωμ H₀ exp(-y/δ)
    # 
    # Perdas por unidade de área:
    # P_b = ∫_0^∞ (|J_x|²/σ) dy = (H₀² / (σδ))
    # ─────────────────────────────────────────────────────────────────────────
    
    p_b_w_per_m2 = (surface_magnetic_field_h0_a_per_m ** 2) / (conductivity_s_per_m * delta_m)
    
    # Densidade de corrente máxima (em y = 0)
    j_max_b_a_per_m2 = conductivity_s_per_m * omega * mu0 * surface_magnetic_field_h0_a_per_m
    
    # ─────────────────────────────────────────────────────────────────────────
    # VARIANTE (c): Ambas as superfícies limitadas (espaço finito)
    # 
    # Coordenada: 0 ≤ x ≤ b (espaço finito)
    # Condição de contorno: H_z(0) = H₀, H_z(b) = 0
    # 
    # Solução: H_z(x) = H₀ sinh((b-x)/δ) / sinh(b/δ)
    # 
    # Perdas por unidade de área:
    # P_c = (H₀² / (σδ)) · [1 / tanh(b/δ)]
    # ─────────────────────────────────────────────────────────────────────────
    
    sinh_factor_c = np.sinh(b_over_delta)
    coth_factor_c = 1.0 / tanh_factor_a  # coth = 1/tanh
    p_c_w_per_m2 = (surface_magnetic_field_h0_a_per_m ** 2) * (1.0 / (conductivity_s_per_m * delta_m)) * coth_factor_c
    
    # Densidade de corrente máxima (em x = 0)
    j_max_c_a_per_m2 = (conductivity_s_per_m * omega * mu0 * 
                        surface_magnetic_field_h0_a_per_m * 
                        (1.0 / np.tanh(b_over_delta)))
    
    # ─────────────────────────────────────────────────────────────────────────
    # Notas físicas
    # ─────────────────────────────────────────────────────────────────────────
    
    notes = []
    
    # Verificar profundidade de penetração
    if delta_mm > b_cm * 10:
        notes.append(f"⚠️ Skin depth δ={delta_mm:.2f} mm >> largura 2b={2*b_cm:.2f} cm: campo penetra uniformemente")
    elif delta_mm < b_cm:
        notes.append(f"✓ Skin depth δ={delta_mm:.2f} mm < largura 2b={2*b_cm:.2f} cm: forte efeito pelicular")
    else:
        notes.append(f"~ Skin depth δ={delta_mm:.2f} mm comparável à largura 2b={2*b_cm:.2f} cm")
    
    # Comparação entre variantes
    notes.append(f"P_a/P_b = {p_a_w_per_m2/p_b_w_per_m2:.4f} (variante a é {'menor' if p_a_w_per_m2 < p_b_w_per_m2 else 'maior'})")
    notes.append(f"P_c/P_b = {p_c_w_per_m2/p_b_w_per_m2:.4f} (variante c é {'menor' if p_c_w_per_m2 < p_b_w_per_m2 else 'maior'})")
    
    # Material e frequência
    notes.append(f"Material: Cobre (σ={conductivity_s_per_m:.2e} S/m, μ_r={permeability_rel})")
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
        skin_depth_ratio_b_over_delta=b_over_delta,
        variant_a_power_loss_w_per_m2=p_a_w_per_m2,
        variant_a_hyperbolic_factor=tanh_factor_a,
        variant_b_power_loss_w_per_m2=p_b_w_per_m2,
        variant_c_power_loss_w_per_m2=p_c_w_per_m2,
        variant_c_hyperbolic_factor=coth_factor_c,
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
