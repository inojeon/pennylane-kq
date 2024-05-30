"""
A device that allows us to implement operation on a single qudit. The backend is a remote simulator.
"""

# import numpy as np

import requests, json, time
from pennylane import DeviceError, QubitDevice

from .kq_device import KoreaQuantumDevice


class KoreaQuantumLocalEmulator(KoreaQuantumDevice):
    """
    The base class for all devices that call to an external server.
    """

    name = "Korea Quantum Local Emulator"
    short_name = "kq.local_emulator"

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

    def __init__(self, wires=4, shots=1024, host="http://localhost:8000"):
        super().__init__(wires=wires, shots=shots)
        self.host = host

    def apply(self, operations, **kwargs):
        print("apply")

    def _job_submit(self, circuit):
        URL = f"{self.host}/job"
        headers = {"Content-Type": "application/json"}
        data = {
            "input_file": circuit.to_openqasm(wires=sorted(circuit.wires)),
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
            URL = f"{self.host}/job/{jobUUID}/status"
            res = requests.get(URL)
            time.sleep(1)
            if res.json().get("status") == "SUCCESS":
                URL = f"{self.host}/job/{jobUUID}/result"
                res = requests.get(URL)
                return res.json()

    def _jobs_submit(self, circuits):
        URL = f"{self.host}/jobs"
        headers = {"Content-Type": "application/json"}
        jobs = [
            {
                "input_file": circuit.to_openqasm(wires=sorted(circuit.wires)),
                "shot": self.shots,
                "type": "qasm",
            }
            for circuit in circuits
        ]
        res = requests.post(URL, data=json.dumps({"jobs": jobs}), headers=headers)

        if res.status_code == 201:
            return res.json().get("collectionUUID")
        else:
            raise DeviceError(
                f"Job sumbit error. post /jobs/ req code : {res.status_code}"
            )

    def _check_jobs_status(self, collectionUUID):
        timeout = 6000
        timeout_start = time.time()

        # time.sleep(0.2)
        while time.time() < timeout_start + timeout:
            time.sleep(0.02)
            URL = f"{self.host}/jobs/{collectionUUID}/status"
            res = requests.get(URL)
            if res.json().get("status") == "SUCCESS":
                URL = f"{self.host}/jobs/{collectionUUID}/result"
                res = requests.get(URL)
                return res.json()

    def batch_execute(self, circuits):
        # res_results = []
        # for circuit in circuits:
        #     jobUUID = self._job_submit(circuit)
        #     res_result = self._check_job_status(jobUUID)
        #     res_results.append(res_result["results"][0])

        collectionUUID = self._jobs_submit(circuits)
        tmp_results = self._check_jobs_status(collectionUUID)

        res_results = [res_result["results"][0] for res_result in tmp_results]

        results = []
        for circuit, res_result in zip(circuits, res_results):
            self._samples = self._convert_counts_to_samples(
                res_result["data"]["counts"], circuit.num_wires
            )

            res = self.statistics(circuit)
            single_measurement = len(circuit.measurements) == 1
            res = res[0] if single_measurement else tuple(res)
            results.append(res)

        return results
