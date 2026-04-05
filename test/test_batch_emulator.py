"""
PennyLane KQ 배치 실행 테스트 (Emulator)
"""
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import pennylane as qml
from pennylane.tape import QuantumScript
import numpy as np

dev = qml.device(
    "kq.emulator", wires=3, shots=1024,
    api_key="your-api-key",
    target="kisti.emulator",
    verify_ssl=False
)

tape1 = QuantumScript(
    [qml.Hadamard(0), qml.CNOT([0, 1])],
    [qml.expval(qml.PauliZ(0))],
    shots=1024,
)

tape2 = QuantumScript(
    [qml.PauliX(0)],
    [qml.expval(qml.PauliZ(0))],
    shots=1024,
)

tape3 = QuantumScript(
    [qml.RY(np.pi / 3, wires=0)],
    [qml.expval(qml.PauliZ(0))],
    shots=1024,
)

print("3개 회로 배치 실행...")
results = dev.execute([tape1, tape2, tape3])

print(f"회로 1 (Bell 상태,  기대 ≈  0.0): {results[0]:.4f}")
print(f"회로 2 (|1⟩ 상태,  기대 ≈ -1.0): {results[1]:.4f}")
print(f"회로 3 (RY(π/3),   기대 ≈  0.5): {results[2]:.4f}")
