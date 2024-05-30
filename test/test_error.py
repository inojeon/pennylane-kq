import pennylane as qml
from pennylane import numpy as np

# dev = qml.device("default.qubit", wires=2)

# dev = qml.device("kq.local_emulator", wires=2, shots=10000)


accessKeyId = "DV7Z3NNQZET1O1QLIS31ZE32OOQTEIFE"
secretAccessKey = "TEhIFzeZhXiR1bIO/DZ8+lyiA8VZp+qHEKc6fxaOIAM="

dev = qml.device(
    "kq.emulator",
    wires=2,
    shots=10000,
    accessKeyId=accessKeyId,
    secretAccessKey=secretAccessKey,
)


@qml.qnode(dev, interface="autograd")
def circuit2(param):
    qml.RY(param[0], wires=0)
    qml.RY(param[1], wires=1)
    qml.CNOT(wires=[0, 1])
    qml.RY(param[2], wires=0)
    qml.RY(param[3], wires=1)
    # return qml.expval(qml.Identity(0))
    return qml.expval(qml.PauliX(1))


theta = np.array(
    [0.5 * np.pi, 0.5 * np.pi, 0.5 * np.pi, 0.5 * np.pi], requires_grad=True
)

# print(circuit1(theta))
print(circuit2(theta))
