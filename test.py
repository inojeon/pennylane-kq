import pennylane as qml

accessKeyId = "9LUUDMA4OYRYG73LM703SQF7FG1JHDNT"
secretAccessKey = "x3om700rKpo+693om1/bEt3rKBilEMJnaAXqGdWuuqE="


# dev = qml.device(
#     "kq.emulator",
#     wires=2,
#     shots=2048,
#     accessKeyId=accessKeyId,
#     secretAccessKey=secretAccessKey,
# )


dev = qml.device(
    "default.qubit",
    wires=2,
    shots=2048,
    # accessKeyId=accessKeyId,
    # secretAccessKey=secretAccessKey,
)


@qml.qnode(dev)
def circuit():
    qml.Hadamard(wires=0)
    qml.CNOT(wires=[0, 1])
    return qml.counts()


result = circuit()
print(result)


dev2 = qml.device(
    "kq.hardware",
    wires=2,
    shots=2048,
    accessKeyId=accessKeyId,
    secretAccessKey=secretAccessKey,
)


@qml.qnode(dev2)
def circuit2():
    qml.Hadamard(wires=1)
    qml.CNOT(wires=[0, 1])
    return qml.counts()


# All counts 만 구현
result2 = circuit2()
print(result2)
