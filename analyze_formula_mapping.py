#!/usr/bin/env python3
"""
Exercise 01 - Rigorous Analysis from Prof. Mauricio's Slides (Pages 16-20)

THEORETICAL FOUNDATION:
======================

1. ELECTROMAGNETIC DIFFUSION (Page 16)
   ∇²H = i ω μ σ H  (Vector Helmholtz equation)

2. CYLINDRICAL SOLUTION (Page 16)
   For a conductor in a conducting medium:
   H_φ = (I/(2πr)) × [cosh(qz)cos(qz) + i sinh(qz)sin(qz)] / [cosh(qc/2)cos(qc/2) + i sinh(qc/2)sin(qc/2)]
   
   where: q = (1/δ) = √(ωμσ/2)

3. CURRENT DENSITY (Page 17)
   j_r = curl(H)
   
4. POWER LOSS (Page 18) - EXACT FORMULA
   P = ∫∫ |J_r|²/σ dA dz
   
   After integration:
   ╔════════════════════════════════════════════════════════════════════╗
   ║ P = (I² q / (π σ)) × ln(b/a) × [sinh(qc) - sin(qc)] / [cosh(qc) + cos(qc)] ║
   ║                                                                                 ║
   ║ where:                                                              ║
   ║   q = √(ωμσ/2)                                                     ║
   ║   I = RMS current                                                  ║
   ║   ω = 2πf                                                          ║
   ║   σ = conductivity (S/m)                                           ║
   ║   μ = permeability (H/m)                                           ║
   ║   a = inner radius (skin depth δ)                                  ║
   ║   b = outer radius                                                 ║
   ║   c = conductor length (thickness of plate)                        ║
   ╚════════════════════════════════════════════════════════════════════╝

5. BIOT-SAVART NUMERICAL METHOD (Page 19)
   H_m(x,y) = (I_m × a)/(2π) × √[(3x²+3y²+a²) / ((x²+y²)(denominator))]
   
   P = (1/2) × √(ωμ/(2σ)) × ∫∫ |H_m(x,y)|² dx dy

REFERENCE DATA (Page 20 - GABARITO):
====================================
Corrente (A) | Perdas Analíticas (W) | Medição Temperatura (W)
    2000     |       63.79          |       64.50
    2250     |       80.74          |       73.70
    2500     |       99.67          |       94.60
    2800     |      125.00          |      119.30

TARGET: Match analytic results with ≤2% error
"""

import sys
from pathlib import Path
import numpy as np

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.schemas.defaults import get_default_exercise01_input


def analyze_geometric_parameters():
    """
    Map physical geometry to cylindrical formula parameters.
    
    ISSUE TO SOLVE:
    The formula assumes a single cylindrical conductor in infinite medium.
    Reality: 3 parallel conductors in a finite plate.
    
    Question: How do a, b, c map to the tank geometry?
    """
    
    default_input = get_default_exercise01_input()
    
    print("=" * 100)
    print("ANALYSIS: Physical Geometry → Cylindrical Formula Parameters")
    print("=" * 100)
    print()
    
    print("PHYSICAL GEOMETRY:")
    print(f"  Plate Width:  {default_input.plate.width_mm:.1f} mm")
    print(f"  Plate Height: {default_input.plate.height_mm:.1f} mm")
    print(f"  Plate Thickness (c): {default_input.plate.thickness_mm:.1f} mm = {default_input.plate.thickness_mm/1000:.6f} m")
    print()
    
    print("CONDUCTORS:")
    for i, cond in enumerate(default_input.conductors):
        print(f"  Conductor {i+1}: ({cond.x_mm:.1f}mm, {cond.y_mm:.1f}mm), I = {cond.current_a:.0f}A")
    print()
    
    print("MATERIAL (Aço Transformador):")
    print(f"  μ = {default_input.material.mu:.6e} H/m")
    print(f"  σ = {default_input.material.sigma:.6e} S/m")
    print()
    
    print("PARAMETERS FOR CYLINDRICAL FORMULA:")
    print()
    
    # Calculate q
    omega = 2 * np.pi * default_input.frequency_hz
    q = np.sqrt(omega * default_input.material.mu * default_input.material.sigma / 2.0)
    delta = 1.0 / q
    
    print(f"  ω = 2π × {default_input.frequency_hz} = {omega:.4f} rad/s")
    print(f"  q = √(ωμσ/2) = √({omega:.4f} × {default_input.material.mu:.6e} × {default_input.material.sigma:.6e} / 2)")
    print(f"    = {q:.4f} m⁻¹")
    print(f"  δ (skin depth) = 1/q = {delta:.6e} m = {delta*1000:.6f} mm")
    print()
    
    print("GEOMETRIC PARAMETER MAPPING (Unknown):")
    print("  a = ??? (What is the 'inner radius'?)")
    print("  b = ??? (What is the 'outer radius'?)")
    print("  c = {:10.6f} m (plate thickness - THIS IS KNOWN)".format(default_input.plate.thickness_mm/1000))
    print()
    
    # Test different interpretations
    print("=" * 100)
    print("HYPOTHESIS TESTING")
    print("=" * 100)
    print()
    
    # Hypothesis 1: a = δ (skin depth), b = δ + plate thickness/2
    print("HYPOTHESIS 1: Radial extent of eddy current field")
    print("  a = δ = skin depth")
    print("  b = δ + (plate height / some factor)")
    print()
    
    a1 = delta
    # Try different values for b
    for factor in [2, 3, 4, 5, 10]:
        b1 = a1 + default_input.plate.height_mm / 1000 / factor
        

        # Calculate power loss (single conductor)
        c = default_input.plate.thickness_mm / 1000
        qc = q * c
        
        term1 = np.sinh(qc) - np.sin(qc)
        term2 = np.cosh(qc) + np.cos(qc)
        
        I = 2000.0
        P1 = (I**2 * q / (np.pi * default_input.material.sigma)) * np.log(b1/a1) * (term1 / term2)
        
        print(f"    Factor {factor:2.0f}: b = δ + H/f → b = {b1:.6e} m")
        print(f"              ln(b/a) = {np.log(b1/a1):.6f}")
        print(f"              P(2000A) = {P1:.2f}W (target: 63.79W, error: {abs(P1-63.79)/63.79*100:.1f}%)")
        print()


if __name__ == "__main__":
    analyze_geometric_parameters()
