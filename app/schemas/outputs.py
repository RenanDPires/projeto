"""Output data models for Exercise 01 — Tank Losses.

These models define the structure of results returned by the exercise solver.

All outputs are in SI units or numerical scalars.
"""


from pydantic import BaseModel, Field


class Exercise01Result(BaseModel):
    """Result of Exercise 01 simulation.

    Contains results from both analytical and approximate methods, with field statistics
    and optional notes for user feedback.

    All numeric outputs are in SI units unless otherwise specified.

    Attributes:
        total_loss_analytical_w: Total loss calculated using analytical formula [W]
        total_loss_approximate_w: Total loss calculated using approximate method (Biot-Savart) [W]
        max_h_field: Maximum magnetic field magnitude on the plate [A/m]
        max_loss_density: Maximum local power loss density [W/m²]
        valid_area_m2: Effective integration area (plate minus holes) [m²]
        notes: List of notes or warnings for the user
    """

    total_loss_analytical_w: float = Field(ge=0, description="Total loss (analytical method) in Watts")
    total_loss_approximate_w: float = Field(ge=0, description="Total loss (approximate method) in Watts")
    max_h_field: float = Field(ge=0, description="Maximum |H| field in A/m")
    max_loss_density: float = Field(ge=0, description="Maximum loss density in W/m²")
    valid_area_m2: float = Field(ge=0, description="Effective integration area in m²")
    notes: list[str] = Field(
        default_factory=list, description="Optional notes and warnings for the user"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_loss_analytical_w": 63.79,
                "total_loss_approximate_w": 65.42,
                "max_h_field": 15000.0,
                "max_loss_density": 2500.0,
                "valid_area_m2": 0.039,
                "notes": ["Mesh resolution: 50x50 points", "Integration excludes 3 holes"],
            }
        }
    }
