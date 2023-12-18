"""
A device that allows us to implement operation on a single qudit. The backend is a remote simulator.
"""

import requests, json, time
from pennylane import DeviceError, QubitDevice


class KoreaQuantumHardware(QubitDevice):
    """
    The base class for all devices that call to an external server.
    """

    name = "Korea Quantum Hardware"
    short_name = "kq.hardware"
    pennylane_requires = ">=0.16.0"
    version = "0.0.1"
    author = "Inho Jeon"
    accessToken = None
    resourceId = "5893a46f-c0f7-4d83-99cb-f86103e2b694"

    operations = {"PauliX", "RX", "CNOT", "RY", "RZ"}
    observables = {"PauliZ", "PauliX", "PauliY"}

    def __init__(self, wires=4, shots=1024, accessKeyId=None, secretAccessKey=None):
        super().__init__(wires=wires, shots=shots)
        self.accessKeyId = accessKeyId
        self.secretAccessKey = secretAccessKey
        # self.hardware_options = hardware_options or "kqHardware"

    def apply(self, operations, **kwargs):
        self.run(self._circuit)

    def _get_token(self):
        print("get KQ Cloud Token")
        api_url = f"http://3.39.145.223:31001/oauth/token"
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
        URL = "http://3.39.145.223:31001/v2/jobs"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.accessToken}",
        }
        data = {
            "resource": {"id": "aae7709c-e335-4420-b231-6f8c88aa85be"},
            "code": circuits[0].to_openqasm(),
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
            URL = f"http://3.39.145.223:31001/v2/jobs/{jobId}"
            headers = {"Authorization": f"Bearer {self.accessToken}"}
            res = requests.get(URL, headers=headers)
            status = res.json().get("status")
            print(f"job status check: {status}")

            if status == "COMPLETED":
                return res.json().get("result")
            time.sleep(1)
        raise DeviceError("Job timeout")

    def batch_execute(
        self, circuits
    ):  # pragma: no cover, pylint:disable=arguments-differ
        # print(self.accessKeyId, self.secretAccessKey)
        if not self.accessToken:
            self._get_token()

        jobId = self._job_submit(circuits)
        result = self._check_job_status(jobId)
        # print(jobId)
        return [result]
