import pennylane as qml
import numpy as np

# dev2 = qml.device(
#     "kq.local_emulator", wires=5, shots=2048, host="http://localhost:8000"
# )

accessKeyId = "DV7Z3NNQZET1O1QLIS31ZE32OOQTEIFE"
secretAccessKey = "TEhIFzeZhXiR1bIO/DZ8+lyiA8VZp+qHEKc6fxaOIAM="

dev2 = qml.device(
    "kq.emulator.fast",
    wires=2,
    shots=2048,
    accessKeyId=accessKeyId,
    secretAccessKey=secretAccessKey,
)


@qml.qnode(dev2)
def circuit1(x):
    qml.CNOT(wires=[0, 1])
    qml.RY(x, wires=0)
    return qml.state()
    # return qml.expval(qml.PauliZ(0) @ qml.PauliZ(1))


print(circuit1(np.pi / 2))

# @qml.qnode(dev2)
# def circuit11(x):
#     qml.Hadamard(wires=0)
#     qml.CNOT(wires=[0, 1])
#     qml.RY(x, wires=0)
#     return qml.expval(qml.PauliZ(0) @ qml.PauliZ(1))


# @qml.qnode(dev)
# def circuit2(x):
#     qml.Hadamard(wires=0)
#     qml.CNOT(wires=[0, 1])
#     qml.RY(x, wires=0)
#     qml.Hadamard(wires=0)
#     return qml.expval(qml.PauliZ(0) @ qml.PauliZ(1))


# @qml.qnode(dev2)
# def circuit22(x):
#     qml.Hadamard(wires=0)
#     qml.CNOT(wires=[0, 1])
#     qml.RY(x, wires=0)
#     qml.Hadamard(wires=0)
#     return qml.expval(qml.PauliZ(0) @ qml.PauliZ(1))


# @qml.qnode(dev)
# def circuit3(x):
#     qml.Hadamard(wires=0)
#     qml.CNOT(wires=[0, 1])
#     qml.RY(x, wires=0)
#     qml.Hadamard(wires=1)
#     return qml.expval(qml.PauliZ(0) @ qml.PauliZ(1))


# @qml.qnode(dev2)
# def circuit33(x):
#     qml.Hadamard(wires=0)
#     qml.CNOT(wires=[0, 1])
#     qml.RY(x, wires=0)
#     qml.Hadamard(wires=1)
#     return qml.expval(qml.PauliZ(0) @ qml.PauliZ(1))


# @qml.qnode(dev)
# def circuit4(x):
#     qml.Hadamard(wires=0)
#     qml.CNOT(wires=[0, 1])
#     qml.RY(x, wires=0)
#     qml.Hadamard(wires=0)
#     qml.Hadamard(wires=1)
#     return qml.expval(qml.PauliZ(0) @ qml.PauliZ(1))


# @qml.qnode(dev2)
# def circuit44(x):
#     qml.Hadamard(wires=0)
#     qml.CNOT(wires=[0, 1])
#     qml.RY(x, wires=0)
#     qml.Hadamard(wires=0)
#     qml.Hadamard(wires=1)
#     return qml.expval(qml.PauliZ(0) @ qml.PauliZ(1))


# import numpy as np

# theta = [0.1 * i * np.pi for i in range(21)]

# for i in theta:
#     c = CHSH(i)
#     print(c)

# x = 0
# print(circuit1(x) - circuit2(x) + circuit3(x) + circuit4(x))
# print(circuit11(x) - circuit22(x) + circuit33(x) + circuit44(x))
# print(circuit3(0.1))
# print(circuit33(0.1))
