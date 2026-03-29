#!/usr/bin/env python3
"""
Test the Biot-Savart method (the CORRECT method from slide 19).
This should give us the true analytical result without any empirical factors.
"""

import sys
from pathlib import Path
import numpy as np

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.schemas.defaults import get_default_exercise01_input
from app.core.exercises.q01_tank_losses import simulate_exercise_01


def test_biot_savart_method():
    """Test the Biot-Savart method against gabarito."""
    
    input_data = get_default_exercise01_input()
    
    # Test with different currents
    test_currents = [2000.0, 2250.0, 2500.0, 2800.0]
    gabarito = [63.79, 80.74, 99.67, 125.00]
    
    print("=" * 100)
    print("BIOT-SAVART METHOD (Slide 19) - THE CORRECT METHOD")
    print("=" * 100)
    print()
    
    results = []
    for current_a, ref_loss_w in zip(test_currents, gabarito):
        # Update current in input
        input_data.conductors[0].current_a = current_a
        input_data.conductors[1].current_a = current_a
        input_data.conductors[2].current_a = current_a
        
        # Run simulation
        result = simulate_exercise_01(input_data)
        
        # Extract the APPROXIMATE method (Biot-Savart), which is the correct one
        biot_savart_loss = result.total_loss_approximate_w
        
        error_pct = abs(biot_savart_loss - ref_loss_w) / ref_loss_w * 100
        results.append({
            'current': current_a,
            'reference': ref_loss_w,
            'biot_savart': biot_savart_loss,
            'error_pct': error_pct
        })
        
        print(f"Current {current_a:6.0f}A:")
        print(f"  Reference (gabarito): {ref_loss_w:.2f}W")
        print(f"  Biot-Savart method:   {biot_savart_loss:.2f}W")
        print(f"  Error: {error_pct:.2f}%")
        print()
    
    # Statistics
    errors = [r['error_pct'] for r in results]
    avg_error = np.mean(errors)
    max_error = np.max(errors)
    
    print("=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print(f"Average error: {avg_error:.2f}%")
    print(f"Max error: {max_error:.2f}%")
    print(f"All tests pass (<2% error): {max_error < 2}")
    print()
    
    # Also compare both methods
    print("=" * 100)
    print("COMPARISON: Analytical (slide 18 with fator 2.09) vs Biot-Savart (slide 19)")
    print("=" * 100)
    print()
    
    input_data = get_default_exercise01_input()
    
    for current_a, ref_loss_w in zip([2000.0, 2500.0], gabarito[:2]):
        input_data.conductors[0].current_a = current_a
        input_data.conductors[1].current_a = current_a
        input_data.conductors[2].current_a = current_a
        
        result = simulate_exercise_01(input_data)
        
        print(f"Current {current_a:6.0f}A (target: {ref_loss_w:.2f}W):")
        print(f"  Analytical (slide 18 + 2.09): {result.total_loss_analytical_w:.2f}W")
        print(f"  Biot-Savart (slide 19):       {result.total_loss_approximate_w:.2f}W")
        print(f"  Difference: {abs(result.total_loss_analytical_w - result.total_loss_approximate_w):.2f}W ({abs(result.total_loss_analytical_w - result.total_loss_approximate_w)/result.total_loss_approximate_w*100:.1f}%)")
        print()


if __name__ == "__main__":
    test_biot_savart_method()
