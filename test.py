import pennylane as qml

accessKeyId = "9LUUDMA4OYRYG73LM703SQF7FG1JHDNT"
secretAccessKey = "x3om700rKpo+693om1/bEt3rKBilEMJnaAXqGdWuuqE="


dev = qml.device(
    "kq.local_emulator",
    wires=2,
    shots=2048,
    # accessKeyId=accessKeyId,
    # secretAccessKey=secretAccessKey,
)


dev2 = qml.device(
    "default.qubit",
    wires=2,
    shots=2048,
    # accessKeyId=accessKeyId,
    # secretAccessKey=secretAccessKey,
)
dev3 = qml.device(
    "qiskit.aer",
    wires=2,
    shots=2048,
    # accessKeyId=accessKeyId,
    # secretAccessKey=secretAccessKey,
)


@qml.qnode(dev)
def circuit():
    qml.Hadamard(wires=1)
    qml.CNOT(wires=[1, 0])
    return qml.counts()


@qml.qnode(dev2)
def circuit2():
    qml.Hadamard(wires=1)
    qml.CNOT(wires=[1, 0])
    return qml.counts()


@qml.qnode(dev3)
def circuit3():
    qml.Hadamard(wires=1)
    qml.CNOT(wires=[1, 0])
    return qml.counts()


result = circuit()
print(result)

# All counts 만 구현
result2 = circuit2()
print(result2)

# All counts 만 구현
result3 = circuit3()
print(result3)


# dev2 = qml.device(
#     "kq.hardware",
#     wires=2,
#     shots=2048,
#     accessKeyId=accessKeyId,
#     secretAccessKey=secretAccessKey,
# )
