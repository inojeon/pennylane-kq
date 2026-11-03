"""Offline QPU integration tests; no hardware jobs are submitted."""
import unittest
from unittest.mock import patch

import numpy as np
import pennylane as qml
from pennylane.tape import QuantumScript

from pennylane_kq import KQQPUDevice


class QPUTests(unittest.TestCase):
    def device(self, target="kriss.hw_20q", wires=3):
        return KQQPUDevice(wires=wires, shots=100, target=target, api_key="test")

    def test_registration_and_capacity(self):
        for target, size in KQQPUDevice.target_capacities.items():
            dev = qml.device("kq.qpu", target=target, wires=size,
                             shots=100, api_key="test")
            self.assertIsInstance(dev, KQQPUDevice)
            with self.assertRaisesRegex(ValueError, "at most"):
                self.device(target, size + 1)
        for target in (None, "kisti.emulator", "kriss.hw_21q"):
            with self.assertRaisesRegex(ValueError, "target"):
                self.device(target)

    def test_direct_execution_validation(self):
        dev = self.device()
        tape = QuantumScript([qml.X(4)], [qml.counts(wires=[4])], shots=100)
        with patch("pennylane_kq.utils.http_client.submit_batch") as submit:
            with self.assertRaisesRegex(ValueError, "device wires"):
                dev.execute([tape])
            submit.assert_not_called()

    def test_request_and_multiple_measurements(self):
        for target in KQQPUDevice.target_capacities:
            dev = self.device(target)
            with patch("pennylane_kq.utils.http_client.submit_batch",
                       return_value=("batch", ["job"])) as submit, patch(
                "pennylane_kq.utils.http_client.poll_batch_results",
                return_value=[{"status": "SUCCESS", "result": {
                    "counts": {"000": 50, "111": 50}}}],
            ) as poll:
                @qml.qnode(dev)
                def circuit():
                    qml.Hadamard(0)
                    qml.CNOT([0, 1])
                    qml.CNOT([1, 2])
                    return qml.expval(qml.Z(0)), qml.expval(qml.Z(1))
                self.assertEqual(tuple(circuit()), (0.0, 0.0))
                self.assertEqual(submit.call_args.args[3], target)
                self.assertEqual(poll.call_args.args[3], target)
                self.assertEqual(submit.call_args.args[1]["jobs"][0]["shots"], 100)

    def test_state_rejected_before_submission(self):
        dev = self.device()
        @qml.qnode(dev)
        def circuit():
            return qml.state()
        with patch("pennylane_kq.utils.http_client.submit_batch") as submit:
            with self.assertRaises(qml.exceptions.DeviceError):
                circuit()
            submit.assert_not_called()

    def test_qasm_keeps_high_level_gate(self):
        tape = QuantumScript([qml.SX(0), qml.Toffoli([0, 1, 2])],
                             [qml.counts(wires=[0, 1, 2])], shots=100)
        qasm = self.device()._prepare_jobs([tape])["jobs"][0]["circuit"]
        self.assertNotIn("gphase", qasm)
        self.assertIn("ccx", qasm)

    def test_implicit_measurements_include_idle_wires(self):
        wires = ["left", "idle", "right"]
        for measurement in (qml.counts, qml.probs, qml.sample):
            with self.subTest(measurement=measurement.__name__):
                dev = self.device(wires=wires)

                def circuit():
                    qml.X("right")
                    return measurement()

                reference = qml.QNode(
                    circuit, qml.device("default.qubit", wires=wires)
                )
                expected = qml.set_shots(reference, shots=100)()
                with patch("pennylane_kq.utils.http_client.submit_batch",
                           return_value=("batch", ["job"])) as submit, patch(
                    "pennylane_kq.utils.http_client.poll_batch_results",
                    return_value=[{"status": "SUCCESS", "result": {
                        "counts": {"100": 100}}}],
                ):
                    actual = qml.QNode(circuit, dev)()

                if measurement is qml.counts:
                    self.assertEqual(actual, expected)
                else:
                    np.testing.assert_array_equal(actual, expected)
                code = submit.call_args.args[1]["jobs"][0]["circuit"]
                self.assertIn("qreg q[3];", code)
                self.assertIn("x q[0];", code)
                self.assertEqual(code.count("measure q["), 3)

    def test_implicit_measurement_without_gates(self):
        dev = self.device()

        @qml.qnode(dev)
        def circuit():
            return qml.counts()

        with patch("pennylane_kq.utils.http_client.submit_batch",
                   return_value=("batch", ["job"])) as submit, patch(
            "pennylane_kq.utils.http_client.poll_batch_results",
            return_value=[{"status": "SUCCESS", "result": {
                "counts": {"000": 100}}}],
        ):
            self.assertEqual(circuit(), {"000": 100})
        code = submit.call_args.args[1]["jobs"][0]["circuit"]
        self.assertIn("qreg q[3];", code)
        self.assertEqual(code.count("measure q["), 3)

    def test_direct_execution_resolves_implicit_measurement_wires(self):
        dev = self.device()
        tape = QuantumScript([qml.X(2)], [qml.counts()], shots=7)
        with patch("pennylane_kq.utils.http_client.submit_batch",
                   return_value=("batch", ["job"])) as submit, patch(
            "pennylane_kq.utils.http_client.poll_batch_results",
            return_value=[{"status": "SUCCESS", "result": {
                "counts": {"100": 7}}}],
        ):
            self.assertEqual(dev.execute(tape), ({"001": 7},))
        code = submit.call_args.args[1]["jobs"][0]["circuit"]
        self.assertIn("qreg q[3];", code)
        self.assertEqual(list(tape.measurements[0].wires), [])

    def test_qnode_shots_override_is_submitted(self):
        dev = self.device(wires=1)

        @qml.set_shots(7)
        @qml.qnode(dev)
        def circuit():
            qml.X(0)
            return qml.counts(wires=[0])

        with patch("pennylane_kq.utils.http_client.submit_batch",
                   return_value=("batch", ["job"])) as submit, patch(
            "pennylane_kq.utils.http_client.poll_batch_results",
            return_value=[{"status": "SUCCESS", "result": {
                "counts": {"1": 7}}}],
        ):
            self.assertEqual(circuit(), {"1": 7})
        self.assertEqual(submit.call_args.args[1]["jobs"][0]["shots"], 7)
        self.assertEqual(dev.shots.total_shots, 100)

    def test_direct_batch_uses_each_circuit_shots(self):
        tapes = [
            QuantumScript([], [qml.counts(wires=[0])], shots=7),
            QuantumScript([qml.X(0)], [qml.counts(wires=[0])], shots=11),
        ]
        with patch("pennylane_kq.utils.http_client.submit_batch",
                   return_value=("batch", ["job-0", "job-1"])) as submit, patch(
            "pennylane_kq.utils.http_client.poll_batch_results",
            return_value=[
                {"status": "SUCCESS", "result": {"counts": {"0": 7}}},
                {"status": "SUCCESS", "result": {"counts": {"1": 11}}},
            ],
        ):
            self.assertEqual(self.device(wires=1).execute(tapes),
                             ({"0": 7}, {"1": 11}))
        jobs = submit.call_args.args[1]["jobs"]
        self.assertEqual([job["shots"] for job in jobs], [7, 11])

    def test_shot_vectors_rejected_before_submission(self):
        for shots in ([5, 10], [(5, 2)]):
            with self.subTest(shots=shots):
                with self.assertRaisesRegex(ValueError, "[Ss]hot vectors"):
                    KQQPUDevice(wires=1, shots=shots, api_key="test",
                                target="kriss.hw_20q")

        dev = self.device(wires=1)

        @qml.set_shots([5, 10])
        @qml.qnode(dev)
        def circuit():
            return qml.counts(wires=[0])

        tape = QuantumScript([], [qml.counts(wires=[0])], shots=[5, 10])
        for execute in (circuit, lambda: dev.execute(tape)):
            with self.subTest(execute=execute), patch(
                "pennylane_kq.utils.http_client.submit_batch",
                side_effect=AssertionError("Invalid shots must not be submitted"),
            ) as submit:
                with self.assertRaisesRegex(ValueError, "[Ss]hot vectors"):
                    execute()
                submit.assert_not_called()

    def test_direct_analytic_circuit_rejected_before_submission(self):
        tape = QuantumScript([], [qml.counts(wires=[0])])
        with patch("pennylane_kq.utils.http_client.submit_batch",
                   side_effect=AssertionError("Analytic circuits must not be submitted")) as submit:
            with self.assertRaisesRegex(ValueError, "finite shots"):
                self.device(wires=1).execute(tape)
            submit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
