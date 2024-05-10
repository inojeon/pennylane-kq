import pennylane as qml

accessKeyId = "DV7Z3NNQZET1O1QLIS31ZE32OOQTEIFE"
secretAccessKey = "TEhIFzeZhXiR1bIO/DZ8+lyiA8VZp+qHEKc6fxaOIAM="

dev = qml.device(
    "kq.emulator",
    wires=2,
    shots=2048,
    accessKeyId=accessKeyId,
    secretAccessKey=secretAccessKey,
)

dev2 = qml.device(
    "default.qubit",
    wires=2,
    shots=2048,
)


@qml.qnode(dev)
def circuit(x):
    qml.RX(x, wires=[0])
    qml.CNOT(wires=[0, 1])
    return qml.expval(qml.PauliZ(1))


@qml.qnode(dev2)
def circuit2(x):
    qml.RX(x, wires=[0])
    qml.CNOT(wires=[0, 1])
    return qml.expval(qml.PauliZ(1))


print("circuit1")
result = circuit(0.1)
print(result)

print("circuit2")
result2 = circuit2(0.1)
print(result2)
