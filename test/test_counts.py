import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import pennylane as qml

dev = qml.device(
    "kq.cloudv2",
    wires=2,
    shots=1024,
    api_key="your-api-key",
    target="kisti.sim1",
    verify_ssl=False,
)


@qml.qnode(dev)
def circuit():
    qml.Hadamard(wires=0)
    qml.CNOT(wires=[0, 1])
    return qml.counts()


result = circuit()
print(result)
