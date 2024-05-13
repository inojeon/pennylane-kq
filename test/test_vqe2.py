import pennylane as qml
from pennylane import numpy as np
import matplotlib.pyplot as plt


def random_scenario_settings():
    # np.random.seed(3)
    preparation_settings = np.random.random(1)
    measurement_settings = np.random.random(4)

    return np.array(preparation_settings.tolist() + measurement_settings.tolist())


chsh_dev = qml.device("kq.local_emulator", wires=2, shots=10000)
# chsh_dev.wires


@qml.qnode(chsh_dev)
def chsh_correlator(settings):
    # state prepartion
    qml.RY(settings[0], wires=[0])
    # qml.RY(0, wires=[1])
    qml.CNOT(wires=[0, 1])

    # measurement basis rotations
    qml.RY(settings[1], wires=[0])
    qml.RY(settings[2], wires=[1])

    # computational basis measurement
    return qml.expval(qml.PauliZ(0) @ qml.PauliZ(1))


def chsh_cost(scenario_settings):
    score = 0
    for x in range(2):
        for y in range(2):
            # construct the settings for inputs `x` and `y`
            qnode_settings = np.array(
                [
                    *scenario_settings[:1],  # State
                    scenario_settings[1 + x],  # Alice Measurement input x
                    scenario_settings[3 + y],  # Bob Measurement input y
                ]
            )
            score += (-1) ** (x * y) * chsh_correlator(qnode_settings)
    return -(score)


# initialize random parameters
init_settings = random_scenario_settings()
print("initial settings :\n", init_settings, "\n")

num_steps = 10
step_size = 0.5

opt = qml.GradientDescentOptimizer(stepsize=step_size)

scores = []
settings_list = []
for i in range(num_steps):
    score = -(chsh_cost(init_settings))  # qpu
    scores.append(score)
    settings_list.append(init_settings)

    # print("\r", i)
    # # print progress
    # if i % 5 == 0:
    print("iteration : ", i, ", score : ", score)
    init_settings = opt.step(chsh_cost, init_settings)  # cpu
    # print(init_settings)

# log data for final score and settings
final_score = -(chsh_cost(init_settings))
scores.append(final_score)
settings_list.append(init_settings)

# find the maximum value and optimal settings
max_score = max(scores)
max_id = scores.index(max_score)
opt_settings = settings_list[max_id]

# return {
#    "max_score" : max_score,
#    "opt_settings" : opt_settings,
#    "max_id" : max_id,
#    "samples" : range(num_steps + 1),
#    "scores" : scores,
#    "settings" : settings_list
# }


print("max score : ", max_score)
print("optimal settings : ", opt_settings, "\n")
print("theoretical max : ", 2 * np.sqrt(2), "\n")


plt.plot(range(num_steps + 1), scores, "o", label="Optimization")
plt.plot(range(num_steps + 1), [2] * len(range(num_steps + 1)), label="Classical Bound")
plt.plot(
    range(num_steps + 1),
    [2 * np.sqrt(2)] * len(range(num_steps + 1)),
    label="Quantum Bound",
)

plt.title("Optimization of CHSH Violation\n")
plt.ylabel("CHSH Score")
plt.xlabel("Epoch")
plt.legend()

plt.show()
