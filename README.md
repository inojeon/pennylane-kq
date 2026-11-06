# PennyLane-KQ

## Devices and targets

| Device | Target | Resource |
| --- | --- | --- |
| `kq.emulator` | `kisti.sim1` | Simulator |
| `kq.emulator` | `kisti.emulator` | KISTI emulator |
| `kq.qpu` | `kriss.hw_20q` | KRISS 20-qubit QPU |
| `kq.qpu` | `kriss.hw_50q` | KRISS 50-qubit QPU |

```python
import pennylane as qml

dev = qml.device("kq.qpu", target="kriss.hw_20q", wires=3, shots=1024,
                 api_key="your-api-key")

@qml.qnode(dev)
def circuit():
    qml.Hadamard(0)
    qml.CNOT([0, 1])
    return qml.counts(wires=[0, 1])

# circuit() submits a real hardware job.
```

Reinstall the package and restart notebook kernels after adding the device.
The host is the cloud web service; that service must register both target codes
and route them to the corresponding KRISS execution services. The plugin does
not provision routing. KRISS emulator_api uses krios for native gate compilation,
topology routing and physical qubit mapping.

QPU target and wires are explicit. Nominal capacity is 20/50 qubits; the server
determines current availability. Wires are logical labels, not physical choices.
Finite shots are required. Polling and the existing 1800-second total wait remain
the defaults; set stream_timeout for longer queue waits. Timeout does not cancel
the server job. Existing gate metadata does not enforce native gate decomposition.

See [Testing](#testing) for the offline suites covering device registration,
shared execution, HTTP requests, and optional QASM compatibility.

Before production use, verify routing and small-circuit results on both real
targets. Offline tests do not verify hardware availability or krios configuration.

PennyLane plugin for the KISTI Quantum Cloud service.

## Overview

**pennylane-kq** provides `kq.emulator` for software simulation and `kq.qpu` for KRISS quantum hardware through KISTI's cloud web service.

With `kq.emulator`, select `target="kisti.sim1"` for the simulator running
locally in the cloud service, or `target="kisti.emulator"` for the KISTI
emulator. The plugin submits both to the cloud API; the server routes jobs
using the `QC-TARGET` header. The simulator runs on the cloud server.

These are the only public devices. Both share the internal `_KQBaseDevice`
implementation for preprocessing, OpenQASM 2 submission, and result processing.
See the [device user guide](KQ_DEVICE_USER_GUIDE.md) for configuration and batch examples.

### Migrating existing notebooks

`kq.cloudv2` and the public `KQCloudV2Device` class have been removed.
Replace emulator calls with `qml.device("kq.emulator", ...)` and
`target="kisti.sim1"` for cloud-local simulation or `target="kisti.emulator"`
for the KISTI emulator. Use `qml.device("kq.qpu", ...)` with an explicit
KRISS target and `wires` for hardware. Replace direct class imports with
`KQEmulatorDevice` or `KQQPUDevice`. The internal base class is not a public device.

After updating the checkout, run `python -m pip install -e .` and restart the
Jupyter kernel so PennyLane reloads the device registrations.

### Features

- Execute PennyLane circuits on remote quantum hardware/emulator
- Real-time SSE (Server-Sent Events) streaming with automatic fallback to HTTP polling
- Batch job submission
- Automatic retry with exponential backoff

## Installation

### From Source

```bash
pip install git+https://github.com/inojeon/pennylane-kq.git
```

For a local checkout:

```bash
python -m pip install -e .
```

### From PyPI (Coming Soon)

```bash
pip install pennylane-kq
```

## Requirements

- Python >= 3.8
- PennyLane >= 0.40
- KISTI Quantum Cloud API key (`api_key`)

## Quick Start

```python
import pennylane as qml

# Create device
dev = qml.device('kq.emulator',
                 wires=2,
                 shots=1024,
                 api_key="your-api-key",
                 target="kisti.emulator")

# Define circuit
@qml.qnode(dev)
def circuit():
    qml.Hadamard(wires=0)
    qml.CNOT(wires=[0, 1])
    return qml.expval(qml.PauliZ(0))

# Execute
result = circuit()
print(f"Expectation value: {result}")
```

## Device Parameters

- `wires` (int or iterable): Number of qubits or wire labels; required for `kq.qpu`
- `shots` (int, required): One positive shot count; statevector mode and shot vectors are unsupported
- `api_key` (str, required): QC-API-KEY for authentication
- `target` (str, required): QC-TARGET device code
- `host` (str): KISTI Quantum Cloud API URL (default: "https://qc-api.kisti.re.kr")
- `use_streaming` (bool): Use SSE streaming (default: False)
- `stream_timeout` (float): Total polling wait limit / SSE timeout in seconds (default: 1800.0)
- `poll_interval` (float): Polling interval in seconds (default: 2.0)
- `max_retries` (int): Maximum retries for failed requests (default: 3)

## Examples

```python
dev = qml.device('kq.emulator',
                 wires=2,
                 shots=1024,
                 api_key="your-api-key",
                 target="kisti.emulator")

@qml.qnode(dev)
def circuit():
    qml.Hadamard(wires=0)
    qml.CNOT(wires=[0, 1])
    return qml.sample(qml.PauliZ(0))

samples = circuit()  # Returns numpy array of 1024 samples
```

## Testing

All scripts stay in `test/`; the filename prefix identifies their purpose:

| Prefix | Files | Purpose |
| --- | --- | --- |
| `test_` | `test_devices.py`, `test_http_client.py`, `test_qasm_compatibility.py` | Offline automated tests |
| `example_` | `example_emulator.py`, `example_qpu.py` | Remote circuit execution examples |
| `benchmark_` | `benchmark_bernstein_vazirani.py`, `benchmark_random_circuit.py` | Performance benchmarks including cloud execution |

Run all offline tests (no remote jobs are submitted):

```bash
python -m unittest discover -s test -p 'test_*.py'
```

`make test` runs the same offline suites using Python's built-in unittest
runner. The QASM compatibility suite runs when Qiskit is installed and otherwise
skips. The optional `make coverage` target requires pytest and pytest-cov.

### Execution examples and benchmarks

Set `API_KEY = "your-api-key"` to your issued API key in each script before
running it. `TARGET` and `SHOTS` can also be edited at the top of the examples.
In JupyterLab, run:

```ipython
%run test/example_emulator.py --target kisti.sim1
%run test/example_emulator.py --target kisti.emulator --mode batch
%run test/example_qpu.py --target kriss.hw_20q
```

For terminal execution, replace `%run` with `python`. The emulator example
supports Bell counts and a three-circuit batch. The QPU example submits one
Bell circuit and reports counts, shot totals, and probabilities.

The two `benchmark_*.py` scripts can be run the same way. They compare
Bernstein-Vazirani execution or measure a deep random circuit. Examples and
benchmarks submit remote jobs when executed; importing them does not execute
circuits.

## Troubleshooting

### SSE Streaming Fails

SSE Streaming is not available now. 
Please use HTTP polling mode instead. (`use_streaming=False`)
### Device Not Found Error

If you get a device-not-found error for `kq.emulator` or `kq.qpu`, make sure the package is installed:

```bash
pip install -e .
python -c "from pennylane_kq import KQEmulatorDevice, KQQPUDevice; print('OK')"
```

### Authentication Error

If you get an authentication error, check that your `api_key` and `target` are correct:

```python
dev = qml.device('kq.emulator',
                 wires=2,
                 shots=1024,
                 api_key="your-api-key",   # Check this
                 target="kisti.emulator")   # Check this
```



## Version

Current version: **0.0.31** (see `pennylane_kq/_version.py`).

## Authors

**KISTI Quantum Computing Team**

Korea Institute of Science and Technology Information (KISTI)

## License

BSD-2-Clause

## Contributing

Install the project with `python -m pip install -e .` and run the offline
tests listed above before submitting changes.

## Support

For issues and questions:
- GitHub Issues: https://github.com/inojeon/pennylane-kq/issues
- Contact: inojeon@kisti.re.kr / soyeongp@kisti.re.kr
