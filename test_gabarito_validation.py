#!/usr/bin/env python3
"""
Comprehensive validation test against 'gabarito' (reference table).

Tests the dual-method loss calculation system against known reference values
for transformer steel (aço transformador) at 60Hz with standard geometry.

Reference Table:
- Material: Aço Transformador (μ=1.256637e-4, σ=1.0e6)
- Geometry: 590×270×5mm, 3 conductors
- Frequency: 60Hz

Current (A) | Expected Loss (W) | Error Tolerance (%)
2000        | 63.79            | ±1%
2250        | 80.74            | ±1%
2500        | 99.67            | ±1%
2800        | 125.00           | ±1%
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.schemas.defaults import get_default_exercise01_input
from app.core.electromagnetics.biot_savart import calculate_loss_analytical


def validate_gabarito():
    """Validate dual-method losses against reference table."""
    
    # Reference table data
    gabarito = [
        {"current_a": 2000.0, "expected_loss_w": 63.79},
        {"current_a": 2250.0, "expected_loss_w": 80.74},
        {"current_a": 2500.0, "expected_loss_w": 99.67},
        {"current_a": 2800.0, "expected_loss_w": 125.00},
    ]
    
    # Get default configuration (60Hz, aço transformador)
    default_input = get_default_exercise01_input()
    
    # Extract material properties
    mu = default_input.material.mu
    sigma = default_input.material.sigma
    frequency_hz = default_input.frequency_hz
    thickness_m = default_input.plate.thickness_mm / 1000.0
    num_conductors = len(default_input.conductors)
    
    print("=" * 80)
    print("GABARITO VALIDATION TEST")
    print("=" * 80)
    print(f"\nConfiguration:")
    print(f"  Material: Aço Transformador")
    print(f"  μ = {mu:.6e} H/m")
    print(f"  σ = {sigma:.6e} S/m")
    print(f"  Frequency: {frequency_hz} Hz")
    print(f"  Plate: {default_input.plate.width_mm}×{default_input.plate.height_mm}×{thickness_m*1000:.1f}mm")
    print(f"  Conductors: {num_conductors}")
    print()
    
    # Test each current value
    all_passed = True
    results = []
    
    for test_case in gabarito:
        current_a = test_case["current_a"]
        expected_loss_w = test_case["expected_loss_w"]
        tolerance_pct = 1.0
        
        # Calculate analytical loss
        computed_loss_w = calculate_loss_analytical(
            im=current_a,
            thickness_m=thickness_m,
            frequency_hz=frequency_hz,
            mu=mu,
            sigma=sigma,
            num_conductors=num_conductors,
        )
        
        # Calculate error
        error_pct = abs(computed_loss_w - expected_loss_w) / expected_loss_w * 100.0
        is_passing = error_pct <= tolerance_pct
        status = "✅ PASS" if is_passing else "❌ FAIL"
        
        results.append({
            "current": current_a,
            "expected": expected_loss_w,
            "computed": computed_loss_w,
            "error": error_pct,
            "status": status,
        })
        
        if not is_passing:
            all_passed = False
        
        print(f"Current: {current_a:6.0f}A | Expected: {expected_loss_w:7.2f}W | "
              f"Computed: {computed_loss_w:7.2f}W | Error: {error_pct:6.3f}% {status}")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    # Statistics
    errors = [r["error"] for r in results]
    avg_error = sum(errors) / len(errors)
    max_error = max(errors)
    
    print(f"Average Error: {avg_error:.3f}%")
    print(f"Maximum Error: {max_error:.3f}%")
    print(f"Tolerance: ±1.0%")
    
    if all_passed:
        print(f"\n✅ ALL TESTS PASSED - GABARITO ACHIEVED")
        return True
    else:
        print(f"\n❌ SOME TESTS FAILED - GABARITO NOT ACHIEVED")
        return False


if __name__ == "__main__":
    success = validate_gabarito()
    sys.exit(0 if success else 1)
