"""Solução da equação de difusão em coordenadas cilíndricas para campo magnético.

Este módulo implementa soluções analíticas da equação de difusão eletromagnética
para geometria cilíndrica, aplicável a problemas de correntes induzidas em tampas
circulares de transformadores.

Referência: Del Vecchio, R. M., "Transformer Design Principles", Cap. 15.5
"""

import numpy as np
from scipy.special import jv, yv  # Funções de Bessel J_ν e Y_ν
from scipy.integrate import quad


def calculate_skin_depth(omega: float, mu: float, sigma: float) -> float:
    """Calcula a profundidade de penetração (skin depth) do campo magnético.
    
    δ = √(2 / (ω μ σ))
    
    Args:
        omega: Frequência angular [rad/s]
        mu: Permeabilidade magnética [H/m]
        sigma: Condutividade elétrica [S/m]
    
    Returns:
        Profundidade de penetração [m]
    """
    if omega <= 0 or sigma <= 0:
        return float('inf')
    return np.sqrt(2.0 / (omega * mu * sigma))


def calculate_propagation_constant(omega: float, mu: float, sigma: float) -> complex:
    """Calcula a constante de propagação complexa.
    
    p = (1 + j) / δ = (1 + j) √(ω μ σ / 2)
    
    Args:
        omega: Frequência angular [rad/s]
        mu: Permeabilidade magnética [H/m]
        sigma: Condutividade elétrica [S/m]
    
    Returns:
        Constante de propagação complexa [1/m]
    """
    if omega <= 0 or sigma <= 0:
        return 0.0 + 0.0j
    
    # (1 + j) = e^(jπ/4) √2
    coefficient = np.sqrt(omega * mu * sigma / 2.0)
    return (1.0 + 1.0j) * coefficient


def magnetic_field_circular_plate(
    r_values: np.ndarray,
    outer_radius_m: float,
    inner_radius_m: float,
    current_a: float,
    frequency_hz: float,
    mu: float,
    sigma: float,
) -> tuple[np.ndarray, np.ndarray, float]:
    """Calcula o campo magnético azimuthal H_φ em uma tampa circular.
    
    Resolve a equação de difusão em coordenadas cilíndricas para geometria
    de uma tampa circular com raio interno e externo usando aproximação
    de campo uniforme com atenuação por skin effect.
    
    Equação de difusão (simetria cilíndrica):
    ∇² H_φ - p² H_φ = 0, onde p² = ωμσ(1-j)/2
    
    Aproximação: Para geometria finita com espessura pequena comparada
    ao raio, usamos campo aproximadamente uniforme com atenuação exponencial
    da superfície para o interior.
    
    Args:
        r_values: Array com valores de raio onde calcular H_φ [m]
        outer_radius_m: Raio externo da tampa [m]
        inner_radius_m: Raio interno da tampa [m]
        current_a: Corrente em Amperes RMS
        frequency_hz: Frequência [Hz]
        mu: Permeabilidade magnética [H/m]
        sigma: Condutividade elétrica [S/m]
    
    Returns:
        Tupla (r_values, h_field_magnitude, skin_depth)
        - r_values: Valores de raio [m]
        - h_field_magnitude: Magnitude de |H_φ(r)| [A/m]
        - skin_depth: Profundidade de penetração [m]
    """
    omega = 2.0 * np.pi * frequency_hz
    
    # Parâmetros da solução
    delta = calculate_skin_depth(omega, mu, sigma)
    
    # Se a frequência for zero (DC), não há skin effect
    if delta == float('inf') or delta == 0:
        # Retorna campo uniforme de Ampère
        h_values = np.full_like(r_values, current_a / (2.0 * np.pi * outer_radius_m))
        return r_values, np.abs(h_values), delta
    
    # Constante de propagação com normalização adequada
    p_magnitude = 1.0 / delta
    
    # Campo na condição de contorno (Lei de Ampère)
    h_boundary = current_a / (2.0 * np.pi * outer_radius_m)
    
    # Calcular campo com atenuação por skin effect
    # Modelo simplificado: assume penetração exponencial do campo
    # H_φ(r) ≈ H_0 * (1 + atenuação com distância da superfície)
    
    h_values = np.zeros_like(r_values, dtype=float)
    
    for i, r in enumerate(r_values):
        if r >= inner_radius_m and r <= outer_radius_m:
            # Distância da superfície externa
            distance_from_boundary = outer_radius_m - r
            
            # Atenuação exponencial com skin effect
            # Fator de decaimento: exp(-distance / δ)
            decay_factor = np.exp(-distance_from_boundary / delta)
            
            # Campo com skin effect
            h_values[i] = h_boundary * decay_factor
        elif r < inner_radius_m:
            # Dentro do furo (não há material condutor, campo uniforme)
            h_values[i] = h_boundary
        else:
            # Fora da placa
            h_values[i] = 0.0
    
    # Garantir valores reais positivos
    h_magnitude = np.abs(h_values)
    
    return r_values, h_magnitude, delta


def induced_current_density_circular_plate(
    r_values: np.ndarray,
    h_magnitude: np.ndarray,
    frequency_hz: float,
    sigma: float,
) -> np.ndarray:
    """Calcula a densidade de corrente induzida a partir do campo magnético.
    
    Lei de Faraday na forma integral:
    ∮ E · dl = -dΦ_B/dt = -jω Φ_B
    
    Para geometria cilíndrica com simetria:
    E_φ ≈ jω μ₀ H_r (indução com campo radial)
    
    Lei de Ohm:
    J = σ E
    
    Aproximação simplificada:
    J_r ≈ σ ω μ₀ H_φ (magnitude estimada)
    
    Args:
        r_values: Array com valores de raio [m]
        h_magnitude: Magnitude do campo H_φ [A/m]
        frequency_hz: Frequência [Hz]
        sigma: Condutividade [S/m]
    
    Returns:
        Densidade de corrente |J_r| [A/m²]
    """
    omega = 2.0 * np.pi * frequency_hz
    
    # Permeabilidade do vácuo
    mu0 = 4.0 * np.pi * 1e-7
    
    # Magnitude da densidade de corrente
    # J ≈ σ ω μ₀ H com coeficiente de proporcionalidade
    # Em regime de pele com campo propagante, J ~ σ c dH/dt ~ σ ω H
    j_magnitude = sigma * omega * mu0 * h_magnitude
    
    # Limitar valores extremos (pode ocorrer em cálculos numéricos)
    j_magnitude = np.minimum(j_magnitude, 1e10)  # Limite físico ~1e10 A/m²
    
    return j_magnitude


def calculate_total_losses_circular_plate(
    outer_radius_m: float,
    inner_radius_m: float,
    thickness_m: float,
    current_a: float,
    frequency_hz: float,
    mu: float,
    sigma: float,
) -> dict:
    """Calcula as perdas totais por correntes induzidas na tampa circular.
    
    P = ∫∫∫ (J²/σ) dV
    
    Em coordenadas cilíndricas com simetria:
    dV = r dr dφ dz
    
    Args:
        outer_radius_m: Raio externo [m]
        inner_radius_m: Raio interno [m]
        thickness_m: Espessura [m]
        current_a: Corrente [A]
        frequency_hz: Frequência [Hz]
        mu: Permeabilidade [H/m]
        sigma: Condutividade [S/m]
    
    Returns:
        Dict com:
        - total_loss_w: Perdas totais [W]
        - max_h_field: Máximo de |H_φ| [A/m]
        - max_j_density: Máximo de |J_r| [A/m²]
        - skin_depth: Profundidade de penetração [m]
        - average_loss_density: Densidade de perdas média [W/m³]
    """
    omega = 2.0 * np.pi * frequency_hz
    
    # Profundidade de penetração
    delta = calculate_skin_depth(omega, mu, sigma)
    
    # Número de raios para integração
    n_radii = 100
    r_values = np.linspace(inner_radius_m, outer_radius_m, n_radii)
    
    # Calcular campos
    _, h_magnitude, _ = magnetic_field_circular_plate(
        r_values, outer_radius_m, inner_radius_m, current_a, frequency_hz, mu, sigma
    )
    
    j_magnitude = induced_current_density_circular_plate(
        r_values, h_magnitude, frequency_hz, sigma
    )
    
    # Máximos
    max_h = np.max(h_magnitude)
    max_j = np.max(j_magnitude)
    
    # Integração das perdas usando regra do trapézio
    # P = 2π ∫ (J²/σ) r dr dz
    # onde a integração em φ dá 2π e em z dá thickness
    
    loss_density = (j_magnitude ** 2) / sigma  # W/m³
    
    # Integração radial (considerar r como peso)
    integrand = loss_density * r_values
    integral_r = np.trapezoid(integrand, r_values)  # Integração em r
    
    # Total: P = 2π * thickness * ∫ (J²/σ) r dr
    total_loss_w = 2.0 * np.pi * thickness_m * integral_r
    
    # Densidade média
    volume_m3 = np.pi * (outer_radius_m**2 - inner_radius_m**2) * thickness_m
    avg_loss_density = total_loss_w / volume_m3 if volume_m3 > 0 else 0.0
    
    return {
        "total_loss_w": float(total_loss_w),
        "max_h_field": float(max_h),
        "max_j_density": float(max_j),
        "skin_depth": float(delta),
        "average_loss_density": float(avg_loss_density),
    }
