"""KRISS QPU 실행 예제. 실행하면 실제 장비에 회로 하나를 제출합니다."""

import pennylane as qml

API_KEY = "your-api-key"
TARGET = "kriss.hw_50q"  # 50큐빗 장비: "kriss.hw_50q"
SHOTS = 1024

dev = qml.device(
    "kq.qpu",
    wires=2,
    shots=SHOTS,
    api_key=API_KEY,
    target=TARGET,
    use_streaming=False,
)


@qml.qnode(dev)
def circuit():
    qml.Hadamard(wires=0)
    qml.CNOT(wires=[0, 1])
    return qml.counts(wires=[0, 1])


print(f"{TARGET}: Bell 회로 실행 중 ({SHOTS} shots)...", flush=True)
counts = circuit()
print("측정 결과:", counts)
print("이상적인 결과: 00과 11이 각각 약 절반씩 측정됩니다.")
print("실제 QPU에서는 노이즈와 유한한 샷 수 때문에 차이가 발생할 수 있습니다.")
