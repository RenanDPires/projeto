"""Renderizacao da Questao 5 (comparacao de metodos analiticos)."""

from __future__ import annotations

from typing import Callable

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from app.schemas import get_material_presets


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
    """Extrai uma grandeza escalar da saida da Q5 para graficos de varredura."""
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


def render_q5_tab(
    plotly_chart_with_csv: Callable[[go.Figure, str, str], None],
    build_sweep_axis: Callable[[float, float, int, bool], np.ndarray],
    apply_log_x_axis: Callable[[list[go.Figure], bool], None],
) -> None:
    """Renderiza a aba completa da Questao 5."""
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
                key="q5_char_dim",
            )

        with col_c2:
            st.markdown("**Material: Cobre**")
            conductivity = st.number_input(
                "Condutividade σ [S/m]",
                min_value=1e6,
                value=5.8e7,
                format="%.2e",
                key="q5_sigma",
            )

        with col_c3:
            st.markdown("**Operação**")
            frequency = st.number_input(
                "Frequência [Hz]",
                min_value=1.0,
                value=60.0,
                key="q5_freq",
            )

        col_c4, col_c5 = st.columns(2)

        with col_c4:
            st.markdown("**Campo Magnético**")
            h0_field = st.number_input(
                "Campo H₀ [A/m]",
                min_value=0.1,
                value=6.0,
                key="q5_h0",
            )

        with col_c5:
            st.markdown("**Permeabilidade Relativa**")
            mu_rel = st.number_input(
                "μᵣ (unitless)",
                min_value=1.0,
                value=1.0,
                key="q5_mu_r",
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
                    material_name="Cobre",
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
                    "Sheet Finito",
                ],
                "Perda [W/m²]": [
                    result.circular_conductor_loss_w_per_m2,
                    result.rectangular_variant_a_loss_w_per_m2,
                    result.rectangular_variant_b_loss_w_per_m2,
                    result.rectangular_variant_c_loss_w_per_m2,
                    result.sheet_semi_infinite_loss_w_per_m2,
                    result.sheet_finite_loss_w_per_m2,
                ],
                "Relativo a Rect(b)": [
                    result.ratio_circular_to_rect_b,
                    result.ratio_rect_a_to_b,
                    1.0,
                    result.ratio_rect_c_to_b,
                    result.ratio_sheet_semi_to_rect_b,
                    result.ratio_sheet_finite_to_rect_b,
                ],
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

                    x_freq = build_sweep_axis(freq_min, freq_max, n_points, log_scale_x)
                    x_current = build_sweep_axis(i_min, i_max, n_points, log_scale_x)

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
                    apply_log_x_axis([fig_freq, fig_current], log_scale_x)

                    plotly_chart_with_csv(fig_freq, "q5_fig_freq", "q5_varredura_frequencia.csv")
                    plotly_chart_with_csv(fig_current, "q5_fig_current", "q5_varredura_corrente.csv")

        else:
            st.info("Execute o cálculo na aba 'Cálculo Comparativo' para ver os resultados.")
