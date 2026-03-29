"""Geracao de malha para integracao numerica 2D."""

import numpy as np
from typing import Tuple


class Mesh2D:
    """Malha 2D regular sobre o dominio da placa."""

    def __init__(self, x: np.ndarray, y: np.ndarray):
        """Inicializa a malha a partir de vetores 1D de coordenadas.

        Args:
            x: Vetor 1D de coordenadas x
            y: Vetor 1D de coordenadas y
        """
        self.x_1d = x
        self.y_1d = y
        self.nx = len(x)
        self.ny = len(y)

        # Cria a malha 2D
        self.X, self.Y = np.meshgrid(x, y, indexing="ij")

    def get_mesh_arrays(self) -> Tuple[np.ndarray, np.ndarray]:
        """Retorna os arrays 2D de coordenadas da malha.

        Returns:
            Tupla (X, Y) de arrays 2D
        """
        return self.X, self.Y

    def get_dx_dy(self) -> Tuple[float, float]:
        """Retorna o passo de malha em x e y.

        Returns:
            Tupla (dx, dy)
        """
        dx = self.x_1d[1] - self.x_1d[0] if self.nx > 1 else 0.0
        dy = self.y_1d[1] - self.y_1d[0] if self.ny > 1 else 0.0
        return dx, dy

    def get_volume_element(self) -> float:
        """Retorna o elemento de area para integracao 2D.

        Returns:
            dx * dy
        """
        dx, dy = self.get_dx_dy()
        return dx * dy


def create_uniform_mesh(
    width_m: float, height_m: float, nx: int, ny: int
) -> Mesh2D:
    """Cria malha 2D uniforme sobre um dominio retangular.

    Args:
        width_m: Largura do dominio em metros
        height_m: Altura do dominio em metros
        nx: Numero de pontos na direcao x
        ny: Numero de pontos na direcao y

    Returns:
        Objeto Mesh2D
    """
    x = np.linspace(0, width_m, nx)
    y = np.linspace(0, height_m, ny)
    return Mesh2D(x, y)
