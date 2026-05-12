"""Renderizacao da Questao 3 (Biot-Savart)."""

from __future__ import annotations

from typing import Callable

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from app.components.geometry_plot import plot_geometry
from app.core.exercises.q01_tank_losses import simulate_exercise_03_biot_only
from app.core.geometry.plate import create_plate_from_input
from app.schemas import HoleInput, MaterialInput, MeshInput, PlateInput, get_default_exercise01_input, get_material_presets


def _get_q3_material_options() -> list[dict]:
    """Retorna materiais para comparacao da Q3 (enunciado + presets do ambiente)."""
    mu0 = 4.0 * np.pi * 1e-7
    materials: list[dict] = [{"name": "Aço carbono (Q3 enunciado)", "sigma": 2.0e7, "mu_r": 500.0}]

    for name, values in get_material_presets().items():
        if name == "Personalizado":
            continue
        materials.append({"name": name, "sigma": float(values["sigma"]), "mu_r": float(values["mu"]) / mu0})

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


def render_q3_tab(
    plotly_chart_with_csv: Callable[[go.Figure, str, str], None],
    apply_im_to_conductors: Callable,
    build_sweep_axis: Callable[[float, float, int, bool], np.ndarray],
    apply_log_x_axis: Callable[[list[go.Figure], bool], None],
) -> None:
    """Questao 3 da avaliacao: calculo usando apenas Biot-Savart."""
    st.markdown("### Questão 3: Campo magnético H(x,y) e perdas na tampa com 3 furos")
    st.caption(
        "Enunciado: calcular perdas para 2000 A, 2250 A, 2500 A e 2800 A em 60 Hz, "
        "com aço carbono (sigma=2e7 S/m, mu_r=500)."
    )

    base_input = get_default_exercise01_input()
    mu0 = 4.0 * np.pi * 1e-7
    q3_material = MaterialInput(mu=mu0 * 500.0, sigma=2.0e7)
    current_cases = [2000.0, 2250.0, 2500.0, 2800.0]

    st.divider()
    st.markdown("#### 1. Parametrizações")
    st.caption("Geometria do enunciado (padrão): placa 590×270×5 mm, três furos de 82 mm. Você pode editar os parâmetros abaixo.")

    with st.expander("**Parâmetros de geometria** (padrão do enunciado)", expanded=True):
        col_q3_geo_1, col_q3_geo_2, col_q3_geo_3 = st.columns(3)
        with col_q3_geo_1:
            st.markdown("**Placa (mm)**")
            q3_plate_width = st.number_input("Largura", min_value=10.0, value=590.0, step=10.0, key="q3_plate_width")
            q3_plate_height = st.number_input("Altura", min_value=10.0, value=270.0, step=10.0, key="q3_plate_height")
            q3_plate_thickness = st.number_input("Espessura", min_value=1.0, value=5.0, step=0.5, key="q3_plate_thickness")
        with col_q3_geo_2:
            st.markdown("**Furos (mm)**")
            q3_hole_diameter = st.number_input("Diâmetro dos furos", min_value=5.0, value=82.0, step=5.0, key="q3_hole_diameter")
            st.caption("3 furos em posição simétrica")
        with col_q3_geo_3:
            st.markdown("**Frequência (Hz)**")
            q3_frequency = st.number_input("f", min_value=0.1, value=60.0, step=10.0, key="q3_frequency_enunciado")

    q3_custom_input = base_input.model_copy(
        update={
            "plate": PlateInput(width_mm=q3_plate_width, height_mm=q3_plate_height, thickness_mm=q3_plate_thickness),
            "frequency_hz": float(q3_frequency),
        }
    )

    q3_custom_input.holes = [
        HoleInput(x_mm=100.0, y_mm=135.0, diameter_mm=q3_hole_diameter),
        HoleInput(x_mm=295.0, y_mm=135.0, diameter_mm=q3_hole_diameter),
        HoleInput(x_mm=490.0, y_mm=135.0, diameter_mm=q3_hole_diameter),
    ]

    try:
        q3_plate = create_plate_from_input(q3_custom_input.plate, q3_custom_input.holes)
        q3_cond_positions = np.array([[c.x_mm * 1e-3, c.y_mm * 1e-3] for c in q3_custom_input.conductors])
        q3_fig_geo = plot_geometry(q3_plate, q3_cond_positions)
        plotly_chart_with_csv(q3_fig_geo, "q3_fig_geometry", "q3_geometria_enunciado.csv")
    except Exception as e:
        st.warning(f"Não foi possível gerar a geometria da Q3: {str(e)}")

    st.markdown("**Materiais habilitados**")
    q3_material_options = _get_q3_material_options()
    q3_selected_materials = []
    q3_cols = st.columns(3)
    for idx, material in enumerate(q3_material_options):
        default_enabled = idx < 6
        with q3_cols[idx % 3]:
            enabled = st.checkbox(material["name"], value=default_enabled, key=f"q3_material_enabled_{idx}")
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
        q3_metric_label = st.selectbox("Grandeza no eixo Y", options=list(q3_metric_options.keys()), index=0, key="q3_metric_y")
        q3_metric_key = q3_metric_options[q3_metric_label]

        col_q3_1, col_q3_2, col_q3_3 = st.columns(3)
        with col_q3_1:
            q3_freq_min = st.number_input("f mín [Hz]", min_value=0.1, value=10.0, key="q3_freq_min")
            q3_freq_max = st.number_input("f máx [Hz]", min_value=1.0, value=5000.0, key="q3_freq_max")
        with col_q3_2:
            q3_i_min = st.number_input("Im mín [A]", min_value=0.1, value=500.0, key="q3_i_min")
            q3_i_max = st.number_input("Im máx [A]", min_value=1.0, value=3000.0, key="q3_i_max")
        with col_q3_3:
            q3_n_points = int(st.slider("Pontos por curva", min_value=8, max_value=40, value=16, key="q3_n_points"))

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
            q3_x_freq = build_sweep_axis(q3_freq_min, q3_freq_max, q3_n_points, q3_log_x)
            q3_x_current = build_sweep_axis(q3_i_min, q3_i_max, q3_n_points, q3_log_x)

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
                            "conductors": apply_im_to_conductors(q3_custom_input.conductors, float(q3_ref_i)),
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
                            "conductors": apply_im_to_conductors(q3_custom_input.conductors, float(i_a)),
                            "mesh": MeshInput(nx=80, ny=80),
                        }
                    )
                    q3_res_i = simulate_exercise_03_biot_only(q3_input_i)
                    y_current.append(_extract_q3_metric_value(q3_res_i, q3_metric_key))

                q3_fig_freq.add_trace(go.Scatter(x=q3_x_freq, y=y_freq, mode="lines", name=material["name"]))
                q3_fig_current.add_trace(go.Scatter(x=q3_x_current, y=y_current, mode="lines", name=material["name"]))

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
            apply_log_x_axis([q3_fig_freq, q3_fig_current], q3_log_x)

            plotly_chart_with_csv(q3_fig_freq, "q3_fig_freq", "q3_varredura_frequencia.csv")
            plotly_chart_with_csv(q3_fig_current, "q3_fig_current", "q3_varredura_corrente.csv")

    st.divider()
    st.markdown("#### 3. Gráficos 3D - Superfícies Biot-Savart")
    st.caption("Superfícies numéricas calculadas com o método Biot-Savart, variando duas grandezas de entrada para obter a perda total na tampa com 3 furos.")

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
        q3_3d_current_max = st.number_input("Im máx para 3D [A]", min_value=100.0, value=3000.0, step=100.0, key="q3_3d_current_max")
    with col_3d_2:
        q3_3d_freq_max = st.number_input("f máx para 3D [Hz]", min_value=1.0, value=max(500.0, float(q3_frequency) * 1.5), step=50.0, key="q3_3d_freq_max")
    with col_3d_3:
        q3_3d_hole_max = st.number_input("Diâmetro máx dos furos para 3D [mm]", min_value=10.0, value=max(100.0, float(q3_hole_diameter) * 1.5), step=5.0, key="q3_3d_hole_max")

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
                    "conductors": apply_im_to_conductors(q3_custom_input.conductors, float(current_val)),
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
                    "conductors": apply_im_to_conductors(q3_custom_input.conductors, float(current_val)),
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

    fig_q3_3d_cf = go.Figure(data=[go.Surface(x=q3_current_3d, y=q3_freq_3d, z=q3_surface_current_freq, colorscale="Viridis", showscale=True)])
    fig_q3_3d_cf.update_layout(
        title="Q3 3D: Perdas por Corrente × Frequência (Biot-Savart)",
        height=560,
        margin={"l": 0, "r": 0, "t": 50, "b": 0},
        scene={"xaxis_title": "Corrente Im [A]", "yaxis_title": "Frequência [Hz]", "zaxis_title": "Perdas [W]"},
    )
    plotly_chart_with_csv(fig_q3_3d_cf, "q3_fig_3d_cf", "q3_perdas_3d_corrente_frequencia.csv")

    fig_q3_3d_ch = go.Figure(data=[go.Surface(x=q3_current_3d, y=q3_hole_3d, z=q3_surface_current_hole, colorscale="Viridis", showscale=True)])
    fig_q3_3d_ch.update_layout(
        title="Q3 3D: Perdas por Corrente × Diâmetro dos Furos (Biot-Savart)",
        height=560,
        margin={"l": 0, "r": 0, "t": 50, "b": 0},
        scene={"xaxis_title": "Corrente Im [A]", "yaxis_title": "Diâmetro dos furos [mm]", "zaxis_title": "Perdas [W]"},
    )
    plotly_chart_with_csv(fig_q3_3d_ch, "q3_fig_3d_ch", "q3_perdas_3d_corrente_furo.csv")

    st.divider()
    st.markdown("#### 4. Heatmaps 2D Sobre a Tampa")
    st.caption("Mapas regionais computacionais (1 cm x 1 cm) sobre a tampa, respeitando a resolução de malha e a máscara geométrica dos furos.")

    col_hm_1, col_hm_2, col_hm_3 = st.columns(3)
    with col_hm_1:
        selected_material_hm = st.selectbox("Material de referência", options=[m["name"] for m in q3_material_options], index=0, key="q3_hm_material")
    with col_hm_2:
        q3_hm_current = st.number_input("Corrente Im do heatmap [A]", min_value=10.0, value=2250.0, step=100.0, key="q3_hm_current")
    with col_hm_3:
        q3_hm_mesh_res = st.slider("Resolução da malha", min_value=60, max_value=320, value=160, step=10, key="q3_hm_mesh_res")

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
                "conductors": apply_im_to_conductors(q3_custom_input.conductors, float(q3_hm_current)),
                "mesh": MeshInput(nx=int(q3_hm_mesh_res), ny=int(q3_hm_mesh_res)),
            }
        )

        try:
            from app.core.electromagnetics.losses import get_loss_density
            from app.core.geometry.mesh import create_uniform_mesh

            plate_hm = create_plate_from_input(q3_input_hm.plate, q3_input_hm.holes)
            mesh_hm = create_uniform_mesh(plate_hm.width_m, plate_hm.height_m, int(q3_hm_mesh_res), int(q3_hm_mesh_res))

            x_mesh, y_mesh = mesh_hm.get_mesh_arrays()
            dx_m, dy_m = mesh_hm.get_dx_dy()
            conductor_pos_hm = np.array([[c.x_mm * 1e-3, c.y_mm * 1e-3] for c in q3_input_hm.conductors])
            conductor_cur_hm = np.array([c.current_a for c in q3_input_hm.conductors])

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
            region_sum_w = np.bincount(flat_idx[flat_valid], weights=weights_w[flat_valid], minlength=n_x_cm * n_y_cm).reshape(n_y_cm, n_x_cm)
            region_count = np.bincount(flat_idx[flat_valid], minlength=n_x_cm * n_y_cm).reshape(n_y_cm, n_x_cm)

            valid_field = valid_mask & np.isfinite(h_field)
            flat_valid_field = valid_field.ravel()
            region_sum_h = np.bincount(flat_idx[flat_valid_field], weights=h_field.ravel()[flat_valid_field], minlength=n_x_cm * n_y_cm).reshape(n_y_cm, n_x_cm)
            region_count_h = np.bincount(flat_idx[flat_valid_field], minlength=n_x_cm * n_y_cm).reshape(n_y_cm, n_x_cm)

            region_map_w = np.where(region_count > 0, region_sum_w, np.nan)
            region_map_h = np.where(region_count_h > 0, region_sum_h / np.maximum(region_count_h, 1), np.nan)
            x_cm_centers = np.arange(n_x_cm, dtype=float) * cell_size_mm + cell_size_mm / 2.0
            y_cm_centers = np.arange(n_y_cm, dtype=float) * cell_size_mm + cell_size_mm / 2.0

            fig_region_field = go.Figure(data=[go.Heatmap(x=x_cm_centers, y=y_cm_centers, z=region_map_h, colorscale="Viridis", colorbar={"title": "Campo médio [A/m]"}, hoverongaps=False)])
            fig_region_field.update_layout(title="Q3: Campo por Região (1 cm x 1 cm)", xaxis_title="X [mm]", yaxis_title="Y [mm]", height=520, margin={"l": 40, "r": 20, "t": 60, "b": 40})
            fig_region_field.update_xaxes(scaleanchor="y", scaleratio=1)
            plotly_chart_with_csv(fig_region_field, "q3_fig_region_field", "q3_campo_por_regiao_cm2.csv")

            fig_region_loss = go.Figure(data=[go.Heatmap(x=x_cm_centers, y=y_cm_centers, z=region_map_w, colorscale="YlOrRd", colorbar={"title": "Perda por região [W]"}, hoverongaps=False)])
            fig_region_loss.update_layout(title="Q3: Perdas por Região (1 cm x 1 cm)", xaxis_title="X [mm]", yaxis_title="Y [mm]", height=520, margin={"l": 40, "r": 20, "t": 60, "b": 40})
            fig_region_loss.update_xaxes(scaleanchor="y", scaleratio=1)
            plotly_chart_with_csv(fig_region_loss, "q3_fig_region_loss", "q3_perdas_por_regiao_cm2.csv")

        except Exception as e:
            st.error(f"Erro ao gerar heatmaps da Q3: {str(e)}")

    st.divider()
    st.markdown("#### 5. Tabela de resultados da Questão 3 (Enunciado)")
    st.caption("Resultados para os casos do enunciado: 2000 A, 2250 A, 2500 A e 2800 A em 60 Hz com aço carbono.")

    q3_rows = []
    for current in current_cases:
        case_input = base_input.model_copy(
            update={
                "frequency_hz": 60.0,
                "material": q3_material,
                "conductors": apply_im_to_conductors(base_input.conductors, float(current)),
                "mesh": MeshInput(nx=200, ny=200),
            }
        )
        case_result = simulate_exercise_03_biot_only(case_input)
        q3_rows.append({"Corrente por condutor [A]": int(current), "Perda [W]": round(case_result["total_loss_biot_w"], 5), "H máximo [A/m]": round(case_result["max_h_field"], 5)})

    st.dataframe(q3_rows, use_container_width=True, hide_index=True)
