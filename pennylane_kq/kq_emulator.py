"""
A device that allows us to implement operation on a single qudit. The backend is a remote simulator.
"""

import requests, json, time
from pennylane import DeviceError, QubitDevice


class KoreaQuantumEmulator(QubitDevice):
    """
    The base class for all devices that call to an external server.
    """

    name = "Korea Quantum Emulator"
    short_name = "kq.emulator"
    pennylane_requires = ">=0.16.0"
    version = "0.0.1"
    author = "Inho Jeon"
    accessToken = None
    resourceId = "f8284e6e-d97e-4afc-a015-39d382273a99"

    operations = {"PauliX", "RX", "CNOT", "RY", "RZ", "Hadamard"}
    observables = {"PauliZ", "PauliX", "PauliY"}

    def __init__(self, wires=4, shots=1024, accessKeyId=None, secretAccessKey=None):
        super().__init__(wires=wires, shots=shots)
        self.accessKeyId = accessKeyId
        self.secretAccessKey = secretAccessKey
        # self.hardware_options = hardware_options or "kqEmulator"

    def apply(self, operations, **kwargs):
        self.run(self._circuit)

    def _get_token(self):
        print("get KQ Cloud Token")
        api_url = f"http://150.183.154.20/oauth/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "apikey",
            "accessKeyId": self.accessKeyId,
            "secretAccessKey": self.secretAccessKey,
        }
        requestData = requests.post(api_url, data=data, headers=headers)
        if requestData.status_code == 200:
            jsondata = requestData.json()
            self.accessToken = jsondata.get("accessToken")
            return True
        else:
            raise DeviceError(
                f"/oauth/token error. req code : {requestData.status_code}"
            )

    def _job_submit(self, circuits):
        print("job submit")
        URL = "http://150.183.154.20/v2/jobs"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.accessToken}",
        }
        data = {
            "resource": {"id": self.resourceId},
            "code": circuits[0].to_openqasm(wires=sorted(circuits[0].wires)),
            "shot": self.shots,
            "name": "test job",
            "type": "QASM",
        }
        res = requests.post(URL, data=json.dumps(data), headers=headers)

        if res.status_code == 201:
            return res.json().get("id")
        else:
            raise DeviceError(f"Job sumbit error. req code : {res.status_code}")

    def _check_job_status(self, jobId):
        timeout = 6000
        timeout_start = time.time()

        while time.time() < timeout_start + timeout:
            URL = f"http://150.183.154.20/v2/jobs/{jobId}"
            headers = {"Authorization": f"Bearer {self.accessToken}"}
            res = requests.get(URL, headers=headers)
            status = res.json().get("status")
            print(f"job status check: {status}")

            if status == "COMPLETED":
                return res.json().get("result")
            time.sleep(1)
        raise DeviceError("Job timeout")

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
        if not self.accessToken:
            self._get_token()

        jobUUID = self._job_submit(circuits)
        res_result = self._check_job_status(jobUUID)

        results = []
        for circuit in circuits:
            self._samples = self._convert_counts_to_samples(
                res_result, circuit.num_wires
            )

            res = self.statistics(circuit)
            single_measurement = len(circuit.measurements) == 1
            res = res[0] if single_measurement else tuple(res)
            results.append(res)

        return results
