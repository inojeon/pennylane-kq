import qiskit
from qiskit_aer import AerSimulator

# Generate 2-qubit GHZ state
circ = qiskit.QuantumCircuit(2, 2)
circ.h(0)
circ.cx(0, 1)
# circ.measure_all()
circ.measure(0, 0)

# Construct an ideal simulator
aersim = AerSimulator()

# Perform an ideal simulation
result_ideal = aersim.run(circ).result()
counts_ideal = result_ideal.get_counts(0)
print("Counts(ideal):", counts_ideal)
