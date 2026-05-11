"""Script para gerar as visualizações finais de Q4."""

from app.core.electromagnetics.rectangular_conductors import (
    create_q4_geometry_figure,
    create_q4_power_loss_comparison
)

# Gerar figuras
fig_geom = create_q4_geometry_figure()
fig_table, results = create_q4_power_loss_comparison()

# Salvar
project_path = "c:/Users/renan/OneDrive/Área de Trabalho/Renan/UFSC/Mauricio/projeto"

fig_geom.write_html(f"{project_path}/Q4_geometry_figure.html")
fig_table.write_html(f"{project_path}/Q4_power_loss_table.html")

print("Figuras salvas com sucesso!")
print()
print("Arquivo 1: Q4_geometry_figure.html")
print("  - Visualiza os perfis H_z(x) para as 3 variantes")
print("  - Mostra geometria dos condutores com dimensões")
print()
print("Arquivo 2: Q4_power_loss_table.html")
print("  - Tabela comparativa de perdas")
print("  - Dados: H0=6.0 A/m, sigma=5.8e7 S/m, b=2.5 cm, f=60 Hz")
print()
print("Parametros calculados:")
print(f"  Skin depth delta = {results['delta_mm']:.4f} mm")
print(f"  Variante (a) - Ambas superficies:      P_a = {results['p_a']:.4e} W/m2")
print(f"  Variante (b) - Uma superficie:         P_b = {results['p_b']:.4e} W/m2")
print(f"  Variante (c) - Espaco finito:          P_c = {results['p_c']:.4e} W/m2")
print(f"  Razao tanh(b/delta) = {results['tanh_ratio']:.6f}")
