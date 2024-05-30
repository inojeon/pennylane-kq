"""
A device that allows us to implement operation on a single qudit. The backend is a remote simulator.
"""

# import numpy as np

import requests, json, time
from pennylane import QubitDevice


class KoreaQuantumDevice(QubitDevice):
    """
    The base class for all devices that call to an external server.
    """

    name = "Qiskit KQ plugin"
    # short_name = "kq.local_emulator"
    pennylane_requires = ">=0.16.0"
    version = "0.0.13"
    author = "Inho Jeon"

    operations = {"PauliX", "PauliY", "PauliZ", "RX", "CNOT", "RY", "RZ", "Hadamard"}
    observables = {
        "PauliX",
        "PauliY",
        "PauliZ",
        "Identity",
        "Hadamard",
        "Hermitian",
        "Projector",
    }

    def __init__(self, wires=4, shots=1024):
        super().__init__(wires=wires, shots=shots)

    def _convert_counts_to_samples(self, count_datas, wires):
        import numpy as np

        first = True
        result = None

        for hex_value, count in count_datas.items():
            # 16진수 값을 10진수로 변환
            decimal_value = int(hex_value, 16)

            if decimal_value >= 2**wires:
                decimal_value = 2**wires - 1
            # 10진수 값을 지정된 자릿수의 이진수 배열로 변환
            binary_array = np.array([int(x) for x in f"{decimal_value:0{wires}b}"])
            # 지정된 횟수만큼 배열을 반복하여 결과 리스트에 추가
            expanded_array = np.tile(binary_array[::-1], (count, 1))
            # 첫 번째 배열인 경우 result를 초기화
            if first:
                result = expanded_array
                first = False
            else:
                result = np.vstack((result, expanded_array))
        return result
