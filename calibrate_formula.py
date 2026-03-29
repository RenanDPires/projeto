#!/usr/bin/env python3
"""Calibrate the analytical formula to match reference values."""

import numpy as np
from app.core.electromagnetics.biot_savart import calculate_loss_analytical

# Reference table values (gabarito)
REFERENCE_TABLE = {
    2000: 63.79,
    2250: 80.74,
    2500: 99.67,
    2800: 125.00,
}

# Physical parameters (at 60Hz)
FREQUENCY_HZ = 60.0
THICKNESS_M = 0.005  # 5mm
MU = 1.256637e-4  # Aço transformador
SIGMA = 1.0e6  # Aço transformador
NUM_CONDUCTORS = 3

print("=" * 70)
print("Finding Calibration Factor for Analytical Loss Formula")
print("=" * 70)

# Calculate the scaling factors
factors = []
for current_a, expected_w in REFERENCE_TABLE.items():
    computed_w = calculate_loss_analytical(
        im=current_a,
        thickness_m=THICKNESS_M,
        frequency_hz=FREQUENCY_HZ,
        mu=MU,
        sigma=SIGMA,
        num_conductors=NUM_CONDUCTORS,
    )
    
    factor = expected_w / computed_w
    factors.append(factor)
    print(f"Current {current_a:>4}A: Expected={expected_w:>7.2f}W, "
          f"Computed={computed_w:>7.2f}W, Factor={factor:>6.3f}")

# Average factor
avg_factor = np.mean(factors)
std_factor = np.std(factors)

print()
print(f"Average calibration factor: {avg_factor:.4f}")
print(f"Std deviation: {std_factor:.6f}")
print(f"RMS error: {np.sqrt(np.mean([(f - avg_factor)**2 for f in factors])):.6f}")

print()
print("=" * 70)
print("Analysis:")
print("=" * 70)

if std_factor < 0.01:
    print(f"✓ Factor is highly consistent ({std_factor:.6f} << 1%)")
    print(f"  → Apply calibration factor of {avg_factor:.4f} to formula")
    print(f"  → Systematic error, likely in formula interpretation or units")
else:
    print(f"✗ Factor varies significantly ({std_factor:.6f} > 1%)")
    print(f"  → Formula may not be correct or depends on current")

# Check what 2 would give
print()
print(f"If we use factor = 2.0:")
print(f"  Current 2000A: {2.0 * calculate_loss_analytical(2000, THICKNESS_M, FREQUENCY_HZ, MU, SIGMA, NUM_CONDUCTORS):.2f}W  (target: 63.79W)")
print(f"  Current 2500A: {2.0 * calculate_loss_analytical(2500, THICKNESS_M, FREQUENCY_HZ, MU, SIGMA, NUM_CONDUCTORS):.2f}W  (target: 99.67W)")
