"""Valores padrao e configuracoes de exemplo da Questao 01.

Essas constantes definem pontos de partida para a interface e para o botao
de restauracao de valores padrao.
"""

from collections import OrderedDict

from .inputs import (
    ConductorInput,
    Exercise01Input,
    HoleInput,
    MaterialInput,
    MeshInput,
    PlateInput,
)


def get_default_exercise01_input() -> Exercise01Input:
    """Retorna uma configuracao padrao valida para a Questao 01.

    Representa a geometria de referencia:
    - Placa retangular (590mm x 270mm) com 5mm de espessura
    - Tres furos com diametros 82mm, 82mm, 82mm (layout simetrico)
    - Tres condutores posicionados nos centros dos furos
    - Material tipo aco transformador
    - Operacao em 60Hz com malha 100x100

    Returns:
        Exercise01Input: Configuracao completa e valida
    """
    return Exercise01Input(
        plate=PlateInput(width_mm=590.0, height_mm=270.0, thickness_mm=5.0),
        holes=[
            HoleInput(x_mm=100.0, y_mm=135.0, diameter_mm=82.0),
            HoleInput(x_mm=295.0, y_mm=135.0, diameter_mm=82.0),
            HoleInput(x_mm=490.0, y_mm=135.0, diameter_mm=82.0),
        ],
        conductors=[
            ConductorInput(x_mm=100.0, y_mm=135.0, current_a=2000.0),
            ConductorInput(x_mm=295.0, y_mm=135.0, current_a=2000.0),
            ConductorInput(x_mm=490.0, y_mm=135.0, current_a=2000.0),
        ],
        material=MaterialInput(
            mu=1.256637e-4,  # Aco transformador (mu_r ≈ 100)
            sigma=1.0e6,  # Aco transformador condutividade [S/m]
        ),
        frequency_hz=60.0,
        mesh=MeshInput(nx=100, ny=100),
    )


# Constantes para limites e valores padrao da interface
DEFAULT_PLATE_WIDTH_MM = 590.0
DEFAULT_PLATE_HEIGHT_MM = 270.0
DEFAULT_PLATE_THICKNESS_MM = 5.0

DEFAULT_HOLE_DIAMETER_MM = 82.0

DEFAULT_CONDUCTOR_CURRENT_A = 2000.0

# Propriedades de material (cobre aproximado)
DEFAULT_MATERIAL_MU = 1.256637e-6  # H/m (non-magnetic)
DEFAULT_MATERIAL_SIGMA = 5.96e7  # S/m (copper conductivity)

# Resolucao de malha
DEFAULT_MESH_NX = 100
DEFAULT_MESH_NY = 100
MIN_MESH_POINTS = 10
MAX_MESH_POINTS = 500

# Faixa de frequencia
DEFAULT_FREQUENCY_HZ = 60.0
MIN_FREQUENCY_HZ = 0.1
MAX_FREQUENCY_HZ = 10000.0

# Restricoes geometricas
MIN_DIMENSION_MM = 1.0
MAX_DIMENSION_MM = 10000.0

# Precisao numerica
INTEGRATION_TOLERANCE = 1e-6
FIELD_CALCULATION_TOLERANCE = 1e-9


# Presets de materiais (valores aproximados em temperatura ambiente).
# Referencias de condutividade e permeabilidade: tabelas publicas tecnicas.
MATERIAL_PRESETS = OrderedDict(
    {
        "Aco transformador (tanque)": {
            "mu": 1.256637e-4,
            "sigma": 1.0e6,
            "description": "Aco elétrico do tanque do transformador (mu_r ≈ 100)",
        },
        "Cobre (Cu)": {
            "mu": 1.256629e-6,
            "sigma": 5.96e7,
            "description": "Alta condutividade, quase nao magnetico",
        },
        "Aluminio (Al)": {
            "mu": 1.256665e-6,
            "sigma": 3.55e7,
            "description": "Condutor comum em barramentos e cabos",
        },
        "Latao (Brass 30% Zn)": {
            "mu": 1.256637e-6,
            "sigma": 1.67e7,
            "description": "Liga metalica com condutividade intermediaria",
        },
        "Aco carbono (1010)": {
            "mu": 1.256637e-4,
            "sigma": 6.99e6,
            "description": "Material ferromagnetico com mu_r aproximado de 100",
        },
        "Inox austenitico (304)": {
            "mu": 1.319469e-6,
            "sigma": 1.45e6,
            "description": "Baixa permeabilidade e condutividade menor",
        },
        "Vacuo (referencia)": {
            "mu": 1.256637061e-6,
            "sigma": 1e-15,
            "description": "Referencia teorica; placa condutiva no vacuo nao e fisica",
        },
        "Personalizado": {
            "mu": DEFAULT_MATERIAL_MU,
            "sigma": DEFAULT_MATERIAL_SIGMA,
            "description": "Defina manualmente mu e sigma",
        },
    }
)


def get_material_presets() -> OrderedDict:
    """Retorna os presets de materiais disponiveis no seletor da interface."""
    return MATERIAL_PRESETS
