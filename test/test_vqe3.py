import pennylane as qml
from pennylane import numpy as np

# dev = qml.device("default.qubit", wires=2)

dev = qml.device("kq.local_emulator", wires=2, shots=5000)


@qml.qnode(dev, interface="autograd")
def circuit1(param):
    qml.RY(param[0], wires=0)
    qml.RY(param[1], wires=1)
    qml.CNOT(wires=[0, 1])
    qml.RY(param[2], wires=0)
    qml.RY(param[3], wires=1)
    return qml.expval(qml.Identity(0) @ qml.Identity(1))


@qml.qnode(dev, interface="autograd")
def circuit2(param):
    qml.RY(param[0], wires=0)
    qml.RY(param[1], wires=1)
    qml.CNOT(wires=[0, 1])
    qml.RY(param[2], wires=0)
    qml.RY(param[3], wires=1)
    return qml.expval(qml.Identity(0) @ qml.PauliX(1))


@qml.qnode(dev, interface="autograd")
def circuit3(param):
    qml.RY(param[0], wires=0)
    qml.RY(param[1], wires=1)
    qml.CNOT(wires=[0, 1])
    qml.RY(param[2], wires=0)
    qml.RY(param[3], wires=1)
    return qml.expval(qml.PauliX(0) @ qml.PauliX(1))


@qml.qnode(dev, interface="autograd")
def circuit4(param):
    qml.RY(param[0], wires=0)
    qml.RY(param[1], wires=1)
    qml.CNOT(wires=[0, 1])
    qml.RY(param[2], wires=0)
    qml.RY(param[3], wires=1)
    return qml.expval(qml.PauliY(0) @ qml.PauliY(1))


def cost_fn(param):
    return (
        2 * circuit1(param)
        - circuit2(param)
        - 0.5 * circuit3(param)
        - 0.5 * circuit4(param)
    )


opt = qml.GradientDescentOptimizer(stepsize=0.4)
theta = np.array(
    [0.5 * np.pi, 0.5 * np.pi, 0.5 * np.pi, 0.5 * np.pi], requires_grad=True
)

# print(circuit2(theta))

# store the values of the cost function
energy = [cost_fn(theta)]

# store the values of the circuit parameter
angle = [theta]

max_iterations = 100
conv_tol = 1e-04

for n in range(max_iterations):
    theta, prev_energy = opt.step_and_cost(cost_fn, theta)

    energy.append(cost_fn(theta))
    angle.append(theta)

    conv = np.abs(energy[-1] - prev_energy)

    # if n % 2 == 0:
    print(f"Step = {n},  Energy = {energy[-1]:.8f}")

    if conv <= conv_tol:
        break
