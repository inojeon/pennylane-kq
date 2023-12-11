import pennylane as qml

accessKeyId = "GIPZ0SG2SCTDGT1HEANA6L6F4VPAIOGJ"
secretAccessKey = "BhPxW18nhxLuB65sYJ6lYMywQPS3PM7QFgsIML8e26I="


dev = qml.device(
    "kq.emulator", accessKeyId=accessKeyId, secretAccessKey=secretAccessKey
)


@qml.qnode(dev)
def circuit(x, y):
    qml.RX(x, wires=0)
    qml.RY(y, wires=0)
    return qml.counts(qml.PauliZ(0))


result = circuit(0, 0)
print(result)
