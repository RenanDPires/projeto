import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.schemas.defaults import get_default_exercise01_input
from app.core.exercises.q01_tank_losses import simulate_exercise_01

inp = get_default_exercise01_input()
for c in inp.conductors:
    c.current_a = 2250.0

r1 = simulate_exercise_01(inp)
print('default holes (82,82,82):', r1.total_loss_approximate_w)

inp2 = get_default_exercise01_input()
for c in inp2.conductors:
    c.current_a = 2250.0
inp2.holes[1].diameter_mm = 114.0
r2 = simulate_exercise_01(inp2)
print('holes (82,114,82):', r2.total_loss_approximate_w)
