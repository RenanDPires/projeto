"""Pagina de apresentacao tecnica do projeto."""

import streamlit as st


def render_home_page() -> None:
    """Exibe pagina de apresentacao tecnica do projeto."""
    st.markdown(
        '<div class="main-title">Apresentação Técnica</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="subtitle">Metodos computacionais, tecnologias e bibliotecas utilizadas em EEL7216 08202 Topicos Especiais Eletron.pot.e Acion. IV</div>',
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
        - Simulação numérica na geometria com 3 furos.
        - Varreduras paramétricas em frequência e corrente para múltiplos materiais.
        - Superfícies 3D de perdas variando pares de grandezas.
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

    st.markdown("### Detalhamento Numérico e Gráfico")
    st.write(
        """
        - Formulação física predominante: regime harmônico quase-estático em eletromagnetismo.
        - EDO/PDE: não há solver genérico de EDO implementado; a Questão 2 apresenta dedução analítica
          da equação de difusão e relações constitutivas, sem integração temporal numérica.
        - Integração numérica (Q1): quadratura de Gauss-Legendre na espessura para agregação volumétrica
          de campo e perdas (atenuação exponencial no modelo de pele).
        - Discretização espacial (Q1/Q3): malhas 2D uniformes em XY para avaliação de H, J e perdas,
          com mascaramento geométrico (anéis/furos) e agregação por células regionais.
        - Integração por área (Q1/Q3): soma discreta de densidade de perdas por elemento de área
          (Riemann em malha cartesiana), convertendo W/m2 para perdas integradas em W.
        - Biot-Savart numérico (Q3): superposição vetorial de contribuições dos condutores em cada nó
          da malha, seguida de pós-processamento para mapas de campo e potência dissipada.
        - Varreduras paramétricas: geração de eixos linear/log, amostragem multi-ponto e cálculo
          repetido de métricas para curvas 2D e superfícies 3D.
        - Visualização científica: superfícies 3D, heatmaps regionais e curvas multi-traço com exportação
          de dados por trace para CSV, permitindo auditoria dos resultados.
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
