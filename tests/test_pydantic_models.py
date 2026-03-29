"""Tests for Pydantic models (schemas).

Verifies that input and output models correctly validate data,
reject invalid inputs, and can be instantiated from dictionaries.
"""

import pytest

from app.schemas import (
    ConductorInput,
    Exercise01Input,
    Exercise01Result,
    HoleInput,
    MaterialInput,
    MeshInput,
    PlateInput,
    get_default_exercise01_input,
)

# ============================================================================
#  HoleInput Tests
# ============================================================================


class TestHoleInput:
    """Test suite for HoleInput model."""

    def test_valid_hole(self):
        """Valid hole should be created without error."""
        hole = HoleInput(x_mm=50.0, y_mm=100.0, diameter_mm=10.0)
        assert hole.x_mm == 50.0
        assert hole.y_mm == 100.0
        assert hole.diameter_mm == 10.0

    def test_zero_diameter_rejected(self):
        """Hole with zero diameter should be rejected."""
        with pytest.raises(ValueError):
            HoleInput(x_mm=50.0, y_mm=100.0, diameter_mm=0.0)

    def test_negative_diameter_rejected(self):
        """Hole with negative diameter should be rejected."""
        with pytest.raises(ValueError):
            HoleInput(x_mm=50.0, y_mm=100.0, diameter_mm=-5.0)

    def test_hole_from_dict(self):
        """HoleInput should be creatable from a dictionary."""
        data = {"x_mm": 75.0, "y_mm": 75.0, "diameter_mm": 15.0}
        hole = HoleInput(**data)
        assert hole.x_mm == 75.0


# ============================================================================
#  ConductorInput Tests
# ============================================================================


class TestConductorInput:
    """Test suite for ConductorInput model."""

    def test_valid_conductor(self):
        """Valid conductor should be created without error."""
        conductor = ConductorInput(x_mm=50.0, y_mm=100.0, current_a=100.0)
        assert conductor.current_a == 100.0

    def test_negative_current_allowed(self):
        """Negative current should be allowed (opposite polarity)."""
        conductor = ConductorInput(x_mm=50.0, y_mm=100.0, current_a=-50.0)
        assert conductor.current_a == -50.0

    def test_zero_current_allowed(self):
        """Zero current is technically valid (no contribution to field)."""
        conductor = ConductorInput(x_mm=50.0, y_mm=100.0, current_a=0.0)
        assert conductor.current_a == 0.0

    def test_conductor_from_dict(self):
        """ConductorInput should be creatable from a dictionary."""
        data = {"x_mm": 25.0, "y_mm": 75.0, "current_a": 200.0}
        conductor = ConductorInput(**data)
        assert conductor.current_a == 200.0


# ============================================================================
#  MaterialInput Tests
# ============================================================================


class TestMaterialInput:
    """Test suite for MaterialInput model."""

    def test_valid_material(self):
        """Valid material should be created without error."""
        material = MaterialInput(mu=1.256e-6, sigma=5.96e7)
        assert material.mu == 1.256e-6
        assert material.sigma == 5.96e7

    def test_zero_mu_rejected(self):
        """Material with zero permeability should be rejected."""
        with pytest.raises(ValueError):
            MaterialInput(mu=0.0, sigma=5.96e7)

    def test_negative_mu_rejected(self):
        """Material with negative permeability should be rejected."""
        with pytest.raises(ValueError):
            MaterialInput(mu=-1e-6, sigma=5.96e7)

    def test_zero_sigma_rejected(self):
        """Material with zero conductivity should be rejected."""
        with pytest.raises(ValueError):
            MaterialInput(mu=1.256e-6, sigma=0.0)

    def test_negative_sigma_rejected(self):
        """Material with negative conductivity should be rejected."""
        with pytest.raises(ValueError):
            MaterialInput(mu=1.256e-6, sigma=-1e6)

    def test_material_from_dict(self):
        """MaterialInput should be creatable from a dictionary."""
        data = {"mu": 2e-6, "sigma": 1e7}
        material = MaterialInput(**data)
        assert material.mu == 2e-6


# ============================================================================
#  MeshInput Tests
# ============================================================================


class TestMeshInput:
    """Test suite for MeshInput model."""

    def test_valid_mesh(self):
        """Valid mesh should be created without error."""
        mesh = MeshInput(nx=50, ny=50)
        assert mesh.nx == 50
        assert mesh.ny == 50

    def test_minimum_mesh_points(self):
        """Mesh with exactly 10 points (minimum) should be valid."""
        mesh = MeshInput(nx=10, ny=10)
        assert mesh.nx == 10
        assert mesh.ny == 10

    def test_below_minimum_mesh_rejected(self):
        """Mesh with fewer than 10 points should be rejected."""
        with pytest.raises(ValueError):
            MeshInput(nx=9, ny=50)

    def test_asymmetric_mesh(self):
        """Asymmetric mesh (different nx, ny) should be valid."""
        mesh = MeshInput(nx=30, ny=100)
        assert mesh.nx == 30
        assert mesh.ny == 100

    def test_mesh_from_dict(self):
        """MeshInput should be creatable from a dictionary."""
        data = {"nx": 100, "ny": 75}
        mesh = MeshInput(**data)
        assert mesh.nx == 100


# ============================================================================
#  PlateInput Tests
# ============================================================================


class TestPlateInput:
    """Test suite for PlateInput model."""

    def test_valid_plate(self):
        """Valid plate should be created without error."""
        plate = PlateInput(width_mm=200.0, height_mm=200.0, thickness_mm=5.0)
        assert plate.width_mm == 200.0
        assert plate.height_mm == 200.0
        assert plate.thickness_mm == 5.0

    def test_zero_width_rejected(self):
        """Plate with zero width should be rejected."""
        with pytest.raises(ValueError):
            PlateInput(width_mm=0.0, height_mm=100.0, thickness_mm=5.0)

    def test_negative_thickness_rejected(self):
        """Plate with negative thickness should be rejected."""
        with pytest.raises(ValueError):
            PlateInput(width_mm=200.0, height_mm=200.0, thickness_mm=-1.0)

    def test_small_plate(self):
        """Very small plate dimensions should be valid."""
        plate = PlateInput(width_mm=0.1, height_mm=0.1, thickness_mm=0.01)
        assert plate.width_mm == 0.1

    def test_plate_from_dict(self):
        """PlateInput should be creatable from a dictionary."""
        data = {"width_mm": 100.0, "height_mm": 150.0, "thickness_mm": 3.0}
        plate = PlateInput(**data)
        assert plate.width_mm == 100.0


# ============================================================================
#  Exercise01Input Tests
# ============================================================================


class TestExercise01Input:
    """Test suite for Exercise01Input (complete input specification)."""

    def test_valid_exercise01_input(self):
        """Valid Exercise01Input should be created without error."""
        ex = Exercise01Input(
            plate=PlateInput(width_mm=200.0, height_mm=200.0, thickness_mm=5.0),
            holes=[HoleInput(x_mm=75.0, y_mm=100.0, diameter_mm=10.0)],
            conductors=[ConductorInput(x_mm=75.0, y_mm=100.0, current_a=100.0)],
            material=MaterialInput(mu=1.256e-6, sigma=5.96e7),
            frequency_hz=50.0,
            mesh=MeshInput(nx=50, ny=50),
        )
        assert ex.plate.width_mm == 200.0
        assert len(ex.conductors) == 1

    def test_empty_holes_allowed(self):
        """Exercise01Input with no holes should be valid."""
        ex = Exercise01Input(
            plate=PlateInput(width_mm=200.0, height_mm=200.0, thickness_mm=5.0),
            holes=[],
            conductors=[ConductorInput(x_mm=75.0, y_mm=100.0, current_a=100.0)],
            material=MaterialInput(mu=1.256e-6, sigma=5.96e7),
            frequency_hz=50.0,
            mesh=MeshInput(nx=50, ny=50),
        )
        assert len(ex.holes) == 0

    def test_multiple_conductors(self):
        """Exercise01Input with multiple conductors should be valid."""
        ex = Exercise01Input(
            plate=PlateInput(width_mm=200.0, height_mm=200.0, thickness_mm=5.0),
            holes=[],
            conductors=[
                ConductorInput(x_mm=75.0, y_mm=100.0, current_a=100.0),
                ConductorInput(x_mm=125.0, y_mm=100.0, current_a=-100.0),
            ],
            material=MaterialInput(mu=1.256e-6, sigma=5.96e7),
            frequency_hz=50.0,
            mesh=MeshInput(nx=50, ny=50),
        )
        assert len(ex.conductors) == 2

    def test_zero_frequency_rejected(self):
        """Exercise01Input with zero frequency should be rejected."""
        with pytest.raises(ValueError):
            Exercise01Input(
                plate=PlateInput(width_mm=200.0, height_mm=200.0, thickness_mm=5.0),
                holes=[],
                conductors=[ConductorInput(x_mm=75.0, y_mm=100.0, current_a=100.0)],
                material=MaterialInput(mu=1.256e-6, sigma=5.96e7),
                frequency_hz=0.0,
                mesh=MeshInput(nx=50, ny=50),
            )

    def test_exercise01_from_dict(self):
        """Exercise01Input should be creatable from nested dictionaries."""
        data = {
            "plate": {"width_mm": 200.0, "height_mm": 200.0, "thickness_mm": 5.0},
            "holes": [{"x_mm": 50.0, "y_mm": 50.0, "diameter_mm": 10.0}],
            "conductors": [{"x_mm": 50.0, "y_mm": 50.0, "current_a": 100.0}],
            "material": {"mu": 1.256e-6, "sigma": 5.96e7},
            "frequency_hz": 50.0,
            "mesh": {"nx": 50, "ny": 50},
        }
        ex = Exercise01Input(**data)
        assert ex.plate.width_mm == 200.0
        assert len(ex.holes) == 1


# ============================================================================
#  Exercise01Result Tests
# ============================================================================


class TestExercise01Result:
    """Test suite for Exercise01Result (output model)."""

    def test_valid_result(self):
        """Valid Exercise01Result should be created without error."""
        result = Exercise01Result(
            total_loss_analytical_w=125.5,
            total_loss_approximate_w=128.0,
            max_h_field=15000.0,
            max_loss_density=2500.0,
            valid_area_m2=0.039,
            notes=["Some note"],
        )
        assert result.total_loss_analytical_w == 125.5
        assert result.total_loss_approximate_w == 128.0
        assert len(result.notes) == 1

    def test_zero_values_allowed(self):
        """Result with zero values should be valid."""
        result = Exercise01Result(
            total_loss_analytical_w=0.0,
            total_loss_approximate_w=0.0,
            max_h_field=0.0,
            max_loss_density=0.0,
            valid_area_m2=0.0,
            notes=[],
        )
        assert result.total_loss_analytical_w == 0.0

    def test_negative_loss_rejected(self):
        """Result with negative loss should be rejected."""
        with pytest.raises(ValueError):
            Exercise01Result(
                total_loss_analytical_w=-10.0,
                total_loss_approximate_w=100.0,
                max_h_field=1000.0,
                max_loss_density=100.0,
                valid_area_m2=0.01,
                notes=[],
            )

    def test_result_from_dict(self):
        """Exercise01Result should be creatable from a dictionary."""
        data = {
            "total_loss_analytical_w": 200.0,
            "total_loss_approximate_w": 205.0,
            "max_h_field": 20000.0,
            "max_loss_density": 3000.0,
            "valid_area_m2": 0.05,
            "notes": ["Test note"],
        }
        result = Exercise01Result(**data)
        assert result.total_loss_analytical_w == 200.0


# ============================================================================
#  Default Values Tests
# ============================================================================


class TestDefaults:
    """Test suite for default configuration function."""

    def test_get_default_returns_valid_input(self):
        """get_default_exercise01_input() should return a valid input."""
        default = get_default_exercise01_input()
        assert isinstance(default, Exercise01Input)
        assert default.plate.width_mm == 590.0
        assert default.plate.height_mm == 270.0
        assert len(default.conductors) >= 1

    def test_default_has_two_holes(self):
        """Default configuration should have three holes as specified."""
        default = get_default_exercise01_input()
        assert len(default.holes) == 3

    def test_default_has_two_conductors(self):
        """Default configuration should have three conductors as specified."""
        default = get_default_exercise01_input()
        assert len(default.conductors) == 3

    def test_default_conductors_opposite_polarity(self):
        """Default conductors should have consistent magnitude."""
        default = get_default_exercise01_input()
        conductors = default.conductors
        # All conductors have the same current magnitude in the new reference design
        assert conductors[0].current_a == conductors[1].current_a == conductors[2].current_a

    def test_default_is_self_consistent(self):
        """Default input should be internally consistent (holes match conductors)."""
        default = get_default_exercise01_input()
        # Hole positions should match conductor positions (typical setup)
        for i, conductor in enumerate(default.conductors):
            if i < len(default.holes):
                hole = default.holes[i]
                assert hole.x_mm == conductor.x_mm
                assert hole.y_mm == conductor.y_mm

    def test_default_frequency_is_50hz(self):
        """Default configuration should use 60 Hz frequency (transformer standard for validation)."""
        default = get_default_exercise01_input()
        assert default.frequency_hz == 60.0

    def test_default_mesh_is_sufficient(self):
        """Default mesh should be reasonably fine (at least 30x30)."""
        default = get_default_exercise01_input()
        assert default.mesh.nx >= 30
        assert default.mesh.ny >= 30


# ============================================================================
#  Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests for the complete input/output flow."""

    def test_realistic_scenario(self):
        """Test a realistic, complete scenario."""
        # Define realistic input
        ex = Exercise01Input(
            plate=PlateInput(width_mm=300.0, height_mm=250.0, thickness_mm=8.0),
            holes=[
                HoleInput(x_mm=75.0, y_mm=125.0, diameter_mm=12.0),
                HoleInput(x_mm=225.0, y_mm=125.0, diameter_mm=12.0),
            ],
            conductors=[
                ConductorInput(x_mm=75.0, y_mm=125.0, current_a=150.0),
                ConductorInput(x_mm=225.0, y_mm=125.0, current_a=-150.0),
            ],
            material=MaterialInput(mu=1.256637e-6, sigma=5.96e7),
            frequency_hz=60.0,
            mesh=MeshInput(nx=75, ny=75),
        )

        # Simulate a result
        result = Exercise01Result(
            total_loss_analytical_w=287.3,
            total_loss_approximate_w=290.2,
            max_h_field=25000.0,
            max_loss_density=5200.0,
            valid_area_m2=0.0702,
            notes=["60 Hz operation", "Copper-like material", "Fine mesh"],
        )

        # Verify round-trip is consistent
        assert ex.frequency_hz == 60.0
        assert result.total_loss_analytical_w > 0.0
        assert len(result.notes) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
