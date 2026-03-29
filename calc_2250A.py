#!/usr/bin/env python3
"""Quick calculation for 2250A at 60Hz."""

import sys
from pathlib import Path
import numpy as np

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.schemas.defaults import get_default_exercise01_input
from app.core.exercises.q01_tank_losses import simulate_exercise_01


def calculate_losses_2250A():
    """Calculate losses for 2250A at 60Hz."""
    
    input_data = get_default_exercise01_input()
    
    # Set current to 2250A for all 3 conductors
    input_data.conductors[0].current_a = 2250.0
    input_data.conductors[1].current_a = 2250.0
    input_data.conductors[2].current_a = 2250.0
    
    # Verify frequency
    print(f"Frequency: {input_data.frequency_hz} Hz")
    print(f"Current per conductor: 2250 A (RMS)")
    print(f"Material: {input_data.material}")
    print(f"Plate thickness: {input_data.plate.thickness_mm} mm")
    print()
    
    # Run simulation
    result = simulate_exercise_01(input_data)
    
    print("=" * 60)
    print("PERDAS PARA 2250 A @ 60 Hz")
    print("=" * 60)
    print()
    print(f"Método Cilindro (Slide 18):     {result.total_loss_analytical_w:.2f} W")
    print(f"Método Biot-Savart (Slide 19):  {result.total_loss_approximate_w:.2f} W")
    print()
    print(f"Gabarito (referência):          80.74 W")
    print()
    print(f"Erro método cilindro:           {abs(result.total_loss_analytical_w - 80.74)/80.74*100:.2f}%")
    print(f"Erro método Biot-Savart:        {abs(result.total_loss_approximate_w - 80.74)/80.74*100:.2f}%")


if __name__ == "__main__":
    calculate_losses_2250A()
