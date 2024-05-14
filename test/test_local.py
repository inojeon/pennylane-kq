import pennylane as qml

dev = qml.device("kq.local_emulator", wires=2, shots=2048, host="http://localhost:8000")


dev2 = qml.device(
    "default.qubit",
    wires=2,
    shots=2048,
    # accessKeyId=accessKeyId,
    # secretAccessKey=secretAccessKey,
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
