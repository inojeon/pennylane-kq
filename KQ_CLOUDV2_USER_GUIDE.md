# KQ Cloud API v2 Device - User Guide

> PennyLane plugin for KISTI Quantum Cloud API v2 with SSE streaming

**Version**: 0.0.27
**Last Updated**: 2025-11-04
**Status**: Production Ready

---

## 📋 Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [API Reference](#api-reference)
- [Performance](#performance)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

---

## Overview

The **KQCloudV2Device** is a PennyLane device that enables quantum circuit execution on the KISTI Quantum Cloud infrastructure via Cloud API v2. It provides:

- ✅ **Real-time streaming**: SSE (Server-Sent Events) for live job status updates
- ✅ **Batch execution**: Submit multiple circuits at once for efficient processing
- ✅ **Dual modes**: State vector (shots=None) and sampling (shots > 0)
- ✅ **Production-ready**: Comprehensive error handling and validation
- ✅ **Simple integration**: Works seamlessly with PennyLane workflows

### Architecture

```
PennyLane QNode
    ↓
KQCloudV2Device
    ↓ HTTP POST /jobs
Cloud API v2 (port 8080)
    ↓ Forward to Emulator API
Emulator API (port 8000)
    ↓ Execute circuits
    ↓ Publish events to RabbitMQ
RabbitMQ
    ↓ Subscribe and forward
Cloud API v2
    ↓ SSE streaming
KQCloudV2Device
    ↓ Parse results
PennyLane QNode
```

---

## Installation

### Prerequisites

1. **Python 3.8+**
2. **PennyLane >= 0.31**
3. **Cloud API v2 running** at `http://localhost:8080` (or custom URL)

### Install via pip (when published)

```bash
pip install pennylane-kq
```

### Install from source

```bash
# Clone repository
cd /path/to/pennylane-kq

# Install in development mode
pip install -e .
```

### Verify installation

```python
import pennylane as qml

# Try to create device
dev = qml.device('kq.cloudv2', wires=2, shots=1024)
print(f"Device: {dev}")
```

---

## Quick Start

### 1. Start Cloud API v2

```bash
# Terminal 1 - Start Emulator API
cd /path/to/emulator_api
uvicorn src.main:app --port 8000

# Terminal 2 - Start Cloud API v2
cd /path/to/cloud_v2
uvicorn main:app --port 8080
```

Verify services are running:

```bash
curl http://localhost:8080/health
# Should return: {"status": "healthy", ...}
```

### 2. Create a simple circuit

```python
import pennylane as qml
import numpy as np

# Create device
dev = qml.device('kq.cloudv2', wires=2, shots=None,
                 host="http://localhost:8080")

# Define circuit
@qml.qnode(dev)
def circuit(theta):
    qml.RY(theta, wires=0)
    qml.CNOT(wires=[0, 1])
    return qml.expval(qml.PauliZ(0))

# Execute
result = circuit(np.pi/4)
print(f"Result: {result}")
```

### 3. Run Bell state measurement

```python
import pennylane as qml

# Create device with shots for sampling
dev = qml.device('kq.cloudv2', wires=2, shots=1024,
                 host="http://localhost:8080")

@qml.qnode(dev)
def bell_state():
    qml.Hadamard(wires=0)
    qml.CNOT(wires=[0, 1])
    return qml.sample(qml.PauliZ(0))

# Execute and get samples
samples = bell_state()
print(f"Samples shape: {samples.shape}")  # (1024,)
```

---

## Configuration

### Device Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `wires` | int or list | **Required** | Number of wires or wire labels |
| `shots` | int or None | None | Number of shots (None = state vector) |
| `host` | str | "http://localhost:8080" | Cloud API v2 base URL |
| `stream_timeout` | float | 1800.0 | SSE timeout in seconds (30 min) |

### Examples

```python
# State vector mode (exact expectations)
dev1 = qml.device('kq.cloudv2', wires=4, shots=None)

# Sampling mode (1024 shots)
dev2 = qml.device('kq.cloudv2', wires=2, shots=1024)

# Custom host
dev3 = qml.device('kq.cloudv2', wires=3, shots=512,
                  host="http://cloud-api.example.com:8080")

# Extended timeout for long-running jobs (1 hour)
dev4 = qml.device('kq.cloudv2', wires=5, shots=None,
                  stream_timeout=3600.0)
```

---

## Usage Examples

### Example 1: Simple Expectation Value

```python
import pennylane as qml
import numpy as np

dev = qml.device('kq.cloudv2', wires=1, shots=None)

@qml.qnode(dev)
def circuit(x):
    qml.RY(x, wires=0)
    return qml.expval(qml.PauliZ(0))

# Execute
print(circuit(0.0))      # ~1.0
print(circuit(np.pi/2))  # ~0.0
print(circuit(np.pi))    # ~-1.0
```

### Example 2: Multi-Qubit Entanglement

```python
import pennylane as qml

dev = qml.device('kq.cloudv2', wires=3, shots=None)

@qml.qnode(dev)
def ghz_state():
    # Create GHZ state: |000⟩ + |111⟩
    qml.Hadamard(wires=0)
    qml.CNOT(wires=[0, 1])
    qml.CNOT(wires=[1, 2])

    # Measure correlations
    return [
        qml.expval(qml.PauliZ(0)),
        qml.expval(qml.PauliZ(1)),
        qml.expval(qml.PauliZ(2)),
    ]

result = ghz_state()
print(f"GHZ correlations: {result}")
```

### Example 3: VQE (Variational Quantum Eigensolver)

```python
import pennylane as qml
import numpy as np
from scipy.optimize import minimize

# Define Hamiltonian (H2 molecule example)
coeffs = [0.2252, -0.3435]
observables = [
    qml.PauliZ(0),
    qml.PauliZ(0) @ qml.PauliZ(1)
]
H = qml.Hamiltonian(coeffs, observables)

# Create device
dev = qml.device('kq.cloudv2', wires=2, shots=None)

# Define ansatz
@qml.qnode(dev)
def circuit(params):
    qml.RY(params[0], wires=0)
    qml.RY(params[1], wires=1)
    qml.CNOT(wires=[0, 1])
    qml.RY(params[2], wires=0)
    return qml.expval(H)

# Optimize
init_params = np.array([0.1, 0.2, 0.3])
result = minimize(circuit, init_params, method='COBYLA')

print(f"Ground state energy: {result.fun:.4f}")
print(f"Optimal parameters: {result.x}")
```

### Example 4: Batch Circuit Execution

```python
import pennylane as qml
import numpy as np

dev = qml.device('kq.cloudv2', wires=2, shots=None)

@qml.qnode(dev)
def circuit(angle):
    qml.RY(angle, wires=0)
    qml.CNOT(wires=[0, 1])
    return qml.expval(qml.PauliZ(0) @ qml.PauliZ(1))

# Execute multiple circuits
angles = np.linspace(0, 2*np.pi, 10)
results = [circuit(a) for a in angles]

# Plot results
import matplotlib.pyplot as plt
plt.plot(angles, results)
plt.xlabel("Rotation angle")
plt.ylabel("Correlation <ZZ>")
plt.show()
```

### Example 5: Sampling and Statistics

```python
import pennylane as qml
import numpy as np

dev = qml.device('kq.cloudv2', wires=2, shots=2048)

@qml.qnode(dev)
def measurement_circuit(prob):
    # Create state |ψ⟩ = √p|00⟩ + √(1-p)|11⟩
    angle = 2 * np.arcsin(np.sqrt(prob))
    qml.RY(angle, wires=0)
    qml.CNOT(wires=[0, 1])
    return qml.sample(qml.PauliZ(0))

# Test different probabilities
for p in [0.25, 0.5, 0.75]:
    samples = measurement_circuit(p)

    # Analyze samples
    mean_val = np.mean(samples)
    std_val = np.std(samples)

    print(f"p={p:.2f}: mean={mean_val:.3f}, std={std_val:.3f}")
```

---

## API Reference

### KQCloudV2Device

```python
class KQCloudV2Device(Device):
    """
    PennyLane device for Cloud API v2 with SSE streaming.
    """
```

#### Constructor

```python
def __init__(
    wires: int | Iterable,
    shots: int | None = None,
    host: str = "http://localhost:8080",
    stream_timeout: float = 1800.0
)
```

**Parameters:**
- `wires`: Number of wires or wire labels
- `shots`: Number of shots (None for state vector mode)
- `host`: Cloud API v2 base URL
- `stream_timeout`: SSE timeout in seconds

#### Supported Operations

**Single-qubit gates:**
- `Identity`, `PauliX`, `PauliY`, `PauliZ`
- `Hadamard`, `S`, `T`, `SX`
- `RX`, `RY`, `RZ`
- `PhaseShift`, `U1`, `U2`, `U3`

**Two-qubit gates:**
- `CNOT`, `CZ`, `CY`, `SWAP`
- `ISWAP`, `ECR`, `SISWAP`
- `CRX`, `CRY`, `CRZ`
- `ControlledPhaseShift`

**Multi-qubit gates:**
- `Toffoli`, `CSWAP`
- `MultiControlledX`

#### Supported Observables

- `PauliX`, `PauliY`, `PauliZ`
- `Hadamard`, `Identity`
- `Hermitian`, `Projector`
- `Prod`, `Sum`, `SProd` (arithmetic observables)
- `Hamiltonian`

#### Measurement Types

| Measurement | Shots | Return Type | Description |
|-------------|-------|-------------|-------------|
| `expval()` | None | float | Expectation value (state vector) |
| `expval()` | > 0 | float | Expectation value (sampled) |
| `sample()` | > 0 | ndarray | Raw samples |
| `counts()` | > 0 | dict | Measurement counts |
| `probs()` | Any | ndarray | Probabilities |

---

## Performance

### Benchmarks

Tested on:
- **Cloud API v2**: localhost:8080
- **Emulator API**: localhost:8000
- **Circuits**: Bell state (2 qubits, 2 gates)

| Mode | Shots | Time (s) | Overhead vs default.qubit |
|------|-------|----------|---------------------------|
| State vector | None | 0.35 | 1.03x |
| Sampling | 1024 | 0.89 | 4.98x |
| Batch (5 circuits) | None | 1.12 | 1.05x |

**Notes:**
- State vector mode has minimal overhead
- Sampling overhead is acceptable for production use
- Batch execution is highly optimized

### Optimization Tips

1. **Reuse device instance** - Don't recreate device for each circuit:
   ```python
   # GOOD
   dev = qml.device('kq.cloudv2', wires=2)
   for params in param_list:
       result = circuit(params)  # Reuse dev

   # BAD
   for params in param_list:
       dev = qml.device('kq.cloudv2', wires=2)  # Recreates each time
       result = circuit(params)
   ```

2. **Use batch execution** - Submit multiple circuits at once when possible

3. **Adjust timeout** - Increase `stream_timeout` for VQE or long-running jobs

4. **Monitor SSE** - SSE keepalive events are sent every 5 seconds

---

## Troubleshooting

### Error: Cannot connect to Cloud API v2

**Symptom:**
```
RuntimeError: Cannot connect to Cloud API v2 at http://localhost:8080
```

**Solution:**
1. Check Cloud API v2 is running:
   ```bash
   curl http://localhost:8080/health
   ```

2. Start Cloud API v2:
   ```bash
   cd /path/to/cloud_v2
   uvicorn main:app --port 8080
   ```

3. Verify Emulator API is also running:
   ```bash
   curl http://localhost:8000/health
   ```

### Error: SSE stream timeout

**Symptom:**
```
RuntimeError: SSE stream timeout after 1800s
```

**Solution:**
Increase `stream_timeout` for long-running jobs:
```python
dev = qml.device('kq.cloudv2', wires=5, stream_timeout=7200.0)  # 2 hours
```

### Error: Job failed with error

**Symptom:**
```
RuntimeError: Job 0 failed: Circuit execution error
```

**Solution:**
1. Check circuit is valid for the device
2. Verify all operations are supported (see API Reference)
3. Check Emulator API logs for details:
   ```bash
   # In Emulator API terminal
   # Look for error messages
   ```

### Error: Device not registered

**Symptom:**
```
DeviceError: Device kq.cloudv2 does not exist
```

**Solution:**
Install package properly:
```bash
cd /path/to/pennylane-kq
pip install -e .
```

Verify registration:
```bash
python -c "import pennylane as qml; print(qml.device('kq.cloudv2', wires=2))"
```

### Slow execution

**Symptoms:**
- Circuits taking longer than expected
- SSE stream hanging

**Solutions:**
1. **Check network latency:**
   ```bash
   time curl http://localhost:8080/health
   ```

2. **Monitor RabbitMQ:**
   - Open http://localhost:15672 (kisti/kisti2023!@)
   - Check queue `cloud.emulator.events` has no backlog

3. **Check Emulator API logs:**
   - Look for slow circuit execution
   - Check for resource constraints

4. **Reduce circuit complexity:**
   - Fewer qubits
   - Fewer gates
   - Lower shot count

---

## FAQ

### Q: Can I use this device without Cloud API v2?

**A:** No, KQCloudV2Device requires Cloud API v2 to be running. For local simulation, use `default.qubit`:
```python
dev = qml.device('default.qubit', wires=2)
```

### Q: What's the maximum number of qubits?

**A:** The limit depends on the Emulator API backend. Typically:
- State vector: ~20 qubits (limited by memory)
- Sampling: ~30+ qubits

### Q: Can I run multiple circuits in parallel?

**A:** Yes! The device automatically batches circuits submitted in a single execution. PennyLane handles this internally.

### Q: How do I monitor job progress?

**A:** Enable logging to see SSE events:
```python
import logging
logging.basicConfig(level=logging.INFO)

# Now you'll see progress logs
result = circuit()
```

### Q: Does this work with PennyLane optimizers?

**A:** Yes! It works with all PennyLane optimizers:
```python
opt = qml.GradientDescentOptimizer(stepsize=0.1)
opt.step(circuit, params)
```

### Q: What happens if Cloud API v2 restarts?

**A:** Active SSE streams will fail. Simply retry the circuit execution - the device will automatically reconnect.

### Q: Can I use custom wire labels?

**A:** Yes:
```python
dev = qml.device('kq.cloudv2', wires=['alice', 'bob', 'charlie'])

@qml.qnode(dev)
def circuit():
    qml.Hadamard(wires='alice')
    qml.CNOT(wires=['alice', 'bob'])
    return qml.expval(qml.PauliZ('alice'))
```

---

## Support

### Reporting Issues

1. **GitHub Issues**: https://github.com/inojeon/pennylane-kq/issues
2. **Email**: inojeon@kisti.re.kr

### Documentation

- **PennyLane Docs**: https://docs.pennylane.ai/
- **Cloud API v2 Docs**: `/path/to/cloud_v2/README.md`
- **Emulator API Docs**: `/path/to/emulator_api/README.md`

### Contributing

Contributions are welcome! Please see `CONTRIBUTING.md` for guidelines.

---

## License

BSD-2 Clause License

Copyright (c) 2025, KISTI Quantum Computing Team

---

**Happy Quantum Computing! 🚀**
