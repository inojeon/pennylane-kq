"""Offline tests for public device imports, registration, and shared behavior."""

import os
import sys
import unittest
from importlib.metadata import distribution
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pennylane as qml
import pennylane_kq
from pennylane_kq import KQEmulatorDevice, KQQPUDevice


DEVICES = (
    ("kq.emulator", KQEmulatorDevice, "kisti.emulator", "KQ Emulator Device"),
    ("kq.qpu", KQQPUDevice, "kriss.hw_20q", "KQ QPU Device"),
    ("kq.qpu", KQQPUDevice, "kriss.hw_50q", "KQ QPU Device"),
)


class DeviceTests(unittest.TestCase):
    def test_public_exports(self):
        self.assertEqual(set(pennylane_kq.__all__),
                         {"KQEmulatorDevice", "KQQPUDevice", "__version__"})
        self.assertFalse(hasattr(pennylane_kq, "KQCloudV2Device"))
        self.assertFalse(hasattr(pennylane_kq, "_KQBaseDevice"))

    def test_device_initialization(self):
        for name, device_class, target, _ in DEVICES:
            with self.subTest(name=name, target=target):
                dev = device_class(wires=2, shots=1024,
                                   api_key="test-key", target=target)
                self.assertEqual(len(dev.wires), 2)
                self.assertEqual(dev.shots.total_shots, 1024)
                self.assertEqual(dev.host, "https://qc-api.kisti.re.kr")
                self.assertEqual(dev.api_key, "test-key")
                self.assertEqual(dev.target, target)
                self.assertEqual(dev.stream_timeout, 1800.0)
                self.assertEqual(dev.poll_interval, 2.0)
                self.assertFalse(dev.use_streaming)

                custom = device_class(
                    wires=["a", "b"], shots=2048, api_key="test-key",
                    target=target, host="http://custom-host:9000/",
                    stream_timeout=3600.0, poll_interval=5.0,
                    use_streaming=True,
                )
                self.assertEqual(list(custom.wires), ["a", "b"])
                self.assertEqual(custom.shots.total_shots, 2048)
                self.assertEqual(custom.host, "http://custom-host:9000")
                self.assertEqual(custom.stream_timeout, 3600.0)
                self.assertEqual(custom.poll_interval, 5.0)
                self.assertTrue(custom.use_streaming)

    def test_required_parameters(self):
        for name, device_class, target, _ in DEVICES:
            for parameter in ("api_key", "target", "shots"):
                with self.subTest(name=name, target=target, missing=parameter):
                    kwargs = dict(wires=2, shots=1024,
                                  api_key="test-key", target=target)
                    del kwargs[parameter]
                    with self.assertRaisesRegex(ValueError, parameter):
                        device_class(**kwargs)
        with self.assertRaisesRegex(ValueError, "wires"):
            KQQPUDevice(shots=1024, api_key="test-key", target="kriss.hw_20q")

    def test_device_metadata(self):
        for name, device_class, target, display_name in DEVICES:
            with self.subTest(name=name, target=target):
                dev = device_class(wires=1, shots=1, api_key="test-key", target=target)
                self.assertEqual(dev.name, display_name)
                self.assertEqual(dev.short_name, name)
                self.assertEqual(dev.version, pennylane_kq.__version__)
                self.assertEqual(dev.author, "KISTI Quantum Computing Team")

    def test_pennylane_device_registration(self):
        registered = {
            entry.name for entry in distribution("pennylane-kq").entry_points
            if entry.group == "pennylane.plugins"
        }
        self.assertEqual(registered, {"kq.emulator", "kq.qpu"})
        for name, device_class, target, _ in DEVICES:
            with self.subTest(name=name, target=target):
                dev = qml.device(name, wires=2, shots=1024,
                                 api_key="test-key", target=target)
                self.assertIsInstance(dev, device_class)
        with self.assertRaises(qml.exceptions.DeviceError):
            qml.device("kq.cloudv2", wires=2, shots=1024,
                       api_key="test-key", target="kisti.emulator")

    def test_shared_execution(self):
        for name, device_class, target, _ in DEVICES:
            with self.subTest(name=name, target=target):
                dev = device_class(wires=2, shots=100, api_key="test-key", target=target)

                @qml.qnode(dev)
                def circuit():
                    qml.Hadamard(0)
                    qml.CNOT([0, 1])
                    return qml.expval(qml.Z(0)), qml.counts(wires=[0, 1])

                with patch("pennylane_kq.utils.http_client.submit_batch",
                           return_value=("batch", ["job"])) as submit, patch(
                    "pennylane_kq.utils.http_client.poll_batch_results",
                    return_value=[{"status": "SUCCESS", "result": {
                        "counts": {"00": 50, "11": 50}}}],
                ) as poll:
                    self.assertEqual(circuit(), (0.0, {"00": 50, "11": 50}))
                self.assertEqual(submit.call_args.args[3], target)
                self.assertEqual(poll.call_args.args[3], target)
                job = submit.call_args.args[1]["jobs"][0]
                self.assertEqual(job["shots"], 100)
                self.assertTrue(job["circuit"].startswith("OPENQASM 2.0;"))


if __name__ == "__main__":
    unittest.main()
