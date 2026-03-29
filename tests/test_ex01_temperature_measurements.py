"""
Test Exercise 01 against temperature measurement reference data.

Reference table (steady-state temperature measurements):
- Material: Aço Transformador (transformer steel)
- Geometry: 590×270×5mm plate, 3 conductors
- Frequency: 60 Hz

Current(A) | Calculation | Measurement
2000       | 63.79       | 64.50
2250       | 80.74       | 73.70
2500       | 99.67       | 94.60
2800       | 125.00      | 119.30

Acceptance: Analytical results within ±5-10% of measurements
(Temperature methods have inherent uncertainty)
"""

import pytest
import numpy as np
from app.schemas.inputs import Exercise01Input, PlateInput, HoleInput, ConductorInput, MaterialInput, MeshInput
from app.core.exercises.q01_tank_losses import simulate_exercise_01


class TestExercise01TemperatureMeasurements:
    """Validate Exercise 01 against temperature measurement reference data."""

    @pytest.fixture
    def setup_transformer_steel(self):
        """Setup transformer steel material and standard geometry."""
        material = MaterialInput(
            mu=1.256637e-4,  # Aço transformador
            sigma=1.0e6,
        )
        
        plate_config = {
            "width_mm": 590.0,
            "height_mm": 270.0,
            "thickness_mm": 5.0,
            "holes": [
                {"x_mm": 100.0, "y_mm": 135.0, "diameter_mm": 82.0},
                {"x_mm": 295.0, "y_mm": 135.0, "diameter_mm": 82.0},
                {"x_mm": 490.0, "y_mm": 135.0, "diameter_mm": 82.0},
            ]
        }
        
        frequency_hz = 60.0
        
        return material, plate_config, frequency_hz

    def create_input(self, material, plate_config, frequency_hz, currents, mesh_nx=50, mesh_ny=50):
        """Create Exercise01Input for given currents."""
        holes = [HoleInput(**h) for h in plate_config["holes"]]
        
        conductors = [
            ConductorInput(
                x_mm=h.x_mm,
                y_mm=h.y_mm,
                current_a=current
            )
            for h, current in zip(holes, currents)
        ]
        
        return Exercise01Input(
            plate=PlateInput(
                width_mm=plate_config["width_mm"],
                height_mm=plate_config["height_mm"],
                thickness_mm=plate_config["thickness_mm"],
            ),
            holes=holes,
            conductors=conductors,
            material=material,
            frequency_hz=frequency_hz,
            mesh=MeshInput(nx=mesh_nx, ny=mesh_ny),
        )

    def test_biot_savart_vs_analytical_gabarito_within_0p8_percent(self, setup_transformer_steel):
        """Validate Biot-Savart against analytical gabarito with <=0.8% error.

        This is a physics-based consistency check (no point-wise calibration).
        """
        material, plate_config, frequency_hz = setup_transformer_steel

        gabarito_analytical = [
            (2000.0, 63.79),
            (2250.0, 80.74),
            (2500.0, 99.67),
            (2800.0, 125.00),
        ]

        errors_pct = []
        for current_a, analytical_ref_w in gabarito_analytical:
            input_data = self.create_input(
                material,
                plate_config,
                frequency_hz,
                [current_a, current_a, current_a],
                mesh_nx=100,
                mesh_ny=100,
            )

            result = simulate_exercise_01(input_data)
            biot_w = result.total_loss_approximate_w
            error_pct = abs(biot_w - analytical_ref_w) / analytical_ref_w * 100.0
            errors_pct.append(error_pct)

        max_error_pct = np.max(errors_pct)
        assert max_error_pct <= 0.8, (
            f"Biot-Savart max error: {max_error_pct:.3f}% exceeds 0.8% criterion"
        )


    @pytest.mark.parametrize("current_a,measurement_w", [
        (2000.0, 64.50),
        (2250.0, 73.70),
        (2500.0, 94.60),
        (2800.0, 119.30),
    ])
    def test_analytical_vs_measurement(self, setup_transformer_steel, current_a, measurement_w):
        """Test analytical formula against temperature measurement data.
        
        Args:
            current_a: Test current [A]
            measurement_w: Temperature measurement result [W]
        """
        material, plate_config, frequency_hz = setup_transformer_steel
        
        # Create input with symmetric currents
        input_data = self.create_input(
            material,
            plate_config,
            frequency_hz,
            [current_a, current_a, current_a]
        )
        
        # Run simulation
        result = simulate_exercise_01(input_data)
        
        # Validate analytical result
        analytical_w = result.total_loss_analytical_w
        
        # Calculate error
        error_pct = abs(analytical_w - measurement_w) / measurement_w * 100.0
        
        # Acceptance: ≤10% error (accounts for temperature measurement uncertainty)
        # Ideal: ≤5% error, but temperature methods have inherent variability
        assert analytical_w > 0, f"Loss must be positive at {current_a}A"
        assert error_pct <= 10.0, (
            f"Analytical loss at {current_a}A: {analytical_w:.2f}W "
            f"vs measurement {measurement_w:.2f}W (error: {error_pct:.2f}%) "
            f"exceeds 10% tolerance"
        )

    def test_all_measurements_average_error(self, setup_transformer_steel):
        """Test that average error across all measurements is acceptable."""
        material, plate_config, frequency_hz = setup_transformer_steel
        
        test_data = [
            (2000.0, 64.50),
            (2250.0, 73.70),
            (2500.0, 94.60),
            (2800.0, 119.30),
        ]
        
        errors = []
        for current_a, measurement_w in test_data:
            input_data = self.create_input(
                material,
                plate_config,
                frequency_hz,
                [current_a, current_a, current_a]
            )
            
            result = simulate_exercise_01(input_data)
            analytical_w = result.total_loss_analytical_w
            error_pct = abs(analytical_w - measurement_w) / measurement_w * 100.0
            errors.append(error_pct)
        
        # Average error should be under 7%
        avg_error = np.mean(errors)
        assert avg_error <= 7.0, (
            f"Average error across all measurements: {avg_error:.2f}% "
            f"exceeds acceptable 7% threshold"
        )

    def test_majority_within_5_percent(self, setup_transformer_steel):
        """Test that majority of measurements are within ±5% tolerance.
        
        At least 2 out of 4 test points should be within ideal ±5% band.
        """
        material, plate_config, frequency_hz = setup_transformer_steel
        
        test_data = [
            (2000.0, 64.50),
            (2250.0, 73.70),
            (2500.0, 94.60),
            (2800.0, 119.30),
        ]
        
        within_5pct = 0
        for current_a, measurement_w in test_data:
            input_data = self.create_input(
                material,
                plate_config,
                frequency_hz,
                [current_a, current_a, current_a]
            )
            
            result = simulate_exercise_01(input_data)
            analytical_w = result.total_loss_analytical_w
            error_pct = abs(analytical_w - measurement_w) / measurement_w * 100.0
            
            if error_pct <= 5.0:
                within_5pct += 1
        
        assert within_5pct >= 2, (
            f"Only {within_5pct}/4 measurements within ±5% tolerance "
            f"(expected ≥2)"
        )
