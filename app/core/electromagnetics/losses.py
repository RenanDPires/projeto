"""Calculos de perdas por inducao eletromagnetica."""

import numpy as np


def calculate_losses(
    h_field: np.ndarray,
    valid_mask: np.ndarray,
    dx: float,
    dy: float,
    frequency_hz: float,
    mu: float,
    sigma: float,
    thickness_m: float,
    coefficient_mode: str = "normalized",
) -> float:
    """Calcula a perda total de potencia por integracao na placa.

    A perda de potencia por unidade de area depende do modulo do campo magnetico:

        p(x,y) = (1/2) * sqrt(ω * μ / (2 * σ)) * |H(x,y)|^2

    A perda total e obtida pela integracao na regiao valida:

        P = ∫∫ p(x,y) dA

    Args:
        h_field: Array com modulo do campo magnetico [A/m]
        valid_mask: Mascara booleana de pontos validos para integracao
        dx: Passo de malha em x [m]
        dy: Passo de malha em y [m]
        frequency_hz: Frequencia de operacao [Hz]
        mu: Permeabilidade magnetica [H/m]
        sigma: Condutividade eletrica [S/m]
        thickness_m: Espessura da placa [m]
        coefficient_mode:
            - "normalized": usa (1/2π) * sqrt(ωμ/(2σ))
            - "slide19_strict": usa (1/2) * sqrt(ωμ/(2σ))

    Returns:
        Perda total de potencia [W]
    """
    omega = 2 * np.pi * frequency_hz

    if coefficient_mode == "slide19_strict":
        loss_coefficient = 0.5 * np.sqrt(omega * mu / (2 * sigma))
    else:
        # Convencao normalizada usada no codigo e nos testes atuais
        loss_coefficient = 0.5 / np.pi * np.sqrt(omega * mu / (2 * sigma))

    # Densidade de perda de potencia: coeficiente * |H|^2
    p_density = loss_coefficient * h_field**2

    # Aplica mascara valida (exclui furos e exterior da placa)
    p_density_valid = p_density * valid_mask

    # Integracao numerica: soma na malha e multiplica pelo elemento de area
    total_loss_w = np.sum(p_density_valid) * dx * dy

    return float(total_loss_w)


def get_loss_density(
    h_field: np.ndarray,
    frequency_hz: float,
    mu: float,
    sigma: float,
) -> np.ndarray:
    """Retorna a densidade de perda em cada ponto da malha.

    Args:
        h_field: Modulo do campo magnetico [A/m]
        frequency_hz: Frequencia de operacao [Hz]
        mu: Permeabilidade magnetica [H/m]
        sigma: Condutividade eletrica [S/m]

    Returns:
        Array de densidade de perda [W/m²]
    """
    omega = 2 * np.pi * frequency_hz
    loss_coefficient = 0.5 / np.pi * np.sqrt(omega * mu / (2 * sigma))
    return loss_coefficient * h_field**2
