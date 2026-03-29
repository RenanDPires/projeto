"""Regras de validacao geometrica e mensagens de erro."""

from typing import List, Tuple
import numpy as np
from app.schemas import PlateInput, HoleInput, ConductorInput
from app.core.geometry.plate import Plate, create_plate_from_input


class GeometricValidationError(Exception):
    """Excecao para violacao de restricoes geometricas."""

    pass


class GeometricValidator:
    """Valida configuracoes geometricas para consistencia fisica."""

    @staticmethod
    def validate_plate(plate: PlateInput) -> List[str]:
        """Valida dimensoes da placa.

        Args:
            plate: PlateInput a validar

        Returns:
            Lista de avisos/erros (vazia se valido)
        """
        errors = []

        if plate.width_mm < 10:
            errors.append("Largura da placa < 10 mm (muito pequena)")
        if plate.height_mm < 10:
            errors.append("Altura da placa < 10 mm (muito pequena)")
        if plate.thickness_mm < 0.5:
            errors.append("Espessura da placa < 0.5 mm (pode ser irrealista)")
        if plate.thickness_mm > 100:
            errors.append("Espessura da placa > 100 mm (muito espessa)")

        if plate.width_mm > plate.height_mm * 5:
            errors.append("Razao de aspecto da placa > 5:1 (muito alongada)")
        if plate.height_mm > plate.width_mm * 5:
            errors.append("Razao de aspecto da placa > 5:1 (muito alongada)")

        return errors

    @staticmethod
    def validate_holes(
        holes: List[HoleInput], plate: PlateInput
    ) -> Tuple[bool, List[str]]:
        """Valida posicoes e tamanhos dos furos.

        Args:
            holes: Lista de furos
            plate: Geometria da placa

        Returns:
            Tupla (is_valid, mensagens)
        """
        errors = []

        # Verifica cada furo individualmente
        for i, hole in enumerate(holes):
            if hole.diameter_mm < 1:
                errors.append(f"Furo {i + 1}: diametro < 1 mm (muito pequeno)")

            if hole.diameter_mm > min(plate.width_mm, plate.height_mm) / 2:
                errors.append(
                    f"Furo {i + 1}: diametro > metade da menor dimensao da placa"
                )

            # Verifica se ultrapassa os limites da placa
            margin_x = hole.diameter_mm / 2
            margin_y = hole.diameter_mm / 2

            if hole.x_mm - margin_x < 0 or hole.x_mm + margin_x > plate.width_mm:
                errors.append(f"Furo {i + 1}: ultrapassa a largura da placa")

            if hole.y_mm - margin_y < 0 or hole.y_mm + margin_y > plate.height_mm:
                errors.append(f"Furo {i + 1}: ultrapassa a altura da placa")

        # Verifica sobreposicao entre furos
        for i in range(len(holes)):
            for j in range(i + 1, len(holes)):
                h1, h2 = holes[i], holes[j]
                dx = h1.x_mm - h2.x_mm
                dy = h1.y_mm - h2.y_mm
                distance = np.sqrt(dx**2 + dy**2)
                min_distance = (h1.diameter_mm + h2.diameter_mm) / 2

                if distance < min_distance:
                    errors.append(
                        f"Furos {i + 1} e {j + 1}: sobrepostos (overlap) "
                        f"(distancia {distance:.1f} mm < minimo {min_distance:.1f} mm)"
                    )

        return len(errors) == 0, errors

    @staticmethod
    def validate_conductors(
        conductors: List[ConductorInput], plate: PlateInput, holes: List[HoleInput] = None
    ) -> Tuple[bool, List[str]]:
        """Valida posicoes e correntes dos condutores.

        Args:
            conductors: Lista de condutores
            plate: Geometria da placa
            holes: Lista opcional de furos (checagens adicionais)

        Returns:
            Tupla (is_valid, mensagens)
        """
        errors = []
        holes = holes or []

        # Verifica cada condutor individualmente
        for i, cond in enumerate(conductors):
            if cond.current_a == 0:
                errors.append(f"Condutor {i + 1}: corrente zero (sem contribuicao)")

            # Verifica se esta dentro da placa
            if not (0 <= cond.x_mm <= plate.width_mm and 0 <= cond.y_mm <= plate.height_mm):
                errors.append(f"Condutor {i + 1}: fora dos limites da placa (outside)")

            # Verifica proximidade com furos (idealmente no centro do furo)
            if holes:
                closest_distance = min(
                    np.sqrt((cond.x_mm - h.x_mm) ** 2 + (cond.y_mm - h.y_mm) ** 2)
                    for h in holes
                )
                if closest_distance > 50:  # Mais de 50 mm de qualquer furo
                    errors.append(
                        f"Condutor {i + 1}: > 50 mm do furo mais proximo "
                        f"(tipicamente no centro do furo)"
                    )

        # Verifica posicoes duplicadas
        for i in range(len(conductors)):
            for j in range(i + 1, len(conductors)):
                c1, c2 = conductors[i], conductors[j]
                dx = c1.x_mm - c2.x_mm
                dy = c1.y_mm - c2.y_mm
                distance = np.sqrt(dx**2 + dy**2)

                if distance < 1:  # Menos de 1 mm de separacao
                    errors.append(
                        f"Condutores {i + 1} e {j + 1}: posicoes (position) praticamente iguais"
                    )

        return len(errors) == 0, errors

    @staticmethod
    def validate_material(mu: float, sigma: float) -> List[str]:
        """Valida propriedades do material.

        Args:
            mu: Permeabilidade
            sigma: Condutividade

        Returns:
            Lista de mensagens de aviso
        """
        errors = []

        # if mu < 1e-7 or mu > 1e-4:
        #     errors.append(f"Unusual permeability: {mu:.3e} H/m")

        if sigma < 1e5 or sigma > 1e8:
            errors.append(f"Condutividade fora da faixa usual: {sigma:.3e} S/m")

        return errors

    @staticmethod
    def validate_all(
        plate: PlateInput,
        holes: List[HoleInput],
        conductors: List[ConductorInput],
        mu: float,
        sigma: float,
    ) -> Tuple[bool, List[str]]:
        """Valida a configuracao completa.

        Args:
            plate: Geometria da placa
            holes: Lista de furos
            conductors: Lista de condutores
            mu: Permeabilidade
            sigma: Condutividade

        Returns:
            Tupla (is_valid, mensagens_de_erro)
        """
        all_errors = []

        all_errors.extend(GeometricValidator.validate_plate(plate))

        holes_valid, holes_errors = GeometricValidator.validate_holes(holes, plate)
        all_errors.extend(holes_errors)

        conds_valid, conds_errors = GeometricValidator.validate_conductors(
            conductors, plate, holes
        )
        all_errors.extend(conds_errors)

        all_errors.extend(GeometricValidator.validate_material(mu, sigma))

        return len(all_errors) == 0, all_errors
