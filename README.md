# PennyLane-KQ

PennyLane plugin for KISTI Quantum Cloud API v2.

## Overview

**pennylane-kq** provides a PennyLane device (`kq.cloudv2`) for executing quantum circuits on KISTI's quantum computing cloud infrastructure.

### Features

- Execute PennyLane circuits on remote quantum emulator
- Real-time SSE (Server-Sent Events) streaming with automatic fallback to HTTP polling
- Support for state vector and sampling modes
- Batch job submission
- Automatic retry with exponential backoff

## Installation

### From Source (Development)

```bash
git clone https://github.com/inojeon/pennylane-kq.git
cd pennylane-kq
pip install -e .
```

### From PyPI (Coming Soon)

```bash
pip install pennylane-kq
```

## Requirements

- Python >= 3.8
- PennyLane >= 0.40
- Cloud API v2 server running at http://localhost:8080

## Quick Start

```python
import pennylane as qml

# Create device
dev = qml.device('kq.cloudv2', wires=2, shots=1024)

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

- `wires` (int, required): Number of qubits
- `shots` (int | None): Number of shots (None for state vector mode)
- `host` (str): Cloud API v2 URL (default: "http://localhost:8080")
- `use_streaming` (bool): Use SSE streaming (default: True)
- `stream_timeout` (float): SSE timeout in seconds (default: 1800.0)
- `poll_interval` (float): Polling interval in seconds (default: 2.0)

## Examples

### State Vector Mode (shots=None)

```python
dev = qml.device('kq.cloudv2', wires=2, shots=None)

@qml.qnode(dev)
def circuit(theta):
    qml.RY(theta, wires=0)
    return qml.expval(qml.PauliZ(0))

result = circuit(0.5)  # Returns expectation value
```

### Sampling Mode (shots>0)

```python
dev = qml.device('kq.cloudv2', wires=2, shots=1024)

@qml.qnode(dev)
def circuit():
    qml.Hadamard(wires=0)
    qml.CNOT(wires=[0, 1])
    return qml.sample(qml.PauliZ(0))

samples = circuit()  # Returns numpy array of 1024 samples
```

### Custom Server URL

```python
dev = qml.device('kq.cloudv2',
                 wires=4,
                 shots=2048,
                 host="http://cloud.kisti.re.kr:8080")
```

### Polling Mode (No SSE)

```python
dev = qml.device('kq.cloudv2',
                 wires=2,
                 shots=1024,
                 use_streaming=False,
                 poll_interval=1.0)
```

## Documentation

- **Developer Guide**: [CLAUDE.md](CLAUDE.md) - Comprehensive developer documentation
- **API Specification**: [docs/API_SPECIFICATION.md](docs/API_SPECIFICATION.md) - API details
- **Cloud API v2**: See `/cloud_v2/CLAUDE.md` in parent project
- **Emulator API**: See `/emulator_api/CLAUDE.md` in parent project

## Testing

Run basic tests:
```bash
python tests/test_kq_cloudv2_basic.py
```

Run integration tests (requires Cloud API v2 running):
```bash
python tests/test_kq_cloudv2_integration.py
```

## Troubleshooting

### Device Not Found Error

If you get `DeviceError: Device 'kq.cloudv2' not found`, make sure the package is installed:

```bash
pip install -e .
python -c "from pennylane_kq import KQCloudV2Device; print('OK')"
```

### Connection Error

If you get `RuntimeError: Cannot connect to Cloud API v2`:

1. Check that Cloud API v2 is running:
   ```bash
   curl http://localhost:8080/api/health
   ```

2. Verify the host parameter matches your server URL

### SSE Streaming Fails

If SSE streaming fails and device falls back to polling:

1. Check that RabbitMQ is running (required for SSE)
2. Use polling mode explicitly: `use_streaming=False`

See [CLAUDE.md](CLAUDE.md) for more troubleshooting tips.

## Version

Current version: **0.0.29**

See [CLAUDE.md](CLAUDE.md) for version history.

## Authors

**KISTI Quantum Computing Team**

Korea Institute of Science and Technology Information (KISTI)

## License

BSD-2-Clause

## Contributing

For development setup and guidelines, see [CLAUDE.md](CLAUDE.md).

## Support

For issues and questions:
- GitHub Issues: https://github.com/inojeon/pennylane-kq/issues
- Contact: inojeon@kisti.re.kr
