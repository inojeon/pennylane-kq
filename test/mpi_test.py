import pennylane as qml
import numpy as np
import time

# -- Random secret --
n = 20
secret = "".join(np.random.choice(["0", "1"], size=n))
print("Random secret:", secret)


# -- Oracle --
def bernstein_vazirani_oracle(secret_bits, ancilla_wire):
    for i, bit in enumerate(secret_bits):
        if bit == "1":
            qml.CNOT(wires=[i, ancilla_wire])


# -- Bernstein-Vazirani algorithm --
def make_bv_qnode(device_name, secret_bits, shots):
    dev = qml.device(device_name, wires=len(secret_bits) + 1, shots=shots)

    @qml.qnode(dev)
    def bv_circuit():
        n_local = len(secret_bits)
        ancilla = n_local

        # ancilla
        qml.PauliX(wires=ancilla)

        # initial state
        for w in range(n_local + 1):
            qml.Hadamard(wires=w)

        # oracle
        bernstein_vazirani_oracle(secret_bits, ancilla)

        for w in range(n_local):
            qml.Hadamard(wires=w)
        return qml.counts(wires=range(n_local))

    return bv_circuit


# -- benchmark --
def benchmark_device(device_name, secret_bits, shots):
    circuit = make_bv_qnode(device_name, secret_bits, shots)
    t0 = time.perf_counter()
    counts = circuit()
    t1 = time.perf_counter()
    return counts, t1 - t0


# -- test --
print("Solution:", secret)

# default.qubit
counts_default, time_default = benchmark_device("default.qubit", secret_bits=secret, shots=10000)
print("\n=== default.qubit ===")
print("Counts:", counts_default)
print(f"Time: {time_default:.6f} s")

try:
    counts_lightning, time_lightning = benchmark_device("lightning.qubit", secret_bits=secret, shots=10000)

    print("\n=== lightning.qubit ===")
    print("Counts:", counts_lightning)
    print(f"Time: {time_lightning:.6f} s")

    speedup = time_default / time_lightning
    print(f"\nSpeedup: {speedup:.2f}x")

except Exception as e:
    print("\n[lightning.qubit failed]")
    print(e)

# -- MPI emulator --
dev_mpi = qml.device(
    "kq.emulator",
    wires=len(secret) + 1,
    shots=10000,
    api_key="your-api-key",
    target="kisti.emulator",
    verify_ssl=False,
)


@qml.qnode(dev_mpi)
def bv_circuit_mpi():
    n_local = len(secret)
    ancilla = n_local

    # ancilla
    qml.PauliX(wires=ancilla)

    # initial state
    for w in range(n_local + 1):
        qml.Hadamard(wires=w)

    # oracle
    bernstein_vazirani_oracle(secret, ancilla)

    for w in range(n_local):
        qml.Hadamard(wires=w)
    return qml.counts(wires=range(n_local))


results_mpi = bv_circuit_mpi()
print(results_mpi)
