import pennylane as qml

accessKeyId = "GIPZ0SG2SCTDGT1HEANA6L6F4VPAIOGJ"
secretAccessKey = "BhPxW18nhxLuB65sYJ6lYMywQPS3PM7QFgsIML8e26I="


dev = qml.device(
    "kq.emulator",
    wires=2,
    shots=2048,
    accessKeyId=accessKeyId,
    secretAccessKey=secretAccessKey,
)


@qml.qnode(dev)
def circuit(x, y):
    qml.Hadamard(wires=0)
    qml.CNOT(wires=[0, 1])
    qml.Hadamard(wires=1)
    # qml.RX(x, wires=0)
    # qml.RY(y, wires=0)
    return qml.counts()


result = circuit(0, 0)
print(result)
# print(dev._circuit.qasm(formatted=True))
