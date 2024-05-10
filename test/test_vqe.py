import pennylane as qml

dev = qml.device(
    "kq.remote_emulator",
    wires=4,
    shots=2048,
)


# dev2 = qml.device(
#     "default.qubit",
#     wires=2,
#     shots=2048,
#     # accessKeyId=accessKeyId,
#     # secretAccessKey=secretAccessKey,
# )


# dev = qml.device("default.qubit", wires=4)


# @qml.qnode(dev)
# def circuit(phi):
#     qml.X(0)
#     qml.X(1)
#     qml.DoubleExcitation(phi, wires=[0, 1, 2, 3])
#     return qml.state()


@qml.qnode(dev)
def circuit(x):
    qml.RX(x, wires=[0])
    qml.CNOT(wires=[0, 1])
    return qml.expval(qml.PauliZ(1))


print(circuit(0.1))
