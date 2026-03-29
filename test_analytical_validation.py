#!/usr/bin/env python3
"""Test analytical loss calculation against reference table values."""

import numpy as np
from app.core.electromagnetics.biot_savart import calculate_loss_analytical

# Reference table values (gabarito)
REFERENCE_TABLE = {
    2000: 63.79,
    2250: 80.74,
    2500: 99.67,
    2800: 125.00,
}

# Physical parameters (default geometry at 60Hz)
FREQUENCY_HZ = 60.0  # Changed from 50Hz to 60Hz
THICKNESS_M = 0.005  # 5mm
MU = 1.256637e-4  # Aço transformador (mu_r ≈ 100)
SIGMA = 1.0e6  # Aço transformador
NUM_CONDUCTORS = 3

print("=" * 70)
print(f"Analytical Loss Validation (Reference: {FREQUENCY_HZ}Hz)")
print("=" * 70)
print(f"Material: Aço Transformador (μ={MU:.4e}, σ={SIGMA:.4e})")
print(f"Geometry: 590×270×5mm plate with {NUM_CONDUCTORS} conductors")
print(f"Frequency: {FREQUENCY_HZ}Hz")
print()

# Test analytical formula
print(f"{'Current (A)':>12} | {'Expected (W)':>12} | {'Computed (W)':>12} | {'Error (%)':>10}")
print("-" * 70)

for current_a, expected_w in REFERENCE_TABLE.items():
    # Calculate analytical loss
    computed_w = calculate_loss_analytical(
        im=current_a,
        thickness_m=THICKNESS_M,
        frequency_hz=FREQUENCY_HZ,
        mu=MU,
        sigma=SIGMA,
        num_conductors=NUM_CONDUCTORS,
    )
    
    # Calculate relative error
    error_pct = abs(computed_w - expected_w) / expected_w * 100
    
    print(f"{current_a:>12} | {expected_w:>12.2f} | {computed_w:>12.2f} | {error_pct:>9.2f}%")

print()
print("Note: Error percentage shows deviation from reference table values.")
print("      Values should match within 5% for proper calibration.")
