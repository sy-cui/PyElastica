# FIXME without appending sys.path make it more generic
import sys

sys.path.append("../")
sys.path.append("../../")

# from collections import defaultdict
# import numpy as np
from matplotlib import pyplot as plt


from elastica import *
from elastica.utils import MaxDimension


class ButterflySimulator(BaseSystemCollection, CallBacks):
    pass


butterfly_sim = ButterflySimulator()
final_time = 40.0

# Options
PLOT_FIGURE = True
SAVE_FIGURE = True
SAVE_RESULTS = True
ADD_UNSHEARABLE_ROD = False

# setting up test params
# FIXME : Doesn't work with elements > 10 (the inverse rotate kernel fails)
n_elem = 4  # Change based on requirements, but be careful
n_elem += n_elem % 2
half_n_elem = n_elem // 2

origin = np.zeros((3, 1))
angle_of_inclination = np.deg2rad(45.0)

# in-plane
horizontal_direction = np.array([0.0, 0.0, 1.0]).reshape(-1, 1)
vertical_direction = np.array([1.0, 0.0, 0.0]).reshape(-1, 1)

# out-of-plane
normal = np.array([0.0, 1.0, 0.0])

total_length = 3.0
base_radius = 0.25
base_area = np.pi * base_radius ** 2
density = 5000
nu = 0.0
youngs_modulus = 1e4
poisson_ratio = 0.5

positions = np.empty((MaxDimension.value(), n_elem + 1))
dl = total_length / n_elem

# First half of positions stem from slope angle_of_inclination
first_half = np.arange(half_n_elem + 1.0).reshape(1, -1)
positions[..., : half_n_elem + 1] = origin + dl * first_half * (
    np.cos(angle_of_inclination) * horizontal_direction
    + np.sin(angle_of_inclination) * vertical_direction
)
positions[..., half_n_elem:] = positions[
    ..., half_n_elem : half_n_elem + 1
] + dl * first_half * (
    np.cos(angle_of_inclination) * horizontal_direction
    - np.sin(angle_of_inclination) * vertical_direction
)

butterfly_rod = CosseratRod.straight_rod(
    n_elem,
    start=origin.reshape(3),
    direction=np.array([0.0, 0.0, 1.0]),
    normal=normal,
    base_length=total_length,
    base_radius=base_radius,
    density=density,
    nu=nu,
    youngs_modulus=youngs_modulus,
    poisson_ratio=poisson_ratio,
    position=positions,
)

butterfly_sim.append(butterfly_rod)

# Add call backs
class VelocityCallBack(CallBackBaseClass):
    """
    Call back function for continuum snake
    """

    def __init__(self, step_skip: int, callback_params: dict):
        CallBackBaseClass.__init__(self)
        self.every = step_skip
        self.callback_params = callback_params

    def make_callback(self, system, time, current_step: int):

        if current_step % self.every == 0:

            self.callback_params["time"].append(time)
            # Collect only x
            self.callback_params["position"].append(system.position_collection.copy())
            return


recorded_history = defaultdict(list)
# initially record history
recorded_history["time"].append(0.0)
recorded_history["position"].append(butterfly_rod.position_collection.copy())

butterfly_sim.collect_diagnostics(butterfly_rod).using(
    VelocityCallBack, step_skip=100, callback_params=recorded_history
)


butterfly_sim.finalize()
timestepper = PositionVerlet()
# timestepper = PEFRL()

dt = 0.01 * dl
total_steps = int(final_time / dt)
print("Total steps", total_steps)
integrate(timestepper, butterfly_sim, final_time, total_steps)

if PLOT_FIGURE:
    fig = plt.figure(figsize=(10, 8), frameon=True, dpi=150)
    ax = fig.add_subplot(111)
    positions = recorded_history["position"]
    # record first position
    first_position = positions.pop(0)
    ax.plot(first_position[2, ...], first_position[0, ...], "r--", lw=2.0)
    n_positions = len(positions)
    for i, pos in enumerate(positions):
        alpha = np.exp(i / n_positions - 1)
        ax.plot(pos[2, ...], pos[0, ...], "b", lw=0.6, alpha=alpha)
    # final position is also separate
    last_position = positions.pop()
    ax.plot(last_position[2, ...], last_position[0, ...], "k--", lw=2.0)
    plt.show()
    if SAVE_FIGURE:
        fig.savefig("butterfly.pdf")

if SAVE_RESULTS:
    import pickle

    filename = "butterfly_data.dat"
    file = open(filename, "wb")
    pickle.dump(butterfly_rod, file)
    file.close()