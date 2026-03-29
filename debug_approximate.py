#!/usr/bin/env python3
"""
Debug the approximate method calculation in detail.
"""

import sys
from pathlib import Path
import numpy as np

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.schemas.defaults import get_default_exercise01_input
from app.core.geometry.plate import create_plate_from_input
from app.core.geometry.mesh import create_uniform_mesh
from app.core.electromagnetics.biot_savart import magnetic_field_three_conductors_analytic
from app.core.electromagnetics.losses import calculate_losses


def debug_approximate_method():
    """Debug the approximate method step by step."""
    
    input_model = get_default_exercise01_input()
    
    # Setup
    plate = create_plate_from_input(input_model.plate, input_model.holes)
    mesh = create_uniform_mesh(
        plate.width_m, plate.height_m, input_model.mesh.nx, input_model.mesh.ny
    )
    
    conductor_positions = np.array(
        [[c.x_mm * 1e-3, c.y_mm * 1e-3] for c in input_model.conductors]
    )
    conductor_currents = np.array([c.current_a for c in input_model.conductors])
    
    print("=" * 80)
    print("DEBUG: APPROXIMATE METHOD CALCULATION")
    print("=" * 80)
    
    # Get mesh
    X, Y = mesh.get_mesh_arrays()
    dx, dy = mesh.get_dx_dy()
    
    print(f"\nMesh Setup:")
    print(f"  dx = {dx:.6e} m")
    print(f"  dy = {dy:.6e} m")
    print(f"  Total area covered: {X.shape[0] * X.shape[1] * dx * dy:.6f} m²")
    
    # Conductor analysis
    if len(conductor_positions) == 3:
        sorted_indices = np.argsort(conductor_positions[:, 0])
        sorted_positions = conductor_positions[sorted_indices]
        
        x_left = sorted_positions[0, 0]
        x_center = sorted_positions[1, 0]
        x_right = sorted_positions[2, 0]
        y_center = sorted_positions[1, 1]
        
        a_left = x_center - x_left
        a_right = x_right - x_center
        a = (a_left + a_right) / 2.0
        im = float(np.mean(np.abs(conductor_currents)))
        
        print(f"\nConductor Configuration:")
        print(f"  Left conductor:   x = {x_left*1000:.2f} mm")
        print(f"  Center conductor: x = {x_center*1000:.2f} mm")
        print(f"  Right conductor:  x = {x_right*1000:.2f} mm")
        print(f"  Spacing a = {a*1000:.2f} mm")
        print(f"  Current im = {im:.2f} A")
        
        # Shift coordinates
        X_shifted = X - x_center
        Y_shifted = Y - y_center
        
        # Calculate field
        h_field = magnetic_field_three_conductors_analytic(
            X_shifted, Y_shifted, im, a
        )
        
        print(f"\nMagnetic Field Statistics:")
        print(f"  Min H: {np.min(h_field):.2e} A/m")
        print(f"  Max H: {np.max(h_field):.2e} A/m")
        print(f"  Mean H: {np.mean(h_field):.2e} A/m")
        print(f"  Std H: {np.std(h_field):.2e} A/m")
        
        # Valid mask
        valid_mask = plate.is_valid_point(X, Y).astype(float)
        valid_count = np.sum(valid_mask)
        print(f"\nMask Statistics:")
        print(f"  Valid points: {valid_count:.0f} / {X.shape[0]*X.shape[1]:.0f}")
        print(f"  Valid area: {valid_count * dx * dy:.6f} m²")
        
        # Field in valid region
        h_valid = h_field[valid_mask > 0]
        print(f"\nField in Valid Region:")
        print(f"  Min H: {np.min(h_valid):.2e} A/m")
        print(f"  Max H: {np.max(h_valid):.2e} A/m")
        print(f"  Mean H: {np.mean(h_valid):.2e} A/m")
        
        # Loss coefficient
        omega = 2 * np.pi * input_model.frequency_hz
        loss_coeff = 0.5 * np.sqrt(omega * input_model.material.mu / (2 * input_model.material.sigma))
        print(f"\nLoss Coefficient:")
        print(f"  ω = {omega:.2f} rad/s")
        print(f"  μ = {input_model.material.mu:.6e} H/m")
        print(f"  σ = {input_model.material.sigma:.2e} S/m")
        print(f"  Coefficient = 0.5*√(ω*μ/(2σ)) = {loss_coeff:.6e}")
        
        # Loss density
        loss_density = loss_coeff * h_field ** 2
        loss_density_valid = loss_density * valid_mask
        
        print(f"\nLoss Density:")
        print(f"  Max density: {np.max(loss_density_valid):.2f} W/m²")
        print(f"  Mean density (valid): {np.mean(loss_density_valid[valid_mask > 0]):.2f} W/m²")
        
        # Total integration
        total_loss = np.sum(loss_density_valid) * dx * dy
        print(f"\nTotal Loss Integration:")
        print(f"  Total loss = Σ(density) * dx * dy = {total_loss:.2f} W")


if __name__ == "__main__":
    debug_approximate_method()
