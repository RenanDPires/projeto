"""Orquestração da simulação da Questão 01 (perdas no tanque)."""

import numpy as np
from app.schemas import Exercise01Input, Exercise01Result
from app.core.geometry.plate import create_plate_from_input
from app.core.geometry.mesh import create_uniform_mesh
from app.core.electromagnetics.biot_savart import (
    magnetic_field_three_conductors_analytic,
    magnetic_field_from_line_currents,
    calculate_loss_analytical,
)
from app.core.electromagnetics.losses import calculate_losses, get_loss_density


def _calcular_campo_magnetico(
    x: np.ndarray,
    y: np.ndarray,
    conductor_positions: np.ndarray,
    conductor_currents: np.ndarray,
    frequency_hz: float,
) -> tuple[np.ndarray, float | None, float]:
    """Calcula |H| via Biot-Savart (fechado para 3 condutores ou genérico).

    Retorna:
        h_field: Campo magnético resultante [A/m]
        param_a_m: Espaçamento médio entre condutores [m] quando aplicável
        param_im_a: Corrente de referência Im [A]
    """
    param_a_m = None
    param_im_a = (
        float(np.mean(np.abs(conductor_currents))) if len(conductor_currents) > 0 else 0.0
    )

    if len(conductor_positions) == 3:
        sorted_indices = np.argsort(conductor_positions[:, 0])
        sorted_positions = conductor_positions[sorted_indices]
        sorted_currents = conductor_currents[sorted_indices]

        x_left = sorted_positions[0, 0]
        x_center = sorted_positions[1, 0]
        x_right = sorted_positions[2, 0]
        y_center = sorted_positions[1, 1]

        a_left = x_center - x_left
        a_right = x_right - x_center
        a = (a_left + a_right) / 2.0
        param_a_m = float(a)

        tol_pos = 1e-9
        tol_spacing = max(1e-9, 1e-3 * max(abs(a_left), abs(a_right), 1.0))
        y_span = np.max(np.abs(sorted_positions[:, 1] - y_center))
        collinear = y_span <= tol_pos
        equally_spaced = abs(a_left - a_right) <= tol_spacing and a_left > 0 and a_right > 0
        same_sign = np.all(sorted_currents >= 0) or np.all(sorted_currents <= 0)
        abs_currents = np.abs(sorted_currents)
        tol_current = max(1e-9, 1e-3 * max(float(np.max(abs_currents)), 1.0))
        same_magnitude = float(np.max(abs_currents) - np.min(abs_currents)) <= tol_current

        if collinear and equally_spaced and same_sign and same_magnitude:
            im = float(np.mean(abs_currents))
            param_im_a = im
            x_shifted = x - x_center
            y_shifted = y - y_center
            h_field = magnetic_field_three_conductors_analytic(x_shifted, y_shifted, im, a)
        else:
            h_field = magnetic_field_from_line_currents(
                x, y, conductor_positions, conductor_currents, frequency_hz
            )
    else:
        h_field = magnetic_field_from_line_currents(
            x, y, conductor_positions, conductor_currents, frequency_hz
        )

    return h_field, param_a_m, param_im_a


def _calcular_perdas_biot_savart(
    h_field: np.ndarray,
    valid_mask: np.ndarray,
    dx: float,
    dy: float,
    input_model: Exercise01Input,
    thickness_m: float,
) -> tuple[float, float]:
    """Calcula perdas pelo método Biot-Savart (normalizado e slide 19 estrito)."""
    total_loss_approximate = calculate_losses(
        h_field,
        valid_mask,
        dx,
        dy,
        input_model.frequency_hz,
        input_model.material.mu,
        input_model.material.sigma,
        thickness_m,
        coefficient_mode="normalized",
    )

    total_loss_approximate_slide19_strict = calculate_losses(
        h_field,
        valid_mask,
        dx,
        dy,
        input_model.frequency_hz,
        input_model.material.mu,
        input_model.material.sigma,
        thickness_m,
        coefficient_mode="slide19_strict",
    )

    return total_loss_approximate, total_loss_approximate_slide19_strict


def _calcular_perdas_analitico(
    conductor_currents: np.ndarray,
    thickness_m: float,
    input_model: Exercise01Input,
) -> float:
    """Calcula perdas pelo método analítico (fórmula cilíndrica)."""
    im_rms = (
        float(np.mean(np.abs(conductor_currents))) if len(conductor_currents) > 0 else 0.0
    )
    return calculate_loss_analytical(
        im=im_rms,
        thickness_m=thickness_m,
        frequency_hz=input_model.frequency_hz,
        mu=input_model.material.mu,
        sigma=input_model.material.sigma,
        num_conductors=len(input_model.conductors),
    )


def simulate_exercise_01(input_model: Exercise01Input) -> Exercise01Result:
    """Executa a simulação completa da Questão 01."""
    # Conversão para SI e construção da geometria
    plate = create_plate_from_input(input_model.plate, input_model.holes)
    mesh = create_uniform_mesh(
        plate.width_m, plate.height_m, input_model.mesh.nx, input_model.mesh.ny
    )

    # Condutores em SI
    conductor_positions = np.array(
        [[c.x_mm * 1e-3, c.y_mm * 1e-3] for c in input_model.conductors]
    )
    conductor_currents = np.array([c.current_a for c in input_model.conductors])

    # Coordenadas da malha
    x, y = mesh.get_mesh_arrays()
    dx, dy = mesh.get_dx_dy()

    # Método Biot-Savart: campo magnético
    h_field, param_a_m, param_im_a = _calcular_campo_magnetico(
        x, y, conductor_positions, conductor_currents, input_model.frequency_hz
    )

    # Máscara de integração (interior da placa e fora dos furos)
    valid_mask = plate.is_valid_point(x, y).astype(float)

    # Método Biot-Savart: perdas
    total_loss_approximate, total_loss_approximate_slide19_strict = _calcular_perdas_biot_savart(
        h_field,
        valid_mask,
        dx,
        dy,
        input_model,
        plate.thickness_m,
    )

    # Método analítico: perdas
    total_loss_analytical = _calcular_perdas_analitico(
        conductor_currents,
        plate.thickness_m,
        input_model,
    )

    # Densidade de perda para métricas auxiliares
    loss_density = get_loss_density(
        h_field, input_model.frequency_hz, input_model.material.mu, input_model.material.sigma
    )

    # Estatísticas
    max_h_field = float(np.max(h_field[valid_mask > 0])) if np.any(valid_mask) else 0.0
    max_loss_density = float(np.max(loss_density * valid_mask))
    valid_area_m2 = plate.get_valid_area_m2()

    # Notas de simulação
    relative_diff = (
        abs(total_loss_analytical - total_loss_approximate) / total_loss_analytical * 100.0
        if total_loss_analytical > 0
        else 0.0
    )
    notes = [
        f"Resolucao da malha: {input_model.mesh.nx}x{input_model.mesh.ny} pontos",
        f"Numero de furos: {len(input_model.holes)}",
        f"Numero de condutores: {len(input_model.conductors)}",
        f"Frequencia de operacao: {input_model.frequency_hz} Hz",
        f"Parametros slide 19: a={((param_a_m or 0.0) * 1000):.1f} mm, x={input_model.plate.width_mm:.1f} mm, y={input_model.plate.height_mm:.1f} mm, Im={param_im_a:.1f} A",
        f"Diferenca (analitico vs Biot-Savart): {relative_diff:.2f}%",
        f"Resultado Biot-Savart com coeficiente estrito slide 19: {total_loss_approximate_slide19_strict:.2f} W",
    ]

    return Exercise01Result(
        total_loss_analytical_w=total_loss_analytical,
        total_loss_approximate_w=total_loss_approximate,
        max_h_field=max_h_field,
        max_loss_density=max_loss_density,
        valid_area_m2=valid_area_m2,
        notes=notes,
    )
