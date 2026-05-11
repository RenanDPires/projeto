"""Script para adicionar interface Q5 ao main.py"""

# Ler o arquivo main.py
with open(r"c:\Users\renan\OneDrive\Área de Trabalho\Renan\UFSC\Mauricio\projeto\app\main.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Adicionar imports se não existirem
import_block = """from app.core.electromagnetics.sheet_conductors import (
    calculate_power_loss_sheet_conductor,
    compare_conductor_geometries,
)
from app.core.exercises.q05_comparison_methods import solve_question_05_comparison"""

if "q05_comparison_methods" not in content:
    # Encontrar a linha do último import antes de "# Configuracao da pagina Streamlit"
    search_str = "from app.components.geometry_plot import plot_geometry"
    if search_str in content:
        content = content.replace(
            search_str + "\n",
            search_str + "\n" + import_block + "\n"
        )
        print("✓ Imports de Q5 adicionados")
    else:
        print("✗ Não foi possível encontrar local para adicionar imports")

# 2. Adicionar função _show_assessment_q5_tab() antes de show_assessment_01_page()
q5_function = '''
def _show_assessment_q5_tab() -> None:
    """Questao 5 da avaliacao: comparacao de metodos para resistencia AC e indutancia de fuga."""
    st.markdown("### Questão 5: Comparação de Métodos para Resistência AC e Indutância de Fuga")
    st.caption(
        "Artigo de Referência: 'Comparison of Analytical Methods for Calculating the AC Resistance "
        "and Leakage Inductance of Medium-Frequency Transformers' - Prof. Mauricio Valencia Ferreira da Luz"
    )
    st.info(
        "Implementação de três geometrias de condutores usados em transformadores de potência: "
        "Circular (Q2), Retangular (Q4), e Tipo Folha (Q5)"
    )

    tab_theory, tab_calculation, tab_comparison = st.tabs(
        ["Parte (a): Teoria", "Parte (b): Cálculo Comparativo", "Figura: Comparação"]
    )

    with tab_theory:
        st.markdown("#### Parte (a): Três Tipos de Condutores")
        
        col_t1, col_t2, col_t3 = st.columns(3)
        
        with col_t1:
            st.subheader("1. Condutor Circular")
            st.markdown("**Aplicação:** Enrolamentos tradicionais")
            st.latex(r"H_\\phi(r) = H_0 e^{-(r_{ext}-r)/\\delta}")
            st.latex(r"\\delta = \\sqrt{\\frac{2}{\\omega\\mu\\sigma}}")
            st.caption("Referência: Q2 - Equação de Difusão em Coordenadas Cilíndricas")
        
        with col_t2:
            st.subheader("2. Condutor Retangular")
            st.markdown("**Aplicação:** Transformadores de potência")
            st.markdown("**Variantes:**")
            st.markdown("- (a) Ambas superfícies: $P_a = \\frac{H_0^2}{\\sigma\\delta}\\tanh(b/\\delta)$")
            st.markdown("- (b) Semi-espaço: $P_b = \\frac{H_0^2}{\\sigma\\delta}$ [BASE]")
            st.markdown("- (c) Finito: $P_c = \\frac{H_0^2}{\\sigma\\delta}\\coth(b/\\delta)$")
            st.caption("Referência: Q4 - Del Vecchio (2010), Kulkarni (2013)")
        
        with col_t3:
            st.subheader("3. Condutor Tipo Folha")
            st.markdown("**Aplicação:** Estruturas laminadas")
            st.latex(r"H(y) = H_0 e^{-y/\\delta}")
            st.markdown("Semi-infinito: $P_{sheet} = \\frac{H_0^2}{\\sigma\\delta}$")
            st.markdown("Espessura finita:")
            st.latex(r"P_{finite} = \\frac{H_0^2}{\\sigma\\delta}\\cdot\\frac{1-e^{-2t/\\delta}}{2}")
            st.caption("Referência: Ferreira et al. - Comparison of Analytical Methods")
        
        st.divider()
        st.markdown("**Equação Fundamental (Difusão em Condutor)**")
        st.latex(r"\\nabla^2 H - \\frac{\\omega\\mu\\sigma}{2}(1-j)H = 0")
        st.markdown("**Profundidade de Penetração (Skin Depth):**")
        st.markdown("Todos os tipos compartilham: $\\delta \\propto 1/\\sqrt{f}$")

    with tab_calculation:
        st.markdown("#### Parte (b): Cálculo Numérico Comparativo")
        
        col_p1, col_p2, col_p3 = st.columns(3)
        
        with col_p1:
            st.markdown("**Geometria & Material**")
            char_dim_cm = st.number_input(
                "Dimensão característica [cm]", 
                min_value=0.1, 
                value=2.5, 
                key="q5_char_dim"
            )
            conductivity = st.number_input(
                "Condutividade σ [S/m]",
                min_value=1e5,
                value=5.8e7,
                format="%.2e",
                key="q5_sigma"
            )
        
        with col_p2:
            st.markdown("**Operação**")
            frequency = st.number_input(
                "Frequência [Hz]",
                min_value=0.1,
                value=60.0,
                key="q5_freq"
            )
            h0_field = st.number_input(
                "Campo H₀ [A/m]",
                min_value=0.1,
                value=6.0,
                key="q5_h0"
            )
        
        with col_p3:
            st.markdown("**Parâmetros Cilíndricos (Q2)**")
            outer_radius_cm = st.number_input(
                "Raio externo [cm]",
                min_value=1.0,
                value=91.0,
                key="q5_r_ext"
            )
            inner_radius_cm = st.number_input(
                "Raio interno [cm]",
                min_value=0.1,
                value=16.5,
                key="q5_r_int"
            )
        
        if st.button("Calcular Comparação Q5", type="primary", key="q5_calc"):
            try:
                result = solve_question_05_comparison(
                    frequency_hz=float(frequency),
                    surface_magnetic_field_h0_a_per_m=float(h0_field),
                    characteristic_dimension_cm=float(char_dim_cm),
                    conductivity_s_per_m=float(conductivity),
                    permeability_rel=1.0,
                    material_name="Cobre",
                    outer_radius_cm=float(outer_radius_cm),
                    inner_radius_cm=float(inner_radius_cm),
                )
                
                st.divider()
                st.markdown("### Resultados da Comparação")
                
                col_r1, col_r2, col_r3, col_r4 = st.columns(4)
                with col_r1:
                    st.metric(
                        "Profundidade δ",
                        f"{result.skin_depth_mm:.4f}",
                        "mm"
                    )
                with col_r2:
                    st.metric(
                        "Razão b/δ",
                        f"{result.dimensionless_ratio:.4f}",
                        "-"
                    )
                with col_r3:
                    st.metric(
                        "Frequência",
                        f"{result.frequency_hz:.1f}",
                        "Hz"
                    )
                with col_r4:
                    st.metric(
                        "H₀",
                        f"{result.surface_magnetic_field_a_per_m:.2f}",
                        "A/m"
                    )
                
                st.divider()
                st.markdown("### Perdas [W/m²] - Comparação dos 3 Tipos")
                
                loss_data = {
                    "Tipo de Condutor": [
                        "Circular",
                        "Retangular (a) - Simétrico",
                        "Retangular (b) - Semi-infinito [BASE]",
                        "Retangular (c) - Finito",
                        "Folha - Semi-infinito",
                        "Folha - Espessura Finita"
                    ],
                    "Perda [W/m²]": [
                        f"{result.circular_conductor_loss_w_per_m2:.4e}",
                        f"{result.rectangular_variant_a_loss_w_per_m2:.4e}",
                        f"{result.rectangular_variant_b_loss_w_per_m2:.4e}",
                        f"{result.rectangular_variant_c_loss_w_per_m2:.4e}",
                        f"{result.sheet_semi_infinite_loss_w_per_m2:.4e}",
                        f"{result.sheet_finite_loss_w_per_m2:.4e}",
                    ],
                    "Relativo a Rect(b)": [
                        f"{result.ratio_circular_to_rect_b:.4f}×",
                        f"{result.ratio_rect_a_to_b:.4f}×",
                        "1.0000×",
                        f"{result.ratio_rect_c_to_b:.4f}×",
                        f"{result.ratio_sheet_semi_to_rect_b:.4f}×",
                        f"{result.ratio_sheet_finite_to_rect_b:.4f}×",
                    ]
                }
                
                df_losses = __import__("pandas").DataFrame(loss_data)
                st.dataframe(df_losses, use_container_width=True)
                
                st.divider()
                st.markdown("### Densidade de Corrente Máxima [A/m²]")
                
                j_data = {
                    "Tipo": ["Circular", "Retangular (a)", "Folha"],
                    "J_max [A/m²]": [
                        f"{result.max_current_density_circular_a_per_m2:.4e}",
                        f"{result.max_current_density_rectangular_a_per_m2:.4e}",
                        f"{result.max_current_density_sheet_a_per_m2:.4e}",
                    ]
                }
                df_j = __import__("pandas").DataFrame(j_data)
                st.dataframe(df_j, use_container_width=True)
                
                st.divider()
                st.markdown("### Interpretação Física")
                st.info(result.notes)
                
            except Exception as e:
                st.error(f"Erro no cálculo: {str(e)}")

    with tab_comparison:
        st.markdown("#### Figura: Visualização Comparativa")
        st.info("Tabelas comparativas gerando...")
        
        try:
            # Usar dados padrão para visualização
            comparison = compare_conductor_geometries(
                surface_magnetic_field_h0_a_per_m=6.0,
                conductivity_s_per_m=5.8e7,
                frequency_hz=60,
                characteristic_dimension_m=0.025,
            )
            
            # Criar tabela de comparação
            comp_data = {
                "Geometria": [
                    comparison["rectangular_symmetric"]["type"],
                    comparison["sheet_semi_infinite"]["type"],
                    comparison["sheet_finite"]["type"],
                ],
                "Perda [W/m²]": [
                    f"{comparison['rectangular_symmetric']['power_loss_w_per_m2']:.4e}",
                    f"{comparison['sheet_semi_infinite']['power_loss_w_per_m2']:.4e}",
                    f"{comparison['sheet_finite']['power_loss_w_per_m2']:.4e}",
                ],
                "Fator": [
                    f"{comparison['rectangular_symmetric']['factor']:.6f}",
                    f"{comparison['sheet_semi_infinite']['factor']:.6f}",
                    f"{comparison['sheet_finite']['factor']:.6f}",
                ],
                "Relativo": [
                    f"{comparison['rectangular_symmetric']['relative_to_baseline']:.4f}×",
                    f"{comparison['sheet_semi_infinite']['relative_to_baseline']:.4f}×",
                    f"{comparison['sheet_finite']['relative_to_baseline']:.4f}×",
                ]
            }
            
            df_comp = __import__("pandas").DataFrame(comp_data)
            st.dataframe(df_comp, use_container_width=True)
            
            st.markdown("**Condições:** H₀=6.0 A/m, σ=5.8e7 S/m, b=2.5cm, f=60Hz, δ=8.53mm")
            
        except Exception as e:
            st.warning(f"Não foi possível gerar figuras: {str(e)}")

'''

search_str = "def show_assessment_01_page() -> None:"
if search_str in content:
    content = content.replace(
        search_str,
        q5_function + "\n\n" + search_str
    )
    print("✓ Função _show_assessment_q5_tab() adicionada")
else:
    print("✗ Não foi possível encontrar show_assessment_01_page()")

# 3. Substituir chamada a _show_placeholder_question_card() por _show_assessment_q5_tab()
old_q5_call = '''    with tab_q5:
        _show_placeholder_question_card(
            "Questão 5: comparação de métodos para resistência AC e indutância de fuga",
            "Próximo passo: incorporar modelos para condutores circulares, retangulares e tipo folha "
            "a partir do artigo de referência.",
        )'''

new_q5_call = '''    with tab_q5:
        _show_assessment_q5_tab()'''

if old_q5_call in content:
    content = content.replace(old_q5_call, new_q5_call)
    print("✓ Chamada de Q5 substitui placeholder")
else:
    print("✗ Não foi possível substituir chamada de Q5")

# Salvar arquivo atualizado
with open(r"c:\Users\renan\OneDrive\Área de Trabalho\Renan\UFSC\Mauricio\projeto\app\main.py", "w", encoding="utf-8") as f:
    f.write(content)

print("✓ Arquivo main.py atualizado com sucesso!")
