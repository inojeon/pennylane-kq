"""
A device that allows us to implement operation on a single qudit. The backend is a remote simulator.
"""

# import numpy as np

import requests, json, time
from pennylane import DeviceError, QubitDevice


class KoreaQuantumRemoteEmulator(QubitDevice):
    """
    The base class for all devices that call to an external server.
    """

    name = "Korea Quantum Remote Emulator"
    short_name = "kq.remote_emulator"
    pennylane_requires = ">=0.16.0"
    version = "0.0.1"
    author = "Inho Jeon"

    operations = {"PauliX", "RX", "CNOT", "RY", "RZ", "Hadamard"}
    observables = {"PauliZ", "PauliX", "PauliY"}

    def __init__(self, wires=4, shots=1024):
        super().__init__(wires=wires, shots=shots)

    def apply(self, operations, **kwargs):
        print("apply")
        # self.run(self._circuit)

    def _job_submit(self, circuits):
        # print(circuits[0].wires)
        # print(circuits[0].to_openqasm(wires=sorted(circuits[0].wires)))
        URL = "http://150.183.117.145:8000/job"
        headers = {"Content-Type": "application/json"}
        data = {
            "input_file": circuits[0].to_openqasm(wires=sorted(circuits[0].wires)),
            "shot": self.shots,
            "type": "qasm",
        }
        res = requests.post(URL, data=json.dumps(data), headers=headers)

        if res.status_code == 201:
            return res.json().get("jobUUID")
        else:
            raise DeviceError(
                f"Job sumbit error. post /job/ req code : {res.status_code}"
            )

    def _check_job_status(self, jobUUID):
        timeout = 6000
        timeout_start = time.time()

        while time.time() < timeout_start + timeout:
            URL = f"http://150.183.117.145:8000/job/{jobUUID}/status"
            res = requests.get(URL)
            time.sleep(1)
            if res.json().get("status") == "SUCCESS":
                URL = f"http://150.183.117.145:8000/job/{jobUUID}/result"
                res = requests.get(URL)
                return res.json()

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
            expanded_array = np.tile(binary_array, (count, 1))
            # 첫 번째 배열인 경우 result를 초기화
            if first:
                result = expanded_array
                first = False
            else:
                result = np.vstack((result, expanded_array))
        return result

    def batch_execute(self, circuits):
        jobUUID = self._job_submit(circuits)
        res_results = self._check_job_status(jobUUID)

        results = []
        for circuit, res_result in zip(circuits, res_results["results"]):
            self._samples = self._convert_counts_to_samples(
                res_result["data"]["counts"], circuit.num_wires
            )

            res = self.statistics(circuit)
            single_measurement = len(circuit.measurements) == 1
            res = res[0] if single_measurement else tuple(res)
            results.append(res)

        return results
