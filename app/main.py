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
from app.core.exercises.q01_tank_losses import simulate_exercise_01, simulate_exercise_03_biot_only
from app.core.exercises.q04_rectangular_conductors import solve_question_04_rectangular_conductors
from app.core.electromagnetics.rectangular_conductors import (
    create_q4_geometry_figure,
    create_q4_power_loss_comparison,
)
from app.core.electromagnetics.biot_savart import calculate_loss_analytical
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


def _plotly_figure_to_csv_bytes(fig: go.Figure) -> bytes:
    """Serializa os dados visiveis da figura Plotly para CSV.

    Formato longo padrao: trace_name, trace_type, x, y, z
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["trace_name", "trace_type", "x", "y", "z"])

    for idx, trace in enumerate(fig.data):
        visible = getattr(trace, "visible", True)
        if visible == "legendonly":
            continue

        trace_name = getattr(trace, "name", None) or f"trace_{idx+1}"
        trace_type = getattr(trace, "type", "unknown")

        if trace_type == "surface":
            z_values = np.array(getattr(trace, "z", []), dtype=object)
            if z_values.ndim != 2:
                continue

            x_raw = getattr(trace, "x", None)
            y_raw = getattr(trace, "y", None)
            x_values = np.array(x_raw, dtype=object) if x_raw is not None else np.arange(z_values.shape[1], dtype=object)
            y_values = np.array(y_raw, dtype=object) if y_raw is not None else np.arange(z_values.shape[0], dtype=object)

            for i in range(z_values.shape[0]):
                for j in range(z_values.shape[1]):
                    if x_values.ndim == 2:
                        x_val = x_values[i, j]
                    else:
                        x_val = x_values[j] if j < len(x_values) else j

                    if y_values.ndim == 2:
                        y_val = y_values[i, j]
                    else:
                        y_val = y_values[i] if i < len(y_values) else i

                    writer.writerow([trace_name, trace_type, x_val, y_val, z_values[i, j]])
            continue

        y_values = getattr(trace, "y", None)
        x_values = getattr(trace, "x", None)
        z_values = getattr(trace, "z", None)

        if y_values is None and z_values is None:
            continue

        y_list = list(y_values) if y_values is not None else []
        x_list = list(x_values) if x_values is not None else list(range(len(y_list)))
        n_rows = min(len(x_list), len(y_list)) if y_list else 0

        for i in range(n_rows):
            writer.writerow([trace_name, trace_type, x_list[i], y_list[i], ""])

    return output.getvalue().encode("utf-8")


def _plotly_chart_with_csv(
    fig: go.Figure,
    key_prefix: str,
    csv_filename: str,
) -> None:
    """Renderiza grafico Plotly e exibe exportacao CSV padrao logo abaixo."""
    st.plotly_chart(fig, use_container_width=True)
    csv_bytes = _plotly_figure_to_csv_bytes(fig)
    st.download_button(
        "Baixar CSV do gráfico",
        data=csv_bytes,
        file_name=csv_filename,
        mime="text/csv",
        key=f"{key_prefix}_csv",
    )


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
            f"Perda aproximada: {result.total_loss_approximate_w:.4f} W",
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


def _get_q5_material_options() -> list[dict]:
    """Retorna materiais predefinidos para comparação da Q5 (base da Q3)."""
    mu0 = 4.0 * np.pi * 1e-7
    material_presets = get_material_presets()
    materials = []
    for name, values in material_presets.items():
        if name == "Personalizado":
            continue
        mu = float(values["mu"])
        sigma = float(values["sigma"])
        mu_rel = mu / mu0
        materials.append(
            {
                "name": name,
                "mu": mu,
                "sigma": sigma,
                "mu_rel": mu_rel,
            }
        )
    return materials


def _extract_q5_metric_value(result, metric_key: str) -> float:
    """Extrai uma grandeza escalar da saída da Q5 para gráficos de varredura."""
    metric_map = {
        "rect_b_loss": float(result.rectangular_variant_b_loss_w_per_m2),
        "rect_a_loss": float(result.rectangular_variant_a_loss_w_per_m2),
        "rect_c_loss": float(result.rectangular_variant_c_loss_w_per_m2),
        "circular_loss": float(result.circular_conductor_loss_w_per_m2),
        "sheet_finite_loss": float(result.sheet_finite_loss_w_per_m2),
        "sheet_semi_loss": float(result.sheet_semi_infinite_loss_w_per_m2),
        "skin_depth_mm": float(result.skin_depth_mm),
    }
    return metric_map[metric_key]


def _get_q1_material_options() -> list[dict]:
    """Retorna materiais da Q1 e demais materiais disponiveis no software."""
    mu0 = 4.0 * np.pi * 1e-7
    materials: list[dict] = [
        {"name": "Aço carbono (Q1)", "sigma": 4.0e6, "mu_r": 200.0},
        {"name": "Aço inox (Q1)", "sigma": 1.33e6, "mu_r": 1.0},
    ]

    for name, values in get_material_presets().items():
        if name == "Personalizado":
            continue
        materials.append(
            {
                "name": name,
                "sigma": float(values["sigma"]),
                "mu_r": float(values["mu"]) / mu0,
            }
        )

    # Remove duplicatas por nome mantendo a primeira ocorrencia.
    deduped: dict[str, dict] = {}
    for material in materials:
        if material["name"] not in deduped:
            deduped[material["name"]] = material
    return list(deduped.values())


def _q1_metric_value(
    metric_key: str,
    i_a: float,
    c_mm: float,
    f_hz: float,
    ln_factor: float,
    mu: float,
    sigma: float,
) -> float:
    """Calcula grandezas escalares da Q1 para varreduras de grafico."""
    if metric_key == "loss_w":
        return float(
            calculate_loss_analytical(
                im=float(i_a),
                thickness_m=float(c_mm) * 1e-3,
                frequency_hz=float(f_hz),
                mu=float(mu),
                sigma=float(sigma),
                num_conductors=1,
                ln_ba=float(ln_factor),
            )
        )

    omega = 2.0 * np.pi * float(f_hz)
    if omega <= 0 or mu <= 0 or sigma <= 0:
        return float("inf")
    skin_depth_m = np.sqrt(2.0 / (omega * float(mu) * float(sigma)))
    return float(skin_depth_m * 1000.0)


def _compute_q1_regional_3d_maps(
    outer_d_mm: float,
    inner_d_mm: float,
    thickness_mm: float,
    frequency_hz: float,
    im_a: float,
    mu: float,
    sigma: float,
    xy_points: int,
    thickness_quad_order: int,
    region_size_mm: float,
) -> dict:
    """Modela campo/perdas 3D da Q1 e agrega resultados por região no plano XY.

    Estratégia numérica:
    - domínio anular no plano XY (malha uniforme);
    - integração em z por quadratura de Gauss-Legendre;
    - agregação por regiões cartesianas (células em mm).
    """
    omega = 2.0 * np.pi * float(frequency_hz)
    if omega <= 0.0 or mu <= 0.0 or sigma <= 0.0:
        raise ValueError("Parâmetros físicos inválidos para modelagem 3D da Q1.")

    outer_r_m = float(outer_d_mm) * 0.5e-3
    inner_r_m = float(inner_d_mm) * 0.5e-3
    thickness_m = float(thickness_mm) * 1e-3
    if outer_r_m <= 0.0 or inner_r_m <= 0.0 or inner_r_m >= outer_r_m or thickness_m <= 0.0:
        raise ValueError("Geometria inválida para modelagem 3D da Q1.")

    n_xy = int(max(40, xy_points))
    quad_order = int(max(2, thickness_quad_order))
    region_size_m = float(max(1.0, region_size_mm)) * 1e-3

    delta_m = np.sqrt(2.0 / (omega * float(mu) * float(sigma)))
    delta_safe = float(max(delta_m, 1e-12))

    x = np.linspace(-outer_r_m, outer_r_m, n_xy)
    y = np.linspace(-outer_r_m, outer_r_m, n_xy)
    x_mesh, y_mesh = np.meshgrid(x, y)
    r_mesh = np.sqrt(x_mesh**2 + y_mesh**2)

    valid_mask = (r_mesh >= inner_r_m) & (r_mesh <= outer_r_m)
    r_safe = np.where(valid_mask, np.maximum(r_mesh, 1e-12), 1.0)

    h_surface = np.where(valid_mask, abs(float(im_a)) / (2.0 * np.pi * r_safe), 0.0)

    z_nodes, z_weights = np.polynomial.legendre.leggauss(quad_order)
    z = 0.5 * (z_nodes + 1.0) * thickness_m
    wz = 0.5 * thickness_m * z_weights

    attenuation_h = np.exp(-z / delta_safe)
    attenuation_p = np.exp(-2.0 * z / delta_safe)

    h_avg_factor = float(np.sum(attenuation_h * wz) / thickness_m)
    h_avg_map = np.where(valid_mask, h_surface * h_avg_factor, np.nan)

    p_factor = (2.0 / (float(sigma) * delta_safe**2)) * float(np.sum(attenuation_p * wz))
    loss_area_map = np.where(valid_mask, (h_surface**2) * p_factor, np.nan)

    dx = float(x[1] - x[0]) if len(x) > 1 else 0.0
    dy = float(y[1] - y[0]) if len(y) > 1 else 0.0
    dA = dx * dy

    total_loss_w = float(np.nansum(loss_area_map) * dA)

    ux = np.where(valid_mask, -y_mesh / r_safe, 0.0)
    uy = np.where(valid_mask, x_mesh / r_safe, 0.0)

    stride = max(1, n_xy // 32)
    x_sub = x_mesh[::stride, ::stride]
    y_sub = y_mesh[::stride, ::stride]
    ux_sub = ux[::stride, ::stride]
    uy_sub = uy[::stride, ::stride]
    mask_sub = valid_mask[::stride, ::stride]

    line_len_mm = 8.0
    line_x: list[float | None] = []
    line_y: list[float | None] = []
    for i in range(x_sub.shape[0]):
        for j in range(x_sub.shape[1]):
            if not bool(mask_sub[i, j]):
                continue
            x0 = float(x_sub[i, j] * 1000.0)
            y0 = float(y_sub[i, j] * 1000.0)
            x1 = x0 + float(ux_sub[i, j] * line_len_mm)
            y1 = y0 + float(uy_sub[i, j] * line_len_mm)
            line_x.extend([x0, x1, None])
            line_y.extend([y0, y1, None])

    span = 2.0 * outer_r_m
    n_regions = int(max(1, np.ceil(span / region_size_m)))

    ix = np.clip(((x_mesh + outer_r_m) / region_size_m).astype(int), 0, n_regions - 1)
    iy = np.clip(((y_mesh + outer_r_m) / region_size_m).astype(int), 0, n_regions - 1)
    flat_idx = (iy * n_regions + ix).ravel()

    valid_loss = np.isfinite(loss_area_map).ravel()
    weights_loss_w = (np.nan_to_num(loss_area_map, nan=0.0) * dA).ravel()
    region_sum_loss = np.bincount(
        flat_idx[valid_loss],
        weights=weights_loss_w[valid_loss],
        minlength=n_regions * n_regions,
    ).reshape(n_regions, n_regions)
    region_count_loss = np.bincount(
        flat_idx[valid_loss],
        minlength=n_regions * n_regions,
    ).reshape(n_regions, n_regions)

    valid_field = np.isfinite(h_avg_map).ravel()
    weights_field = np.nan_to_num(h_avg_map, nan=0.0).ravel()
    region_sum_h = np.bincount(
        flat_idx[valid_field],
        weights=weights_field[valid_field],
        minlength=n_regions * n_regions,
    ).reshape(n_regions, n_regions)
    region_count_h = np.bincount(
        flat_idx[valid_field],
        minlength=n_regions * n_regions,
    ).reshape(n_regions, n_regions)

    region_loss_w = np.where(region_count_loss > 0, region_sum_loss, np.nan)
    region_field_h = np.where(region_count_h > 0, region_sum_h / np.maximum(region_count_h, 1), np.nan)

    centers_mm = (
        (np.arange(n_regions, dtype=float) + 0.5) * region_size_m - outer_r_m
    ) * 1000.0

    top_loss = []
    top_field = []
    for iy_idx in range(n_regions):
        for ix_idx in range(n_regions):
            x0 = (-outer_r_m + ix_idx * region_size_m) * 1000.0
            x1 = x0 + region_size_m * 1000.0
            y0 = (-outer_r_m + iy_idx * region_size_m) * 1000.0
            y1 = y0 + region_size_m * 1000.0
            region_label = f"X[{x0:.0f},{x1:.0f}] mm | Y[{y0:.0f},{y1:.0f}] mm"

            loss_val = region_loss_w[iy_idx, ix_idx]
            if np.isfinite(loss_val):
                top_loss.append({"Região": region_label, "Perda integrada [W]": float(loss_val)})

            h_val = region_field_h[iy_idx, ix_idx]
            if np.isfinite(h_val):
                top_field.append({"Região": region_label, "Campo médio [A/m]": float(h_val)})

    top_loss = sorted(top_loss, key=lambda r: r["Perda integrada [W]"], reverse=True)
    top_field = sorted(top_field, key=lambda r: r["Campo médio [A/m]"], reverse=True)

    return {
        "delta_mm": float(delta_m * 1000.0),
        "total_loss_w": total_loss_w,
        "active_regions": int(np.sum(np.isfinite(region_loss_w))),
        "region_centers_mm": centers_mm,
        "region_loss_w": region_loss_w,
        "region_field_h": region_field_h,
        "line_x": line_x,
        "line_y": line_y,
        "top_loss": top_loss,
        "top_field": top_field,
        "outer_radius_mm": float(outer_r_m * 1000.0),
        "inner_radius_mm": float(inner_r_m * 1000.0),
    }


def _get_q3_material_options() -> list[dict]:
    """Retorna materiais para comparacao da Q3 (enunciado + presets do ambiente)."""
    mu0 = 4.0 * np.pi * 1e-7
    materials: list[dict] = [
        {"name": "Aço carbono (Q3 enunciado)", "sigma": 2.0e7, "mu_r": 500.0},
    ]

    for name, values in get_material_presets().items():
        if name == "Personalizado":
            continue
        materials.append(
            {
                "name": name,
                "sigma": float(values["sigma"]),
                "mu_r": float(values["mu"]) / mu0,
            }
        )

    deduped: dict[str, dict] = {}
    for material in materials:
        if material["name"] not in deduped:
            deduped[material["name"]] = material
    return list(deduped.values())


def _extract_q3_metric_value(result: dict, metric_key: str) -> float:
    """Extrai grandeza escalar da simulacao Biot-Savart da Q3."""
    metric_map = {
        "loss_w": float(result["total_loss_biot_w"]),
        "h_max": float(result["max_h_field"]),
        "loss_density_max": float(result["max_loss_density"]),
    }
    return metric_map[metric_key]


def _show_exercise_01_intro_sections() -> None:
    """Exibe base teorica e resultados validados com conteudo expansivel."""
    slides_dir = PROJECT_ROOT / "base_teorica" / "Exercicio_1"
    section_slides = {
        "Base teórica 1:": [
            "pagina 16.png",
            "pagina 17.png",
            "pagina 18.png",
        ],
        "Base teórica 2: Método Biot-Savart": ["pagina 19.png"],
        "Resultados validados": ["pagina 20.png"],
    }



def _show_assessment_q1_tab() -> None:
    """Questao 1 da avaliacao: perdas na tampa circular."""
    st.markdown("### Questão 1: Perdas por correntes induzidas na tampa circular")
    st.caption(
        "Dados do enunciado: f=60 Hz, D=910 mm, d=165 mm, c=9.52 mm, Im=1000 Arms. "
        "Método: Análise analítica."
    )

    st.divider()
    st.markdown("#### 1. Parametrizações")

    col_a, col_b = st.columns(2)
    with col_a:
        frequency_hz = st.number_input("Frequência [Hz]", min_value=0.1, value=60.0, key="av1_q1_f")
        outer_d_mm = st.number_input(
            "Diâmetro externo D [mm]", min_value=1.0, value=910.0, key="av1_q1_d_ext"
        )
        inner_d_mm = st.number_input(
            "Diâmetro interno d [mm]", min_value=1.0, value=165.0, key="av1_q1_d_int"
        )
    with col_b:
        thickness_mm = st.number_input(
            "Espessura c [mm]", min_value=0.01, value=9.52, key="av1_q1_thickness"
        )
        im_a = st.number_input("Corrente Im [Arms]", min_value=0.0, value=1000.0, key="av1_q1_im")

    if inner_d_mm >= outer_d_mm:
        st.error("O diâmetro interno deve ser menor que o diâmetro externo.")
        return

    mu0 = 4.0 * np.pi * 1e-7
    ln_ba = float(np.log(outer_d_mm / inner_d_mm))
    materials = _get_q1_material_options()

    st.divider()
    st.markdown("#### 2. Gráficos 2D - Perdas (multi-material)")
    st.caption(
        "Curvas em X para todos os materiais habilitados, "
        "incluindo os materiais base da Q1 e os demais disponíveis no software."
    )

    st.markdown("**Materiais habilitados**")
    enabled_materials = []
    material_cols = st.columns(3)
    for idx, material in enumerate(materials):
        default_enabled = idx < 6
        with material_cols[idx % 3]:
            enabled = st.checkbox(
                material["name"],
                value=default_enabled,
                key=f"q1_material_enabled_{idx}",
            )
        if enabled:
            enabled_materials.append(material)

    if not enabled_materials:
        st.warning("Selecione ao menos um material para gerar os gráficos da Q1.")
    else:
        metric_options = {
            "Perda analítica [W]": "loss_w",
            "Skin Depth [mm]": "skin_depth_mm",
        }
        metric_label = st.selectbox(
            "Grandeza no eixo Y",
            options=list(metric_options.keys()),
            index=0,
            key="q1_metric_y",
        )
        metric_key = metric_options[metric_label]

        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            freq_min = st.number_input("f mín [Hz]", min_value=0.1, value=10.0, key="q1_freq_min")
            freq_max = st.number_input("f máx [Hz]", min_value=1.0, value=500.0, key="q1_freq_max")
        with col_s2:
            i_min = st.number_input("Im mín [A]", min_value=0.1, value=100.0, key="q1_i_min")
            i_max = st.number_input("Im máx [A]", min_value=1.0, value=3000.0, key="q1_i_max")
        with col_s3:
            n_points = int(
                st.slider("Pontos por curva", min_value=8, max_value=60, value=24, key="q1_n_points")
            )
        log_scale_x = st.toggle("Escala log no eixo X", value=True, key="q1_log_x")

        if freq_max <= freq_min:
            st.warning("Ajuste a faixa de frequência: f máx deve ser maior que f mín.")
        elif i_max <= i_min:
            st.warning("Ajuste a faixa de corrente: Im máx deve ser maior que Im mín.")
        else:
            if log_scale_x:
                x_freq = _limit_sweep_points(np.geomspace(freq_min, freq_max, n_points), max_points=n_points)
                x_current = _limit_sweep_points(np.geomspace(i_min, i_max, n_points), max_points=n_points)
            else:
                x_freq = _limit_sweep_points(np.linspace(freq_min, freq_max, n_points), max_points=n_points)
                x_current = _limit_sweep_points(np.linspace(i_min, i_max, n_points), max_points=n_points)

            fig_freq = go.Figure()
            fig_current = go.Figure()

            for material in enabled_materials:
                mu_value = mu0 * float(material["mu_r"])
                sigma_value = float(material["sigma"])

                y_freq = [
                    _q1_metric_value(
                        metric_key,
                        i_a=float(im_a),
                        c_mm=float(thickness_mm),
                        f_hz=float(f_hz),
                        ln_factor=ln_ba,
                        mu=mu_value,
                        sigma=sigma_value,
                    )
                    for f_hz in x_freq
                ]
                y_current = [
                    _q1_metric_value(
                        metric_key,
                        i_a=float(i_a),
                        c_mm=float(thickness_mm),
                        f_hz=float(frequency_hz),
                        ln_factor=ln_ba,
                        mu=mu_value,
                        sigma=sigma_value,
                    )
                    for i_a in x_current
                ]

                fig_freq.add_trace(
                    go.Scatter(x=x_freq, y=y_freq, mode="lines", name=material["name"])
                )
                fig_current.add_trace(
                    go.Scatter(x=x_current, y=y_current, mode="lines", name=material["name"])
                )

            fig_freq.update_layout(
                title=f"Q1: {metric_label} vs Frequência",
                xaxis_title="Frequência [Hz]",
                yaxis_title=metric_label,
                hovermode="x unified",
                height=430,
            )
            fig_current.update_layout(
                title=f"Q1: {metric_label} vs Corrente Im",
                xaxis_title="Corrente Im [A]",
                yaxis_title=metric_label,
                hovermode="x unified",
                height=430,
            )
            if log_scale_x:
                fig_freq.update_xaxes(type="log")
                fig_current.update_xaxes(type="log")

            _plotly_chart_with_csv(fig_freq, "q1_fig_freq", "q1_varredura_frequencia.csv")
            _plotly_chart_with_csv(fig_current, "q1_fig_current", "q1_varredura_corrente.csv")

    st.divider()
    st.markdown("#### 3. Gráficos 3D - Superfícies analíticas")
    st.caption("Visualizações tridimensionais de perdas em função de pares de parâmetros.")

    selected_material_3d = st.selectbox(
        "Material de referência para superfícies 3D",
        options=[m["name"] for m in materials],
        index=0,
        key="av1_q1_3d_material",
    )
    material_cfg_3d = next(m for m in materials if m["name"] == selected_material_3d)
    mu_graph = mu0 * float(material_cfg_3d["mu_r"])
    sigma_graph = float(material_cfg_3d["sigma"])

    def _q1_loss(i_a: float, c_mm: float, f_hz: float, ln_factor: float) -> float:
        return _q1_metric_value(
            "loss_w",
            i_a=float(i_a),
            c_mm=float(c_mm),
            f_hz=float(f_hz),
            ln_factor=float(ln_factor),
            mu=mu_graph,
            sigma=sigma_graph,
        )

    show_3d = st.toggle("Gerar gráficos 3D", value=True, key="av1_q1_show_3d")
    if not show_3d:
        st.info("Ative 'Gerar gráficos 3D' para exibir as superfícies da Q1.")
    else:
        current_3d = np.linspace(0.0, max(3000.0, float(im_a) * 1.2), 12)
        thickness_3d = np.linspace(0.1, max(25.0, float(thickness_mm) * 1.5), 12)
        frequency_3d = np.linspace(0.1, max(180.0, float(frequency_hz) * 1.5), 12)

        z_current_thickness = np.zeros((len(thickness_3d), len(current_3d)))
        z_current_frequency = np.zeros((len(frequency_3d), len(current_3d)))
        z_thickness_frequency = np.zeros((len(frequency_3d), len(thickness_3d)))

        for i, c_val in enumerate(thickness_3d):
            for j, i_val in enumerate(current_3d):
                z_current_thickness[i, j] = _q1_loss(i_val, c_val, float(frequency_hz), ln_ba)

        for i, f_val in enumerate(frequency_3d):
            for j, i_val in enumerate(current_3d):
                z_current_frequency[i, j] = _q1_loss(i_val, float(thickness_mm), f_val, ln_ba)

        for i, f_val in enumerate(frequency_3d):
            for j, c_val in enumerate(thickness_3d):
                z_thickness_frequency[i, j] = _q1_loss(float(im_a), c_val, f_val, ln_ba)

        fig_3d_ct = go.Figure(
            data=[
                go.Surface(
                    x=current_3d,
                    y=thickness_3d,
                    z=z_current_thickness,
                    colorscale="Viridis",
                    showscale=True,
                )
            ]
        )
        fig_3d_ct.update_layout(
            title=f"Q1 3D: Perdas por Corrente × Espessura (f = {frequency_hz:.1f} Hz)",
            height=560,
            margin={"l": 0, "r": 0, "t": 50, "b": 0},
            scene={"xaxis_title": "Corrente [A]", "yaxis_title": "Espessura [mm]", "zaxis_title": "Perdas [W]"},
        )
        _plotly_chart_with_csv(fig_3d_ct, "q1_fig_3d_ct", "q1_perdas_3d_corrente_espessura.csv")

        fig_3d_cf = go.Figure(
            data=[
                go.Surface(
                    x=current_3d,
                    y=frequency_3d,
                    z=z_current_frequency,
                    colorscale="Viridis",
                    showscale=True,
                )
            ]
        )
        fig_3d_cf.update_layout(
            title=f"Q1 3D: Perdas por Corrente × Frequência (c = {thickness_mm:.2f} mm)",
            height=560,
            margin={"l": 0, "r": 0, "t": 50, "b": 0},
            scene={"xaxis_title": "Corrente [A]", "yaxis_title": "Frequência [Hz]", "zaxis_title": "Perdas [W]"},
        )
        _plotly_chart_with_csv(fig_3d_cf, "q1_fig_3d_cf", "q1_perdas_3d_corrente_frequencia.csv")

        fig_3d_tf = go.Figure(
            data=[
                go.Surface(
                    x=thickness_3d,
                    y=frequency_3d,
                    z=z_thickness_frequency,
                    colorscale="Viridis",
                    showscale=True,
                )
            ]
        )
        fig_3d_tf.update_layout(
            title=f"Q1 3D: Perdas por Espessura × Frequência (Im = {im_a:.1f} A)",
            height=560,
            margin={"l": 0, "r": 0, "t": 50, "b": 0},
            scene={"xaxis_title": "Espessura [mm]", "yaxis_title": "Frequência [Hz]", "zaxis_title": "Perdas [W]"},
        )
        _plotly_chart_with_csv(fig_3d_tf, "q1_fig_3d_tf", "q1_perdas_3d_espessura_frequencia.csv")

    st.markdown("##### Campo e perdas por região (modelo volumétrico 3D)")
    st.caption(
        "Modelo numérico avançado com integração em espessura por quadratura de Gauss-Legendre "
        "e agregação por regiões no plano da tampa circular."
    )

    col_reg_1, col_reg_2, col_reg_3, col_reg_4 = st.columns(4)
    with col_reg_1:
        selected_material_reg = st.selectbox(
            "Material de referência regional",
            options=[m["name"] for m in materials],
            index=0,
            key="q1_region_material",
        )
    with col_reg_2:
        q1_region_size_mm = st.number_input(
            "Tamanho da região [mm]",
            min_value=5.0,
            value=10.0,
            step=5.0,
            key="q1_region_size_mm",
        )
    with col_reg_3:
        q1_region_mesh_xy = st.slider(
            "Malha XY (n x n)",
            min_value=80,
            max_value=360,
            value=180,
            step=20,
            key="q1_region_mesh_xy",
        )
    with col_reg_4:
        q1_region_quad = st.slider(
            "Ordem da quadratura em z",
            min_value=2,
            max_value=14,
            value=8,
            step=2,
            key="q1_region_quad",
        )

    show_q1_regions = st.toggle("Gerar mapas regionais 3D", value=True, key="q1_show_regions")
    if not show_q1_regions:
        st.info("Ative 'Gerar mapas regionais 3D' para exibir campo e perdas por região na Q1.")
    else:
        material_reg = next(m for m in materials if m["name"] == selected_material_reg)
        mu_reg = mu0 * float(material_reg["mu_r"])
        sigma_reg = float(material_reg["sigma"])

        try:
            region_data = _compute_q1_regional_3d_maps(
                outer_d_mm=float(outer_d_mm),
                inner_d_mm=float(inner_d_mm),
                thickness_mm=float(thickness_mm),
                frequency_hz=float(frequency_hz),
                im_a=float(im_a),
                mu=mu_reg,
                sigma=sigma_reg,
                xy_points=int(q1_region_mesh_xy),
                thickness_quad_order=int(q1_region_quad),
                region_size_mm=float(q1_region_size_mm),
            )

            st.markdown(
                f"**Modelo 3D regional:** δ={region_data['delta_mm']:.4f} mm | "
                f"Perda total integrada={region_data['total_loss_w']:.4f} W | "
                f"Regiões ativas={region_data['active_regions']}"
            )

            outer_r_mm = float(region_data["outer_radius_mm"])
            inner_r_mm = float(region_data["inner_radius_mm"])
            shapes_ring = [
                {
                    "type": "circle",
                    "x0": -outer_r_mm,
                    "x1": outer_r_mm,
                    "y0": -outer_r_mm,
                    "y1": outer_r_mm,
                    "line": {"color": "black", "width": 2},
                    "fillcolor": "rgba(0,0,0,0)",
                },
                {
                    "type": "circle",
                    "x0": -inner_r_mm,
                    "x1": inner_r_mm,
                    "y0": -inner_r_mm,
                    "y1": inner_r_mm,
                    "line": {"color": "white", "width": 1.5},
                    "fillcolor": "rgba(255,255,255,0.15)",
                },
            ]

            fig_q1_field_region = go.Figure(
                data=[
                    go.Heatmap(
                        x=region_data["region_centers_mm"],
                        y=region_data["region_centers_mm"],
                        z=region_data["region_field_h"],
                        colorscale="Viridis",
                        colorbar={"title": "Campo médio [A/m]"},
                        hoverongaps=False,
                    )
                ]
            )
            fig_q1_field_region.add_trace(
                go.Scatter(
                    x=region_data["line_x"],
                    y=region_data["line_y"],
                    mode="lines",
                    line={"color": "rgba(255,255,255,0.70)", "width": 1},
                    name="Linhas de campo",
                    hoverinfo="skip",
                )
            )
            fig_q1_field_region.update_layout(
                title="Q1: Campo por Região (modelo 3D)",
                xaxis_title="X [mm]",
                yaxis_title="Y [mm]",
                height=520,
                shapes=shapes_ring,
                margin={"l": 40, "r": 20, "t": 60, "b": 40},
            )
            fig_q1_field_region.update_xaxes(scaleanchor="y", scaleratio=1)
            _plotly_chart_with_csv(
                fig_q1_field_region,
                "q1_fig_region_field",
                "q1_campo_por_regiao_modelo_3d.csv",
            )

            fig_q1_loss_region = go.Figure(
                data=[
                    go.Heatmap(
                        x=region_data["region_centers_mm"],
                        y=region_data["region_centers_mm"],
                        z=region_data["region_loss_w"],
                        colorscale="YlOrRd",
                        colorbar={"title": "Perda por região [W]"},
                        hoverongaps=False,
                    )
                ]
            )
            fig_q1_loss_region.update_layout(
                title="Q1: Perdas por Região (modelo 3D)",
                xaxis_title="X [mm]",
                yaxis_title="Y [mm]",
                height=520,
                shapes=shapes_ring,
                margin={"l": 40, "r": 20, "t": 60, "b": 40},
            )
            fig_q1_loss_region.update_xaxes(scaleanchor="y", scaleratio=1)
            _plotly_chart_with_csv(
                fig_q1_loss_region,
                "q1_fig_region_loss",
                "q1_perdas_por_regiao_modelo_3d.csv",
            )

            st.markdown("**Perdas por região (Top 15 células)**")
            st.dataframe(region_data["top_loss"][:15], use_container_width=True, hide_index=True)

            st.markdown("**Campo por região (Top 15 células)**")
            st.dataframe(region_data["top_field"][:15], use_container_width=True, hide_index=True)

        except Exception as exc:
            st.error(f"Erro ao gerar mapas regionais 3D da Q1: {str(exc)}")

    st.divider()
    st.markdown("#### 4. Tabela de resultados da Questão 1 (Enunciado)")
    st.caption("Resultados para o caso do enunciado com todos os materiais disponíveis.")

    rows = []
    for material in materials:
        mu = mu0 * material["mu_r"]
        p_analytical = calculate_loss_analytical(
            im=float(im_a),
            thickness_m=float(thickness_mm) * 1e-3,
            frequency_hz=float(frequency_hz),
            mu=float(mu),
            sigma=float(material["sigma"]),
            num_conductors=1,
            ln_ba=ln_ba,
        )
        rows.append(
            {
                "Material": material["name"],
                "μr": material["mu_r"],
                "σ [S/m]": f"{material['sigma']:.2e}",
                "ln(D/d)": f"{ln_ba:.4f}",
                "Perda [W]": f"{float(p_analytical):.4f}",
            }
        )

    st.dataframe(rows, use_container_width=True, hide_index=True)

    st.caption(
        "Constantes do caso enunciado: método analítico com 1 condutor, "
        f"D={outer_d_mm:.1f} mm, d={inner_d_mm:.1f} mm, c={thickness_mm:.2f} mm, "
        f"Im={im_a:.1f} A, f={frequency_hz:.1f} Hz."
    )


def _show_assessment_q2_tab() -> None:
    """Questao 2 da avaliacao: deducao teorica em coordenadas cilindricas (sem calculo numerico)."""
    st.markdown("### Questão 2: Dedução da Equação de Difusão na Tampa Circular")
    st.caption(
        "Escopo desta aba: apenas dedução analítica das partes (a), (b) e (c), "
        "sem cálculo numérico."
    )
    st.info(
        "Referência principal: Del Vecchio, item 15.5 \"Tank Losses Associated with the Bushings\", "
        "página 456."
    )

    tab_a, tab_b, tab_c = st.tabs(
        [
            "Parte (a): Difusão e Hφ",
            "Parte (b): Densidade de corrente Jr",
            "Parte (c): Perdas totais",
        ]
    )

    with tab_a:
        st.markdown("#### Parte (a): Equação de difusão em coordenadas cilíndricas e componente Hφ")
        st.markdown(
            "Adota-se regime senoidal em frequência angular $\\omega$, com meio condutor "
            "linear e isotrópico, e simetria axial na tampa circular."
        )

        st.markdown("**1) Equações de Maxwell no domínio fasorial (aproximação quasi-estática):**")
        st.latex(r"\nabla \times \mathbf{H} = \mathbf{J}")
        st.latex(r"\nabla \times \mathbf{E} = -j\omega\mu\mathbf{H}")
        st.latex(r"\mathbf{J} = \sigma\mathbf{E}")

        st.markdown("**2) Eliminação de E para obter a difusão em H:**")
        st.latex(r"\nabla \times \left(\frac{1}{\sigma}\nabla \times \mathbf{H}\right) = -j\omega\mu\mathbf{H}")
        st.latex(r"\nabla^2\mathbf{H} = j\omega\mu\sigma\,\mathbf{H}")

        st.markdown("**3) Componente azimutal dominante $H_\varphi(r)$ em coordenadas cilíndricas:**")
        st.latex(
            r"\frac{1}{r}\frac{d}{dr}\left(r\frac{dH_\varphi}{dr}\right) - \frac{H_\varphi}{r^2} = j\omega\mu\sigma\,H_\varphi"
        )
        st.latex(
            r"\frac{d^2H_\varphi}{dr^2} + \frac{1}{r}\frac{dH_\varphi}{dr} - \left(\frac{1}{r^2}+k^2\right)H_\varphi = 0"
        )

        st.markdown("com")
        st.latex(r"k^2 = j\omega\mu\sigma, \quad k = \frac{1+j}{\delta}, \quad \delta = \sqrt{\frac{2}{\omega\mu\sigma}}")

        st.markdown("**4) Solução geral (equação de Bessel modificada de ordem 1):**")
        st.latex(r"H_\varphi(r) = C_1 I_1(kr) + C_2 K_1(kr)")

        st.markdown(
            "As constantes $C_1$ e $C_2$ são definidas pelas condições de contorno no anel "
            "da tampa ($a \le r \le b$)."
        )

        st.markdown("**5) Aproximação de pele local (quando $\delta \ll b$):**")
        st.latex(r"H_\varphi(r) \approx H_\varphi(b)\,\exp\!\left[-(1+j)\frac{(b-r)}{\delta}\right]")

    with tab_b:
        st.markdown("#### Parte (b): Dedução da componente radial induzida Jr")
        st.markdown("A partir da lei de Ampère no condutor:")
        st.latex(r"\nabla \times \mathbf{H} = \mathbf{J}")

        st.markdown(
            "Para o modelo axisimétrico local na espessura da tampa (coordenada $z$), "
            "a componente radial pode ser escrita como:"
        )
        st.latex(r"J_r = -\frac{\partial H_\varphi}{\partial z}")

        st.markdown(
            "Com a solução difusiva na espessura do metal:"
        )
        st.latex(r"H_\varphi(r,z) = H_\varphi(r,0)\,e^{-(1+j)z/\delta}")

        st.markdown("segue:")
        st.latex(r"J_r(r,z) = \frac{1+j}{\delta}\,H_\varphi(r,0)\,e^{-(1+j)z/\delta}")
        st.latex(r"J_r(r,z) = \frac{1+j}{\delta}\,H_\varphi(r,z)")

        st.markdown("Magnitude:")
        st.latex(r"|J_r(r,z)| = \frac{\sqrt{2}}{\delta}\,|H_\varphi(r,z)|")

        st.markdown(
            "Também vale a relação constitutiva $J_r = \sigma E_r$, com $E_r$ obtido de Faraday."
        )

    with tab_c:
        st.markdown("#### Parte (c): Dedução das perdas totais por correntes induzidas")
        st.markdown("A densidade de potência dissipada por Joule é:")
        st.latex(r"p = \frac{|J_r|^2}{\sigma}")

        st.markdown(
            "Para a tampa anular ($a \le r \le b$, $0 \le z \le c$, $0 \le \varphi \le 2\pi$), "
            "as perdas totais são:"
        )
        st.latex(
            r"P_{tot} = \int_0^{2\pi}\int_a^b\int_0^c \frac{|J_r(r,z)|^2}{\sigma}\,r\,dz\,dr\,d\varphi"
        )
        st.latex(r"P_{tot} = \frac{2\pi}{\sigma}\int_a^b r\left[\int_0^c |J_r(r,z)|^2dz\right]dr")

        st.markdown("Substituindo $J_r(r,z)=J_r(r,0)e^{-(1+j)z/\delta}$:")
        st.latex(r"|J_r(r,z)|^2 = |J_r(r,0)|^2e^{-2z/\delta}")
        st.latex(r"\int_0^c e^{-2z/\delta}dz = \frac{\delta}{2}\left(1-e^{-2c/\delta}\right)")

        st.markdown("Logo, a expressão deduzida para perdas totais fica:")
        st.latex(
            r"P_{tot} = \frac{\pi\delta}{\sigma}\left(1-e^{-2c/\delta}\right)\int_a^b r\,|J_r(r,0)|^2dr"
        )

        st.markdown("Usando $J_r=(1+j)H_\varphi/\delta$, forma equivalente em $H_\varphi$:")
        st.latex(
            r"P_{tot} = \frac{2\pi}{\sigma\delta^2}\int_a^b\int_0^c r\,|H_\varphi(r,z)|^2\,dz\,dr"
        )

        st.warning(
        
            "Não há parâmetros de entrada nem cálculo numérico nesta aba."
        )


def _show_assessment_q3_tab() -> None:
    """Questao 3 da avaliacao: calculo usando apenas Biot-Savart."""
    st.markdown("### Questão 3: Campo magnético H(x,y) e perdas na tampa com 3 furos")
    st.caption(
        "Enunciado: calcular perdas para 2000 A, 2250 A, 2500 A e 2800 A em 60 Hz, "
        "com aço carbono (sigma=2e7 S/m, mu_r=500). Método: Biot-Savart."
    )

    base_input = get_default_exercise01_input()
    mu0 = 4.0 * np.pi * 1e-7
    q3_material = MaterialInput(mu=mu0 * 500.0, sigma=2.0e7)
    current_cases = [2000.0, 2250.0, 2500.0, 2800.0]

    st.divider()
    st.markdown("#### 1. Parametrizações")
    st.caption(
        "Geometria do enunciado (padrão): placa 590×270×5 mm, três furos de 82 mm. "
        "Você pode editar os parâmetros abaixo."
    )

    # Seção de geometria editável com valores padrão do enunciado
    with st.expander("**Parâmetros de geometria** (padrão do enunciado)", expanded=True):
        col_q3_geo_1, col_q3_geo_2, col_q3_geo_3 = st.columns(3)
        with col_q3_geo_1:
            st.markdown("**Placa (mm)**")
            q3_plate_width = st.number_input(
                "Largura", min_value=10.0, value=590.0, step=10.0, key="q3_plate_width"
            )
            q3_plate_height = st.number_input(
                "Altura", min_value=10.0, value=270.0, step=10.0, key="q3_plate_height"
            )
            q3_plate_thickness = st.number_input(
                "Espessura", min_value=1.0, value=5.0, step=0.5, key="q3_plate_thickness"
            )
        with col_q3_geo_2:
            st.markdown("**Furos (mm)**")
            q3_hole_diameter = st.number_input(
                "Diâmetro dos furos", min_value=5.0, value=82.0, step=5.0, key="q3_hole_diameter"
            )
            st.caption("3 furos em posição simétrica")
        with col_q3_geo_3:
            st.markdown("**Frequência (Hz)**")
            q3_frequency = st.number_input(
                "f", min_value=0.1, value=60.0, step=10.0, key="q3_frequency_enunciado"
            )

    # Criar input editável com os parâmetros fornecidos
    q3_custom_input = base_input.model_copy(
        update={
            "plate": PlateInput(
                width_mm=q3_plate_width,
                height_mm=q3_plate_height,
                thickness_mm=q3_plate_thickness,
            ),
            "frequency_hz": float(q3_frequency),
        }
    )

    # Atualizar furos com diâmetro editado (mantendo posições do enunciado)
    q3_custom_input.holes = [
        HoleInput(x_mm=100.0, y_mm=135.0, diameter_mm=q3_hole_diameter),
        HoleInput(x_mm=295.0, y_mm=135.0, diameter_mm=q3_hole_diameter),
        HoleInput(x_mm=490.0, y_mm=135.0, diameter_mm=q3_hole_diameter),
    ]

    try:
        q3_plate = create_plate_from_input(q3_custom_input.plate, q3_custom_input.holes)
        q3_cond_positions = np.array([[c.x_mm * 1e-3, c.y_mm * 1e-3] for c in q3_custom_input.conductors])
        q3_fig_geo = plot_geometry(q3_plate, q3_cond_positions)
        _plotly_chart_with_csv(q3_fig_geo, "q3_fig_geometry", "q3_geometria_enunciado.csv")
    except Exception as e:
        st.warning(f"Não foi possível gerar a geometria da Q3: {str(e)}")

    st.markdown("**Materiais habilitados**")
    q3_material_options = _get_q3_material_options()
    q3_selected_materials = []
    q3_cols = st.columns(3)
    for idx, material in enumerate(q3_material_options):
        default_enabled = idx < 6
        with q3_cols[idx % 3]:
            enabled = st.checkbox(
                material["name"],
                value=default_enabled,
                key=f"q3_material_enabled_{idx}",
            )
        if enabled:
            q3_selected_materials.append(material)

    if not q3_selected_materials:
        st.warning("Selecione ao menos um material para gerar os gráficos da Q3.")
    else:
        q3_metric_options = {
            "Perda [W]": "loss_w",
            "H máximo [A/m]": "h_max",
            "Densidade máxima de perdas [W/m²]": "loss_density_max",
        }
        q3_metric_label = st.selectbox(
            "Grandeza no eixo Y",
            options=list(q3_metric_options.keys()),
            index=0,
            key="q3_metric_y",
        )
        q3_metric_key = q3_metric_options[q3_metric_label]

        col_q3_1, col_q3_2, col_q3_3 = st.columns(3)
        with col_q3_1:
            q3_freq_min = st.number_input("f mín [Hz]", min_value=0.1, value=10.0, key="q3_freq_min")
            q3_freq_max = st.number_input("f máx [Hz]", min_value=1.0, value=5000.0, key="q3_freq_max")
        with col_q3_2:
            q3_i_min = st.number_input("Im mín [A]", min_value=0.1, value=500.0, key="q3_i_min")
            q3_i_max = st.number_input("Im máx [A]", min_value=1.0, value=3000.0, key="q3_i_max")
        with col_q3_3:
            q3_n_points = int(
                st.slider("Pontos por curva", min_value=8, max_value=40, value=16, key="q3_n_points")
            )

        col_q3_ref_1, col_q3_ref_2, col_q3_ref_3 = st.columns(3)
        with col_q3_ref_1:
            q3_ref_freq = st.number_input("f de referência [Hz]", min_value=0.1, value=60.0, key="q3_ref_freq")
        with col_q3_ref_2:
            q3_ref_i = st.number_input("Im de referência [A]", min_value=0.1, value=2800.0, key="q3_ref_i")
        with col_q3_ref_3:
            q3_log_x = st.toggle("Escala log no eixo X", value=True, key="q3_log_x")

        if q3_freq_max <= q3_freq_min:
            st.warning("Ajuste a faixa de frequência: f máx deve ser maior que f mín.")
        elif q3_i_max <= q3_i_min:
            st.warning("Ajuste a faixa de corrente: Im máx deve ser maior que Im mín.")
        else:
            if q3_log_x:
                q3_x_freq = _limit_sweep_points(
                    np.geomspace(q3_freq_min, q3_freq_max, q3_n_points), max_points=q3_n_points
                )
                q3_x_current = _limit_sweep_points(
                    np.geomspace(q3_i_min, q3_i_max, q3_n_points), max_points=q3_n_points
                )
            else:
                q3_x_freq = _limit_sweep_points(
                    np.linspace(q3_freq_min, q3_freq_max, q3_n_points), max_points=q3_n_points
                )
                q3_x_current = _limit_sweep_points(
                    np.linspace(q3_i_min, q3_i_max, q3_n_points), max_points=q3_n_points
                )

            q3_fig_freq = go.Figure()
            q3_fig_current = go.Figure()

            for material in q3_selected_materials:
                q3_mu = mu0 * float(material["mu_r"])
                q3_sigma = float(material["sigma"])

                y_freq = []
                for f_hz in q3_x_freq:
                    q3_input_f = q3_custom_input.model_copy(
                        update={
                            "frequency_hz": float(f_hz),
                            "material": MaterialInput(mu=q3_mu, sigma=q3_sigma),
                            "conductors": _apply_im_to_conductors(q3_custom_input.conductors, float(q3_ref_i)),
                            "mesh": MeshInput(nx=80, ny=80),
                        }
                    )
                    q3_res_f = simulate_exercise_03_biot_only(q3_input_f)
                    y_freq.append(_extract_q3_metric_value(q3_res_f, q3_metric_key))

                y_current = []
                for i_a in q3_x_current:
                    q3_input_i = q3_custom_input.model_copy(
                        update={
                            "frequency_hz": float(q3_ref_freq),
                            "material": MaterialInput(mu=q3_mu, sigma=q3_sigma),
                            "conductors": _apply_im_to_conductors(q3_custom_input.conductors, float(i_a)),
                            "mesh": MeshInput(nx=80, ny=80),
                        }
                    )
                    q3_res_i = simulate_exercise_03_biot_only(q3_input_i)
                    y_current.append(_extract_q3_metric_value(q3_res_i, q3_metric_key))

                q3_fig_freq.add_trace(
                    go.Scatter(x=q3_x_freq, y=y_freq, mode="lines", name=material["name"])
                )
                q3_fig_current.add_trace(
                    go.Scatter(x=q3_x_current, y=y_current, mode="lines", name=material["name"])
                )

            q3_fig_freq.update_layout(
                title=f"Q3: {q3_metric_label} vs Frequência",
                xaxis_title="Frequência [Hz]",
                yaxis_title=q3_metric_label,
                hovermode="x unified",
                height=430,
            )
            q3_fig_current.update_layout(
                title=f"Q3: {q3_metric_label} vs Corrente Im",
                xaxis_title="Corrente Im [A]",
                yaxis_title=q3_metric_label,
                hovermode="x unified",
                height=430,
            )
            if q3_log_x:
                q3_fig_freq.update_xaxes(type="log")
                q3_fig_current.update_xaxes(type="log")

            _plotly_chart_with_csv(q3_fig_freq, "q3_fig_freq", "q3_varredura_frequencia.csv")
            _plotly_chart_with_csv(q3_fig_current, "q3_fig_current", "q3_varredura_corrente.csv")

            q3_x_sigma = [float(m["sigma"]) for m in q3_selected_materials]
            q3_x_mu = [float(m["mu_r"]) for m in q3_selected_materials]
            q3_y_material = []
            for material in q3_selected_materials:
                q3_mu = mu0 * float(material["mu_r"])
                q3_sigma = float(material["sigma"])
                q3_input_mat = q3_custom_input.model_copy(
                    update={
                        "frequency_hz": float(q3_ref_freq),
                        "material": MaterialInput(mu=q3_mu, sigma=q3_sigma),
                        "conductors": _apply_im_to_conductors(q3_custom_input.conductors, float(q3_ref_i)),
                        "mesh": MeshInput(nx=80, ny=80),
                    }
                )
                q3_res_mat = simulate_exercise_03_biot_only(q3_input_mat)
                q3_y_material.append(_extract_q3_metric_value(q3_res_mat, q3_metric_key))

    st.divider()
    st.markdown("#### 3. Gráficos 3D - Superfícies Biot-Savart")
    st.caption(
        "Superfícies numéricas calculadas com o método Biot-Savart, variando duas grandezas de entrada "
        "para obter a perda total na tampa com 3 furos."
    )

    q3_3d_material = st.selectbox(
        "Material de referência para as superfícies 3D",
        options=[m["name"] for m in q3_material_options],
        index=0,
        key="q3_3d_material",
    )
    q3_3d_material_cfg = next(m for m in q3_material_options if m["name"] == q3_3d_material)
    q3_3d_mu = mu0 * float(q3_3d_material_cfg["mu_r"])
    q3_3d_sigma = float(q3_3d_material_cfg["sigma"])

    col_3d_1, col_3d_2, col_3d_3 = st.columns(3)
    with col_3d_1:
        q3_3d_current_max = st.number_input(
            "Im máx para 3D [A]",
            min_value=100.0,
            value=3000.0,
            step=100.0,
            key="q3_3d_current_max",
        )
    with col_3d_2:
        q3_3d_freq_max = st.number_input(
            "f máx para 3D [Hz]",
            min_value=1.0,
            value=max(500.0, float(q3_frequency) * 1.5),
            step=50.0,
            key="q3_3d_freq_max",
        )
    with col_3d_3:
        q3_3d_hole_max = st.number_input(
            "Diâmetro máx dos furos para 3D [mm]",
            min_value=10.0,
            value=max(100.0, float(q3_hole_diameter) * 1.5),
            step=5.0,
            key="q3_3d_hole_max",
        )

    q3_show_3d = st.toggle("Gerar superfícies 3D da Q3", value=False, key="q3_show_3d")
    if not q3_show_3d:
        st.info("Ative 'Gerar superfícies 3D da Q3' para visualizar as superfícies Biot-Savart.")
    else:
        q3_current_3d = np.linspace(0.0, float(q3_3d_current_max), 5)
        q3_freq_3d = np.linspace(0.1, float(q3_3d_freq_max), 5)
        q3_hole_3d = np.linspace(float(q3_hole_diameter), float(q3_3d_hole_max), 5)

        q3_surface_current_freq = np.zeros((len(q3_freq_3d), len(q3_current_3d)))
        q3_surface_current_hole = np.zeros((len(q3_hole_3d), len(q3_current_3d)))

        for i, freq_val in enumerate(q3_freq_3d):
            for j, current_val in enumerate(q3_current_3d):
                q3_input_sf = q3_custom_input.model_copy(
                    update={
                        "frequency_hz": float(freq_val),
                        "material": MaterialInput(mu=q3_3d_mu, sigma=q3_3d_sigma),
                        "conductors": _apply_im_to_conductors(q3_custom_input.conductors, float(current_val)),
                        "mesh": MeshInput(nx=80, ny=80),
                    }
                )
                q3_res_sf = simulate_exercise_03_biot_only(q3_input_sf)
                q3_surface_current_freq[i, j] = float(q3_res_sf["total_loss_biot_w"])

        for i, hole_val in enumerate(q3_hole_3d):
            for j, current_val in enumerate(q3_current_3d):
                q3_input_sh = q3_custom_input.model_copy(
                    update={
                        "frequency_hz": float(q3_frequency),
                        "material": MaterialInput(mu=q3_3d_mu, sigma=q3_3d_sigma),
                        "conductors": _apply_im_to_conductors(q3_custom_input.conductors, float(current_val)),
                        "holes": [
                            HoleInput(x_mm=100.0, y_mm=135.0, diameter_mm=float(hole_val)),
                            HoleInput(x_mm=295.0, y_mm=135.0, diameter_mm=float(hole_val)),
                            HoleInput(x_mm=490.0, y_mm=135.0, diameter_mm=float(hole_val)),
                        ],
                        "mesh": MeshInput(nx=80, ny=80),
                    }
                )
                q3_res_sh = simulate_exercise_03_biot_only(q3_input_sh)
                q3_surface_current_hole[i, j] = float(q3_res_sh["total_loss_biot_w"])

        fig_q3_3d_cf = go.Figure(
            data=[
                go.Surface(
                    x=q3_current_3d,
                    y=q3_freq_3d,
                    z=q3_surface_current_freq,
                    colorscale="Viridis",
                    showscale=True,
                )
            ]
        )
        fig_q3_3d_cf.update_layout(
            title="Q3 3D: Perdas por Corrente × Frequência (Biot-Savart)",
            height=560,
            margin={"l": 0, "r": 0, "t": 50, "b": 0},
            scene={
                "xaxis_title": "Corrente Im [A]",
                "yaxis_title": "Frequência [Hz]",
                "zaxis_title": "Perdas [W]",
            },
        )
        _plotly_chart_with_csv(fig_q3_3d_cf, "q3_fig_3d_cf", "q3_perdas_3d_corrente_frequencia.csv")

        fig_q3_3d_ch = go.Figure(
            data=[
                go.Surface(
                    x=q3_current_3d,
                    y=q3_hole_3d,
                    z=q3_surface_current_hole,
                    colorscale="Viridis",
                    showscale=True,
                )
            ]
        )
        fig_q3_3d_ch.update_layout(
            title="Q3 3D: Perdas por Corrente × Diâmetro dos Furos (Biot-Savart)",
            height=560,
            margin={"l": 0, "r": 0, "t": 50, "b": 0},
            scene={
                "xaxis_title": "Corrente Im [A]",
                "yaxis_title": "Diâmetro dos furos [mm]",
                "zaxis_title": "Perdas [W]",
            },
        )
        _plotly_chart_with_csv(fig_q3_3d_ch, "q3_fig_3d_ch", "q3_perdas_3d_corrente_furo.csv")

    st.divider()
    st.markdown("#### 4. Heatmaps 2D Sobre a Tampa")
    st.caption(
        "Mapas regionais computacionais (1 cm x 1 cm) sobre a tampa, "
        "respeitando a resolução de malha e a máscara geométrica dos furos."
    )

    col_hm_1, col_hm_2, col_hm_3 = st.columns(3)
    with col_hm_1:
        selected_material_hm = st.selectbox(
            "Material de referência",
            options=[m["name"] for m in q3_material_options],
            index=0,
            key="q3_hm_material",
        )
    with col_hm_2:
        q3_hm_current = st.number_input(
            "Corrente Im do heatmap [A]",
            min_value=10.0,
            value=2250.0,
            step=100.0,
            key="q3_hm_current",
        )
    with col_hm_3:
        q3_hm_mesh_res = st.slider(
            "Resolução da malha",
            min_value=60,
            max_value=320,
            value=160,
            step=10,
            key="q3_hm_mesh_res",
        )

    show_heatmaps = st.toggle("Gerar heatmaps 2D", value=True, key="q3_show_heatmaps")
    if not show_heatmaps:
        st.info("Ative 'Gerar heatmaps 2D' para exibir os mapas sobre a tampa.")
    else:
        material_hm_cfg = next(m for m in q3_material_options if m["name"] == selected_material_hm)
        mu_hm = mu0 * float(material_hm_cfg["mu_r"])
        sigma_hm = float(material_hm_cfg["sigma"])

        q3_input_hm = q3_custom_input.model_copy(
            update={
                "frequency_hz": float(q3_frequency),
                "material": MaterialInput(mu=mu_hm, sigma=sigma_hm),
                "conductors": _apply_im_to_conductors(q3_custom_input.conductors, float(q3_hm_current)),
                "mesh": MeshInput(nx=int(q3_hm_mesh_res), ny=int(q3_hm_mesh_res)),
            }
        )

        try:
            from app.core.geometry.mesh import create_uniform_mesh
            from app.core.electromagnetics.losses import get_loss_density

            plate_hm = create_plate_from_input(q3_input_hm.plate, q3_input_hm.holes)
            mesh_hm = create_uniform_mesh(
                plate_hm.width_m, plate_hm.height_m, int(q3_hm_mesh_res), int(q3_hm_mesh_res)
            )

            x_mesh, y_mesh = mesh_hm.get_mesh_arrays()
            dx_m, dy_m = mesh_hm.get_dx_dy()
            conductor_pos_hm = np.array(
                [[c.x_mm * 1e-3, c.y_mm * 1e-3] for c in q3_input_hm.conductors]
            )
            conductor_cur_hm = np.array([c.current_a for c in q3_input_hm.conductors])

            # Campo vetorial computacional ponto a ponto na malha (Biot-Savart).
            hx = np.zeros_like(x_mesh, dtype=float)
            hy = np.zeros_like(y_mesh, dtype=float)
            for pos, current in zip(conductor_pos_hm, conductor_cur_hm):
                dx = x_mesh - pos[0]
                dy = y_mesh - pos[1]
                r2 = np.maximum(dx**2 + dy**2, 1e-24)
                coef = float(current) / (2.0 * np.pi * r2)
                hx += -coef * dy
                hy += coef * dx

            h_field = np.sqrt(hx**2 + hy**2)

            valid_mask = plate_hm.is_valid_point(x_mesh, y_mesh)
            loss_density = get_loss_density(h_field, q3_input_hm.frequency_hz, mu_hm, sigma_hm)

            # Define NaN fora da tampa para deixar apenas a geometria válida visível.
            h_map = np.where(valid_mask, h_field, np.nan)
            loss_map = np.where(valid_mask, loss_density, np.nan)
            h_map = np.where(np.isfinite(h_map), h_map, np.nan)
            loss_map = np.where(np.isfinite(loss_map), loss_map, np.nan)

            x_mm = (x_mesh[0, :] if x_mesh.ndim == 2 else x_mesh) * 1000.0
            y_mm = (y_mesh[:, 0] if y_mesh.ndim == 2 else y_mesh) * 1000.0

            def _overlay_shapes() -> list[dict]:
                shapes = [
                    {
                        "type": "rect",
                        "x0": 0.0,
                        "y0": 0.0,
                        "x1": float(q3_plate_width),
                        "y1": float(q3_plate_height),
                        "line": {"color": "black", "width": 2},
                        "fillcolor": "rgba(0,0,0,0)",
                    }
                ]
                for hole in q3_custom_input.holes:
                    r = float(hole.diameter_mm) / 2.0
                    x0 = float(hole.x_mm) - r
                    x1 = float(hole.x_mm) + r
                    y0 = float(hole.y_mm) - r
                    y1 = float(hole.y_mm) + r
                    shapes.append(
                        {
                            "type": "circle",
                            "x0": x0,
                            "x1": x1,
                            "y0": y0,
                            "y1": y1,
                            "line": {"color": "white", "width": 1.5},
                            "fillcolor": "rgba(255,255,255,0.15)",
                        }
                    )
                return shapes

            conductor_x_mm = [float(c.x_mm) for c in q3_input_hm.conductors]
            conductor_y_mm = [float(c.y_mm) for c in q3_input_hm.conductors]

            # Linhas de campo a partir da direção do vetor H em pontos subamostrados.
            stride = max(1, int(q3_hm_mesh_res // 32))
            x_sub = x_mesh[::stride, ::stride]
            y_sub = y_mesh[::stride, ::stride]
            hx_sub = hx[::stride, ::stride]
            hy_sub = hy[::stride, ::stride]
            mask_sub = valid_mask[::stride, ::stride]

            norm_sub = np.sqrt(hx_sub**2 + hy_sub**2)
            norm_sub = np.where(norm_sub > 1e-12, norm_sub, 1.0)
            ux = hx_sub / norm_sub
            uy = hy_sub / norm_sub

            line_len_mm = 6.0
            line_x = []
            line_y = []
            for i in range(x_sub.shape[0]):
                for j in range(x_sub.shape[1]):
                    if not bool(mask_sub[i, j]):
                        continue
                    x0 = float(x_sub[i, j] * 1000.0)
                    y0 = float(y_sub[i, j] * 1000.0)
                    x1 = x0 + float(ux[i, j] * line_len_mm)
                    y1 = y0 + float(uy[i, j] * line_len_mm)
                    line_x.extend([x0, x1, None])
                    line_y.extend([y0, y1, None])

            # Agregação por região de 1 cm x 1 cm (perda integrada em W por célula).
            cell_size_mm = 10.0
            n_x_cm = max(1, int(np.ceil(float(q3_plate_width) / cell_size_mm)))
            n_y_cm = max(1, int(np.ceil(float(q3_plate_height) / cell_size_mm)))

            x_mm_full = x_mesh * 1000.0
            y_mm_full = y_mesh * 1000.0
            ix = np.clip((x_mm_full / cell_size_mm).astype(int), 0, n_x_cm - 1)
            iy = np.clip((y_mm_full / cell_size_mm).astype(int), 0, n_y_cm - 1)

            valid_loss = valid_mask & np.isfinite(loss_density)
            flat_idx = (iy * n_x_cm + ix).ravel()
            flat_valid = valid_loss.ravel()

            weights_w = (loss_density * dx_m * dy_m).ravel()
            region_sum_w = np.bincount(
                flat_idx[flat_valid],
                weights=weights_w[flat_valid],
                minlength=n_x_cm * n_y_cm,
            ).reshape(n_y_cm, n_x_cm)
            region_count = np.bincount(
                flat_idx[flat_valid],
                minlength=n_x_cm * n_y_cm,
            ).reshape(n_y_cm, n_x_cm)

            valid_field = valid_mask & np.isfinite(h_field)
            flat_valid_field = valid_field.ravel()
            region_sum_h = np.bincount(
                flat_idx[flat_valid_field],
                weights=h_field.ravel()[flat_valid_field],
                minlength=n_x_cm * n_y_cm,
            ).reshape(n_y_cm, n_x_cm)
            region_count_h = np.bincount(
                flat_idx[flat_valid_field],
                minlength=n_x_cm * n_y_cm,
            ).reshape(n_y_cm, n_x_cm)

            region_map_w = np.where(region_count > 0, region_sum_w, np.nan)
            region_map_h = np.where(region_count_h > 0, region_sum_h / np.maximum(region_count_h, 1), np.nan)
            x_cm_centers = np.arange(n_x_cm, dtype=float) * cell_size_mm + cell_size_mm / 2.0
            y_cm_centers = np.arange(n_y_cm, dtype=float) * cell_size_mm + cell_size_mm / 2.0

            fig_region_field = go.Figure(
                data=[
                    go.Heatmap(
                        x=x_cm_centers,
                        y=y_cm_centers,
                        z=region_map_h,
                        colorscale="Viridis",
                        colorbar={"title": "Campo médio [A/m]"},
                        hoverongaps=False,
                    )
                ]
            )
            fig_region_field.add_trace(
                go.Scatter(
                    x=line_x,
                    y=line_y,
                    mode="lines",
                    line={"color": "rgba(255,255,255,0.70)", "width": 1},
                    name="Linhas de campo",
                    hoverinfo="skip",
                )
            )
            fig_region_field.add_trace(
                go.Scatter(
                    x=conductor_x_mm,
                    y=conductor_y_mm,
                    mode="markers",
                    marker={"size": 9, "color": "red", "symbol": "x"},
                    name="Condutores",
                )
            )
            fig_region_field.update_layout(
                title="Q3: Campo por Região (1 cm x 1 cm) com Linhas de Campo",
                xaxis_title="X [mm]",
                yaxis_title="Y [mm]",
                height=520,
                shapes=_overlay_shapes(),
                margin={"l": 40, "r": 20, "t": 60, "b": 40},
            )
            fig_region_field.update_xaxes(scaleanchor="y", scaleratio=1)
            _plotly_chart_with_csv(fig_region_field, "q3_fig_region_field", "q3_campo_por_regiao_cm2.csv")

            fig_region_loss = go.Figure(
                data=[
                    go.Heatmap(
                        x=x_cm_centers,
                        y=y_cm_centers,
                        z=region_map_w,
                        colorscale="YlOrRd",
                        colorbar={"title": "Perda por região [W]"},
                        hoverongaps=False,
                    )
                ]
            )
            fig_region_loss.update_layout(
                title="Q3: Perdas por Região (1 cm x 1 cm)",
                xaxis_title="X [mm]",
                yaxis_title="Y [mm]",
                height=520,
                shapes=_overlay_shapes(),
                margin={"l": 40, "r": 20, "t": 60, "b": 40},
            )
            fig_region_loss.update_xaxes(scaleanchor="y", scaleratio=1)
            _plotly_chart_with_csv(fig_region_loss, "q3_fig_region_loss", "q3_perdas_por_regiao_cm2.csv")

            top_regions = []
            for iy_idx in range(n_y_cm):
                for ix_idx in range(n_x_cm):
                    value_w = region_map_w[iy_idx, ix_idx]
                    if np.isnan(value_w):
                        continue
                    top_regions.append(
                        {
                            "Região": f"X[{ix_idx*10:.0f},{(ix_idx+1)*10:.0f}] mm | Y[{iy_idx*10:.0f},{(iy_idx+1)*10:.0f}] mm",
                            "Perda integrada [W]": float(value_w),
                        }
                    )

            top_regions = sorted(top_regions, key=lambda r: r["Perda integrada [W]"], reverse=True)
            st.markdown("**Perdas por região (Top 15 células de 1 cm²)**")
            st.dataframe(top_regions[:15], use_container_width=True, hide_index=True)

            top_field_regions = []
            for iy_idx in range(n_y_cm):
                for ix_idx in range(n_x_cm):
                    value_h = region_map_h[iy_idx, ix_idx]
                    if np.isnan(value_h):
                        continue
                    top_field_regions.append(
                        {
                            "Região": f"X[{ix_idx*10:.0f},{(ix_idx+1)*10:.0f}] mm | Y[{iy_idx*10:.0f},{(iy_idx+1)*10:.0f}] mm",
                            "Campo médio [A/m]": float(value_h),
                        }
                    )

            top_field_regions = sorted(top_field_regions, key=lambda r: r["Campo médio [A/m]"], reverse=True)
            st.markdown("**Campo por região (Top 15 células de 1 cm²)**")
            st.dataframe(top_field_regions[:15], use_container_width=True, hide_index=True)

        except Exception as e:
            st.error(f"Erro ao gerar heatmaps da Q3: {str(e)}")

    st.divider()
    st.markdown("#### 5. Tabela de resultados da Questão 3 (Enunciado)")
    st.caption("Resultados para os casos do enunciado: 2000 A, 2250 A, 2500 A e 2800 A em 60 Hz com aço carbono.")

    # Tabela de resultados - sempre visível (sem botão)
    q3_rows = []
    for current in current_cases:
        case_input = base_input.model_copy(
            update={
                "frequency_hz": 60.0,
                "material": q3_material,
                "conductors": _apply_im_to_conductors(base_input.conductors, float(current)),
                "mesh": MeshInput(nx=200, ny=200),
            }
        )
        case_result = simulate_exercise_03_biot_only(case_input)
        q3_rows.append(
            {
                "Corrente por condutor [A]": int(current),
                "Perda [W]": round(case_result["total_loss_biot_w"], 5),
                "H máximo [A/m]": round(case_result["max_h_field"], 5),
            }
        )

    st.dataframe(q3_rows, use_container_width=True, hide_index=True)


def _show_assessment_q4_tab() -> None:
    """Questao 4 da avaliacao: condutores retangulares de cobre."""
    st.markdown("### Questão 4: Condutores Retangulares de Cobre")
    st.caption(
        "Enunciado: (a) Deduzir equações de campo H_z, densidade de corrente J_x "
        "e perdas para três variantes de geometria; "
        "(b) Calcular densidade superficial de perdas [W/m²]"
    )
    st.info(
        "Referências: Del Vecchio (2010) Seção 15.3.2.1, pág 426 | "
        "Kulkarni & Khaparde (2013) Seção 4.5.1, pág 150"
    )

    # Abas para as partes (a) derivação e (b) cálculo
    tab_derivation, tab_calculation, tab_figures = st.tabs(
        ["Parte (a): Deduções", "Parte (b): Cálculo Numérico", "Figura 3: Geometrias"]
    )

    with tab_derivation:
        st.markdown("#### Parte (a): Deduções das Equações")
        
        st.markdown("**Três Variantes de Condutores Retangulares**")
        
        col_a1, col_a2, col_a3 = st.columns(3)
        
        with col_a1:
            st.subheader("Variante (a)")
            st.latex(r"\text{Campo em ambas as superfícies}")
            st.latex(r"H_z(x) = H_0 \cosh\left(\frac{x}{\delta}\right)")
            st.latex(
                r"P_a = \frac{H_0^2}{\sigma\delta} \tanh\left(\frac{b}{\delta}\right)"
            )
            st.caption("Aplicação: Condutor imerso em campo uniforme")
        
        with col_a2:
            st.subheader("Variante (b)")
            st.latex(r"\text{Campo em uma superfície (semi-espaço)}")
            st.latex(r"H_z(y) = H_0 \exp\left(-\frac{y}{\delta}\right)")
            st.latex(r"P_b = \frac{H_0^2}{\sigma\delta}")
            st.caption("Aplicação: Condutor em placa laminar")
        
        with col_a3:
            st.subheader("Variante (c)")
            st.latex(r"\text{Espaço finito (sanduíche)}")
            st.latex(
                r"H_z(x) = H_0 \frac{\sinh\left(\frac{b-x}{\delta}\right)}{\sinh\left(\frac{b}{\delta}\right)}"
            )
            st.latex(
                r"P_c = \frac{H_0^2}{\sigma\delta} \coth\left(\frac{b}{\delta}\right)"
            )
            st.caption("Aplicação: Sanduíche com confinamento")
        
        st.divider()
        st.markdown("**Equação de Difusão (Maxwell)**")
        st.latex(
            r"\nabla^2 H_z - \frac{\omega\mu\sigma}{2}(1-j) H_z = 0"
        )
        st.latex(
            r"\text{Profundidade de penetração: } \delta = \sqrt{\frac{2}{\omega\mu\sigma}}"
        )

    with tab_calculation:
        st.markdown("#### Parte (b): Cálculo da Densidade Superficial de Perdas")
        
        col_b1, col_b2, col_b3 = st.columns(3)
        
        with col_b1:
            st.markdown("**Geometria**")
            half_width_b_cm = st.number_input(
                "Meia-largura b [cm]", min_value=0.1, value=2.5, key="q4_b"
            )
            full_width = 2 * half_width_b_cm
            st.metric("Largura total 2b", f"{full_width:.2f} cm")
        
        with col_b2:
            st.markdown("**Material: Cobre**")
            conductivity = st.number_input(
                "Condutividade σ [S/m]", 
                min_value=1e6, 
                value=5.8e7,
                format="%.2e",
                key="q4_sigma"
            )
        
        with col_b3:
            st.markdown("**Operação**")
            frequency = st.number_input(
                "Frequência [Hz]", min_value=1.0, value=60.0, key="q4_freq"
            )
            h0_field = st.number_input(
                "Campo H₀ [A/m]", min_value=0.1, value=6.0, key="q4_h0"
            )
        
        if st.button("Calcular Questão 4", type="primary", key="q4_calc"):
            try:
                # Calcular usando módulo Q4
                result = solve_question_04_rectangular_conductors(
                    half_width_b_cm=float(half_width_b_cm),
                    surface_magnetic_field_h0_a_per_m=float(h0_field),
                    conductivity_s_per_m=float(conductivity),
                    frequency_hz=float(frequency),
                    permeability_rel=1.0,
                )
                
                st.divider()
                st.markdown("### Resultados")
                
                # Parâmetros derivados
                col_r1, col_r2, col_r3, col_r4 = st.columns(4)
                with col_r1:
                    st.metric(
                        "Profundidade δ",
                        f"{result.skin_depth_mm:.4f}",
                        "mm"
                    )
                with col_r2:
                    st.metric(
                        "Frequência angular ω",
                        f"{result.omega_rad_s:.2f}",
                        "rad/s"
                    )
                with col_r3:
                    st.metric(
                        "Razão b/δ",
                        f"{result.skin_depth_ratio_b_over_delta:.4f}",
                        ""
                    )
                with col_r4:
                    st.metric(
                        "Fator tanh(b/δ)",
                        f"{result.variant_a_hyperbolic_factor:.6f}",
                        ""
                    )
                
                st.divider()
                
                # Tabela comparativa de perdas
                st.markdown("**Densidade Superficial de Perdas [W/m²]**")
                
                table_data = {
                    "Variante": ["(a) Campo em ambas", "(b) Campo em uma", "(c) Espaço finito"],
                    "Fórmula": [
                        "H₀²/(σδ) · tanh(b/δ)",
                        "H₀²/(σδ)",
                        "H₀²/(σδ) · coth(b/δ)"
                    ],
                    "Perdas [W/m²]": [
                        f"{result.variant_a_power_loss_w_per_m2:.6e}",
                        f"{result.variant_b_power_loss_w_per_m2:.6e}",
                        f"{result.variant_c_power_loss_w_per_m2:.6e}"
                    ],
                    "Relativo a (b)": [
                        f"{result.power_loss_ratio_a_to_b:.6f}",
                        "1.0000",
                        f"{result.power_loss_ratio_c_to_b:.6f}"
                    ]
                }
                
                st.dataframe(table_data, use_container_width=True, hide_index=True)
                
                st.divider()
                
                # Densidade de corrente máxima
                st.markdown("**Densidade de Corrente Induzida Máxima [A/m²]**")
                
                col_j1, col_j2, col_j3 = st.columns(3)
                with col_j1:
                    st.metric("J_max (a)", f"{result.max_current_density_var_a_a_per_m2:.4e}", "A/m²")
                with col_j2:
                    st.metric("J_max (b)", f"{result.max_current_density_var_b_a_per_m2:.4e}", "A/m²")
                with col_j3:
                    st.metric("J_max (c)", f"{result.max_current_density_var_c_a_per_m2:.4e}", "A/m²")
                
                st.divider()
                
                # Notas
                st.markdown("**Notas Físicas**")
                for note in result.notes:
                    st.caption(f"• {note}")
                
            except Exception as e:
                st.error(f"Erro no cálculo: {str(e)}")

    with tab_figures:
        st.markdown("#### Figura 3: Geometrias das Três Variantes")
        st.info("Visualizações das geometrias e perfis de campo magnético para cada variante.")
        
        try:
            # Gerar figuras
            fig_geometry = create_q4_geometry_figure()
            fig_table, calc_results = create_q4_power_loss_comparison()
            
            # Exibir
            _plotly_chart_with_csv(fig_geometry, "q4_fig_geometry", "q4_geometrias.csv")
            _plotly_chart_with_csv(fig_table, "q4_fig_table", "q4_comparacao_perdas.csv")
            
        except Exception as e:
            st.warning(f"Não foi possível gerar as figuras: {str(e)}")


def show_assessment_01_page() -> None:
    """Pagina agregadora da Avaliacao 1 com estrutura por questao."""
    st.markdown("## Avaliação 1")
    st.write(
        "Esta página organiza a avaliação por questão. Nesta primeira versão, "
        "as Questões 1 e 3 estão alinhadas aos métodos já implementados, com espaço "
        "preparado para evolução das demais questões."
    )

    tab_q1, tab_q2, tab_q3, tab_q4, tab_q5 = st.tabs(
        ["Questão 1", "Questão 2", "Questão 3", "Questão 4", "Questão 5"]
    )

    with tab_q1:
        _show_assessment_q1_tab()

    with tab_q2:
        _show_assessment_q2_tab()

    with tab_q3:
        _show_assessment_q3_tab()

    with tab_q4:
        _show_assessment_q4_tab()

    with tab_q5:
        _show_assessment_q5_tab()


def _show_assessment_q5_tab() -> None:
    """Questao 5: Comparacao de metodos analiticos (Kaymak et al. 2016)."""
    st.markdown("### Questão 5: Comparação de Métodos Analíticos para AC Resistance")
    st.caption(
        "Enunciado: Implementar equações de perdas em condutores circulares, retangulares "
        "e tipo folha a partir do artigo de referência."
    )
    st.info(
        "**Referência Principal**: Kaymak, M., Shen, Z., & De Doncker, R. W. (2016). "
        "\"Comparison of Analytical Methods for Calculating the AC Resistance and Leakage "
        "Inductance of Medium-Frequency Transformers\". "
        "IEEE Transactions on Industry Applications, 52(5), 3963–3972."
    )
    
    # Abas para teoria e cálculo
    tab_theory, tab_calculation, tab_comparison = st.tabs(
        ["Teoria & Métodos", "Cálculo Comparativo", "Resultados"]
    )
    
    with tab_theory:
        st.markdown("#### Referências do Artigo Kaymak et al. 2016")
        
        st.markdown("**Profundidade de Penetração (Skin Depth)**")
        st.markdown("Equação (1), página 2:")
        st.latex(r"\delta = \sqrt{\frac{1}{\pi\mu\sigma f}}")
        
        st.markdown("**Fator de Resistência AC**")
        st.markdown("Equação (2), página 2:")
        st.latex(r"F_r = \frac{R_{ac}}{R_{dc}} = \frac{R_{ac}}{l_{MLT} \cdot m}{h_w \cdot d_w \cdot \sigma}")
        
        st.divider()
        st.markdown("#### Seis Métodos Analíticos Comparados (Kaymak et al., Seção II)")
        
        col_m1, col_m2, col_m3 = st.columns(3)
        
        with col_m1:
            st.subheader("Dowell 1")
            st.markdown("Equações 5-6, página 2")
            st.latex(r"F_{r,n} = \triangle'[\phi'_1 + \frac{2}{3}(m^2-1)\phi'_2]")
            st.caption("Clássico, não contabiliza isolamento")
        
        with col_m2:
            st.subheader("Dowell 2")
            st.markdown("Equações 8-9, página 2")
            st.latex(r"F_{r,n} = \triangle''[\phi''_1 + \frac{2}{3}(m^2-1)\phi''_2]")
            st.caption("Melhor acurácia com η (porosidade)")
        
        with col_m3:
            st.subheader("Ferreira 1")
            st.markdown("Equação 10, página 2")
            st.latex(r"F_{r,n} = \triangle''[\phi''_1 + \eta^2\frac{2}{3}(m^2-1)\phi''_2]")
            st.caption("Competitivo para cilíndricos")
        
        col_m4, col_m5, col_m6 = st.columns(3)
        
        with col_m4:
            st.subheader("Ferreira 2")
            st.markdown("Equações 11-14, página 3")
            st.latex(r"F_{r,n} = \frac{\gamma^2}{2}[\tau_1 - \frac{2\pi}{3}4(m^2-1)\tau_2]")
            st.caption("Exato: funções de Kelvin")
        
        with col_m5:
            st.subheader("Reatti")
            st.markdown("Equação 15, página 3")
            st.latex(r"F_{r,n} = \frac{\gamma^2}{2}[\tau_1 - \frac{2\pi\eta}{2}(...)\tau_2]")
            st.caption("Ferreira modificado")
        
        with col_m6:
            st.subheader("Dimitrakakis")
            st.markdown("Equações 16-19, página 3")
            st.latex(r"F_r = \triangle[...]")
            st.caption("FEM-based, menos portátil")
        
        st.divider()
        st.markdown("#### Três Geometrias de Condutores")
        
        col_g1, col_g2, col_g3 = st.columns(3)
        
        with col_g1:
            st.subheader("Circular")
            st.markdown("Ferreira 2 (Bessel)")
            st.latex(r"P_{circ} \approx \frac{H_0^2}{\sigma\delta}")
            st.caption("Coordenadas cilíndricas")
        
        with col_g2:
            st.subheader("Retangular (3 variantes)")
            st.markdown("Dowell (Eq. 5, 8, 9)")
            st.latex(r"P_a = (H_0^2/\sigma\delta)\tanh(b/\delta)")
            st.latex(r"P_b = H_0^2/\sigma\delta")
            st.latex(r"P_c = (H_0^2/\sigma\delta)\coth(b/\delta)")
            st.caption("Diferentes BC")
        
        with col_g3:
            st.subheader("Sheet (Folha)")
            st.markdown("Baseado em Dowell")
            st.latex(r"P_{sheet,\infty} = H_0^2/\sigma\delta")
            st.latex(r"P_{sheet,t} = (H_0^2/\sigma\delta)\cdot[1-e^{-2t/\delta}]/2")
            st.caption("Finito vs semi-inf")
        
        st.divider()
        st.markdown("#### Resultado Principal (Kaymak et al., Seção IV)")
        st.success(
            "**Melhor Método**: Dowell 2 oferece a melhor acurácia em comparação com "
            "FEM simulations e medições experimentais em ampla faixa de parâmetros. "
            "Desvios típicos: ±10-20%.\n\n"
            "**Erro Máximo**: Ocorre quando Δ (ptaxa de penetração) é grande, "
            "η (porosidade) é pequeno, e m (camadas) é grande. "
            "Veja Fig. 10-11 do artigo para mapas de erro."
        )
    
    with tab_calculation:
        st.markdown("#### Cálculo Comparativo Q5")
        
        col_c1, col_c2, col_c3 = st.columns(3)
        
        with col_c1:
            st.markdown("**Geometria**")
            char_dim_cm = st.number_input(
                "Dimensão característica [cm]",
                min_value=0.1,
                value=2.5,
                key="q5_char_dim"
            )
        
        with col_c2:
            st.markdown("**Material: Cobre**")
            conductivity = st.number_input(
                "Condutividade σ [S/m]",
                min_value=1e6,
                value=5.8e7,
                format="%.2e",
                key="q5_sigma"
            )
        
        with col_c3:
            st.markdown("**Operação**")
            frequency = st.number_input(
                "Frequência [Hz]",
                min_value=1.0,
                value=60.0,
                key="q5_freq"
            )
        
        col_c4, col_c5 = st.columns(2)
        
        with col_c4:
            st.markdown("**Campo Magnético**")
            h0_field = st.number_input(
                "Campo H₀ [A/m]",
                min_value=0.1,
                value=6.0,
                key="q5_h0"
            )
        
        with col_c5:
            st.markdown("**Permeabilidade Relativa**")
            mu_rel = st.number_input(
                "μᵣ (unitless)",
                min_value=1.0,
                value=1.0,
                key="q5_mu_r"
            )

        col_c6, col_c7 = st.columns(2)
        with col_c6:
            i_ref_a = st.number_input(
                "Corrente de referência Im [A]",
                min_value=1.0,
                value=2000.0,
                key="q5_i_ref_a",
                help="Usada na varredura de corrente assumindo H0 proporcional a Im.",
            )
        with col_c7:
            st.caption("Hipótese para gráfico de corrente: H0(Im) = H0_ref * (Im / Im_ref).")
        
        if st.button("Calcular Questão 5 (Kaymak et al.)", type="primary", key="q5_calc"):
            try:
                from app.core.exercises.q05_comparison_methods import solve_question_05_comparison
                
                result = solve_question_05_comparison(
                    frequency_hz=frequency,
                    surface_magnetic_field_h0_a_per_m=h0_field,
                    characteristic_dimension_cm=char_dim_cm,
                    conductivity_s_per_m=conductivity,
                    permeability_rel=mu_rel,
                    material_name="Cobre"
                )
                
                st.session_state.q5_result = result
                st.session_state.q5_inputs = {
                    "frequency": float(frequency),
                    "h0_field": float(h0_field),
                    "char_dim_cm": float(char_dim_cm),
                    "conductivity": float(conductivity),
                    "mu_rel": float(mu_rel),
                    "i_ref_a": float(i_ref_a),
                }
                st.success("✓ Cálculo concluído!")
            
            except Exception as e:
                st.error(f"Erro na execução: {str(e)}")
    
    with tab_comparison:
        st.markdown("#### Resultados da Comparação")
        
        if "q5_result" in st.session_state:
            result = st.session_state.q5_result
            
            st.markdown("**Parâmetros Calculados**")
            col_r1, col_r2, col_r3, col_r4 = st.columns(4)
            
            with col_r1:
                st.metric("Skin Depth (δ)", f"{result.skin_depth_mm:.3f} mm")
            with col_r2:
                st.metric("Penetration Ratio", f"{result.dimensionless_ratio:.4f}")
            with col_r3:
                st.metric("Frequência", f"{result.frequency_hz:.1f} Hz")
            with col_r4:
                st.metric("Condutividade", f"{result.conductivity_s_per_m:.2e} S/m")
            
            st.divider()
            
            st.markdown("**Comparação de Perdas [W/m²]**")
            
            comparison_data = {
                "Geometria / Variante": [
                    "Circular",
                    "Retang. (a) Simétrico",
                    "Retang. (b) Baseline",
                    "Retang. (c) Finito",
                    "Sheet Semi-∞",
                    "Sheet Finito"
                ],
                "Perda [W/m²]": [
                    result.circular_conductor_loss_w_per_m2,
                    result.rectangular_variant_a_loss_w_per_m2,
                    result.rectangular_variant_b_loss_w_per_m2,
                    result.rectangular_variant_c_loss_w_per_m2,
                    result.sheet_semi_infinite_loss_w_per_m2,
                    result.sheet_finite_loss_w_per_m2
                ],
                "Relativo a Rect(b)": [
                    result.ratio_circular_to_rect_b,
                    result.ratio_rect_a_to_b,
                    1.0,
                    result.ratio_rect_c_to_b,
                    result.ratio_sheet_semi_to_rect_b,
                    result.ratio_sheet_finite_to_rect_b
                ]
            }
            
            df = __import__("pandas").DataFrame(comparison_data)
            st.dataframe(df, use_container_width=True)
            
            st.divider()
            
            st.markdown("**Interpretação Física**")
            st.markdown(result.notes)

            st.divider()
            st.markdown("### Varreduras em X por Material (base da Q3)")
            st.caption(
                "Cada curva representa um material disponível no código. "
                "Use os seletores para habilitar/desabilitar materiais na visualização."
            )

            q5_base_inputs = st.session_state.get(
                "q5_inputs",
                {
                    "frequency": float(result.frequency_hz),
                    "h0_field": float(result.surface_magnetic_field_a_per_m),
                    "char_dim_cm": float(result.characteristic_dimension_mm / 10.0),
                    "conductivity": float(result.conductivity_s_per_m),
                    "mu_rel": float(result.permeability_rel),
                    "i_ref_a": 2000.0,
                },
            )

            material_options = _get_q5_material_options()
            st.markdown("**Materiais habilitados**")
            selected_material_data = []
            material_cols = st.columns(3)
            for idx, material in enumerate(material_options):
                default_enabled = "Vacuo" not in material["name"]
                with material_cols[idx % 3]:
                    enabled = st.checkbox(
                        material["name"],
                        value=default_enabled,
                        key=f"q5_material_enabled_{idx}",
                    )
                if enabled:
                    selected_material_data.append(material)

            if not selected_material_data:
                st.warning("Selecione ao menos um material para gerar os gráficos de varredura.")
            else:
                metric_options = {
                    "Perda Retangular (b) [W/m²]": "rect_b_loss",
                    "Perda Retangular (a) [W/m²]": "rect_a_loss",
                    "Perda Retangular (c) [W/m²]": "rect_c_loss",
                    "Perda Circular [W/m²]": "circular_loss",
                    "Perda Sheet Finito [W/m²]": "sheet_finite_loss",
                    "Perda Sheet Semi-∞ [W/m²]": "sheet_semi_loss",
                    "Skin Depth [mm]": "skin_depth_mm",
                }
                metric_label = st.selectbox(
                    "Grandeza no eixo Y",
                    options=list(metric_options.keys()),
                    index=0,
                    key="q5_metric_y",
                )
                metric_key = metric_options[metric_label]

                col_sweep_1, col_sweep_2, col_sweep_3 = st.columns(3)
                with col_sweep_1:
                    freq_min = st.number_input("f mín [Hz]", min_value=0.1, value=10.0, key="q5_freq_min")
                    freq_max = st.number_input("f máx [Hz]", min_value=1.0, value=500.0, key="q5_freq_max")
                with col_sweep_2:
                    i_min = st.number_input("Im mín [A]", min_value=0.1, value=500.0, key="q5_i_min")
                    i_max = st.number_input("Im máx [A]", min_value=1.0, value=5000.0, key="q5_i_max")
                with col_sweep_3:
                    n_points = int(
                        st.slider("Pontos por curva", min_value=8, max_value=60, value=24, key="q5_n_points")
                    )
                log_scale_x = st.toggle("Escala log no eixo X", value=True, key="q5_log_x")

                if freq_max <= freq_min:
                    st.warning("Ajuste a faixa de frequência: f máx deve ser maior que f mín.")
                elif i_max <= i_min:
                    st.warning("Ajuste a faixa de corrente: Im máx deve ser maior que Im mín.")
                else:
                    from app.core.exercises.q05_comparison_methods import solve_question_05_comparison

                    if log_scale_x:
                        x_freq = _limit_sweep_points(np.geomspace(freq_min, freq_max, n_points), max_points=n_points)
                        x_current = _limit_sweep_points(np.geomspace(i_min, i_max, n_points), max_points=n_points)
                    else:
                        x_freq = _limit_sweep_points(np.linspace(freq_min, freq_max, n_points), max_points=n_points)
                        x_current = _limit_sweep_points(np.linspace(i_min, i_max, n_points), max_points=n_points)

                    fig_freq = go.Figure()
                    fig_current = go.Figure()

                    for material in selected_material_data:
                        y_freq = []
                        for f_hz in x_freq:
                            res_f = solve_question_05_comparison(
                                frequency_hz=float(f_hz),
                                surface_magnetic_field_h0_a_per_m=float(q5_base_inputs["h0_field"]),
                                characteristic_dimension_cm=float(q5_base_inputs["char_dim_cm"]),
                                conductivity_s_per_m=float(material["sigma"]),
                                permeability_rel=float(material["mu_rel"]),
                                material_name=material["name"],
                            )
                            y_freq.append(_extract_q5_metric_value(res_f, metric_key))

                        y_current = []
                        for i_a in x_current:
                            h0_scaled = float(q5_base_inputs["h0_field"]) * (
                                float(i_a) / max(float(q5_base_inputs["i_ref_a"]), 1e-12)
                            )
                            res_i = solve_question_05_comparison(
                                frequency_hz=float(q5_base_inputs["frequency"]),
                                surface_magnetic_field_h0_a_per_m=h0_scaled,
                                characteristic_dimension_cm=float(q5_base_inputs["char_dim_cm"]),
                                conductivity_s_per_m=float(material["sigma"]),
                                permeability_rel=float(material["mu_rel"]),
                                material_name=material["name"],
                            )
                            y_current.append(_extract_q5_metric_value(res_i, metric_key))

                        fig_freq.add_trace(
                            go.Scatter(
                                x=x_freq,
                                y=y_freq,
                                mode="lines",
                                name=material["name"],
                            )
                        )
                        fig_current.add_trace(
                            go.Scatter(
                                x=x_current,
                                y=y_current,
                                mode="lines",
                                name=material["name"],
                            )
                        )

                    fig_freq.update_layout(
                        title=f"Q5: {metric_label} vs Frequência (todos os materiais selecionados)",
                        xaxis_title="Frequência [Hz]",
                        yaxis_title=metric_label,
                        hovermode="x unified",
                        height=430,
                    )
                    fig_current.update_layout(
                        title=f"Q5: {metric_label} vs Corrente Im (H0 proporcional a Im)",
                        xaxis_title="Corrente Im [A]",
                        yaxis_title=metric_label,
                        hovermode="x unified",
                        height=430,
                    )
                    if log_scale_x:
                        fig_freq.update_xaxes(type="log")
                        fig_current.update_xaxes(type="log")

                    _plotly_chart_with_csv(fig_freq, "q5_fig_freq", "q5_varredura_frequencia.csv")
                    _plotly_chart_with_csv(fig_current, "q5_fig_current", "q5_varredura_corrente.csv")

                    material_x_sigma = [float(m["sigma"]) for m in selected_material_data]
                    material_x_mu = [float(m["mu_rel"]) for m in selected_material_data]
                    material_y = []
                    for material in selected_material_data:
                        res_mat = solve_question_05_comparison(
                            frequency_hz=float(q5_base_inputs["frequency"]),
                            surface_magnetic_field_h0_a_per_m=float(q5_base_inputs["h0_field"]),
                            characteristic_dimension_cm=float(q5_base_inputs["char_dim_cm"]),
                            conductivity_s_per_m=float(material["sigma"]),
                            permeability_rel=float(material["mu_rel"]),
                            material_name=material["name"],
                        )
                        material_y.append(_extract_q5_metric_value(res_mat, metric_key))

                    fig_material_props = make_subplots(
                        rows=1,
                        cols=2,
                        subplot_titles=("Variação com condutividade σ", "Variação com permeabilidade relativa μr"),
                    )
                    fig_material_props.add_trace(
                        go.Scatter(
                            x=material_x_sigma,
                            y=material_y,
                            mode="markers+lines",
                            text=[m["name"] for m in selected_material_data],
                            name="σ",
                        ),
                        row=1,
                        col=1,
                    )
                    fig_material_props.add_trace(
                        go.Scatter(
                            x=material_x_mu,
                            y=material_y,
                            mode="markers+lines",
                            text=[m["name"] for m in selected_material_data],
                            name="μr",
                        ),
                        row=1,
                        col=2,
                    )
                    fig_material_props.update_xaxes(title_text="σ [S/m]", row=1, col=1, type="log")
                    fig_material_props.update_xaxes(title_text="μr [-]", row=1, col=2, type="log")
                    fig_material_props.update_yaxes(title_text=metric_label, row=1, col=1)
                    fig_material_props.update_yaxes(title_text=metric_label, row=1, col=2)
                    fig_material_props.update_layout(
                        title="Q5: Grandeza vs propriedades dos materiais",
                        hovermode="closest",
                        height=450,
                        showlegend=False,
                    )
                    if log_scale_x:
                        fig_material_props.update_xaxes(type="log", row=1, col=1)
                        fig_material_props.update_xaxes(type="log", row=1, col=2)
                    _plotly_chart_with_csv(
                        fig_material_props,
                        "q5_fig_material_props",
                        "q5_varredura_materiais.csv",
                    )
        
        else:
            st.info("Execute o cálculo na aba 'Cálculo Comparativo' para ver os resultados.")





def main():
    """Funcao principal da aplicacao."""
    # Navegacao lateral
    st.sidebar.markdown("# Eletromag Lab")
    st.sidebar.markdown("Laboratório visual de eletromagnetismo")
    st.sidebar.divider()

    page = st.sidebar.radio(
        "Navegação",
        options=["Avaliação 1", "Apresentação"],
        index=0,
    )


    if page == "Avaliação 1":
        show_assessment_01_page()
    elif page == "Apresentação":
        show_home_page()


def show_home_page():
    """Exibe página de apresentação técnica do projeto."""
    st.markdown(
        '<div class="main-title">Apresentação Técnica</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="subtitle">Métodos computacionais, tecnologias e bibliotecas utilizadas no Eletromag Lab</div>',
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown("### Métodos Computacionais Implementados")
    st.markdown("#### Questão 1")
    st.write(
        """
        - Método analítico para perdas por correntes induzidas em tampa circular.
        - Visualizações 3D de perdas variando duas grandezas por superfície.
        - Modelo volumétrico 3D regional com integração em espessura por quadratura
          de Gauss-Legendre e agregação por células no plano.
        """
    )

    st.markdown("#### Questão 2")
    st.write(
        """
        - Dedução analítica da equação de difusão em coordenadas cilíndricas.
        - Formulação de densidade de corrente induzida e perdas totais sem cálculo numérico.
        """
    )

    st.markdown("#### Questão 3")
    st.write(
        """
        - Simulação numérica com método Biot-Savart na geometria com 3 furos.
        - Varreduras paramétricas em frequência e corrente para múltiplos materiais.
        - Superfícies 3D de perdas variando pares de grandezas (método Biot-Savart).
        - Mapas regionais de campo e perdas (malha computacional + integração por região).
        """
    )

    st.markdown("#### Questão 4")
    st.write(
        """
        - Formulações analíticas para variantes de condutores retangulares.
        - Cálculo de profundidade de penetração, densidade de corrente e perdas superficiais.
        """
    )

    st.markdown("#### Questão 5")
    st.write(
        """
        - Comparação de métodos analíticos para resistência AC (referência Kaymak et al.).
        - Estudo comparativo por geometria, material e varreduras em X.
        """
    )

    st.divider()

    st.markdown("### Tecnologias Utilizadas")
    st.write(
        """
        - Linguagem: Python
        - Interface: Streamlit
        - Computação numérica: NumPy (com rotinas vetorizadas)
        - Modelagem de dados: Pydantic
        - Geração de relatórios: ReportLab
        """
    )

    st.divider()

    st.markdown("### Bibliotecas e Pacotes Gráficos")
    st.write(
        """
        - Plotly Graph Objects (go): gráficos 2D/3D, heatmaps e superfícies.
        - Plotly Subplots (make_subplots): composição de múltiplos gráficos.
        - Kaleido: exportação de figuras Plotly para imagem.
        - Componentes geométricos próprios do projeto para visualização da geometria física.
        """
    )

    st.info("Use a seção 'Avaliação 1' no menu lateral para executar os experimentos e comparar os métodos.")


def show_exercise_01_page(biot_only: bool = False):
    """Exibe a pagina da Questao 01 (perdas no tanque)."""
    st.markdown("## Questão 3: Tampa com 3 furos e condutores")
    if biot_only:
        st.caption("Modo da Q3: exibição exclusiva do método Biot-Savart.")

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
        st.session_state.material_preset = "Aco carbono"

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
        _plotly_chart_with_csv(fig_geo, "sim_fig_geometry", "simulacao_geometria.csv")

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

    if biot_only:
        st.markdown("#### Resultado (Biot-Savart)")
        col_biot, col_h, col_loss = st.columns(3)
        with col_biot:
            st.metric(
                "**Perda**",
                f"{result.total_loss_approximate_w:.2f}",
                "W",
                help="Método Biot-Savart com integração numérica",
            )
        with col_h:
            st.metric("**H máximo**", f"{result.max_h_field:.2f}", "A/m")
        with col_loss:
            st.metric("**Densidade máxima de perdas**", f"{result.max_loss_density:.2f}", "W/m²")
    else:
        st.markdown("#### Comparação de métodos")
        col_analytical, col_approximate, col_diff = st.columns(3)

        with col_analytical:
            st.metric(
                "**Perda**",
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

    if not biot_only:
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

            st.write(f"Resultado= {result.total_loss_analytical_w:.2f} W")

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

                end_current_a = 3000.0
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
                if not biot_only:
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
                _plotly_chart_with_csv(fig_losses, "sim_fig_losses", "simulacao_perdas_corrente.csv")
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
            if not biot_only:
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
            _plotly_chart_with_csv(fig_thickness, "sim_fig_thickness", "simulacao_perdas_espessura.csv")
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
            if not biot_only:
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
            _plotly_chart_with_csv(fig_frequency, "sim_fig_frequency", "simulacao_perdas_frequencia.csv")
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

            max_current = 3000.0
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

            if biot_only:
                fig_3d = go.Figure(
                    data=[
                        go.Surface(
                            x=current_3d,
                            y=thickness_3d,
                            z=approximate_surface,
                            colorscale="Viridis",
                            name="Biot-Savart",
                            showscale=True,
                        )
                    ]
                )
                fig_3d.update_layout(
                    height=600,
                    margin={"l": 0, "r": 0, "t": 40, "b": 0},
                    scene={
                        "xaxis_title": "Corrente [A]",
                        "yaxis_title": "Espessura [mm]",
                        "zaxis_title": "Perdas [W]",
                    },
                )
            else:
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
            _plotly_chart_with_csv(fig_3d, "sim_fig_3d_ce", "simulacao_perdas_3d_corrente_espessura.csv")
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

            if biot_only:
                fig_3d_freq = go.Figure(
                    data=[
                        go.Surface(
                            x=current_3d_freq,
                            y=frequency_3d,
                            z=approximate_surface_freq,
                            colorscale="Viridis",
                            name="Biot-Savart",
                            showscale=True,
                        )
                    ]
                )
                fig_3d_freq.update_layout(
                    height=600,
                    margin={"l": 0, "r": 0, "t": 40, "b": 0},
                    scene={
                        "xaxis_title": "Corrente [A]",
                        "yaxis_title": "Frequência [Hz]",
                        "zaxis_title": "Perdas [W]",
                    },
                )
            else:
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
            _plotly_chart_with_csv(fig_3d_freq, "sim_fig_3d_cf", "simulacao_perdas_3d_corrente_frequencia.csv")
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

            if biot_only:
                fig_3d_thick_freq = go.Figure(
                    data=[
                        go.Surface(
                            x=thickness_3d_freq,
                            y=frequency_3d_thick,
                            z=approximate_surface_thick_freq,
                            colorscale="Viridis",
                            name="Biot-Savart",
                            showscale=True,
                        )
                    ]
                )
                fig_3d_thick_freq.update_layout(
                    height=600,
                    margin={"l": 0, "r": 0, "t": 40, "b": 0},
                    scene={
                        "xaxis_title": "Espessura [mm]",
                        "yaxis_title": "Frequência [Hz]",
                        "zaxis_title": "Perdas [W]",
                    },
                )
            else:
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
            _plotly_chart_with_csv(fig_3d_thick_freq, "sim_fig_3d_ef", "simulacao_perdas_3d_espessura_frequencia.csv")
            figures_3d.append(("Perdas por espessura x frequencia", fig_3d_thick_freq))
            st.caption(
                f"Grade de cálculo: {len(thickness_3d_freq)} × {len(frequency_3d_thick)} pontos"
            )

if __name__ == "__main__":
    main()
