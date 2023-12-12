"""
A device that allows us to implement operation on a single qudit. The backend is a remote simulator.
"""

# import numpy as np

import requests, json, time
from pennylane import DeviceError, QubitDevice


class KoreaQuantumLocalEmulator(QubitDevice):
    """
    The base class for all devices that call to an external server.
    """

    name = "Korea Quantum Local Emulator"
    short_name = "kq.local_emulator"
    pennylane_requires = ">=0.16.0"
    version = "0.0.1"
    author = "Inho Jeon"

    operations = {"PauliX", "RX", "CNOT", "RY", "RZ"}
    observables = {"PauliZ", "PauliX", "PauliY"}

    def __init__(self, wires=4, shots=1024):
        super().__init__(wires=wires, shots=shots)

    def apply(self, operations, **kwargs):
        print("apply")
        # self.run(self._circuit)

    def _job_submit(self, circuits):
        URL = "http://localhost:8000/job/"
        headers = {"Content-Type": "application/json"}
        data = {
            "input_file": circuits[0].to_openqasm(),
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
            URL = f"http://localhost:8000/job/{jobUUID}/status/"
            res = requests.get(URL)
            time.sleep(1)
            if res.json().get("status") == "SUCCESS":
                URL = f"http://localhost:8000/job/{jobUUID}/result/"
                res = requests.get(URL)
                return res.json()

    def batch_execute(
        self, circuits
    ):  # pragma: no cover, pylint:disable=arguments-differ
        # print(self.accessKeyId, self.secretAccessKey)
        jobUUID = self._job_submit(circuits)
        result = self._check_job_status(jobUUID)

        return [result["results"][0]["data"]["counts"]]
