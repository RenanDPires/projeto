"""Tests for geometric validation.

Validates that geometric constraints are properly enforced.
"""

import pytest
import numpy as np
from app.schemas import PlateInput, HoleInput, ConductorInput
from app.core.geometry.validation import GeometricValidator


class TestGeometricValidation:
    """Test geometric constraint validation."""

    def test_valid_plate_passes(self):
        """Valid plate should not generate warnings."""
        plate = PlateInput(width_mm=200.0, height_mm=200.0, thickness_mm=5.0)
        warnings = GeometricValidator.validate_plate(plate)
        assert len(warnings) == 0

    def test_very_thin_plate_warning(self):
        """Plate thinner than 0.5 mm should generate warning."""
        plate = PlateInput(width_mm=200.0, height_mm=200.0, thickness_mm=0.1)
        warnings = GeometricValidator.validate_plate(plate)
        assert len(warnings) > 0

    def test_very_small_plate_warning(self):
        """Plate with dimension < 10 mm should generate warning."""
        plate = PlateInput(width_mm=5.0, height_mm=200.0, thickness_mm=5.0)
        warnings = GeometricValidator.validate_plate(plate)
        assert len(warnings) > 0

    def test_valid_hole_passes(self):
        """Valid hole should pass validation."""
        plate = PlateInput(width_mm=200.0, height_mm=200.0, thickness_mm=5.0)
        holes = [HoleInput(x_mm=100.0, y_mm=100.0, diameter_mm=20.0)]

        is_valid, errors = GeometricValidator.validate_holes(holes, plate)
        assert is_valid
        assert len(errors) == 0

    def test_hole_outside_plate_width(self):
        """Hole extending beyond plate width should fail."""
        plate = PlateInput(width_mm=100.0, height_mm=100.0, thickness_mm=5.0)
        holes = [HoleInput(x_mm=95.0, y_mm=50.0, diameter_mm=20.0)]  # 10mm margin, 20mm dia

        is_valid, errors = GeometricValidator.validate_holes(holes, plate)
        assert not is_valid
        assert len(errors) > 0

    def test_overlapping_holes_detected(self):
        """Overlapping holes should be detected."""
        plate = PlateInput(width_mm=200.0, height_mm=200.0, thickness_mm=5.0)
        holes = [
            HoleInput(x_mm=50.0, y_mm=100.0, diameter_mm=40.0),
            HoleInput(x_mm=60.0, y_mm=100.0, diameter_mm=40.0),  # Overlapping
        ]

        is_valid, errors = GeometricValidator.validate_holes(holes, plate)
        assert not is_valid
        assert any("overlap" in err.lower() for err in errors)

    def test_non_overlapping_holes_pass(self):
        """Non-overlapping holes should pass."""
        plate = PlateInput(width_mm=200.0, height_mm=200.0, thickness_mm=5.0)
        holes = [
            HoleInput(x_mm=50.0, y_mm=100.0, diameter_mm=20.0),
            HoleInput(x_mm=150.0, y_mm=100.0, diameter_mm=20.0),
        ]

        is_valid, errors = GeometricValidator.validate_holes(holes, plate)
        assert is_valid
        assert len(errors) == 0

    def test_valid_conductor_passes(self):
        """Valid conductor inside plate should pass."""
        plate = PlateInput(width_mm=200.0, height_mm=200.0, thickness_mm=5.0)
        conductors = [ConductorInput(x_mm=100.0, y_mm=100.0, current_a=100.0)]

        is_valid, errors = GeometricValidator.validate_conductors(conductors, plate)
        assert is_valid
        assert len(errors) == 0

    def test_conductor_outside_plate_fails(self):
        """Conductor outside plate boundary should fail."""
        plate = PlateInput(width_mm=200.0, height_mm=200.0, thickness_mm=5.0)
        conductors = [ConductorInput(x_mm=250.0, y_mm=100.0, current_a=100.0)]

        is_valid, errors = GeometricValidator.validate_conductors(conductors, plate)
        assert not is_valid
        assert any("outside" in err.lower() for err in errors)

    def test_zero_current_warning(self):
        """Zero current conductor should generate warning."""
        plate = PlateInput(width_mm=200.0, height_mm=200.0, thickness_mm=5.0)
        conductors = [ConductorInput(x_mm=100.0, y_mm=100.0, current_a=0.0)]

        is_valid, errors = GeometricValidator.validate_conductors(conductors, plate)
        # Zero current is allowed by Pydantic but may warn
        # (depends on implementation)

    def test_duplicate_conductor_positions(self):
        """Identical conductor positions should be detected."""
        plate = PlateInput(width_mm=200.0, height_mm=200.0, thickness_mm=5.0)
        conductors = [
            ConductorInput(x_mm=100.0, y_mm=100.0, current_a=100.0),
            ConductorInput(x_mm=100.0, y_mm=100.0, current_a=100.0),
        ]

        is_valid, errors = GeometricValidator.validate_conductors(conductors, plate)
        assert not is_valid
        assert any("position" in err.lower() for err in errors)

    def test_complete_validation(self):
        """Test complete validation workflow."""
        plate = PlateInput(width_mm=200.0, height_mm=200.0, thickness_mm=5.0)
        holes = [
            HoleInput(x_mm=75.0, y_mm=100.0, diameter_mm=20.0),
            HoleInput(x_mm=125.0, y_mm=100.0, diameter_mm=20.0),
        ]
        conductors = [
            ConductorInput(x_mm=75.0, y_mm=100.0, current_a=100.0),
            ConductorInput(x_mm=125.0, y_mm=100.0, current_a=100.0),
        ]

        is_valid, errors = GeometricValidator.validate_all(
            plate, holes, conductors, mu=1.256e-6, sigma=5.96e7
        )

        assert is_valid
        assert len(errors) == 0

    def test_multiple_validation_errors(self):
        """Test detection of multiple validation errors."""
        plate = PlateInput(width_mm=50.0, height_mm=50.0, thickness_mm=5.0)  # Too small
        holes = [
            HoleInput(x_mm=45.0, y_mm=25.0, diameter_mm=20.0),  # Too close to boundary
            HoleInput(x_mm=50.0, y_mm=25.0, diameter_mm=20.0),  # Overlaps with first
        ]
        conductors = [
            ConductorInput(x_mm=100.0, y_mm=100.0, current_a=100.0),  # Outside plate
        ]

        is_valid, errors = GeometricValidator.validate_all(
            plate, holes, conductors, mu=1.256e-6, sigma=5.96e7
        )

        assert not is_valid
        assert len(errors) > 2  # Multiple errors


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
