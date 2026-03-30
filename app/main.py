"""Aplicacao principal do Eletromag Lab em Streamlit.

Ponto de entrada da interface para simulacoes de eletromagnetismo.
Execute com:
    streamlit run app/main.py
"""

import streamlit as st
import numpy as np
import io
import csv
import json
import sys
import textwrap
import importlib
import subprocess
import shutil
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
from datetime import datetime

# Garante importacao do projeto mesmo com diretorio de execucao diferente.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.schemas import (
    Exercise01Input,
    PlateInput,
    HoleInput,
    ConductorInput,
    MaterialInput,
    MeshInput,
    get_default_exercise01_input,
    get_material_presets,
)
from app.core.exercises.q01_tank_losses import simulate_exercise_01
from app.core.geometry.validation import GeometricValidator
from app.core.geometry.plate import create_plate_from_input
from app.components.geometry_plot import plot_geometry

# Configuracao da pagina Streamlit
st.set_page_config(
    page_title="Eletromag Lab",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS customizado para melhorar a apresentacao
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.5rem;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 4px;
        padding: 12px;
        margin-bottom: 10px;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 4px;
        padding: 12px;
        margin-bottom: 10px;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 4px;
        padding: 12px;
        margin-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def _build_result_payload(input_data: Exercise01Input, result) -> dict:
    """Monta payload serializavel com entradas e saidas da simulacao."""
    return {
        "timestamp_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "input": input_data.model_dump(),
        "result": result.model_dump(),
    }


def _summary_csv_bytes(payload: dict) -> bytes:
    """Converte payload da simulacao para CSV (chave/valor)."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["field", "value"])

    flat_rows = {
        "timestamp_utc": payload["timestamp_utc"],
        "plate_width_mm": payload["input"]["plate"]["width_mm"],
        "plate_height_mm": payload["input"]["plate"]["height_mm"],
        "frequency_hz": payload["input"]["frequency_hz"],
        "material_mu": payload["input"]["material"]["mu"],
        "material_sigma": payload["input"]["material"]["sigma"],
        "mesh_nx": payload["input"]["mesh"]["nx"],
        "mesh_ny": payload["input"]["mesh"]["ny"],
        "n_holes": len(payload["input"]["holes"]),
        "n_conductors": len(payload["input"]["conductors"]),
        "total_loss_analytical_w": payload["result"]["total_loss_analytical_w"],
        "total_loss_approximate_w": payload["result"]["total_loss_approximate_w"],
        "max_h_field_a_per_m": payload["result"]["max_h_field"],
        "max_loss_density_w_per_m2": payload["result"]["max_loss_density"],
        "valid_area_m2": payload["result"]["valid_area_m2"],
        "notes": " | ".join(payload["result"].get("notes", [])),
    }

    for key, value in flat_rows.items():
        writer.writerow([key, value])

    return output.getvalue().encode("utf-8")


def _figure_to_png_bytes(fig: go.Figure, width: int = 1400, height: int = 900) -> bytes:
    """Converte figura Plotly em PNG para insercao no PDF."""
    try:
        return fig.to_image(format="png", width=width, height=height, scale=2)
    except Exception as exc:
        # Kaleido 1.x depende de um Chrome gerenciado; tenta provisionar automaticamente.
        if "browser seemed to close immediately" not in str(exc).lower():
            raise

        chrome_installer = shutil.which("choreo_get_chrome")
        if chrome_installer is None:
            scripts_dir = Path(sys.executable).resolve().parent
            candidate = scripts_dir / "choreo_get_chrome.exe"
            if candidate.exists():
                chrome_installer = str(candidate)

        if chrome_installer is None:
            raise

        subprocess.run([chrome_installer], check=True, capture_output=True, text=True)
        return fig.to_image(format="png", width=width, height=height, scale=2)


def _build_exercise_01_pdf(
    calc_input: Exercise01Input,
    result,
    analytical_details: dict,
    biot_details: dict,
    fig_geo: go.Figure | None,
    figures_2d: list[tuple[str, go.Figure]],
    figures_3d: list[tuple[str, go.Figure]],
    include_2d: bool,
    include_3d: bool,
) -> bytes:
    """Gera PDF unico com geometria, equacoes, resultados e visualizacoes."""
    A4 = importlib.import_module("reportlab.lib.pagesizes").A4
    ImageReader = importlib.import_module("reportlab.lib.utils").ImageReader
    canvas = importlib.import_module("reportlab.pdfgen.canvas")

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    page_w, page_h = A4
    margin = 36

    def _new_page() -> float:
        c.showPage()
        return page_h - margin

    def _write_lines(lines: list[str], y: float, size: int = 10, step: float = 14.0) -> float:
        c.setFont("Helvetica", size)
        for line in lines:
            if y < margin + 30:
                y = _new_page()
                c.setFont("Helvetica", size)
            c.drawString(margin, y, line)
            y -= step
        return y

    def _draw_figure_page(title: str, fig: go.Figure, subtitle: str | None = None):
        c.setFont("Helvetica-Bold", 14)
        c.drawString(margin, page_h - margin, title)
        y_top = page_h - margin - 22
        if subtitle:
            c.setFont("Helvetica", 10)
            c.drawString(margin, y_top, subtitle)
            y_top -= 18

        img_bytes = _figure_to_png_bytes(fig)
        img = ImageReader(io.BytesIO(img_bytes))
        img_w, img_h = img.getSize()

        avail_w = page_w - 2 * margin
        avail_h = y_top - margin
        ratio = min(avail_w / img_w, avail_h / img_h)
        draw_w = img_w * ratio
        draw_h = img_h * ratio
        x = margin + (avail_w - draw_w) / 2
        y = margin + (avail_h - draw_h) / 2
        c.drawImage(img, x, y, width=draw_w, height=draw_h, preserveAspectRatio=True, mask="auto")
        c.showPage()

    # Capa e resumo
    y = page_h - margin
    c.setFont("Helvetica-Bold", 18)
    c.drawString(margin, y, "Eletromag - Exercicio 1")
    y -= 26
    c.setFont("Helvetica", 10)
    c.drawString(margin, y, f"Gerado em: {datetime.utcnow().isoformat(timespec='seconds')}Z")
    y -= 24

    c.setFont("Helvetica-Bold", 13)
    c.drawString(margin, y, "Resultados")
    y -= 18
    y = _write_lines(
        [
            f"Perda analitica: {result.total_loss_analytical_w:.4f} W",
            f"Perda aproximada (Biot-Savart): {result.total_loss_approximate_w:.4f} W",
            f"Maximo campo H: {result.max_h_field:.4f} A/m",
            f"Maxima densidade de perdas: {result.max_loss_density:.4f} W/m2",
            f"Area valida: {result.valid_area_m2:.6f} m2",
        ],
        y,
    )

    y -= 8
    c.setFont("Helvetica-Bold", 13)
    c.drawString(margin, y, "Equacoes")
    y -= 18
    equations = [
        "Metodo analitico:",
        "P = ((Im^2 * q) / (pi * sigma)) * ln(b/a) * ((sinh(qc)-sin(qc))/(cosh(qc)+cos(qc)))",
        "",
        "Metodo aproximado (Biot-Savart):",
        "Hm(x,y) = (Im*a / (2*pi)) * sqrt((3x^2+3y^2+a^2)/((x^2+y^2)*(x^4+y^4+2x^2y^2-2a^2x^2+2a^2y^2+a^4)))",
        "P = (1/(2*pi))*sqrt((omega*mu)/(2*sigma)) * integral integral |Hm(x,y)|^2 dx dy",
    ]
    wrapped_equations: list[str] = []
    for line in equations:
        if not line:
            wrapped_equations.append("")
            continue
        wrapped_equations.extend(textwrap.wrap(line, width=110) or [line])
    y = _write_lines(wrapped_equations, y)

    y -= 8
    c.setFont("Helvetica-Bold", 13)
    c.drawString(margin, y, "Parametros de calculo")
    y -= 18
    param_lines = [
        f"f = {calc_input.frequency_hz:.3f} Hz",
        f"mu = {calc_input.material.mu:.6e} H/m",
        f"sigma = {calc_input.material.sigma:.6e} S/m",
        f"espessura = {calc_input.plate.thickness_mm:.3f} mm",
        f"Im (medio abs) = {analytical_details['im_rms_a']:.3f} A",
        f"omega = {analytical_details['omega_rad_s']:.6f} rad/s",
        f"a (3 condutores) = {biot_details['a_mm']:.3f} mm" if biot_details["a_mm"] is not None else "a (3 condutores) = n/a",
    ]
    _write_lines(param_lines, y)
    c.showPage()

    # Figura da geometria (sempre que disponivel)
    if fig_geo is not None:
        _draw_figure_page("Figura da geometria", fig_geo)

    # Graficos 2D opcionais
    if include_2d:
        for title, fig in figures_2d:
            _draw_figure_page(f"Grafico 2D - {title}", fig)

    # Graficos 3D opcionais
    if include_3d:
        for title, fig in figures_3d:
            _draw_figure_page(f"Grafico 3D - {title}", fig)

    c.save()
    return buffer.getvalue()


def _apply_im_to_conductors(
    conductors: list[ConductorInput],
    im_a: float,
) -> list[ConductorInput]:
    """Aplica Im global aos condutores preservando o sinal de cada um."""
    out = []
    for cond in conductors:
        sign = -1.0 if cond.current_a < 0 else 1.0
        out.append(
            ConductorInput(
                x_mm=cond.x_mm,
                y_mm=cond.y_mm,
                current_a=sign * abs(im_a),
            )
        )
    return out


def _apply_spacing_a_to_x_positions(items: list, a_mm: float) -> list:
    """Aplica o espacamento `a` no eixo x para 3 itens.

    Mantem o item central como referencia e funciona para HoleInput e ConductorInput.
    """
    if len(items) != 3:
        return items

    x_values = np.array([float(it.x_mm) for it in items], dtype=float)
    sorted_indices = np.argsort(x_values)
    mid_idx = int(sorted_indices[1])
    x_center = float(x_values[mid_idx])

    new_x_sorted = [x_center - a_mm, x_center, x_center + a_mm]

    updated = [None, None, None]
    for rank, idx in enumerate(sorted_indices):
        payload = items[idx].model_dump()
        payload["x_mm"] = float(new_x_sorted[rank])
        updated[idx] = type(items[idx])(**payload)

    return updated


def _get_three_conductor_spacing_mm(conductors: list[ConductorInput]) -> float | None:
    """Retorna o espacamento medio em x para 3 condutores, em mm."""
    if len(conductors) != 3:
        return None

    x_values = sorted(float(c.x_mm) for c in conductors)
    return (x_values[2] - x_values[1] + x_values[1] - x_values[0]) / 2.0


def _build_analytical_details(input_data: Exercise01Input) -> dict:
    """Calcula valores intermediarios usados no metodo analitico."""
    im_rms = (
        float(np.mean(np.abs([c.current_a for c in input_data.conductors])))
        if input_data.conductors
        else 0.0
    )
    omega = 2.0 * np.pi * input_data.frequency_hz
    q = np.sqrt(omega * input_data.material.mu * input_data.material.sigma / 2.0)
    delta_m = 1.0 / q if q > 0 else 0.0
    thickness_m = input_data.plate.thickness_mm * 1e-3
    qc = q * thickness_m
    transfer = (np.sinh(qc) - np.sin(qc)) / (np.cosh(qc) + np.cos(qc))
    ln_ba = 4.347
    pre_factor = (im_rms**2 * q) / (np.pi * input_data.material.sigma)

    return {
        "im_rms_a": im_rms,
        "omega_rad_s": omega,
        "q_inv_m": q,
        "delta_m": delta_m,
        "thickness_m": thickness_m,
        "qc": qc,
        "ln_ba": ln_ba,
        "transfer": transfer,
        "pre_factor_w": pre_factor,
    }


def _build_biot_details(input_data: Exercise01Input) -> dict:
    """Calcula valores intermediarios usados no metodo Biot-Savart."""
    im_rms = (
        float(np.mean(np.abs([c.current_a for c in input_data.conductors])))
        if input_data.conductors
        else 0.0
    )
    omega = 2.0 * np.pi * input_data.frequency_hz
    coefficient_normalized = 0.5 / np.pi * np.sqrt(
        omega * input_data.material.mu / (2.0 * input_data.material.sigma)
    )
    coefficient_strict = 0.5 * np.sqrt(
        omega * input_data.material.mu / (2.0 * input_data.material.sigma)
    )
    spacing_mm = _get_three_conductor_spacing_mm(input_data.conductors)
    valid_area_m2 = 0.0
    try:
        plate = create_plate_from_input(input_data.plate, input_data.holes)
        valid_area_m2 = plate.get_valid_area_m2()
    except Exception:
        pass

    return {
        "im_rms_a": im_rms,
        "omega_rad_s": omega,
        "coefficient_normalized": coefficient_normalized,
        "coefficient_strict": coefficient_strict,
        "a_mm": spacing_mm,
        "plate_x_mm": float(input_data.plate.width_mm),
        "plate_y_mm": float(input_data.plate.height_mm),
        "valid_area_m2": valid_area_m2,
    }


def _limit_sweep_points(values: np.ndarray, max_points: int = 25) -> np.ndarray:
    """Limita pontos de varredura para manter a interface responsiva."""
    if len(values) <= max_points:
        return values

    indices = np.linspace(0, len(values) - 1, max_points, dtype=int)
    return values[np.unique(indices)]


def _show_exercise_01_intro_sections() -> None:
    """Exibe base teorica e resultados validados com conteudo expansivel."""
    slides_dir = PROJECT_ROOT / "base_teorica" / "Exercicio_1"
    section_slides = {
        "Base teórica 1: Método analítico": [
            "pagina 16.png",
            "pagina 17.png",
            "pagina 18.png",
        ],
        "Base teórica 2: Método Biot-Savart": ["pagina 19.png"],
        "Resultados validados": ["pagina 20.png"],
    }

    st.markdown("### Apresentação da questão")

    for section_title, filenames in section_slides.items():
        with st.expander(section_title, expanded=False):
            for filename in filenames:
                img_path = slides_dir / filename
                if img_path.exists():
                    st.image(str(img_path), caption=filename, use_container_width=True)
                else:
                    st.warning(f"Slide não encontrado: {img_path}")


def main():
    """Funcao principal da aplicacao."""
    # Navegacao lateral
    st.sidebar.markdown("# Eletromag Lab")
    st.sidebar.markdown("Laboratório visual de eletromagnetismo")
    st.sidebar.divider()

    page = st.sidebar.radio(
        "Navegação",
        options=["Início", "Questão 1: Perdas no Tanque"],
        index=0,
    )

    if page == "Início":
        show_home_page()
    elif page == "Questão 1: Perdas no Tanque":
        show_exercise_01_page()


def show_home_page():
    """Exibe a pagina inicial com visao geral do projeto."""
    st.markdown(
        '<div class="main-title">Eletromag Lab</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="subtitle">Ambiente interativo para exploração visual de problemas de eletromagnetismo</div>',
        unsafe_allow_html=True,
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### O que é?")
        st.write(
            """
            Um laboratório educacional desenvolvido em Python para permitir que
            estudantes explorem problemas de eletromagnetismo através de simulações
            visuais e interativas.

            **Recursos principais:**
            - Edicao visual de geometria
            - Calculos numericos precisos
            - Visualizacao de campos e resultados
            - Atualizacoes em tempo real
            """
        )

    with col2:
        st.markdown("### Exercícios disponíveis")
        st.write(
            """
            **Questão 1 — Perdas no tanque**

            Calcule perdas magnéticas em uma placa com condutores carregados.
            Edite geometria, propriedades do material e frequência de operação
            para explorar o comportamento do campo magnético.

            *Status: MVP funcional*
            """
        )

    st.divider()

    st.markdown("### Primeiros passos")
    st.info(
        """
        Selecione um exercício no menu lateral para começar.

        Para cada exercício, você pode:
        1. Editar parâmetros geométricos e físicos
        2. Recalcular automaticamente a solução
        3. Visualizar campos e distribuição de perdas
        4. Exportar resultados em JSON/CSV
        """
    )

    st.divider()

    col_specs, col_code = st.columns(2)

    with col_specs:
        st.markdown("### Documentação")
        st.write("Consulte o arquivo `specs.md` para a especificação técnica completa.")

    with col_code:
        st.markdown("### Stack técnico")
        st.write(
            """
            - **Frontend**: Streamlit, Plotly
            - **Backend**: NumPy, SciPy, Pydantic
            - **Qual. de código**: Pytest, Ruff, Black, Mypy
            """
        )


def show_exercise_01_page():
    """Exibe a pagina da Questao 01 (perdas no tanque)."""
    st.markdown("## Questão 1: Perdas no tanque devido aos condutores carregados")

    st.divider()
    _show_exercise_01_intro_sections()
    st.divider()

    # Inicializacao do estado da sessao
    if "exercise_01_input" not in st.session_state:
        st.session_state.exercise_01_input = get_default_exercise01_input()

    if "simulation_result" not in st.session_state:
        st.session_state.simulation_result = None

    if "calculated_input" not in st.session_state:
        st.session_state.calculated_input = None

    if "material_preset" not in st.session_state:
        st.session_state.material_preset = "Aco transformador (tanque)"

    if "im_a" not in st.session_state:
        first_current = (
            abs(st.session_state.exercise_01_input.conductors[0].current_a)
            if st.session_state.exercise_01_input.conductors
            else 100.0
        )
        st.session_state.im_a = float(first_current)

    if "a_spacing_mm" not in st.session_state:
        if len(st.session_state.exercise_01_input.conductors) == 3:
            xs = sorted([c.x_mm for c in st.session_state.exercise_01_input.conductors])
            st.session_state.a_spacing_mm = float((xs[2] - xs[1] + xs[1] - xs[0]) / 2.0)
        else:
            st.session_state.a_spacing_mm = 100.0

    input_data = st.session_state.exercise_01_input
    material_presets = get_material_presets()

    # ─── PARÂMETROS ──────────────────────────────────────────────────────────
    st.markdown("### Parâmetros")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Placa")
        plate_width = st.number_input(
            "Largura da placa [mm]",
            min_value=1.0,
            value=input_data.plate.width_mm,
            step=10.0,
            key="plate_width",
        )
        plate_height = st.number_input(
            "Altura da placa [mm]",
            min_value=1.0,
            value=input_data.plate.height_mm,
            step=10.0,
            key="plate_height",
        )
        plate_thickness = st.number_input(
            "Espessura da placa [mm]",
            min_value=0.1,
            value=input_data.plate.thickness_mm,
            step=0.5,
            key="plate_thickness",
        )
        hole_diameter_mm = st.number_input(
            "Diâmetro dos furos [mm]",
            min_value=1.0,
            value=(float(input_data.holes[0].diameter_mm) if input_data.holes else 82.0),
            step=1.0,
            key="hole_diameter_mm",
        )

    with col2:
        st.markdown("#### Material")
        preset_names = list(material_presets.keys())
        selected_preset = st.selectbox(
            "Material da placa",
            options=preset_names,
            index=(
                preset_names.index(st.session_state.material_preset)
                if st.session_state.material_preset in preset_names
                else 0
            ),
            key="material_preset",
        )
        preset_values = material_presets[selected_preset]
        st.caption(preset_values["description"])

        if selected_preset == "Personalizado":
            material_mu = st.number_input(
                "Permeabilidade μ [H/m]",
                min_value=1e-8,
                value=float(input_data.material.mu),
                format="%.3e",
                key="material_mu",
            )
            material_sigma = st.number_input(
                "Condutividade σ [S/m]",
                min_value=1e-15,
                value=float(input_data.material.sigma),
                format="%.3e",
                key="material_sigma",
            )
        else:
            material_mu = float(preset_values["mu"])
            material_sigma = float(preset_values["sigma"])
            st.text_input(
                "Permeabilidade μ [H/m]",
                value=f"{material_mu:.6e}",
                disabled=True,
            )
            st.text_input(
                "Condutividade σ [S/m]",
                value=f"{material_sigma:.6e}",
                disabled=True,
            )

    frequency = st.number_input(
        "Frequência [Hz]",
        min_value=0.1,
        value=input_data.frequency_hz,
        step=1.0,
        key="frequency",
    )
    im_a = st.number_input(
        "Corrente de referencia Im [A]",
        min_value=0.0,
        value=float(st.session_state.im_a),
        step=10.0,
        key="im_a",
        help="Magnitude de corrente aplicada a todos os condutores.",
    )

    a_spacing_mm = st.number_input(
        "a (distância x entre centros) [mm]",
        min_value=0.0,
        value=float(st.session_state.a_spacing_mm),
        step=1.0,
        key="a_spacing_mm",
        help="Aplicado nas posições x quando houver exatamente 3 furos/3 condutores.",
    )

    mesh_nx = 1000
    mesh_ny = 1000

    edited_holes = list(input_data.holes)
    edited_conductors = list(input_data.conductors)
    st.caption("Os valores individuais de corrente definem apenas o sinal (+/-); Im define a magnitude global.")
    if len(edited_holes) != 3 or len(edited_conductors) != 3:
        st.caption("O parâmetro a global requer exatamente 3 furos e 3 condutores.")

    # ─── MONTAGEM DA ENTRADA DE SIMULACAO ───────────────────────────────────
    try:
        holes_for_sim = edited_holes
        conductors_positioned = edited_conductors

        if len(edited_holes) == 3:
            holes_for_sim = _apply_spacing_a_to_x_positions(edited_holes, float(a_spacing_mm))

        # Aplica diametro global dos furos definido no frontend
        holes_for_sim = [
            h.model_copy(update={"diameter_mm": float(hole_diameter_mm)})
            for h in holes_for_sim
        ]

        if len(edited_conductors) == 3:
            conductors_positioned = _apply_spacing_a_to_x_positions(
                edited_conductors, float(a_spacing_mm)
            )
        conductors_for_sim = _apply_im_to_conductors(conductors_positioned, im_a)

        draft_input = Exercise01Input(
            plate=PlateInput(
                width_mm=plate_width,
                height_mm=plate_height,
                thickness_mm=plate_thickness,
            ),
            holes=holes_for_sim,
            conductors=conductors_for_sim,
            material=MaterialInput(mu=material_mu, sigma=material_sigma),
            frequency_hz=frequency,
            mesh=MeshInput(nx=mesh_nx, ny=mesh_ny),
        )
        st.session_state.exercise_01_input = draft_input
        input_data = draft_input

        is_valid, errors = GeometricValidator.validate_all(
            draft_input.plate,
            draft_input.holes,
            draft_input.conductors,
            draft_input.material.mu,
            draft_input.material.sigma,
        )
        if errors:
            st.warning("Validação geométrica/física encontrou inconsistências:")
            for error in errors:
                st.write(f"- {error}")
    except Exception as e:
        st.error(f"Erro de validação dos dados: {e}")
        return

    # Detecta se houve alteracao apos o ultimo calculo valido
    params_changed = (
        st.session_state.calculated_input is None
        or draft_input.model_dump() != st.session_state.calculated_input.model_dump()
    )

    # ─── BOTOES ──────────────────────────────────────────────────────────────
    st.divider()
    col_btn_calc, col_btn_reset = st.columns([1, 1])

    with col_btn_calc:
        if st.button("Calcular", use_container_width=True, type="primary", key="btn_calc"):
            try:
                is_valid, errors = GeometricValidator.validate_all(
                    input_data.plate,
                    input_data.holes,
                    input_data.conductors,
                    input_data.material.mu,
                    input_data.material.sigma,
                )
                if not is_valid:
                    st.error("Corrija os erros de validação antes de calcular.")
                    for error in errors:
                        st.write(f"- {error}")
                elif input_data.conductors:
                    st.session_state.simulation_result = simulate_exercise_01(input_data)
                    st.session_state.calculated_input = input_data
                    params_changed = False
                    st.rerun()
                else:
                    st.error("Adicione pelo menos um condutor")
            except Exception as e:
                st.error(f"Erro na simulação: {str(e)}")

    with col_btn_reset:
        if st.button("Restaurar padrão", use_container_width=True, key="btn_reset"):
            st.session_state.exercise_01_input = get_default_exercise01_input()
            st.session_state.simulation_result = None
            st.session_state.calculated_input = None
            st.rerun()

    # ─── GEOMETRIA E RESULTADOS (somente quando calculado e sem alteracoes) ────
    if params_changed:
        if st.session_state.calculated_input is not None:
            st.info("Parâmetros alterados. Clique em **Calcular** para atualizar.")
        return

    if st.session_state.simulation_result is None:
        return

    result = st.session_state.simulation_result
    calc_input = st.session_state.calculated_input
    vis_input = calc_input.model_copy(update={"mesh": MeshInput(nx=80, ny=80)})

    # ─── GEOMETRIA ───────────────────────────────────────────────────────────
    st.divider()
    st.markdown("### Geometria")

    fig_geo = None
    try:
        plate = create_plate_from_input(calc_input.plate, calc_input.holes)
        conductor_positions = np.array(
            [[c.x_mm * 1e-3, c.y_mm * 1e-3] for c in calc_input.conductors]
        )
        fig_geo = plot_geometry(plate, conductor_positions)
        st.plotly_chart(fig_geo, use_container_width=True)

        col_area, col_valid = st.columns(2)
        with col_area:
            plate_area = plate.width_m * plate.height_m
            st.metric("Área total da placa", f"{plate_area*1e6:.1f}", "mm²")
        with col_valid:
            valid_area = plate.get_valid_area_m2()
            st.metric("Área útil (sem furos)", f"{valid_area*1e6:.1f}", "mm²")
    except Exception as e:
        st.error(f"Erro ao desenhar geometria: {str(e)}")

    # ─── RESULTADOS ──────────────────────────────────────────────────────────
    st.divider()
    st.markdown("### Resultados da simulação")

    st.markdown("#### Comparação de métodos")
    col_analytical, col_approximate, col_diff = st.columns(3)

    with col_analytical:
        st.metric(
            "**Perda (Analítico)**",
            f"{result.total_loss_analytical_w:.2f}",
            "W",
            help="Fórmula analítica exata para geometria cilíndrica",
        )

    with col_approximate:
        st.metric(
            "**Perda (Aproximado)**",
            f"{result.total_loss_approximate_w:.2f}",
            "W",
            help="Método Biot-Savart com integração numérica",
        )

    with col_diff:
        diff_pct = (
            abs(result.total_loss_analytical_w - result.total_loss_approximate_w)
            / result.total_loss_analytical_w
            * 100
            if result.total_loss_analytical_w > 0
            else 0
        )
        st.metric("**Diferença**", f"{diff_pct:.1f}%", help="Desvio relativo entre métodos")

    analytical_details = _build_analytical_details(calc_input)
    biot_details = _build_biot_details(calc_input)

    st.divider()
    st.markdown("#### Equações utilizadas e detalhes de cálculo")

    with st.expander("Método analítico", expanded=False):
        st.latex(
            r"P = \left(\frac{I_m^2 q}{\pi \sigma}\right) \ln\left(\frac{b}{a}\right) "
            r"\left[\frac{\sinh(qc)-\sin(qc)}{\cosh(qc)+\cos(qc)}\right]"
        )
 
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            st.write(f"Im = {analytical_details['im_rms_a']:.2f} A")
            st.write(f"f = {calc_input.frequency_hz:.2f} Hz")
            st.write(f"ω = 2πf = {analytical_details['omega_rad_s']:.4f} rad/s")
            st.write(f"μ = {calc_input.material.mu:.6e} H/m")
            st.write(f"σ = {calc_input.material.sigma:.6e} S/m")
            st.write(f"c = {analytical_details['thickness_m']*1000:.3f} mm")

        st.write(f"Resultado analítico = {result.total_loss_analytical_w:.2f} W")

    with st.expander("Método aproximado (Biot-Savart)", expanded=False):
        st.latex(
            r"H_m(x,y)=\frac{I_m a}{2\pi}"
            r"\sqrt{\frac{3x^2+3y^2+a^2}{(x^2+y^2)(x^4+y^4+2x^2y^2-2a^2x^2+2a^2y^2+a^4)}}"
        )
        st.latex(
            r"P = \frac{1}{2\pi}\sqrt{\frac{\omega\mu}{2\sigma}}\iint |H_m(x,y)|^2\,dx\,dy"
        )
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if biot_details["a_mm"] is not None:
                st.write(f"a = {biot_details['a_mm']:.3f} mm")
            st.write(f"x = {biot_details['plate_x_mm']:.3f} mm")
            st.write(f"y = {biot_details['plate_y_mm']:.3f} mm")
            st.write(f"Im = {biot_details['im_rms_a']:.2f} A")
            st.write(f"ω = {biot_details['omega_rad_s']:.4f} rad/s")


        st.write(f"Resultado Biot-Savart = {result.total_loss_approximate_w:.2f} W")

    st.divider()

    figures_2d: list[tuple[str, go.Figure]] = []
    with st.expander("Visualizações 2D", expanded=True):
        st.caption("Visualizações com malha 80 x 80 para manter desempenho interativo.")
        show_2d = st.toggle("Gerar gráficos 2D", value=False, key="show_2d_graphs")
        if not show_2d:
            st.info("Ative 'Gerar gráficos 2D' para calcular e exibir as curvas.")
        else:
            st.markdown("#### Curvas de perdas por corrente")

            if calc_input.conductors:
                reference_current_a = float(max(im_a, 0.0))

                # Preserva o padrao de sinais de corrente do ultimo estado calculado
                base_conductors = calc_input.conductors

                end_current_a = reference_current_a * 1.1
                end_current_int = int(np.floor(end_current_a))
                sweep_currents = np.arange(0, end_current_int + 1, 1, dtype=float)
                sweep_currents = _limit_sweep_points(sweep_currents)

                analytical_losses = []
                approximate_losses = []
                for sweep_i in sweep_currents:
                    sweep_input = vis_input.model_copy(
                        update={
                            "conductors": _apply_im_to_conductors(base_conductors, float(sweep_i))
                        }
                    )
                    sweep_result = simulate_exercise_01(sweep_input)
                    analytical_losses.append(sweep_result.total_loss_analytical_w)
                    approximate_losses.append(sweep_result.total_loss_approximate_w)

                fig_losses = go.Figure()
                fig_losses.add_trace(
                    go.Scatter(
                        x=sweep_currents,
                        y=analytical_losses,
                        mode="lines",
                        name="Analítico",
                        line={"width": 3},
                    )
                )
                fig_losses.add_trace(
                    go.Scatter(
                        x=sweep_currents,
                        y=approximate_losses,
                        mode="lines",
                        name="Biot-Savart",
                        line={"width": 3},
                    )
                )
                fig_losses.update_layout(
                    xaxis_title="Corrente [A]",
                    yaxis_title="Perdas [W]",
                    legend_title="Método",
                    margin={"l": 20, "r": 20, "t": 20, "b": 20},
                    hovermode="x unified",
                    height=350,
                )
                st.plotly_chart(fig_losses, use_container_width=True)
                figures_2d.append(("Perdas por corrente", fig_losses))
                st.caption(
                    f"Intervalo avaliado: 0 até {end_current_int} A com passo de 1 A (corrente informada + 10%)."
                )
            else:
                st.info("Adicione ao menos um condutor para visualizar as curvas de perdas.")

            st.markdown("#### Curvas de perdas por espessura")
            end_thickness_mm = float(calc_input.plate.thickness_mm * 1.1)
            sweep_thickness_mm = np.arange(0.1, end_thickness_mm + 0.05, 0.1, dtype=float)
            sweep_thickness_mm = _limit_sweep_points(sweep_thickness_mm)

            analytical_losses_thickness = []
            approximate_losses_thickness = []
            for sweep_thickness in sweep_thickness_mm:
                sweep_input = vis_input.model_copy(
                    update={
                        "plate": vis_input.plate.model_copy(
                            update={"thickness_mm": float(sweep_thickness)}
                        )
                    }
                )
                sweep_result = simulate_exercise_01(sweep_input)
                analytical_losses_thickness.append(sweep_result.total_loss_analytical_w)
                approximate_losses_thickness.append(sweep_result.total_loss_approximate_w)

            fig_thickness = go.Figure()
            fig_thickness.add_trace(
                go.Scatter(
                    x=sweep_thickness_mm,
                    y=analytical_losses_thickness,
                    mode="lines",
                    name="Analítico",
                    line={"width": 3},
                )
            )
            fig_thickness.add_trace(
                go.Scatter(
                    x=sweep_thickness_mm,
                    y=approximate_losses_thickness,
                    mode="lines",
                    name="Biot-Savart",
                    line={"width": 3},
                )
            )
            fig_thickness.update_layout(
                xaxis_title="Espessura [mm]",
                yaxis_title="Perdas [W]",
                legend_title="Método",
                margin={"l": 20, "r": 20, "t": 20, "b": 20},
                hovermode="x unified",
                height=350,
            )
            st.plotly_chart(fig_thickness, use_container_width=True)
            figures_2d.append(("Perdas por espessura", fig_thickness))
            st.caption(
                f"Intervalo avaliado: 0.1 até {end_thickness_mm:.1f} mm (espessura informada + 10%)."
            )

            st.markdown("#### Curvas de perdas por frequência")
            end_frequency_hz = float(calc_input.frequency_hz * 1.1)
            sweep_frequency_hz = np.arange(0.1, end_frequency_hz + 1.0, 1.0, dtype=float)
            sweep_frequency_hz = _limit_sweep_points(sweep_frequency_hz)

            analytical_losses_frequency = []
            approximate_losses_frequency = []
            for sweep_frequency in sweep_frequency_hz:
                sweep_input = vis_input.model_copy(update={"frequency_hz": float(sweep_frequency)})
                sweep_result = simulate_exercise_01(sweep_input)
                analytical_losses_frequency.append(sweep_result.total_loss_analytical_w)
                approximate_losses_frequency.append(sweep_result.total_loss_approximate_w)

            fig_frequency = go.Figure()
            fig_frequency.add_trace(
                go.Scatter(
                    x=sweep_frequency_hz,
                    y=analytical_losses_frequency,
                    mode="lines",
                    name="Analítico",
                    line={"width": 3},
                )
            )
            fig_frequency.add_trace(
                go.Scatter(
                    x=sweep_frequency_hz,
                    y=approximate_losses_frequency,
                    mode="lines",
                    name="Biot-Savart",
                    line={"width": 3},
                )
            )
            fig_frequency.update_layout(
                xaxis_title="Frequência [Hz]",
                yaxis_title="Perdas [W]",
                legend_title="Método",
                margin={"l": 20, "r": 20, "t": 20, "b": 20},
                hovermode="x unified",
                height=350,
            )
            st.plotly_chart(fig_frequency, use_container_width=True)
            figures_2d.append(("Perdas por frequencia", fig_frequency))
            st.caption(
                f"Intervalo avaliado: 0.1 até {end_frequency_hz:.1f} Hz (frequência informada + 10%)."
            )

    st.divider()

    figures_3d: list[tuple[str, go.Figure]] = []
    with st.expander("Visualizações 3D", expanded=False):
        st.caption("Visualizações com malha 80 x 80 e grade reduzida para manter desempenho interativo.")
        show_3d = st.toggle("Gerar gráficos 3D", value=False, key="show_3d_graphs")
        if not show_3d:
            st.info("Ative 'Gerar gráficos 3D' para calcular e exibir as superfícies.")
        elif not calc_input.conductors:
            st.info("Adicione ao menos um condutor para visualizar o gráfico 3D.")
        else:
            reference_current_a = float(max(im_a, 0.0))
            base_conductors = calc_input.conductors

            st.markdown("#### Gráfico 3D: Perdas por Corrente × Espessura")
            st.caption(f"Frequência fixa em {calc_input.frequency_hz:.1f} Hz")

            max_current = reference_current_a * 1.1
            max_thickness = float(calc_input.plate.thickness_mm * 1.1)
            current_3d = np.linspace(0, max_current, 5)
            thickness_3d = np.linspace(0.1, max_thickness, 5)

            analytical_surface = np.zeros((len(thickness_3d), len(current_3d)))
            approximate_surface = np.zeros((len(thickness_3d), len(current_3d)))
            for i, thickness_val in enumerate(thickness_3d):
                for j, current_val in enumerate(current_3d):
                    surf_input = vis_input.model_copy(
                        update={
                            "plate": vis_input.plate.model_copy(
                                update={"thickness_mm": float(thickness_val)}
                            ),
                            "conductors": _apply_im_to_conductors(base_conductors, float(current_val)),
                        }
                    )
                    surf_result = simulate_exercise_01(surf_input)
                    analytical_surface[i, j] = surf_result.total_loss_analytical_w
                    approximate_surface[i, j] = surf_result.total_loss_approximate_w

            fig_3d = make_subplots(
                rows=1,
                cols=2,
                specs=[[{"type": "surface"}, {"type": "surface"}]],
                subplot_titles=("Analítico", "Biot-Savart"),
                horizontal_spacing=0.1,
            )
            fig_3d.add_trace(
                go.Surface(
                    x=current_3d,
                    y=thickness_3d,
                    z=analytical_surface,
                    colorscale="Viridis",
                    name="Analítico",
                    showscale=True,
                    colorbar={"x": 0.45, "len": 0.7},
                ),
                row=1,
                col=1,
            )
            fig_3d.add_trace(
                go.Surface(
                    x=current_3d,
                    y=thickness_3d,
                    z=approximate_surface,
                    colorscale="Viridis",
                    name="Biot-Savart",
                    showscale=True,
                    colorbar={"x": 1.02, "len": 0.7},
                ),
                row=1,
                col=2,
            )
            fig_3d.update_xaxes(title_text="Corrente [A]", row=1, col=1)
            fig_3d.update_xaxes(title_text="Corrente [A]", row=1, col=2)
            fig_3d.update_yaxes(title_text="Espessura [mm]", row=1, col=1)
            fig_3d.update_yaxes(title_text="Espessura [mm]", row=1, col=2)
            fig_3d.update_layout(
                height=600,
                margin={"l": 0, "r": 0, "t": 40, "b": 0},
                scene={
                    "xaxis_title": "Corrente [A]",
                    "yaxis_title": "Espessura [mm]",
                    "zaxis_title": "Perdas [W]",
                },
                scene2={
                    "xaxis_title": "Corrente [A]",
                    "yaxis_title": "Espessura [mm]",
                    "zaxis_title": "Perdas [W]",
                },
            )
            st.plotly_chart(fig_3d, use_container_width=True)
            figures_3d.append(("Perdas por corrente x espessura", fig_3d))
            st.caption(f"Grade de cálculo: {len(current_3d)} × {len(thickness_3d)} pontos")

            st.markdown("#### Gráfico 3D: Perdas por Corrente × Frequência")
            st.caption(f"Espessura fixa em {calc_input.plate.thickness_mm:.1f} mm")

            max_frequency = float(calc_input.frequency_hz * 1.1)
            current_3d_freq = np.linspace(0, max_current, 5)
            frequency_3d = np.linspace(0.1, max_frequency, 5)

            analytical_surface_freq = np.zeros((len(frequency_3d), len(current_3d_freq)))
            approximate_surface_freq = np.zeros((len(frequency_3d), len(current_3d_freq)))
            for i, freq_val in enumerate(frequency_3d):
                for j, current_val in enumerate(current_3d_freq):
                    surf_input = vis_input.model_copy(
                        update={
                            "frequency_hz": float(freq_val),
                            "conductors": _apply_im_to_conductors(base_conductors, float(current_val)),
                        }
                    )
                    surf_result = simulate_exercise_01(surf_input)
                    analytical_surface_freq[i, j] = surf_result.total_loss_analytical_w
                    approximate_surface_freq[i, j] = surf_result.total_loss_approximate_w

            fig_3d_freq = make_subplots(
                rows=1,
                cols=2,
                specs=[[{"type": "surface"}, {"type": "surface"}]],
                subplot_titles=("Analítico", "Biot-Savart"),
                horizontal_spacing=0.1,
            )
            fig_3d_freq.add_trace(
                go.Surface(
                    x=current_3d_freq,
                    y=frequency_3d,
                    z=analytical_surface_freq,
                    colorscale="Viridis",
                    name="Analítico",
                    showscale=True,
                    colorbar={"x": 0.45, "len": 0.7},
                ),
                row=1,
                col=1,
            )
            fig_3d_freq.add_trace(
                go.Surface(
                    x=current_3d_freq,
                    y=frequency_3d,
                    z=approximate_surface_freq,
                    colorscale="Viridis",
                    name="Biot-Savart",
                    showscale=True,
                    colorbar={"x": 1.02, "len": 0.7},
                ),
                row=1,
                col=2,
            )
            fig_3d_freq.update_xaxes(title_text="Corrente [A]", row=1, col=1)
            fig_3d_freq.update_xaxes(title_text="Corrente [A]", row=1, col=2)
            fig_3d_freq.update_yaxes(title_text="Frequência [Hz]", row=1, col=1)
            fig_3d_freq.update_yaxes(title_text="Frequência [Hz]", row=1, col=2)
            fig_3d_freq.update_layout(
                height=600,
                margin={"l": 0, "r": 0, "t": 40, "b": 0},
                scene={
                    "xaxis_title": "Corrente [A]",
                    "yaxis_title": "Frequência [Hz]",
                    "zaxis_title": "Perdas [W]",
                },
                scene2={
                    "xaxis_title": "Corrente [A]",
                    "yaxis_title": "Frequência [Hz]",
                    "zaxis_title": "Perdas [W]",
                },
            )
            st.plotly_chart(fig_3d_freq, use_container_width=True)
            figures_3d.append(("Perdas por corrente x frequencia", fig_3d_freq))
            st.caption(f"Grade de cálculo: {len(current_3d_freq)} × {len(frequency_3d)} pontos")

            st.markdown("#### Gráfico 3D: Perdas por Espessura × Frequência")
            st.caption(f"Corrente fixa em {reference_current_a:.1f} A")

            thickness_3d_freq = np.linspace(0.1, max_thickness, 5)
            frequency_3d_thick = np.linspace(0.1, max_frequency, 5)

            analytical_surface_thick_freq = np.zeros((len(frequency_3d_thick), len(thickness_3d_freq)))
            approximate_surface_thick_freq = np.zeros((len(frequency_3d_thick), len(thickness_3d_freq)))
            for i, freq_val in enumerate(frequency_3d_thick):
                for j, thickness_val in enumerate(thickness_3d_freq):
                    surf_input = vis_input.model_copy(
                        update={
                            "frequency_hz": float(freq_val),
                            "plate": vis_input.plate.model_copy(
                                update={"thickness_mm": float(thickness_val)}
                            ),
                        }
                    )
                    surf_result = simulate_exercise_01(surf_input)
                    analytical_surface_thick_freq[i, j] = surf_result.total_loss_analytical_w
                    approximate_surface_thick_freq[i, j] = surf_result.total_loss_approximate_w

            fig_3d_thick_freq = make_subplots(
                rows=1,
                cols=2,
                specs=[[{"type": "surface"}, {"type": "surface"}]],
                subplot_titles=("Analítico", "Biot-Savart"),
                horizontal_spacing=0.1,
            )
            fig_3d_thick_freq.add_trace(
                go.Surface(
                    x=thickness_3d_freq,
                    y=frequency_3d_thick,
                    z=analytical_surface_thick_freq,
                    colorscale="Viridis",
                    name="Analítico",
                    showscale=True,
                    colorbar={"x": 0.45, "len": 0.7},
                ),
                row=1,
                col=1,
            )
            fig_3d_thick_freq.add_trace(
                go.Surface(
                    x=thickness_3d_freq,
                    y=frequency_3d_thick,
                    z=approximate_surface_thick_freq,
                    colorscale="Viridis",
                    name="Biot-Savart",
                    showscale=True,
                    colorbar={"x": 1.02, "len": 0.7},
                ),
                row=1,
                col=2,
            )
            fig_3d_thick_freq.update_xaxes(title_text="Espessura [mm]", row=1, col=1)
            fig_3d_thick_freq.update_xaxes(title_text="Espessura [mm]", row=1, col=2)
            fig_3d_thick_freq.update_yaxes(title_text="Frequência [Hz]", row=1, col=1)
            fig_3d_thick_freq.update_yaxes(title_text="Frequência [Hz]", row=1, col=2)
            fig_3d_thick_freq.update_layout(
                height=600,
                margin={"l": 0, "r": 0, "t": 40, "b": 0},
                scene={
                    "xaxis_title": "Espessura [mm]",
                    "yaxis_title": "Frequência [Hz]",
                    "zaxis_title": "Perdas [W]",
                },
                scene2={
                    "xaxis_title": "Espessura [mm]",
                    "yaxis_title": "Frequência [Hz]",
                    "zaxis_title": "Perdas [W]",
                },
            )
            st.plotly_chart(fig_3d_thick_freq, use_container_width=True)
            figures_3d.append(("Perdas por espessura x frequencia", fig_3d_thick_freq))
            st.caption(
                f"Grade de cálculo: {len(thickness_3d_freq)} × {len(frequency_3d_thick)} pontos"
            )

if __name__ == "__main__":
    main()
