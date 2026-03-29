"""Modulo de conversoes entre unidades de interface e unidades SI."""


def mm_to_m(value_mm: float) -> float:
    """Converte milimetros para metros.

    Args:
        value_mm: Valor em milimetros

    Returns:
        Valor em metros
    """
    return value_mm * 1e-3


def a_to_a(value_a: float) -> float:
    """Converte ampere para ampere (identidade).

    Args:
        value_a: Valor em ampere

    Returns:
        Valor em ampere
    """
    return value_a


def hz_to_hz(value_hz: float) -> float:
    """Converte hertz para hertz (identidade).

    Args:
        value_hz: Valor em hertz

    Returns:
        Valor em hertz
    """
    return value_hz
