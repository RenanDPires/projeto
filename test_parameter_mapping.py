#!/usr/bin/env python3
"""
Hypothesis 2: Understanding the parameter mapping

From the slides, the formula assumes:
- A cylindrical conductor of radius a
- Eddy currents induced in surrounding medium up to radius b

In the tank geometry:
- Conductor holes have diameter ~82mm (radius a1 ≈ 41mm)
- But conductors themselves are wires, maybe 5-10mm diameter?

Let me test if 'a' refers to conductor radius and 'b' to something physical.
"""

import sys
from pathlib import Path
import numpy as np

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.schemas.defaults import get_default_exercise01_input


def test_geometric_interpretations():
    """Test various interpretations of a, b parameters."""
    
    default_input = get_default_exercise01_input()
    
    omega = 2 * np.pi * default_input.frequency_hz
    q = np.sqrt(omega * default_input.material.mu * default_input.material.sigma / 2.0)
    delta = 1.0 / q
    c = default_input.plate.thickness_mm / 1000
    qc = q * c
    
    print("=" * 110)
    print("HYPOTHESIS 2: Conductor Radius-based Interpretation")
    print("=" * 110)
    print()
    
    print(f"Skin depth δ = {delta*1000:.4f} mm")
    print(f"Plate thickness c = {c*1000:.1f} mm")
    print()
    
    # From geometry: conductors pass through holes of 82mm diameter
    hole_radius = 82 / 2 / 1000  # mm → m
    
    print("POSSIBILITY A: a = hole radius, b = varies")
    print(f"  a = 82/2 mm = {hole_radius*1000:.1f} mm = {hole_radius:.6e}m")
    print()
    
    # The question: what is b?
    # Option 1: b related to spacing between conductors
    conductor_spacing_mm = 214  # 295 - 100 = 195mm
    
    print("Testing different 'b' values:")
    print()
    
    test_cases = [
        ("b = hole radius + δ", hole_radius + delta),
        ("b = hole radius + 2δ", hole_radius + 2*delta),
        ("b = hole radius × 2", hole_radius * 2),
        ("b = hole radius × 3", hole_radius * 3),
        ("b = half distance to neighbor", hole_radius + conductor_spacing_mm/1000/2),
        ("b = quarter plate width", hole_radius + default_input.plate.width_mm/1000/4),
        ("b = quarter plate height", hole_radius + default_input.plate.height_mm/1000/4),
    ]
    
    target_loss = 63.79
    
    for label, b_val in test_cases:
        if b_val <= hole_radius:
            print(f"  {label:<40} b = {b_val*1000:8.4f}mm - INVALID (b ≤ a)")
            continue
        
        ln_ratio = np.log(b_val / hole_radius)
        
        term1 = np.sinh(qc) - np.sin(qc)
        term2 = np.cosh(qc) + np.cos(qc)
        
        # Power for one conductor or all three?
        # Try for all 3 conductors with combined current effect
        I = 2000
        P_single = (I**2 * q / (np.pi * default_input.material.sigma)) * ln_ratio * (term1 / term2)
        
        # Maybe we need to account for 3 conductors differently?
        P_three_simple = 3 * P_single  # Adding them
        
        error_single = abs(P_single - target_loss) / target_loss * 100
        error_three = abs(P_three_simple - target_loss) / target_loss * 100
        
        print(f"  {label:<40} b = {b_val*1000:8.4f}mm")
        print(f"      ln(b/a) = {ln_ratio:8.4f}")
        print(f"      P(1 conductor) = {P_single:8.2f}W (error: {error_single:6.1f}%)", end="")
        if error_single < 5:
            print(" ✓")
        else:
            print()
        
        if error_three < 5:
            print(f"      P(3 conductors) = {P_three_simple:8.2f}W (error: {error_three:6.1f}%) ✓")
        print()


def test_alternative_formula():
    """
    Maybe the formula interpretation is different. 
    What if the formula accounts for multiple conductors differently?
    """
    print()
    print("=" * 110)
    print("HYPOTHESIS 3: Alternative Parameter Interpretation")
    print("=" * 110)
    print()
    
    default_input = get_default_exercise01_input()
    
    omega = 2 * np.pi * default_input.frequency_hz
    q = np.sqrt(omega * default_input.material.mu * default_input.material.sigma / 2.0)
    delta = 1.0 / q
    c = default_input.plate.thickness_mm / 1000
    qc = q * c
    
    # What if a and b are not related to conductor geometry directly,
    # but to the extent of the eddy current region?
    
    # Theory: eddy currents flow within ~δ (skin depth) near the conductor
    # and spread out over distance ~ √(c*L_characteristic)
    
    # Try: a = δ, b determined by boundary condition
    a = delta
    
    # The conductor spacing gives us a characteristic length
    # Maybe b/a should be related to conductor spacing?
    conductor_spacing = 214 / 1000  # mm → m
    
    test_ratios = [
        ("ln(b/a) = 2", 2.0),
        ("ln(b/a) = 2.5", 2.5),
        ("ln(b/a) = 3", 3.0),
        ("ln(b/a) = 3.5", 3.5),
        ("ln(b/a) = 3.92 (spacing/a)", np.log(conductor_spacing/a if a > 0 else 1)),
        ("ln(b/a) = 4", 4.0),
        ("ln(b/a) = 4.5", 4.5),
        ("ln(b/a) = 5", 5.0),
    ]
    
    target_loss = 63.79
    
    print("Testing ln(b/a) values (with a = skin depth):")
    print()
    
    for label, ln_ratio in test_ratios:
        term1 = np.sinh(qc) - np.sin(qc)
        term2 = np.cosh(qc) + np.cos(qc)
        
        I = 2000
        P = (I**2 * q / (np.pi * default_input.material.sigma)) * ln_ratio * (term1 / term2)
        
        error = abs(P - target_loss) / target_loss * 100
        
        status = "✓ MATCH!" if error < 2 else ""
        print(f"  {label:<35} P(2000A) = {P:8.2f}W (error: {error:5.1f}%) {status}")


if __name__ == "__main__":
    test_geometric_interpretations()
    test_alternative_formula()
