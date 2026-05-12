"""Renderizacao da Questao 2 (deducao teorica)."""

import streamlit as st


def render_q2_tab() -> None:
    """Questao 2 da avaliacao: deducao teorica em coordenadas cilindricas."""
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

        st.markdown("**3) Componente azimutal dominante $H_\\varphi(r)$ em coordenadas cilíndricas:**")
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
            "da tampa ($a \\le r \\le b$)."
        )

        st.markdown("**5) Aproximação de pele local (quando $\\delta \\ll b$):**")
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

        st.markdown("Com a solução difusiva na espessura do metal:")
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
            "Para a tampa anular ($a \\le r \\le b$, $0 \\le z \\le c$, $0 \\le \\varphi \\le 2\\pi$), "
            "as perdas totais são:"
        )
        st.latex(
            r"P_{tot} = \int_0^{2\pi}\int_a^b\int_0^c \frac{|J_r(r,z)|^2}{\sigma}\,r\,dz\,dr\,d\varphi"
        )
        st.latex(r"P_{tot} = \frac{2\pi}{\sigma}\int_a^b r\left[\int_0^c |J_r(r,z)|^2dz\right]dr")

        st.markdown("Substituindo $J_r(r,z)=J_r(r,0)e^{-(1+j)z/\\delta}$:")
        st.latex(r"|J_r(r,z)|^2 = |J_r(r,0)|^2e^{-2z/\delta}")
        st.latex(r"\int_0^c e^{-2z/\delta}dz = \frac{\delta}{2}\left(1-e^{-2c/\delta}\right)")

        st.markdown("Logo, a expressão deduzida para perdas totais fica:")
        st.latex(
            r"P_{tot} = \frac{\pi\delta}{\sigma}\left(1-e^{-2c/\delta}\right)\int_a^b r\,|J_r(r,0)|^2dr"
        )

        st.markdown("Usando $J_r=(1+j)H_\\varphi/\\delta$, forma equivalente em $H_\\varphi$:")
        st.latex(
            r"P_{tot} = \frac{2\pi}{\sigma\delta^2}\int_a^b\int_0^c r\,|H_\varphi(r,z)|^2\,dz\,dr"
        )

        st.warning("Não há parâmetros de entrada nem cálculo numérico nesta aba.")
