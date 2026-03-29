#!/usr/bin/env python3
"""
Compare the old method (generic Biot-Savart superposition) vs new method (specific 3-conductor).
"""

import sys
from pathlib import Path
import numpy as np

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.schemas.defaults import get_default_exercise01_input
from app.core.geometry.plate import create_plate_from_input
from app.core.geometry.mesh import create_uniform_mesh
from app.core.electromagnetics.biot_savart import (
    magnetic_field_three_conductors_analytic,
    magnetic_field_from_line_currents,
)
from app.core.electromagnetics.losses import calculate_losses


def compare_methods():
    """Compare old vs new field calculation."""
    
    input_model = get_default_exercise01_input()
    
    plate = create_plate_from_input(input_model.plate, input_model.holes)
    mesh = create_uniform_mesh(
        plate.width_m, plate.height_m, input_model.mesh.nx, input_model.mesh.ny
    )
    
    conductor_positions = np.array(
        [[c.x_mm * 1e-3, c.y_mm * 1e-3] for c in input_model.conductors]
    )
    conductor_currents = np.array([c.current_a for c in input_model.conductors])
    
    X, Y = mesh.get_mesh_arrays()
    dx, dy = mesh.get_dx_dy()
    valid_mask = plate.is_valid_point(X, Y).astype(float)
    
    print("=" * 80)
    print("COMPARISON: OLD METHOD vs NEW METHOD")
    print("=" * 80)
    
    # ─── OLD METHOD: Generic Biot-Savart superposition ────────────────────────
    h_field_old = magnetic_field_from_line_currents(
        X, Y, conductor_positions, conductor_currents, input_model.frequency_hz
    )
    
    loss_old = calculate_losses(
        h_field_old,
        valid_mask,
        dx,
        dy,
        input_model.frequency_hz,
        input_model.material.mu,
        input_model.material.sigma,
        input_model.plate.thickness_mm / 1000.0,
    )
    
    print(f"\nOLD METHOD (Generic Biot-Savart Superposition):")
    print(f"  Max H field:  {np.max(h_field_old[valid_mask > 0]):.2e} A/m")
    print(f"  Mean H field: {np.mean(h_field_old[valid_mask > 0]):.2e} A/m")
    print(f"  Total Loss:   {loss_old:.2f} W")
    
    # ─── NEW METHOD: 3-conductor analytic formula ────────────────────────────
    sorted_indices = np.argsort(conductor_positions[:, 0])
    sorted_positions = conductor_positions[sorted_indices]
    
    x_center = sorted_positions[1, 0]
    x_left = sorted_positions[0, 0]
    x_right = sorted_positions[2, 0]
    y_center = sorted_positions[1, 1]
    
    a = (x_center - x_left + x_right - x_center) / 2.0
    im = float(np.mean(np.abs(conductor_currents)))
    
    X_shifted = X - x_center
    Y_shifted = Y - y_center
    
    h_field_new = magnetic_field_three_conductors_analytic(
        X_shifted, Y_shifted, im, a
    )
    
    loss_new = calculate_losses(
        h_field_new,
        valid_mask,
        dx,
        dy,
        input_model.frequency_hz,
        input_model.material.mu,
        input_model.material.sigma,
        input_model.plate.thickness_mm / 1000.0,
    )
    
    print(f"\nNEW METHOD (3-Conductor Analytic Biot-Savart):")
    print(f"  Max H field:  {np.max(h_field_new[valid_mask > 0]):.2e} A/m")
    print(f"  Mean H field: {np.mean(h_field_new[valid_mask > 0]):.2e} A/m")
    print(f"  Total Loss:   {loss_new:.2f} W")
    
    print(f"\nCOMPARISON:")
    print(f"  Ratio (new/old): {loss_new/loss_old:.3f}")
    print(f"  Analytical Loss:   {63.78:.2f} W (gabarito reference)")
    print(f"  Old Approx Error:  {abs(loss_old - 63.78) / 63.78 * 100:.1f}%")
    print(f"  New Approx Error:  {abs(loss_new - 63.78) / 63.78 * 100:.1f}%")
    
    return loss_old, loss_new


if __name__ == "__main__":
    compare_methods()
