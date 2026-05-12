"""Pagina de apresentacao tecnica do projeto."""

import streamlit as st


def render_home_page() -> None:
    """Exibe pagina de apresentacao tecnica do projeto."""
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
