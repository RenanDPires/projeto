"""Geometrias e coordenadas para Questão 4 - Condutores Retangulares de Cobre

Este arquivo contém as descrições das três variantes de condutores retangulares
e suas respectivas geometrias e coordenadas.
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_q4_geometry_figure():
    """Cria figura mostrando as 3 variantes de condutores retangulares."""
    
    # Parâmetros
    b_cm = 2.5  # half-width em cm
    b_m = b_cm / 100  # em metros
    delta_mm = 27.023  # skin depth em mm
    delta_m = delta_mm / 1000  # em metros
    
    # Criar subplots (3 variantes lado a lado)
    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=(
            "Variante (a): Campo em ambas as superfícies",
            "Variante (b): Campo em uma superfície",
            "Variante (c): Ambas as superfícies limitadas"
        ),
        specs=[[{"type": "xy"}, {"type": "xy"}, {"type": "xy"}]],
        horizontal_spacing=0.12
    )
    
    # ─────────────────────────────────────────────────────────────────────────
    # VARIANTE (a): cosh(y/δ)
    # ─────────────────────────────────────────────────────────────────────────
    y_a = np.linspace(-4*delta_m, 4*delta_m, 200)
    h_a = np.cosh(y_a / delta_m)
    
    fig.add_trace(
        go.Scatter(
            x=h_a, y=y_a*1e3,
            mode='lines',
            line=dict(color='#FF6B6B', width=3),
            name='H_z(a) = H₀·cosh(y/δ)',
            showlegend=False
        ),
        row=1, col=1
    )
    
    # Adicionar geometria do condutor
    fig.add_shape(
        type="rect",
        x0=0, x1=max(h_a), y0=-b_cm*10, y1=b_cm*10,
        line=dict(color="black", width=2),
        fillcolor="lightgray",
        opacity=0.3,
        row=1, col=1
    )
    
    # Anotações para variante (a)
    fig.add_annotation(
        x=max(h_a)*0.7, y=b_cm*10 + 5,
        text=f"Largura: 2b = {2*b_cm:.1f} cm<br>δ = {delta_mm:.1f} mm",
        showarrow=False,
        bgcolor="yellow",
        opacity=0.8,
        row=1, col=1
    )
    
    fig.add_annotation(
        x=max(h_a)*0.7, y=-b_cm*10 - 5,
        text="H₀ = 6.0 A/m (ambas)",
        showarrow=False,
        bgcolor="lightblue",
        opacity=0.8,
        row=1, col=1
    )
    
    # ─────────────────────────────────────────────────────────────────────────
    # VARIANTE (b): exp(-y/δ) - semi-espaço
    # ─────────────────────────────────────────────────────────────────────────
    y_b = np.linspace(0, 6*delta_m, 200)
    h_b = np.exp(-y_b / delta_m)
    
    fig.add_trace(
        go.Scatter(
            x=h_b, y=y_b*1e3,
            mode='lines',
            line=dict(color='#4ECDC4', width=3),
            name='H_z(b) = H₀·exp(-y/δ)',
            showlegend=False
        ),
        row=1, col=2
    )
    
    # Geometria: semi-espaço
    fig.add_shape(
        type="rect",
        x0=0, x1=max(h_b), y0=0, y1=6*delta_m*1e3,
        line=dict(color="black", width=2),
        fillcolor="lightgray",
        opacity=0.3,
        row=1, col=2
    )
    
    # Linha de contorno (superfície)
    fig.add_shape(
        type="line",
        x0=0, x1=max(h_b), y0=0, y1=0,
        line=dict(color="red", width=3),
        row=1, col=2
    )
    
    fig.add_annotation(
        x=max(h_b)*0.7, y=2*delta_m*1e3,
        text=f"Semi-espaço<br>δ = {delta_mm:.1f} mm<br>H₀ na superfície",
        showarrow=False,
        bgcolor="lightblue",
        opacity=0.8,
        row=1, col=2
    )
    
    # ─────────────────────────────────────────────────────────────────────────
    # VARIANTE (c): sinh((b-y)/δ)/sinh(b/δ) - espaço finito
    # ─────────────────────────────────────────────────────────────────────────
    y_c = np.linspace(0, b_m, 200)
    b_over_delta = b_m / delta_m
    h_c = np.sinh((b_m - y_c) / delta_m) / np.sinh(b_over_delta)
    
    fig.add_trace(
        go.Scatter(
            x=h_c, y=y_c*1e3,
            mode='lines',
            line=dict(color='#95E1D3', width=3),
            name=f'H_z(c) = H₀·sinh((b-y)/δ)/sinh(b/δ)',
            showlegend=False
        ),
        row=1, col=3
    )
    
    # Geometria: espaço finito (sanduíche)
    fig.add_shape(
        type="rect",
        x0=0, x1=max(h_c), y0=0, y1=b_m*1e3,
        line=dict(color="black", width=2),
        fillcolor="lightgray",
        opacity=0.3,
        row=1, col=3
    )
    
    # Linhas de contorno (duas superfícies)
    fig.add_shape(
        type="line",
        x0=0, x1=max(h_c), y0=0, y1=0,
        line=dict(color="red", width=3),
        row=1, col=3
    )
    fig.add_shape(
        type="line",
        x0=0, x1=max(h_c), y0=b_m*1e3, y1=b_m*1e3,
        line=dict(color="blue", width=3),
        row=1, col=3
    )
    
    fig.add_annotation(
        x=max(h_c)*0.7, y=b_m*1e3/2,
        text=f"Espaço finito (b={b_cm} cm)<br>δ = {delta_mm:.1f} mm<br>H₀(0) lado esq.",
        showarrow=False,
        bgcolor="lightblue",
        opacity=0.8,
        row=1, col=3
    )
    
    # Atualizar eixos
    fig.update_xaxes(title_text="Magnitude H_z [A/m]", row=1, col=1)
    fig.update_xaxes(title_text="Magnitude H_z [A/m]", row=1, col=2)
    fig.update_xaxes(title_text="Magnitude H_z [A/m]", row=1, col=3)
    
    fig.update_yaxes(title_text="Profundidade y [mm]", row=1, col=1)
    fig.update_yaxes(title_text="Profundidade y [mm]", row=1, col=2)
    fig.update_yaxes(title_text="Profundidade y [mm]", row=1, col=3)
    
    fig.update_layout(
        title_text="<b>QUESTÃO 4 - Figura 3: Três Variantes de Condutores Retangulares de Cobre</b>",
        height=500,
        showlegend=True,
    )
    
    return fig


def create_q4_power_loss_comparison():
    """Cria tabela comparativa de perdas para as 3 variantes."""
    
    # Dados
    H0 = 6.0  # A/m
    sigma = 5.8e7  # S/m (cobre)
    b_cm = 2.5  # cm
    b_m = b_cm / 100  # m
    f = 60  # Hz
    mu = 4 * np.pi * 1e-7  # H/m
    omega = 2 * np.pi * f
    
    # Profundidade de penetração
    delta_m = np.sqrt(2 / (omega * mu * sigma))
    delta_mm = delta_m * 1e3
    
    # Variante (a): ambas as superfícies
    # P_a = H₀² · (1/σδ) · tanh(b/δ)
    tanh_term = np.tanh(b_m / delta_m)
    p_a_w_m2 = (H0**2) * (1 / (sigma * delta_m)) * tanh_term
    
    # Variante (b): semi-espaço
    # P_b = H₀² / (σδ)
    p_b_w_m2 = (H0**2) / (sigma * delta_m)
    
    # Variante (c): espaço finito
    # P_c ≈ H₀² · (1/σδ) · [1/tanh(b/δ)]
    p_c_w_m2 = (H0**2) * (1 / (sigma * delta_m)) / tanh_term if tanh_term != 0 else 0
    
    # Criar tabela
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=[
                '<b>Variante</b>',
                '<b>Descrição</b>',
                '<b>Fórmula de Perdas</b>',
                '<b>Perdas (W/m²)</b>',
                '<b>Fator Relativo</b>'
            ],
            fill_color='paleturquoise',
            align='left',
            font=dict(size=11, color='black')
        ),
        cells=dict(
            values=[
                ['(a)', '(b)', '(c)'],
                [
                    'Campo em ambas<br/>superfícies',
                    'Campo em uma<br/>superfície',
                    'Espaço finito<br/>(sanduíche)'
                ],
                [
                    'H₀²/(σδ) · tanh(b/δ)',
                    'H₀²/(σδ)',
                    'H₀²/(σδ) · 1/tanh(b/δ)'
                ],
                [
                    f'{p_a_w_m2:.4e}',
                    f'{p_b_w_m2:.4e}',
                    f'{p_c_w_m2:.4e}'
                ],
                [
                    f'{p_a_w_m2/p_b_w_m2:.4f}',
                    '1.0000',
                    f'{p_c_w_m2/p_b_w_m2:.4f}'
                ]
            ],
            fill_color='lavender',
            align='left',
            font=dict(size=10)
        )
    )])
    
    fig.update_layout(
        title_text=f'<b>Comparação de Perdas Superficiais - Variantes (a), (b), (c)</b><br>' +
                   f'H₀ = {H0} A/m | σ = {sigma:.2e} S/m | b = {b_cm} cm | f = {f} Hz | δ = {delta_mm:.3f} mm',
        height=300
    )
    
    return fig, {
        'delta_m': delta_m,
        'delta_mm': delta_mm,
        'p_a': p_a_w_m2,
        'p_b': p_b_w_m2,
        'p_c': p_c_w_m2,
        'tanh_ratio': tanh_term
    }


if __name__ == "__main__":
    # Gerar figuras
    fig_geom = create_q4_geometry_figure()
    fig_table, results = create_q4_power_loss_comparison()
    
    print("✓ Figuras geradas com sucesso!")
    print(f"\nResultados numéricos:")
    print(f"  Profundidade de penetração δ = {results['delta_mm']:.3f} mm")
    print(f"  Variante (a): P_a = {results['p_a']:.4e} W/m²")
    print(f"  Variante (b): P_b = {results['p_b']:.4e} W/m²")
    print(f"  Variante (c): P_c = {results['p_c']:.4e} W/m²")
    print(f"  Razão tanh(b/δ) = {results['tanh_ratio']:.4f}")
