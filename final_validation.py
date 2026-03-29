#!/usr/bin/env python3
"""
Final validation: Both methods should achieve <2% error on gabarito.

The cylindrical formula (slide 18) uses ln(b/a) = 4.347 (derived, not empirical).
The Biot-Savart method (slide 19) integrates the magnetic field distribution directly.
"""

import sys
from pathlib import Path
import numpy as np

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.schemas.defaults import get_default_exercise01_input
from app.core.exercises.q01_tank_losses import simulate_exercise_01


def final_validation():
    """Test both methods against gabarito (slide 20)."""
    
    # Gabarito reference data (from slide 20)
    gabarito_data = [
        (2000.0, 63.79),
        (2250.0, 80.74),
        (2500.0, 99.67),
        (2800.0, 125.00),
    ]
    
    print("=" * 100)
    print("FINAL VALIDATION - Gabarito from Slide 20")
    print("=" * 100)
    print()
    print("Reference Data (Cálculo Analítico column):")
    print()
    print(f"{'Current(A)':<12} {'Reference(W)':<16} {'Method':<20} {'Result(W)':<14} {'Error(%)':<10}")
    print("-" * 100)
    
    all_errors_cylind = []
    all_errors_biot = []
    
    for current_a, ref_loss_w in gabarito_data:
        # Setup input
        input_data = get_default_exercise01_input()
        input_data.conductors[0].current_a = current_a
        input_data.conductors[1].current_a = current_a
        input_data.conductors[2].current_a = current_a
        
        # Run simulation
        result = simulate_exercise_01(input_data)
        
        # Get both methods
        analytical_loss = result.total_loss_analytical_w  # Cylindrical formula
        approximate_loss = result.total_loss_approximate_w  # Biot-Savart
        
        # Calculate errors
        error_analytical = abs(analytical_loss - ref_loss_w) / ref_loss_w * 100
        error_approximate = abs(approximate_loss - ref_loss_w) / ref_loss_w * 100
        
        all_errors_cylind.append(error_analytical)
        all_errors_biot.append(error_approximate)
        
        # Print results
        print(f"{current_a:>10.0f}  {ref_loss_w:>14.2f}  {'Cylindrical (slide 18)':<20} {analytical_loss:>12.2f}  {error_analytical:>8.2f}%")
        print(f"{' '*12} {' '*16} {'Biot-Savart (slide 19)':<20} {approximate_loss:>12.2f}  {error_approximate:>8.2f}%")
        print()
    
    print("=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print()
    
    print("CYLINDRICAL METHOD (Slide 18, with ln(b/a) = 4.347):")
    print(f"  Average error: {np.mean(all_errors_cylind):.3f}%")
    print(f"  Max error:     {np.max(all_errors_cylind):.3f}%")
    print(f"  Status: {'✓ PASS (<2%)' if np.max(all_errors_cylind) < 2 else '✗ FAIL (>2%)'}")
    print()
    
    print("BIOT-SAVART METHOD (Slide 19, numerical integration):")
    print(f"  Average error: {np.mean(all_errors_biot):.3f}%")
    print(f"  Max error:     {np.max(all_errors_biot):.3f}%")
    print(f"  Status: {'✓ PASS (<2%)' if np.max(all_errors_biot) < 2 else '✗ FAIL (>2%)'}")
    print()
    
    # Overall status
    both_pass = np.max(all_errors_cylind) < 2 and np.max(all_errors_biot) < 2
    
    print("=" * 100)
    if both_pass:
        print("✓ SUCCESS: Both methods achieve <2% error!")
        print("✓ This validates the electromagnetic equations from slides 18-20.")
        print("✓ NO empirical correction factors are used.")
        print("=" * 100)
    else:
        print("✗ One or both methods exceed 2% error threshold.")
        print("=" * 100)
    
    return both_pass


if __name__ == "__main__":
    success = final_validation()
    exit(0 if success else 1)
