import sys
from pathlib import Path
import numpy as np

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.schemas.defaults import get_default_exercise01_input
from app.core.exercises.q01_tank_losses import simulate_exercise_01


def run(currs):
    inp = get_default_exercise01_input()
    for i,c in enumerate(currs):
        inp.conductors[i].current_a = c
    r = simulate_exercise_01(inp)
    return r.total_loss_approximate_w, r.total_loss_analytical_w

cases = [
    ("all +", [2250,2250,2250]),
    ("alt +-+", [2250,-2250,2250]),
    ("balanced inst", [2250,-1125,-1125]),
    ("line/sqrt3 all+", [2250/np.sqrt(3)]*3),
    ("line/sqrt3 balanced", [2250/np.sqrt(3),-2250/(2*np.sqrt(3)),-2250/(2*np.sqrt(3))]),
]

for name, c in cases:
    approx, anal = run(c)
    print(name, c)
    print("  approx", round(approx,2), "anal", round(anal,2))
