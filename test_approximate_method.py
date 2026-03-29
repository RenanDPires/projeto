#!/usr/bin/env python3
"""
Test the approximate method (Biot-Savart) with corrected formula.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.schemas.defaults import get_default_exercise01_input
from app.core.exercises.q01_tank_losses import simulate_exercise_01


def test_approximate_method():
    """Test approximate method at gabarito conditions."""
    
    # Get default configuration (60Hz, aço transformador, 3 conductors at 2000A)
    input_model = get_default_exercise01_input()
    
    print("=" * 80)
    print("APPROXIMATE METHOD TEST (Biot-Savart with corrected formula)")
    print("=" * 80)
    print(f"\nConfiguration:")
    print(f"  Frequency: {input_model.frequency_hz} Hz")
    print(f"  Plate: {input_model.plate.width_mm}×{input_model.plate.height_mm}×{input_model.plate.thickness_mm}mm")
    print(f"  Conductors: {len(input_model.conductors)} at {[f'{c.current_a:.0f}A' for c in input_model.conductors]}")
    print(f"  Mesh: {input_model.mesh.nx}×{input_model.mesh.ny}")
    print()
    
    # Run simulation
    result = simulate_exercise_01(input_model)
    
    print(f"Results:")
    print(f"  Analytical Loss:   {result.total_loss_analytical_w:8.2f} W (reference: 63.79W)")
    print(f"  Approximate Loss:  {result.total_loss_approximate_w:8.2f} W")
    print(f"  Difference:        {abs(result.total_loss_analytical_w - result.total_loss_approximate_w):8.2f} W")
    print()
    
    # Check if results are reasonable
    if result.total_loss_approximate_w > 0:
        ratio = result.total_loss_approximate_w / result.total_loss_analytical_w
        print(f"Approximate/Analytical Ratio: {ratio:.3f}")
        print()
        
        if 0.8 <= ratio <= 1.2:  # Within 20% is reasonable for mesh-based approximation
            print("✅ Approximate method producing reasonable results")
            return True
        else:
            print("⚠️ Approximate method result differs significantly from analytical")
            print("   (This may be expected for mesh-based approximation with this mesh size)")
            return False
    else:
        print("❌ Approximate method returned zero loss")
        return False


if __name__ == "__main__":
    success = test_approximate_method()
    sys.exit(0 if success else 1)
