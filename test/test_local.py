import pennylane as qml


dev2 = qml.device(
    "default.qubit",
    wires=2,
    shots=2048,
)

@qml.qnode(dev2)
def circuit2(x):
    qml.RX(x, wires=[0])
    qml.CNOT(wires=[0, 1])
    return qml.expval(qml.PauliZ(1))


print("circuit2")
result2 = circuit2(0.1)
print(result2)
