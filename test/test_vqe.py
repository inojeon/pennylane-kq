import pennylane as qml
from pennylane import numpy as np

symbols = ["H", "H"]
coordinates = np.array([0.0, 0.0, -0.6614, 0.0, 0.0, 0.6614])

H, qubits = qml.qchem.molecular_hamiltonian(symbols, coordinates)
print("Number of qubits = ", qubits)
print("The Hamiltonian is ", H)

# dev = qml.device("kq.local_emulator", wires=qubits)
# dev = qml.device("default.qubit", wires=qubits)


accessKeyId = "DV7Z3NNQZET1O1QLIS31ZE32OOQTEIFE"
secretAccessKey = "TEhIFzeZhXiR1bIO/DZ8+lyiA8VZp+qHEKc6fxaOIAM="

dev = qml.device(
    "kq.emulator",
    wires=qubits,
    shots=2048,
    accessKeyId=accessKeyId,
    secretAccessKey=secretAccessKey,
)

electrons = 2
hf = qml.qchem.hf_state(electrons, qubits)

print(hf)


def circuit(param, wires):
    # qml.BasisState(hf, wires=wires)
    qml.PauliX(wires=0)
    qml.PauliX(wires=1)
    qml.DoubleExcitation(param, wires=[0, 1, 2, 3])


@qml.qnode(dev, interface="autograd")
def cost_fn(param):
    circuit(param, wires=range(qubits))
    return qml.expval(H)


opt = qml.GradientDescentOptimizer(stepsize=0.4)
theta = np.array(0.0, requires_grad=True)

# store the values of the cost function
energy = [cost_fn(theta)]

# store the values of the circuit parameter
angle = [theta]

max_iterations = 4
conv_tol = 1e-06

print("start for loop")

for n in range(max_iterations):
    theta, prev_energy = opt.step_and_cost(cost_fn, theta)

    energy.append(cost_fn(theta))
    angle.append(theta)

    conv = np.abs(energy[-1] - prev_energy)

    print(f"Step = {n},  Energy = {energy[-1]:.8f} Ha")

    if conv <= conv_tol:
        break

print("\n" f"Final value of the ground-state energy = {energy[-1]:.8f} Ha")
print("\n" f"Optimal value of the circuit parameter = {angle[-1]:.4f}")
