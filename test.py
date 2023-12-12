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


# dev = qml.device(
#     "kq.local_emulator",
#     wires=2,
#     shots=2048,
# )


@qml.qnode(dev)
def circuit():
    qml.Hadamard(wires=1)
    qml.CNOT(wires=[0, 1])
    return qml.counts()


# All counts 만 구현
result = circuit()
print(result)
