"""Visualizacao de geometria com Plotly.

Cria graficos 2D interativos da placa, furos e condutores.
"""

import numpy as np
import plotly.graph_objects as go
from app.core.geometry.plate import Plate


def plot_geometry(plate: Plate, conductor_positions: np.ndarray = None) -> go.Figure:
    """Cria figura interativa da geometria da placa.

    Args:
        plate: Objeto Plate com furos
        conductor_positions: Array (n_condutores, 2) com posicoes [m]

    Returns:
        Objeto Figure do Plotly
    """
    fig = go.Figure()

    # Converte para mm para exibicao
    scale = 1000

    # Desenha contorno da placa
    plate_x = [0, plate.width_m * scale, plate.width_m * scale, 0, 0]
    plate_y = [0, 0, plate.height_m * scale, plate.height_m * scale, 0]

    fig.add_trace(
        go.Scatter(
            x=plate_x,
            y=plate_y,
            mode="lines",
            name="Tanque",
            line=dict(color="black", width=2),
            hoverinfo="text",
            text="Tanque",
        )
    )

    # Desenha furos
    for i, (center, radius) in enumerate(
        zip(plate.hole_centers, plate.hole_radii)
    ):
        theta = np.linspace(0, 2 * np.pi, 100)
        hole_x = (center[0] + radius * np.cos(theta)) * scale
        hole_y = (center[1] + radius * np.sin(theta)) * scale

        fig.add_trace(
            go.Scatter(
                x=hole_x,
                y=hole_y,
                mode="lines",
                name=f"Furo {i + 1}",
                line=dict(color="red", width=1),
                hovertemplate=f"Furo {i + 1}<br>Centro: ({center[0]*scale:.1f}, {center[1]*scale:.1f}) mm<br>Raio: {radius*scale:.1f} mm<extra></extra>",
            )
        )

    # Desenha condutores quando fornecidos
    if conductor_positions is not None:
        for i, pos in enumerate(conductor_positions):
            fig.add_trace(
                go.Scatter(
                    x=[pos[0] * scale],
                    y=[pos[1] * scale],
                    mode="markers+text",
                    name=f"Condutor {i + 1}",
                    marker=dict(size=10, color="blue", symbol="x"),
                    text=[f"C{i+1}"],
                    textposition="top center",
                    hovertemplate=f"Condutor {i + 1}<br>Posicao: ({pos[0]*scale:.1f}, {pos[1]*scale:.1f}) mm<extra></extra>",
                )
            )

    # Atualiza layout
    fig.update_layout(
        title="Geometria da Placa - vista superior",
        xaxis_title="X [mm]",
        yaxis_title="Y [mm]",
        hovermode="closest",
        height=500,
        template="plotly_white",
        showlegend=True,
        xaxis=dict(scaleanchor="y", scaleratio=1),
        yaxis=dict(scaleanchor="x", scaleratio=1),
    )

    fig.update_xaxes(zeroline=True, zerolinewidth=1, zerolinecolor="gray")
    fig.update_yaxes(zeroline=True, zerolinewidth=1, zerolinecolor="gray")

    return fig


def plot_field_heatmap(X: np.ndarray, Y: np.ndarray, field: np.ndarray, title: str = "Magnitude de Campo") -> go.Figure:
    """Cria mapa de calor de um campo 2D.

    Args:
        X: Array de coordenadas X [m]
        Y: Array de coordenadas Y [m]
        field: Array 2D de campo
        title: Titulo do grafico

    Returns:
        Objeto Figure do Plotly
    """
    fig = go.Figure(
        data=go.Heatmap(
            z=field,
            x=X[0, :] * 1000,  # Converte para mm
            y=Y[:, 0] * 1000,  # Converte para mm
            colorscale="Viridis",
            colorbar=dict(title="Magnitude"),
        )
    )

    fig.update_layout(
        title=title,
        xaxis_title="X [mm]",
        yaxis_title="Y [mm]",
        height=500,
        template="plotly_white",
    )

    return fig


def plot_field_and_geometry(
    X: np.ndarray,
    Y: np.ndarray,
    field: np.ndarray,
    plate: Plate,
    conductor_positions: np.ndarray = None,
    title: str = "Field with Geometry",
) -> go.Figure:
    """Cria figura combinando mapa de calor do campo e sobreposicao da geometria.

    Args:
        X: Array de coordenadas X [m]
        Y: Array de coordenadas Y [m]
        field: Array 2D de campo
        plate: Geometria da placa
        conductor_positions: Posicoes dos condutores [m]
        title: Titulo do grafico

    Returns:
        Objeto Figure do Plotly
    """
    scale = 1000  # para mm

    fig = go.Figure(
        data=go.Heatmap(
            z=field,
            x=X[0, :] * scale,
            y=Y[:, 0] * scale,
            colorscale="Viridis",
            colorbar=dict(title="Magnitude"),
            name="Field",
        )
    )

    # Adiciona contorno da placa
    plate_x = [0, plate.width_m * scale, plate.width_m * scale, 0, 0]
    plate_y = [0, 0, plate.height_m * scale, plate.height_m * scale, 0]

    fig.add_trace(
        go.Scatter(
            x=plate_x,
            y=plate_y,
            mode="lines",
            name="Plate",
            line=dict(color="white", width=2),
        )
    )

    # Adiciona furos
    for i, (center, radius) in enumerate(
        zip(plate.hole_centers, plate.hole_radii)
    ):
        theta = np.linspace(0, 2 * np.pi, 50)
        hole_x = (center[0] + radius * np.cos(theta)) * scale
        hole_y = (center[1] + radius * np.sin(theta)) * scale

        fig.add_trace(
            go.Scatter(
                x=hole_x,
                y=hole_y,
                mode="lines",
                name=f"Hole {i + 1}",
                line=dict(color="white", width=1),
            )
        )

    # Adiciona condutores
    if conductor_positions is not None:
        for i, pos in enumerate(conductor_positions):
            fig.add_trace(
                go.Scatter(
                    x=[pos[0] * scale],
                    y=[pos[1] * scale],
                    mode="markers+text",
                    name=f"Conductor {i + 1}",
                    marker=dict(size=8, color="red", symbol="x"),
                    text=[f"C{i+1}"],
                    textposition="top center",
                )
            )

    fig.update_layout(
        title=title,
        xaxis_title="X [mm]",
        yaxis_title="Y [mm]",
        height=600,
        template="plotly_white",
        showlegend=True,
    )

    return fig


def _h_vector_from_line_currents_2d(
    x_m: float,
    y_m: float,
    conductor_positions: np.ndarray,
    conductor_currents: np.ndarray,
) -> tuple[float, float]:
    """Calcula vetor H no plano a partir de correntes retas no eixo z.

    Usa a direcao de Biot-Savart para condutores longos:
    H = I/(2*pi*r) * phi_hat, evaluated in Cartesian components.
    """
    hx = 0.0
    hy = 0.0

    for pos, current in zip(conductor_positions, conductor_currents):
        dx = x_m - float(pos[0])
        dy = y_m - float(pos[1])
        r2 = dx * dx + dy * dy + 1e-14

        coeff = float(current) / (2.0 * np.pi * r2)
        hx += -coeff * dy
        hy += coeff * dx

    return hx, hy


def _trace_field_line_bidirectional(
    seed_x_m: float,
    seed_y_m: float,
    z_m: float,
    conductor_positions: np.ndarray,
    conductor_currents: np.ndarray,
    step_m: float,
    n_steps: int,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Integra uma linha de campo nos dois sentidos tangenciais para continuidade."""

    def _walk(direction: float) -> list[tuple[float, float, float]]:
        x = seed_x_m
        y = seed_y_m
        pts = [(x, y, z_m)]

        for _ in range(n_steps):
            hx, hy = _h_vector_from_line_currents_2d(
                x,
                y,
                conductor_positions,
                conductor_currents,
            )
            mag = float(np.hypot(hx, hy))
            if mag < 1e-12:
                break

            ux = hx / mag
            uy = hy / mag
            x = x + direction * step_m * ux
            y = y + direction * step_m * uy

            if x < x_min or x > x_max or y < y_min or y > y_max:
                break

            pts.append((x, y, z_m))

        return pts

    fw = _walk(+1.0)
    bw = _walk(-1.0)

    bw_rev = list(reversed(bw))
    if bw_rev:
        bw_rev = bw_rev[:-1]

    line = bw_rev + fw

    xs = np.array([p[0] for p in line], dtype=float)
    ys = np.array([p[1] for p in line], dtype=float)
    zs = np.array([p[2] for p in line], dtype=float)
    return xs, ys, zs


def plot_field_lines_3d(
    plate: Plate,
    conductor_positions: np.ndarray,
    conductor_currents: np.ndarray,
    title: str = "Linhas de campo magnetico 3D (Biot-Savart)",
    n_seed_per_conductor: int = 14,
    n_rings: int = 3,
    n_steps: int = 220,
) -> go.Figure:
    """Cria visualizacao 3D interativa com linhas de campo em torno de condutores e placa.

    Observacao do modelo fisico:
    - Conductors are approximated as long straight wires along z.
    - Field lines are tangent to H vector from Biot-Savart superposition.
    """
    scale = 1000.0

    fig = go.Figure()

    z_half = max(plate.thickness_m * 0.5, min(plate.width_m, plate.height_m) * 0.01)
    z_bottom = -z_half
    z_top = z_half

    # Superficies superior e inferior da placa
    surf_x = np.array([[0.0, plate.width_m], [0.0, plate.width_m]], dtype=float) * scale
    surf_y = np.array([[0.0, 0.0], [plate.height_m, plate.height_m]], dtype=float) * scale
    surf_z_top = np.full((2, 2), z_top * scale)
    surf_z_bottom = np.full((2, 2), z_bottom * scale)

    fig.add_trace(
        go.Surface(
            x=surf_x,
            y=surf_y,
            z=surf_z_top,
            showscale=False,
            opacity=0.28,
            colorscale=[[0, "#7f8c8d"], [1, "#7f8c8d"]],
            name="Tampa (face superior)",
        )
    )
    fig.add_trace(
        go.Surface(
            x=surf_x,
            y=surf_y,
            z=surf_z_bottom,
            showscale=False,
            opacity=0.18,
            colorscale=[[0, "#95a5a6"], [1, "#95a5a6"]],
            name="Tampa (face inferior)",
        )
    )

    # Contornos dos furos na face superior e inferior
    for i, (center, radius) in enumerate(zip(plate.hole_centers, plate.hole_radii)):
        theta = np.linspace(0, 2 * np.pi, 80)
        hx = (center[0] + radius * np.cos(theta)) * scale
        hy = (center[1] + radius * np.sin(theta)) * scale
        fig.add_trace(
            go.Scatter3d(
                x=hx,
                y=hy,
                z=np.full_like(hx, z_top * scale),
                mode="lines",
                line=dict(color="#e74c3c", width=4),
                name=f"Furo {i + 1} (topo)",
                showlegend=(i == 0),
            )
        )
        fig.add_trace(
            go.Scatter3d(
                x=hx,
                y=hy,
                z=np.full_like(hx, z_bottom * scale),
                mode="lines",
                line=dict(color="#c0392b", width=3),
                name=f"Furo {i + 1} (base)",
                showlegend=False,
            )
        )

    # Conductors as vertical segments
    for i, (pos, current) in enumerate(zip(conductor_positions, conductor_currents)):
        color = "#1f77b4" if current >= 0 else "#d62728"
        fig.add_trace(
            go.Scatter3d(
                x=[pos[0] * scale, pos[0] * scale],
                y=[pos[1] * scale, pos[1] * scale],
                z=[(z_bottom * 2.0) * scale, (z_top * 2.0) * scale],
                mode="lines+markers",
                line=dict(color=color, width=8),
                marker=dict(size=3, color=color),
                name=f"C{i + 1} ({current:.0f} A)",
            )
        )

    # Field lines: several z slices to give 3D volume perception
    extent = max(plate.width_m, plate.height_m)
    margin = 0.15 * extent
    x_min = -margin
    x_max = plate.width_m + margin
    y_min = -margin
    y_max = plate.height_m + margin

    z_levels = np.array([z_bottom, 0.0, z_top], dtype=float)
    min_size = min(plate.width_m, plate.height_m)
    ring_radii = np.linspace(0.04 * min_size, 0.16 * min_size, n_rings)
    step_m = 0.006 * min_size

    for pos in conductor_positions:
        for z_level in z_levels:
            for radius in ring_radii:
                for ang in np.linspace(0.0, 2 * np.pi, n_seed_per_conductor, endpoint=False):
                    sx = float(pos[0] + radius * np.cos(ang))
                    sy = float(pos[1] + radius * np.sin(ang))

                    xs, ys, zs = _trace_field_line_bidirectional(
                        sx,
                        sy,
                        float(z_level),
                        conductor_positions,
                        conductor_currents,
                        step_m,
                        n_steps,
                        x_min,
                        x_max,
                        y_min,
                        y_max,
                    )

                    if xs.size < 8:
                        continue

                    fig.add_trace(
                        go.Scatter3d(
                            x=xs * scale,
                            y=ys * scale,
                            z=zs * scale,
                            mode="lines",
                            line=dict(color="#f39c12", width=2),
                            name="Linha de campo",
                            showlegend=False,
                            hoverinfo="skip",
                        )
                    )

    fig.update_layout(
        title=title,
        template="plotly_white",
        height=760,
        showlegend=True,
        legend=dict(itemsizing="constant"),
        scene=dict(
            xaxis_title="X [mm]",
            yaxis_title="Y [mm]",
            zaxis_title="Z [mm]",
            aspectmode="data",
            camera=dict(eye=dict(x=1.65, y=1.45, z=0.8)),
        ),
    )

    return fig
