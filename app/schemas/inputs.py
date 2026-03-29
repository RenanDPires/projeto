"""Input data models for Exercise 01 — Tank Losses.

These models define the structure and validation rules for all user inputs
required by the electromagnetic loss calculation problem.

All inputs are in user-facing units (mm, A, Hz) and must be converted to SI
units internally by the solver.
"""


from pydantic import BaseModel, Field


class HoleInput(BaseModel):
    """Represents a hole (circular opening) in the plate through which a conductor passes.

    Attributes:
        x_mm: X-coordinate of hole center [mm]
        y_mm: Y-coordinate of hole center [mm]
        diameter_mm: Hole diameter [mm]
    """

    x_mm: float = Field(..., description="Hole center X position in mm")
    y_mm: float = Field(..., description="Hole center Y position in mm")
    diameter_mm: float = Field(gt=0, description="Hole diameter in mm (must be positive)")

    model_config = {"json_schema_extra": {"example": {"x_mm": 50, "y_mm": 50, "diameter_mm": 10}}}


class ConductorInput(BaseModel):
    """Represents a current-carrying conductor passing through the plate.

    Attributes:
        x_mm: X-coordinate of conductor position [mm]
        y_mm: Y-coordinate of conductor position [mm]
        current_a: Current magnitude [A]
    """

    x_mm: float = Field(..., description="Conductor X position in mm")
    y_mm: float = Field(..., description="Conductor Y position in mm")
    current_a: float = Field(..., description="Current in Amperes (can be positive or negative)")

    model_config = {"json_schema_extra": {"example": {"x_mm": 50, "y_mm": 50, "current_a": 100}}}


class MaterialInput(BaseModel):
    """Represents material properties of the plate.

    These are physical constants that characterize the plate's electromagnetic behavior.

    Attributes:
        mu: Magnetic permeability [H/m]
        sigma: Electrical conductivity [S/m]
    """

    mu: float = Field(gt=0, description="Magnetic permeability in H/m (must be positive)")
    sigma: float = Field(gt=0, description="Electrical conductivity in S/m (must be positive)")

    model_config = {
        "json_schema_extra": {"example": {"mu": 1.256e-6, "sigma": 5.96e7}}  # Copper-like values
    }


class MeshInput(BaseModel):
    """Represents discretization parameters for numerical integration.

    A regular 2D mesh will be generated with nx points in x-direction and ny in y-direction.

    Attributes:
        nx: Number of points along x-axis
        ny: Number of points along y-axis
    """

    nx: int = Field(ge=10, description="Number of mesh points in x (minimum 10)")
    ny: int = Field(ge=10, description="Number of mesh points in y (minimum 10)")

    model_config = {"json_schema_extra": {"example": {"nx": 50, "ny": 50}}}


class PlateInput(BaseModel):
    """Represents the geometry of the plate.

    The plate is modeled as a rectangular domain with circular holes subtracted.
    All dimensions in user-facing units (mm).

    Attributes:
        width_mm: Plate width [mm]
        height_mm: Plate height [mm]
        thickness_mm: Plate thickness [mm] (used for loss calculation)
    """

    width_mm: float = Field(gt=0, description="Plate width in mm (must be positive)")
    height_mm: float = Field(gt=0, description="Plate height in mm (must be positive)")
    thickness_mm: float = Field(gt=0, description="Plate thickness in mm (must be positive)")

    model_config = {
        "json_schema_extra": {"example": {"width_mm": 200, "height_mm": 200, "thickness_mm": 5}}
    }


class Exercise01Input(BaseModel):
    """Complete input specification for Exercise 01 — Tank Losses.

    Aggregates all geometric, physical, and numerical parameters required
    to compute magnetic field distribution and loss density in a plate with
    current-carrying conductors.

    Attributes:
        plate: Plate geometry (dimensions)
        holes: List of circular holes in the plate
        conductors: List of current-carrying conductors
        material: Material properties (μ, σ)
        frequency_hz: Operating frequency [Hz]
        mesh: Mesh discretization parameters (nx, ny)
    """

    plate: PlateInput
    holes: list[HoleInput] = Field(
        default_factory=list, description="List of holes in the plate (may be empty)"
    )
    conductors: list[ConductorInput] = Field(
        ..., description="List of conductors (must have at least one)"
    )
    material: MaterialInput
    frequency_hz: float = Field(gt=0, description="Operating frequency in Hz (must be positive)")
    mesh: MeshInput

    model_config = {"json_schema_extra": {"example": "See defaults.py for a complete example"}}


# Type aliases for convenience
InputDict = dict  # Dictionary representation of input models
