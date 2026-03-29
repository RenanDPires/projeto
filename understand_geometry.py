#!/usr/bin/env python3
"""
Hypothesis: The formula uses parameters a, b but the relationship K = ln(b/a)
might involve some geometric scaling that I'm not considering correctly.

The formula from slide 18 is for a CYLINDER, but we have a REC TANGULAR PLATE.

Possibility 1: a and b come from effective cylindrical approximation
Possibility 2: K is already the correct value and should be used directly
Possibility 3: a, b should scale with plate geometry differently

Let me check if K is related to the number of conductors...
"""

import sys
from pathlib import Path
import numpy as np

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.schemas.defaults import get_default_exercise01_input


def test_whether_K_depends_on_num_conductors():
    """
    If the formula is for ONE conductor, and we have 3, maybe:
    - K should be divided by 3?
    - Or the loss should be multiplied by 3?
    - Or K should be computed per conductor?
    """
    
    default_input = get_default_exercise01_input()
    
    omega = 2 * np.pi * default_input.frequency_hz
    q = np.sqrt(omega * default_input.material.mu * default_input.material.sigma / 2.0)
    c = default_input.plate.thickness_mm / 1000
    qc = q * c
    
    term1 = np.sinh(qc) - np.sin(qc)
    term2 = np.cosh(qc) + np.cos(qc)
    
    # Reference data
    current_test = 2000.0
    expected_loss_total = 63.79
    
    print("=" * 100)
    print("TEST: Relationship between K and number of conductors")
    print("=" * 100)
    print(f"\nTest case: {current_test}A → {expected_loss_total}W (total for 3 conductors)")
    print()
    
    # Hypothesis 1: K is for total (all 3 conductors together)
    # This is what we've been assuming
    K_total = expected_loss_total * np.pi * default_input.material.sigma / (current_test**2 * q * (term1/term2))
    print(f"Hypothesis 1: K applies to total loss")
    print(f"  K_total = {K_total:.6f}")
    print(f"  ln(b/a) = {K_total:.6f}")
    print(f"  b/a = e^{K_total:.6f} = {np.exp(K_total):.6f}")
    print()
    
    # Hypothesis 2: K is per conductor, so total = K × num_conductors
    # Then K_per = K_total / 3
    K_per_conductor = K_total / 3
    print(f"Hypothesis 2: K is per conductor, total = 3 × K")
    print(f"  K_per = {K_per_conductor:.6f}")
    print(f"  ln(b/a) = {K_per_conductor:.6f}")
    print(f"  b/a = e^{K_per_conductor:.6f} = {np.exp(K_per_conductor):.6f}")
    print()
    
    # Hypothesis 3: The formula should be divided by 3 due to geometry
    # P_cylinder = (I² q / π σ) × ln(b/a) × [...]
    # But we have 3 conductors, and the current is total (not per conductor)
    # Maybe effective I = I_total / √3 for 3-phase?
    I_per_phase = current_test / np.sqrt(3)
    K_if_current_per_phase = expected_loss_total * np.pi * default_input.material.sigma / (I_per_phase**2 * q * (term1/term2))
    print(f"Hypothesis 3: Current is per-phase (I_total/√3)")
    print(f"  I_per_phase = {I_per_phase:.2f}A")
    print(f"  K_if_per_phase = {K_if_current_per_phase:.6f}")
    print()
    
    # Let's also check dimensions
    print("=" * 100)
    print("Check: Dimensional analysis")
    print("=" * 100)
    print()
    
    delta = 1.0 / q
    print(f"Skin depth δ = {delta*1000:.4f} mm = {delta:.6e} m")
    print(f"Plate thickness c = {c*1000:.1f} mm = {c:.6e} m")
    print(f"Plate width W = {default_input.plate.width_mm:.1f} mm")
    print(f"Plate height H = {default_input.plate.height_mm:.1f} mm")
    print()
    
    # For a rectangular geometry mapped to cylindrical
    # Maybe:
    # a = δ (skin depth at conductor surface)
    # b = ???
    print(f"If a = δ = {delta*1000:.4f} mm and K = ln(b/a) = 4.3467:")
    b1 = delta * np.exp(K_total)
    print(f"  Then b = {b1*1000:.2f} mm")
    print()
    
    # Or maybe effective radius based on plate area
    # A ≈ π b²  →  b ≈ √(A/π)
    A = (default_input.plate.width_mm * default_input.plate.height_mm) / (1000**2)
    b_from_area = np.sqrt(A / np.pi)
    print(f"Plate area A = W × H = {default_input.plate.width_mm:.0f} × {default_input.plate.height_mm:.0f} = {A:.6f} m²")
    print(f"If this were circular: b = √(A/π) = {b_from_area*100:.2f} cm")
    print(f"  ln(b/δ) = ln({b_from_area*100:.2f}cm / {delta*1000:.4f}mm) = {np.log(b_from_area/delta):.6f}")
    print()
    
    # Or perimeter-based
    perimeter = 2 * (default_input.plate.width_mm + default_input.plate.height_mm) / 1000
    b_from_perimeter = perimeter / (2 * np.pi)
    print(f"Plate perimeter L = 2(W+H) = {perimeter*1000:.0f} mm")
    print(f"If this were circular: b = L/(2π) = {b_from_perimeter*1000:.2f} mm")
    print(f"  ln(b/δ) = ln({b_from_perimeter*1000:.2f}mm / {delta*1000:.4f}mm) = {np.log(b_from_perimeter/delta):.6f}")
    print()


if __name__ == "__main__":
    test_whether_K_depends_on_num_conductors()
