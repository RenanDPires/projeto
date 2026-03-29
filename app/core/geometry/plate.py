"""Modulo de geometria para representacao de placa e furos.

Implementa operacoes geometricas da placa, deteccao de furos e classificacao de pontos.
"""

import numpy as np
from dataclasses import dataclass
from typing import Tuple


@dataclass
class Plate:
    """Representa uma placa retangular com furos circulares.

    Attributes:
        width_m: Largura da placa em metros
        height_m: Altura da placa em metros
        thickness_m: Espessura da placa em metros
        hole_centers: Array (n_furos, 2) com centros dos furos em metros
        hole_radii: Array (n_furos,) com raios dos furos em metros
    """

    width_m: float
    height_m: float
    thickness_m: float
    hole_centers: np.ndarray  # (n_holes, 2)
    hole_radii: np.ndarray  # (n_holes,)

    def __post_init__(self):
        """Valida dimensoes da placa."""
        if self.width_m <= 0 or self.height_m <= 0 or self.thickness_m <= 0:
            raise ValueError("Todas as dimensoes devem ser positivas")

        if len(self.hole_centers) != len(self.hole_radii):
            raise ValueError("Inconsistencia entre centros e raios dos furos")

    def is_inside_plate(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        """Verifica se os pontos estao dentro dos limites da placa.

        Args:
            x: Coordenadas X [m]
            y: Coordenadas Y [m]

        Returns:
            Array booleano em que True indica ponto dentro da placa
        """
        return (x >= 0) & (x <= self.width_m) & (y >= 0) & (y <= self.height_m)

    def is_inside_hole(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        """Verifica se os pontos estao dentro de algum furo.

        Args:
            x: Coordenadas X [m]
            y: Coordenadas Y [m]

        Returns:
            Array booleano em que True indica ponto dentro de um furo
        """
        inside_any_hole = np.zeros(x.shape, dtype=bool)

        for center, radius in zip(self.hole_centers, self.hole_radii):
            dx = x - center[0]
            dy = y - center[1]
            distance_sq = dx**2 + dy**2
            inside_any_hole |= distance_sq <= radius**2

        return inside_any_hole

    def is_valid_point(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        """Verifica se pontos sao validos para integracao (na placa e fora dos furos).

        Args:
            x: Coordenadas X [m]
            y: Coordenadas Y [m]

        Returns:
            Array booleano em que True indica ponto valido
        """
        return self.is_inside_plate(x, y) & ~self.is_inside_hole(x, y)

    def get_valid_area_m2(self) -> float:
        """Calcula a area valida de integracao (placa menos furos).

        Returns:
            Area valida em metros quadrados
        """
        plate_area = self.width_m * self.height_m
        holes_area = np.sum(np.pi * self.hole_radii**2)
        return plate_area - holes_area


def create_plate_from_input(
    plate_input, holes_input, scale_mm_to_m: float = 1e-3
) -> Plate:
    """Cria um objeto Plate a partir dos modelos de entrada.

    Args:
        plate_input: Modelo PlateInput
        holes_input: Lista de modelos HoleInput
        scale_mm_to_m: Fator de conversao de mm para m (padrao 1e-3)

    Returns:
        Objeto Plate com dimensoes convertidas para SI
    """
    # Converte para metros
    width_m = plate_input.width_mm * scale_mm_to_m
    height_m = plate_input.height_mm * scale_mm_to_m
    thickness_m = plate_input.thickness_mm * scale_mm_to_m

    if not holes_input:
        hole_centers = np.empty((0, 2))
        hole_radii = np.empty(0)
    else:
        hole_centers = np.array(
            [[h.x_mm * scale_mm_to_m, h.y_mm * scale_mm_to_m] for h in holes_input]
        )
        hole_radii = np.array([h.diameter_mm * scale_mm_to_m / 2 for h in holes_input])

    return Plate(
        width_m=width_m,
        height_m=height_m,
        thickness_m=thickness_m,
        hole_centers=hole_centers,
        hole_radii=hole_radii,
    )
