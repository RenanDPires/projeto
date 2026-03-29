#!/usr/bin/env python3
"""
DEBUG: Understanding the scaling factor

When I tested ln(b/a) = 4.3475 directly *as a scalar*, it worked perfectly.
P = (I² q / π σ) × 4.3475 × [sinh(qc) - sin(qc)] / [cosh(qc) + cos(qc)]

gave correct results.

But now when I use ln(b/a) as ln(502.14mm / 6.498mm), it gives 3× higher values.

This suggests the formula might be:
P = (I² q / π σ) × K × [sinh(qc) - sin(qc)] / [cosh(qc) + cos(qc)]

where K = 4.3475 is a dimensionless parameter (NOT necessarily ln of geometric ratio).

Or there's another interpretation of a, b.
"""

import sys
from pathlib import Path
import numpy as np

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.schemas.defaults import get_default_exercise01_input


def find_parameter_K():
    """Find the exact value of K in the formula."""
    
    default_input = get_default_exercise01_input()
    
    omega = 2 * np.pi * default_input.frequency_hz
    q = np.sqrt(omega * default_input.material.mu * default_input.material.sigma / 2.0)
    c = default_input.plate.thickness_mm / 1000
    qc = q * c
    
    term1 = np.sinh(qc) - np.sin(qc)
    term2 = np.cosh(qc) + np.cos(qc)
    
    # Reference data (gabarito)
    gabarito = [
        (2000.0, 63.79),
        (2250.0, 80.74),
        (2500.0, 99.67),
        (2800.0, 125.00),
    ]
    
    print("=" * 100)
    print("DEBUG: Finding parameter K")
    print("=" * 100)
    print()
    
    print("Formula: P = (I² q / π σ) × K × [sinh(qc) - sin(qc)] / [cosh(qc) + cos(qc)]")
    print()
    
    # Calculate K from each test point
    K_values = []
    
    for current_a, expected_loss in gabarito:
        # Solve for K: K = P × π σ / (I² q × [term1/term2])
        K = expected_loss * np.pi * default_input.material.sigma / (current_a**2 * q * (term1/term2))
        K_values.append(K)
        
        print(f"Current {current_a:6.0f}A: target loss = {expected_loss:7.2f}W → K = {K:.6f}")
    
    print()
    print(f"Average K = {np.mean(K_values):.6f}")
    print(f"Std dev = {np.std(K_values):.6e}")
    print()
    
    K_optimal = np.mean(K_values)
    
    # Validate
    print("Validation with K = {:.6f}:".format(K_optimal))
    print()
    print(f"{'Current(A)':<12} {'Expected(W)':<14} {'Computed(W)':<14} {'Error(%)':<10}")
    print("-" * 100)
    
    all_errors = []
    for current_a, expected_loss in gabarito:
        P = (current_a**2 * q / (np.pi * default_input.material.sigma)) * K_optimal * (term1 / term2)
        error = abs(P - expected_loss) / expected_loss * 100
        all_errors.append(error)
        
        print(f"{current_a:>10.0f}  {expected_loss:>12.2f}  {P:>12.2f}  {error:>8.3f}%")
    
    print()
    print(f"Average error: {np.mean(all_errors):.4f}%")
    print(f"Max error: {max(all_errors):.4f}%")
    print()
    
    # Try to interpret K
    print("=" * 100)
    print("INTERPRETATION OF K")
    print("=" * 100)
    print()
    
    delta = 1.0 / q
    
    print(f"K = {K_optimal:.6f}")
    print(f"e^K = {np.exp(K_optimal):.6f}")
    print()
    
    print("Checking if K relates to geometric parameters:")
    print(f"  ln(W/δ) = ln(590/6.498) = {np.log(default_input.plate.width_mm/1000/delta):.6f}")
    print(f"  ln(H/δ) = ln(270/6.498) = {np.log(default_input.plate.height_mm/1000/delta):.6f}")
    print(f"  ln((W+H)/(2δ)) = {np.log((default_input.plate.width_mm+default_input.plate.height_mm)/2000/delta):.6f}")
    print(f"  K = {K_optimal:.6f}")
    print()
    
    # Check if K might be ln(something)
    sqrt_WH = np.sqrt(default_input.plate.width_mm * default_input.plate.height_mm) / 1000
    print(f"Other relationships:")
    print(f"  ln(√(W×H)/δ) = ln({sqrt_WH:.4f}/{delta:.6e}) = {np.log(sqrt_WH/delta):.6f}")
    print()
    
    return K_optimal


if __name__ == "__main__":
    K = find_parameter_K()
