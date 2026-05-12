"""Renderizacao da Questao 4 (condutores retangulares)."""

from __future__ import annotations

from typing import Callable

import plotly.graph_objects as go
import streamlit as st

from app.core.exercises.q04_rectangular_conductors import solve_question_04_rectangular_conductors
from app.core.electromagnetics.rectangular_conductors import (
    create_q4_geometry_figure,
    create_q4_power_loss_comparison,
)


def render_q4_tab(plotly_chart_with_csv: Callable[[go.Figure, str, str], None]) -> None:
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
                key="q4_sigma",
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
                result = solve_question_04_rectangular_conductors(
                    half_width_b_cm=float(half_width_b_cm),
                    surface_magnetic_field_h0_a_per_m=float(h0_field),
                    conductivity_s_per_m=float(conductivity),
                    frequency_hz=float(frequency),
                    permeability_rel=1.0,
                )

                st.divider()
                st.markdown("### Resultados")

                col_r1, col_r2, col_r3, col_r4 = st.columns(4)
                with col_r1:
                    st.metric(
                        "Profundidade δ",
                        f"{result.skin_depth_mm:.4f}",
                        "mm",
                    )
                with col_r2:
                    st.metric(
                        "Frequência angular ω",
                        f"{result.omega_rad_s:.2f}",
                        "rad/s",
                    )
                with col_r3:
                    st.metric(
                        "Razão b/δ",
                        f"{result.skin_depth_ratio_b_over_delta:.4f}",
                        "",
                    )
                with col_r4:
                    st.metric(
                        "Fator tanh(b/δ)",
                        f"{result.variant_a_hyperbolic_factor:.6f}",
                        "",
                    )

                st.divider()
                st.markdown("**Densidade Superficial de Perdas [W/m²]**")

                table_data = {
                    "Variante": ["(a) Campo em ambas", "(b) Campo em uma", "(c) Espaço finito"],
                    "Fórmula": [
                        "H₀²/(σδ) · tanh(b/δ)",
                        "H₀²/(σδ)",
                        "H₀²/(σδ) · coth(b/δ)",
                    ],
                    "Perdas [W/m²]": [
                        f"{result.variant_a_power_loss_w_per_m2:.6e}",
                        f"{result.variant_b_power_loss_w_per_m2:.6e}",
                        f"{result.variant_c_power_loss_w_per_m2:.6e}",
                    ],
                    "Relativo a (b)": [
                        f"{result.power_loss_ratio_a_to_b:.6f}",
                        "1.0000",
                        f"{result.power_loss_ratio_c_to_b:.6f}",
                    ],
                }

                st.dataframe(table_data, use_container_width=True, hide_index=True)

                st.divider()
                st.markdown("**Densidade de Corrente Induzida Máxima [A/m²]**")

                col_j1, col_j2, col_j3 = st.columns(3)
                with col_j1:
                    st.metric("J_max (a)", f"{result.max_current_density_var_a_a_per_m2:.4e}", "A/m²")
                with col_j2:
                    st.metric("J_max (b)", f"{result.max_current_density_var_b_a_per_m2:.4e}", "A/m²")
                with col_j3:
                    st.metric("J_max (c)", f"{result.max_current_density_var_c_a_per_m2:.4e}", "A/m²")

                st.divider()
                st.markdown("**Notas Físicas**")
                for note in result.notes:
                    st.caption(f"• {note}")

            except Exception as e:
                st.error(f"Erro no cálculo: {str(e)}")

    with tab_figures:
        st.markdown("#### Figura 3: Geometrias das Três Variantes")
        st.info("Visualizações das geometrias e perfis de campo magnético para cada variante.")

        try:
            fig_geometry = create_q4_geometry_figure()
            fig_table, _ = create_q4_power_loss_comparison()

            plotly_chart_with_csv(fig_geometry, "q4_fig_geometry", "q4_geometrias.csv")
            plotly_chart_with_csv(fig_table, "q4_fig_table", "q4_comparacao_perdas.csv")

        except Exception as e:
            st.warning(f"Não foi possível gerar as figuras: {str(e)}")
