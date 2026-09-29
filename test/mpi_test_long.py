import pennylane as qml
import numpy as np
import time

N_QUBITS = 28
N_LAYERS = 5
SHOTS = 50000

API_KEY = "your-api-key"
TARGET = "kisti.emulator"
VERIFY_SSL = False

dev = qml.device(
    "kq.emulator",
    wires=N_QUBITS,
    shots=SHOTS,
    api_key=API_KEY,
    target=TARGET,
    verify_ssl=VERIFY_SSL,
)

params = np.random.uniform(0, 2 * np.pi, size=(N_LAYERS, N_QUBITS, 3))


@qml.qnode(dev)
def circuit():
    for layer in range(N_LAYERS):
        for q in range(N_QUBITS):
            qml.RX(params[layer, q, 0], wires=q)
            qml.RY(params[layer, q, 1], wires=q)
            qml.RZ(params[layer, q, 2], wires=q)
        for q in range(N_QUBITS - 1):
            qml.CNOT(wires=[q, q + 1])
        qml.CNOT(wires=[N_QUBITS - 1, 0])
    return qml.counts(wires=range(N_QUBITS))


if __name__ == "__main__":
    print(f"Deep Random Circuit: {N_QUBITS}q x {N_LAYERS} layers, {SHOTS} shots")
    print(f"Total gates: ~{N_LAYERS * (N_QUBITS * 3 + N_QUBITS)}")
    print(f"State vector size: 2^{N_QUBITS} = {2**N_QUBITS:,} amplitudes")
    print()

    t0 = time.perf_counter()
    result = circuit()
    dt = time.perf_counter() - t0

    top5 = sorted(result.items(), key=lambda x: -x[1])[:5]
    print(f"Time: {dt:.2f} s")
    print(f"Unique outcomes: {len(result)}")
    print(f"Top 5: {top5}")
