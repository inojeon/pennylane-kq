import pennylane as qml

dev = qml.device("kq.local_emulator", wires=2, shots=2048, host="http://localhost:8000")


@qml.qnode(dev)
def circuit(x):
    qml.RX(x, wires=[0])
    qml.CNOT(wires=[0, 1])
    return qml.expval(qml.PauliZ(1))


print("circuit1")
result = circuit(0.1)
print(result)