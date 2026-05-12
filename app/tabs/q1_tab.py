"""Renderizacao da Questao 1 (perdas na tampa circular)."""

from __future__ import annotations

from typing import Callable

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from app.core.electromagnetics.biot_savart import calculate_loss_analytical
from app.schemas import get_material_presets


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
    """Modela campo/perdas 3D da Q1 e agrega resultados por região no plano XY."""
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

    centers_mm = ((np.arange(n_regions, dtype=float) + 0.5) * region_size_m - outer_r_m) * 1000.0

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


def render_q1_tab(
    plotly_chart_with_csv: Callable[[go.Figure, str, str], None],
    build_sweep_axis: Callable[[float, float, int, bool], np.ndarray],
    apply_log_x_axis: Callable[[list[go.Figure], bool], None],
) -> None:
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
        outer_d_mm = st.number_input("Diâmetro externo D [mm]", min_value=1.0, value=910.0, key="av1_q1_d_ext")
        inner_d_mm = st.number_input("Diâmetro interno d [mm]", min_value=1.0, value=165.0, key="av1_q1_d_int")
    with col_b:
        thickness_mm = st.number_input("Espessura c [mm]", min_value=0.01, value=9.52, key="av1_q1_thickness")
        im_a = st.number_input("Corrente Im [Arms]", min_value=0.0, value=1000.0, key="av1_q1_im")

    if inner_d_mm >= outer_d_mm:
        st.error("O diâmetro interno deve ser menor que o diâmetro externo.")
        return

    mu0 = 4.0 * np.pi * 1e-7
    ln_ba = float(np.log(outer_d_mm / inner_d_mm))
    materials = _get_q1_material_options()

    st.divider()
    st.markdown("#### 2. Gráficos 2D - Perdas (multi-material)")
    st.caption("Curvas em X para todos os materiais habilitados, incluindo os materiais base da Q1 e os demais disponíveis no software.")

    st.markdown("**Materiais habilitados**")
    enabled_materials = []
    material_cols = st.columns(3)
    for idx, material in enumerate(materials):
        default_enabled = idx < 6
        with material_cols[idx % 3]:
            enabled = st.checkbox(material["name"], value=default_enabled, key=f"q1_material_enabled_{idx}")
        if enabled:
            enabled_materials.append(material)

    if not enabled_materials:
        st.warning("Selecione ao menos um material para gerar os gráficos da Q1.")
    else:
        metric_options = {"Perda analítica [W]": "loss_w", "Skin Depth [mm]": "skin_depth_mm"}
        metric_label = st.selectbox("Grandeza no eixo Y", options=list(metric_options.keys()), index=0, key="q1_metric_y")
        metric_key = metric_options[metric_label]

        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            freq_min = st.number_input("f mín [Hz]", min_value=0.1, value=10.0, key="q1_freq_min")
            freq_max = st.number_input("f máx [Hz]", min_value=1.0, value=500.0, key="q1_freq_max")
        with col_s2:
            i_min = st.number_input("Im mín [A]", min_value=0.1, value=100.0, key="q1_i_min")
            i_max = st.number_input("Im máx [A]", min_value=1.0, value=3000.0, key="q1_i_max")
        with col_s3:
            n_points = int(st.slider("Pontos por curva", min_value=8, max_value=60, value=24, key="q1_n_points"))
        log_scale_x = st.toggle("Escala log no eixo X", value=True, key="q1_log_x")

        if freq_max <= freq_min:
            st.warning("Ajuste a faixa de frequência: f máx deve ser maior que f mín.")
        elif i_max <= i_min:
            st.warning("Ajuste a faixa de corrente: Im máx deve ser maior que Im mín.")
        else:
            x_freq = build_sweep_axis(freq_min, freq_max, n_points, log_scale_x)
            x_current = build_sweep_axis(i_min, i_max, n_points, log_scale_x)

            fig_freq = go.Figure()
            fig_current = go.Figure()

            for material in enabled_materials:
                mu_value = mu0 * float(material["mu_r"])
                sigma_value = float(material["sigma"])

                y_freq = [_q1_metric_value(metric_key, float(im_a), float(thickness_mm), float(f_hz), ln_ba, mu_value, sigma_value) for f_hz in x_freq]
                y_current = [_q1_metric_value(metric_key, float(i_a), float(thickness_mm), float(frequency_hz), ln_ba, mu_value, sigma_value) for i_a in x_current]

                fig_freq.add_trace(go.Scatter(x=x_freq, y=y_freq, mode="lines", name=material["name"]))
                fig_current.add_trace(go.Scatter(x=x_current, y=y_current, mode="lines", name=material["name"]))

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
            apply_log_x_axis([fig_freq, fig_current], log_scale_x)

            plotly_chart_with_csv(fig_freq, "q1_fig_freq", "q1_varredura_frequencia.csv")
            plotly_chart_with_csv(fig_current, "q1_fig_current", "q1_varredura_corrente.csv")

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
        return _q1_metric_value("loss_w", float(i_a), float(c_mm), float(f_hz), float(ln_factor), mu_graph, sigma_graph)

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

        fig_3d_ct = go.Figure(data=[go.Surface(x=current_3d, y=thickness_3d, z=z_current_thickness, colorscale="Viridis", showscale=True)])
        fig_3d_ct.update_layout(
            title=f"Q1 3D: Perdas por Corrente × Espessura (f = {frequency_hz:.1f} Hz)",
            height=560,
            margin={"l": 0, "r": 0, "t": 50, "b": 0},
            scene={"xaxis_title": "Corrente [A]", "yaxis_title": "Espessura [mm]", "zaxis_title": "Perdas [W]"},
        )
        plotly_chart_with_csv(fig_3d_ct, "q1_fig_3d_ct", "q1_perdas_3d_corrente_espessura.csv")

        fig_3d_cf = go.Figure(data=[go.Surface(x=current_3d, y=frequency_3d, z=z_current_frequency, colorscale="Viridis", showscale=True)])
        fig_3d_cf.update_layout(
            title=f"Q1 3D: Perdas por Corrente × Frequência (c = {thickness_mm:.2f} mm)",
            height=560,
            margin={"l": 0, "r": 0, "t": 50, "b": 0},
            scene={"xaxis_title": "Corrente [A]", "yaxis_title": "Frequência [Hz]", "zaxis_title": "Perdas [W]"},
        )
        plotly_chart_with_csv(fig_3d_cf, "q1_fig_3d_cf", "q1_perdas_3d_corrente_frequencia.csv")

        fig_3d_tf = go.Figure(data=[go.Surface(x=thickness_3d, y=frequency_3d, z=z_thickness_frequency, colorscale="Viridis", showscale=True)])
        fig_3d_tf.update_layout(
            title=f"Q1 3D: Perdas por Espessura × Frequência (Im = {im_a:.1f} A)",
            height=560,
            margin={"l": 0, "r": 0, "t": 50, "b": 0},
            scene={"xaxis_title": "Espessura [mm]", "yaxis_title": "Frequência [Hz]", "zaxis_title": "Perdas [W]"},
        )
        plotly_chart_with_csv(fig_3d_tf, "q1_fig_3d_tf", "q1_perdas_3d_espessura_frequencia.csv")

    st.markdown("##### Campo e perdas por região (modelo volumétrico 3D)")
    st.caption("Modelo numérico avançado com integração em espessura por quadratura de Gauss-Legendre e agregação por regiões no plano da tampa circular.")

    col_reg_1, col_reg_2, col_reg_3, col_reg_4 = st.columns(4)
    with col_reg_1:
        selected_material_reg = st.selectbox("Material de referência regional", options=[m["name"] for m in materials], index=0, key="q1_region_material")
    with col_reg_2:
        q1_region_size_mm = st.number_input("Tamanho da região [mm]", min_value=5.0, value=10.0, step=5.0, key="q1_region_size_mm")
    with col_reg_3:
        q1_region_mesh_xy = st.slider("Malha XY (n x n)", min_value=80, max_value=360, value=180, step=20, key="q1_region_mesh_xy")
    with col_reg_4:
        q1_region_quad = st.slider("Ordem da quadratura em z", min_value=2, max_value=14, value=8, step=2, key="q1_region_quad")

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

            st.markdown(f"**Modelo 3D regional:** δ={region_data['delta_mm']:.4f} mm | Perda total integrada={region_data['total_loss_w']:.4f} W | Regiões ativas={region_data['active_regions']}")

            outer_r_mm = float(region_data["outer_radius_mm"])
            inner_r_mm = float(region_data["inner_radius_mm"])
            shapes_ring = [
                {"type": "circle", "x0": -outer_r_mm, "x1": outer_r_mm, "y0": -outer_r_mm, "y1": outer_r_mm, "line": {"color": "black", "width": 2}, "fillcolor": "rgba(0,0,0,0)"},
                {"type": "circle", "x0": -inner_r_mm, "x1": inner_r_mm, "y0": -inner_r_mm, "y1": inner_r_mm, "line": {"color": "white", "width": 1.5}, "fillcolor": "rgba(255,255,255,0.15)"},
            ]

            fig_q1_field_region = go.Figure(data=[go.Heatmap(x=region_data["region_centers_mm"], y=region_data["region_centers_mm"], z=region_data["region_field_h"], colorscale="Viridis", colorbar={"title": "Campo médio [A/m]"}, hoverongaps=False)])
            fig_q1_field_region.add_trace(go.Scatter(x=region_data["line_x"], y=region_data["line_y"], mode="lines", line={"color": "rgba(255,255,255,0.70)", "width": 1}, name="Linhas de campo", hoverinfo="skip"))
            fig_q1_field_region.update_layout(title="Q1: Campo por Região (modelo 3D)", xaxis_title="X [mm]", yaxis_title="Y [mm]", height=520, shapes=shapes_ring, margin={"l": 40, "r": 20, "t": 60, "b": 40})
            fig_q1_field_region.update_xaxes(scaleanchor="y", scaleratio=1)
            plotly_chart_with_csv(fig_q1_field_region, "q1_fig_region_field", "q1_campo_por_regiao_modelo_3d.csv")

            fig_q1_loss_region = go.Figure(data=[go.Heatmap(x=region_data["region_centers_mm"], y=region_data["region_centers_mm"], z=region_data["region_loss_w"], colorscale="YlOrRd", colorbar={"title": "Perda por região [W]"}, hoverongaps=False)])
            fig_q1_loss_region.update_layout(title="Q1: Perdas por Região (modelo 3D)", xaxis_title="X [mm]", yaxis_title="Y [mm]", height=520, shapes=shapes_ring, margin={"l": 40, "r": 20, "t": 60, "b": 40})
            fig_q1_loss_region.update_xaxes(scaleanchor="y", scaleratio=1)
            plotly_chart_with_csv(fig_q1_loss_region, "q1_fig_region_loss", "q1_perdas_por_regiao_modelo_3d.csv")

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
        rows.append({
            "Material": material["name"],
            "μr": material["mu_r"],
            "σ [S/m]": f"{material['sigma']:.2e}",
            "ln(D/d)": f"{ln_ba:.4f}",
            "Perda [W]": f"{float(p_analytical):.4f}",
        })

    st.dataframe(rows, use_container_width=True, hide_index=True)

    st.caption(
        "Constantes do caso enunciado: método analítico com 1 condutor, "
        f"D={outer_d_mm:.1f} mm, d={inner_d_mm:.1f} mm, c={thickness_mm:.2f} mm, "
        f"Im={im_a:.1f} A, f={frequency_hz:.1f} Hz."
    )
