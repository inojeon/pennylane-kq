"""Optional parser and semantic checks requiring Qiskit."""
import unittest
import numpy as np
import pennylane as qml
from pennylane.tape import QuantumScript
from pennylane_kq import KQQPUDevice

try:
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector
except ImportError:
    QuantumCircuit = None


@unittest.skipIf(QuantumCircuit is None, "Qiskit is required for round-trip tests")
class QASMTests(unittest.TestCase):
    def test_probabilities_including_controlled_phase(self):
        for op in (qml.SX(0), qml.ECR([0, 1]), qml.SISWAP([0, 1]),
                   qml.ctrl(qml.GlobalPhase(0.7), control=0),
                   qml.QubitUnitary(np.array([[0, 1], [1, 0]]), 0)):
            with self.subTest(operation=op.name):
                ops = [qml.Hadamard(0), op, qml.Hadamard(0)]
                tape = QuantumScript(ops, [qml.counts(wires=[0, 1])], shots=100)
                dev = KQQPUDevice(wires=2, shots=100, api_key="test",
                                  target="kriss.hw_20q")
                code = dev._prepare_jobs([tape])["jobs"][0]["circuit"]
                qc = QuantumCircuit.from_qasm_str(code)
                qc.remove_final_measurements()
                actual = Statevector.from_instruction(qc).probabilities().reshape(2, 2).T.ravel()
                expected = qml.device("default.qubit", wires=2).execute(
                    QuantumScript(ops, [qml.probs(wires=[0, 1])]))
                np.testing.assert_allclose(actual, expected, atol=1e-10)
