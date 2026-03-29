#!/usr/bin/env python3
"""Detailed debugging of analytical loss formula."""

import numpy as np
from app.core.electromagnetics.biot_savart import calculate_loss_analytical

# Physical parameters (default geometry at 60Hz)
FREQUENCY_HZ = 60.0
THICKNESS_M = 0.005  # 5mm
MU = 1.256637e-4  # Aço transformador
SIGMA = 1.0e6  # Aço transformador
NUM_CONDUCTORS = 3
CURRENT_A = 2000.0

print("=" * 70)
print("Detailed Loss Formula Analysis")
print("=" * 70)

# Manual calculation to debug
omega = 2 * np.pi * FREQUENCY_HZ
print(f"\nBasic Parameters:")
print(f"  ω = 2π × f = 2π × {FREQUENCY_HZ} = {omega:.4f} rad/s")
print(f"  μ = {MU:.4e} H/m")
print(f"  σ = {SIGMA:.4e} S/m")
print(f"  c (thickness) = {THICKNESS_M:.4e} m")
print(f"  I = {CURRENT_A:.1f} A")

# q = inverse skin depth
q = np.sqrt(omega * MU * SIGMA / 2.0)
delta = 1.0 / q
print(f"\nSkin Depth Calculation:")
print(f"  q = sqrt(ω μ σ / 2) = {q:.4f} m⁻¹")
print(f"  δ = 1/q = {delta:.6e} m = {delta*1e6:.6f} μm")

# Radii
a = max(delta, 1e-6)
b = THICKNESS_M if THICKNESS_M > 0 else 1e-3
if b <= a:
    b = a * 2.0
log_ratio = np.log(b / a)

print(f"\nGeometric Radii:")
print(f"  a (inner radius) = {a:.6e} m")
print(f"  b (outer radius) = {b:.6e} m")
print(f"  ln(b/a) = {log_ratio:.6f}")

# Hyperbolic and trig terms
qc = q * THICKNESS_M
cosh_qc = np.cosh(qc)
sinh_qc = np.sinh(qc)
cos_qc = np.cos(qc)
sin_qc = np.sin(qc)

print(f"\nHyperbolic/Trig Terms (qc = {qc:.6f}):")
print(f"  sinh(qc) = {sinh_qc:.6f}")
print(f"  cosh(qc) = {cosh_qc:.6f}")
print(f"  sin(qc) = {sin_qc:.6f}")
print(f"  cos(qc) = {cos_qc:.6f}")

numerator = sinh_qc - sin_qc
denominator = cosh_qc + cos_qc
print(f"\nTransfer Function:")
print(f"  Numerator: sinh(qc) - sin(qc) = {numerator:.6f}")
print(f"  Denominator: cosh(qc) + cos(qc) = {denominator:.6f}")
print(f"  Transfer: {numerator / denominator:.6f}")

# Loss per conductor
loss_term = (CURRENT_A**2 * q / np.pi / SIGMA)
loss_per_conductor = loss_term * log_ratio * (numerator / denominator)
total_loss = NUM_CONDUCTORS * loss_per_conductor

print(f"\nLoss Calculation:")
print(f"  I² = {CURRENT_A**2:.6e} A²")
print(f"  I² × q / (π σ) = {loss_term:.6e}")
print(f"  × ln(b/a) = {loss_term * log_ratio:.6e}")
print(f"  × transfer function = {loss_per_conductor:.6e}")
print(f"  × {NUM_CONDUCTORS} conductors = {total_loss:.6e} W")

# Compare with function
computed = calculate_loss_analytical(
    im=CURRENT_A,
    thickness_m=THICKNESS_M,
    frequency_hz=FREQUENCY_HZ,
    mu=MU,
    sigma=SIGMA,
    num_conductors=NUM_CONDUCTORS,
)
print(f"\nFunction output: {computed:.2f} W")
print(f"Manual calc: {total_loss:.2f} W")
print(f"Expected (from table): 63.79 W")
print(f"\nRatio (Function / Expected): {computed / 63.79:.4f}")
