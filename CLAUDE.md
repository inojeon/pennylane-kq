# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with the **pennylane-kq** PennyLane plugin.

---

## Project Overview

**pennylane-kq** is a PennyLane plugin that enables quantum circuit execution on KISTI's quantum computing cloud infrastructure via the Cloud API v2.

### Purpose

- **Client library** for executing PennyLane quantum circuits on KISTI Cloud API v2
- **Device implementation** (`KQCloudV2Device`) for seamless PennyLane integration
- **Circuit serialization** utilities for converting PennyLane circuits to JSON format

### Version

Current version: `0.0.29` (defined in `pennylane_kq/_version.py`)

---

## Architecture

```
User Code (PennyLane)
    ↓
KQCloudV2Device
    ↓ serialize (serialization_utils.py)
JSON Circuit
    ↓ HTTP POST /api/jobs
Cloud API v2 (http://localhost:8080)
    ↓ SSE streaming or HTTP polling
Results
    ↓ deserialize + format
PennyLane Results (numpy arrays, floats)
```

### Key Components

1. **KQCloudV2Device** (`kq_cloudv2_device.py`)
   - PennyLane Device class implementation
   - Handles batch submission, streaming, polling, and result formatting
   - Version: 0.0.29

2. **Serialization Utils** (`serialization_utils.py`)
   - Circuit → JSON conversion
   - JSON → Circuit reconstruction
   - Supports operations, observables, measurements

3. **Version** (`_version.py`)
   - Single source of truth for package version

4. **Package Init** (`__init__.py`)
   - Exports `KQCloudV2Device` and `__version__`

---

## Core Components

### 1. KQCloudV2Device

**Location**: `pennylane_kq/kq_cloudv2_device.py`

**Purpose**: Main device class for Cloud API v2 integration

**Key Features**:
- SSE (Server-Sent Events) streaming with automatic fallback to HTTP polling
- Batch job submission (multiple circuits in one request)
- Exponential backoff retry logic
- Support for both state vector (shots=None) and sampling (shots>0) modes
- Flexible counts format handling (hex: "0x3" or binary: "11")

**Device Metadata**:
```python
name = "KQ Cloud API v2 Device"
short_name = "kq.cloudv2"
version = "0.0.29"
author = "KISTI Quantum Computing Team"
```

**Usage**:
```python
import pennylane as qml

# Create device
dev = qml.device('kq.cloudv2',
                 wires=2,
                 shots=1024,
                 host="http://localhost:8080",
                 use_streaming=True,
                 stream_timeout=1800.0,
                 poll_interval=2.0)

# Define circuit
@qml.qnode(dev)
def circuit():
    qml.Hadamard(wires=0)
    qml.CNOT(wires=[0, 1])
    return qml.expval(qml.PauliZ(0))

# Execute
result = circuit()
```

**Parameters**:
- `wires` (int): Number of qubits
- `shots` (int | None): Number of shots (None for state vector)
- `host` (str): Cloud API v2 URL (default: "http://localhost:8080")
- `use_streaming` (bool): Use SSE streaming (default: True)
- `stream_timeout` (float): SSE timeout in seconds (default: 1800.0)
- `poll_interval` (float): Polling interval in seconds (default: 2.0)

**Supported Operations** (109 total):
- Single-qubit gates: Hadamard, PauliX, PauliY, PauliZ, S, T, SX, RX, RY, RZ, PhaseShift, etc.
- Multi-qubit gates: CNOT, CZ, SWAP, Toffoli, CSWAP, etc.
- Controlled operations: ControlledPhaseShift, CRX, CRY, CRZ, etc.
- Special operations: QubitUnitary, MultiControlledX, etc.

**Supported Observables**:
- Pauli: PauliX, PauliY, PauliZ
- Special: Identity, Hadamard
- Composite: Hamiltonian, Hermitian, Projector
- Tensor products: e.g., `PauliX(0) @ PauliY(1)`

**Supported Measurements**:
- `qml.expval(obs)`: Expectation value
- `qml.var(obs)`: Variance
- `qml.sample(obs)`: Raw samples
- `qml.probs()`: Probability distribution
- `qml.counts()`: Measurement counts

### 2. Serialization Utils

**Location**: `pennylane_kq/serialization_utils.py`

**Purpose**: Convert PennyLane circuits to/from JSON format

**Key Functions**:

1. **Operation Serialization**:
   ```python
   serialize_operation(op) -> Dict[str, Any]
   deserialize_operation(data: Dict[str, Any]) -> Operation
   ```

2. **Observable Serialization**:
   ```python
   serialize_observable(obs) -> Dict[str, Any]
   deserialize_observable(data: Dict[str, Any]) -> Observable
   ```

3. **Measurement Serialization**:
   ```python
   serialize_measurement(measurement) -> Dict[str, Any]
   deserialize_measurement(data: Dict[str, Any]) -> MeasurementProcess
   ```

4. **Circuit Serialization**:
   ```python
   serialize_circuit(circuit: QuantumScript) -> Dict[str, Any]
   deserialize_circuit(data: Dict[str, Any]) -> QuantumScript
   ```

5. **Helper Functions**:
   ```python
   circuit_to_json_string(circuit: QuantumScript) -> str
   json_string_to_circuit(json_str: str) -> QuantumScript
   ```

**JSON Format Example**:
```json
{
  "operations": [
    {"name": "Hadamard", "wires": [0], "params": []},
    {"name": "CNOT", "wires": [0, 1], "params": []}
  ],
  "measurements": [
    {
      "type": "expval",
      "obs": {"type": "Simple", "name": "PauliZ", "wires": [0]}
    }
  ],
  "shots": null,
  "batch_size": null,
  "wires": [0, 1],
  "num_wires": 2
}
```

---

## Development Guide

### Adding New Operations

If you need to add support for a new PennyLane operation:

1. **Add to `operations` list** in `kq_cloudv2_device.py`:
   ```python
   operations = [
       # ... existing operations ...
       "NewOperation",  # Add new operation name
   ]
   ```

2. **Ensure backend support**: Verify that emulator_api supports the operation (check `emulator_api/src/emulator/circuit_executor.py`)

3. **Test**: Add test case to `tests/test_kq_cloudv2_integration.py`

### Adding New Observables

To support a new observable type:

1. **Add to `observables` list** in `kq_cloudv2_device.py`:
   ```python
   observables = [
       # ... existing observables ...
       "NewObservable",  # Add new observable name
   ]
   ```

2. **Update serialization** if needed (for complex observables):
   - Modify `serialize_observable()` in `serialization_utils.py`
   - Modify `deserialize_observable()` in `serialization_utils.py`

### Adding New Measurements

To support a new measurement type:

1. **Update serialization** in `serialization_utils.py`:
   - Add mapping in `serialize_measurement()` type_map
   - Add case in `deserialize_measurement()`

2. **Update result formatting** in `kq_cloudv2_device.py`:
   - Modify `_format_result()` method to handle new measurement type

### Modifying Retry Logic

To adjust retry behavior for failed requests:

**Location**: `kq_cloudv2_device.py:530-580` (in `_submit_batch()` method)

**Current behavior**:
- Max retries: 3
- Exponential backoff with jitter
- Base delay: 1 second, multiplier: 2

**To modify**:
```python
# Change in _submit_batch() method
max_retries = 5  # Increase max retries
base_delay = 2.0  # Increase base delay
delay = base_delay * (2 ** attempt) + random.uniform(0, 1)  # Modify backoff formula
```

### Modifying SSE/Polling Fallback

**Location**: `kq_cloudv2_device.py:438-467` (in `_stream_batch_results()` method)

**Current behavior**:
- Try SSE first if `use_streaming=True`
- Automatically fallback to polling on SSE failure
- Log warnings on fallback

**To disable fallback** (SSE only, no polling):
```python
# In _stream_batch_results(), remove the except block
# Or raise exception instead of calling _poll_batch_results()
```

**To disable SSE** (polling only):
```python
# Create device with use_streaming=False
dev = qml.device('kq.cloudv2', wires=2, use_streaming=False)
```

---

## Testing

### Test Files

1. **Basic Tests** (`tests/test_kq_cloudv2_basic.py`)
   - Import tests
   - Device initialization
   - Metadata checks
   - PennyLane registration

2. **Integration Tests** (`tests/test_kq_cloudv2_integration.py`)
   - Simple circuit execution (expval)
   - Sampling circuits
   - Batch execution
   - VQE workflow
   - Error handling

### Running Tests

**Prerequisites**:
- Cloud API v2 running at http://localhost:8080
- Emulator API running at http://localhost:8000
- RabbitMQ running (for SSE streaming)

**Start Services** (in separate terminals):
```bash
# Terminal 1: Emulator API
cd /Users/ino/Work/kisti/quantum/2025/api_v4/emulator_api
uvicorn src.main:app --port 8000

# Terminal 2: Cloud API v2
cd /Users/ino/Work/kisti/quantum/2025/api_v4/cloud_v2
uvicorn main:app --port 8080
```

**Run Tests**:
```bash
cd /Users/ino/Work/kisti/quantum/2025/api_v4/pennylane-kq

# Basic tests (no services required)
python tests/test_kq_cloudv2_basic.py

# Integration tests (requires services)
python tests/test_kq_cloudv2_integration.py
```

**Expected Output**:
```
============================================================
KQCloudV2Device Basic Tests
============================================================
✅ KQCloudV2Device imported successfully
✅ Device initialized with default parameters
✅ Device initialized with custom parameters
✅ Device metadata correct
✅ Device supports 109 operations
✅ Device supports 7 observables
✅ Device registered with PennyLane successfully

============================================================
✅ ALL BASIC TESTS PASSED
============================================================
```

### Testing Without Services

**Polling-only mode** (no RabbitMQ required):
```python
dev = qml.device('kq.cloudv2', wires=2, use_streaming=False)
```

**Mock API responses** (for unit tests without services):
```python
# Use unittest.mock to mock requests.post/get
from unittest.mock import patch, Mock

with patch('requests.post') as mock_post:
    mock_post.return_value = Mock(
        status_code=201,
        json=lambda: {"batch_uuid": "test-uuid", "job_uuids": ["job1"]}
    )
    # Test device methods
```

---

## Configuration

### Device Parameters

**Required**:
- `wires` (int): Number of qubits

**Optional**:
- `shots` (int | None): Number of shots (default: None = state vector)
- `host` (str): Cloud API v2 URL (default: "http://localhost:8080")
- `use_streaming` (bool): Use SSE streaming (default: True)
- `stream_timeout` (float): SSE timeout in seconds (default: 1800.0)
- `poll_interval` (float): HTTP polling interval in seconds (default: 2.0)

### Environment Variables

None - all configuration via device parameters.

### Installation

**From source** (development):
```bash
cd pennylane-kq
pip install -e .
```

**From package** (production):
```bash
pip install pennylane-kq
```

**Dependencies**:
- `pennylane >= 0.31`
- `numpy`
- `requests >= 2.26.0`

---

## API Specification

### Request Format

**Endpoint**: `POST {host}/api/jobs`

**Headers**:
```json
{
  "Content-Type": "application/json"
}
```

**Body**:
```json
{
  "jobs": [
    {
      "type": "json",
      "circuit": {
        "operations": [...],
        "measurements": [...],
        "shots": 1024
      }
    }
  ]
}
```

**Circuit Format**: See serialization_utils.py for full JSON schema

### Response Format

**Success (201 Created)**:
```json
{
  "batch_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "job_uuids": [
    "660e8400-e29b-41d4-a716-446655440000"
  ],
  "status": "submitted",
  "created_at": "2025-01-01T00:00:00Z"
}
```

**Error (4xx/5xx)**:
```json
{
  "detail": "Error message"
}
```

### SSE Streaming Format

**Endpoint**: `GET {host}/api/stream/batch/{batch_uuid}`

**Headers**:
```
Accept: text/event-stream
```

**Event Format**:
```
event: batch.completed
data: {"batch_uuid": "...", "jobs": [...]}

event: job.completed
data: {"job_uuid": "...", "status": "completed", "result": {...}}
```

### Polling Format

**Endpoint**: `GET {host}/api/batches/{batch_uuid}`

**Response**:
```json
{
  "batch_uuid": "...",
  "status": "completed",
  "jobs": [
    {
      "job_uuid": "...",
      "status": "completed",
      "result": {
        "measurement_type": "expval",
        "value": 0.5
      }
    }
  ]
}
```

---

## Known Limitations

1. **Single measurement per circuit**
   - PennyLane circuits with multiple measurements will fail
   - Workaround: Use separate circuits for each measurement

2. **Counts format assumptions**
   - Assumes counts keys are either hex ("0x3") or binary ("11") strings
   - Other formats will cause parsing errors

3. **No mid-circuit measurements**
   - Only supports measurements at the end of the circuit
   - Mid-circuit measurements are not supported by the backend

4. **Limited error details**
   - API errors may not provide detailed context
   - Check Cloud API v2 logs for more information

5. **No job cancellation**
   - Once submitted, jobs cannot be cancelled
   - Workaround: Set reasonable timeouts

6. **SSE timeout limitations**
   - Long-running jobs may exceed SSE timeout (default: 30 minutes)
   - Workaround: Use polling mode or increase timeout

---

## Troubleshooting

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'pennylane_kq'`

**Solution**:
```bash
cd pennylane-kq
pip install -e .
```

### Device Not Found

**Problem**: `qml.device('kq.cloudv2', ...) raises DeviceError`

**Solution**: Check that package is installed and entry point is registered:
```bash
pip list | grep pennylane-kq
python -c "import pennylane_kq; print(pennylane_kq.__version__)"
```

### Connection Errors

**Problem**: `RuntimeError: Cannot connect to Cloud API v2`

**Solution**:
1. Check that Cloud API v2 is running:
   ```bash
   curl http://localhost:8080/api/health
   ```
2. Verify host parameter is correct:
   ```python
   dev = qml.device('kq.cloudv2', wires=2, host="http://localhost:8080")
   ```

### SSE Streaming Fails

**Problem**: SSE connection fails, device falls back to polling

**Solution**:
1. Check RabbitMQ is running:
   ```bash
   docker ps | grep rabbitmq
   ```
2. Check Cloud API v2 RabbitMQ configuration in `.env`
3. Use polling mode explicitly:
   ```python
   dev = qml.device('kq.cloudv2', wires=2, use_streaming=False)
   ```

### Timeout Errors

**Problem**: `TimeoutError: Batch execution timed out`

**Solution**:
1. Increase timeout:
   ```python
   dev = qml.device('kq.cloudv2', wires=2, stream_timeout=3600.0)
   ```
2. Check backend performance (may be slow for large circuits)

### Counts Parsing Errors

**Problem**: `ValueError: Invalid count state format`

**Solution**: Check that counts format matches expected format (hex or binary):
```python
# Valid formats:
{"0x0": 500, "0x3": 500}  # Hex
{"00": 500, "11": 500}    # Binary

# Invalid format:
{"0": 500, "3": 500}      # Decimal (not supported)
```

### Result Type Errors

**Problem**: `TypeError: Expected numpy array, got dict`

**Solution**: Check measurement type matches expected return type:
- `qml.expval()` → float
- `qml.sample()` → numpy array
- `qml.probs()` → numpy array
- `qml.counts()` → dict

---

## File Structure

```
pennylane-kq/
├── pennylane_kq/
│   ├── __init__.py                    # Package init (exports KQCloudV2Device)
│   ├── _version.py                    # Version number (0.0.29)
│   ├── kq_cloudv2_device.py           # Main device implementation (253 lines)
│   └── utils/                         # Utility modules (modularized)
│       ├── __init__.py                # Utils package init
│       ├── http_client.py             # HTTP communication (329 lines)
│       ├── result_formatter.py        # Result formatting (229 lines)
│       └── serialization_utils.py     # Circuit JSON serialization (362 lines)
├── tests/
│   ├── test_kq_cloudv2_basic.py       # Basic tests
│   └── test_kq_cloudv2_integration.py # Integration tests
├── setup.py                           # Package setup (entry points)
├── README.md                          # User documentation
├── CLAUDE.md                          # This file (developer guide)
└── docs/
    └── API_SPECIFICATION.md           # API details

Deleted (legacy):
- kq_device.py                   # Old base device
- kq_vqe_simple_device.py        # Old VQE device
- old/                           # Deprecated implementations
- benchmark_parallel.py          # Experimental code
- config/                        # Unused config folder
```

**Architecture**:
- **Device Layer**: `kq_cloudv2_device.py` - PennyLane device interface
- **Communication Layer**: `utils/http_client.py` - HTTP/SSE communication
- **Processing Layer**: `utils/result_formatter.py` - Result validation & formatting
- **Serialization Layer**: `utils/serialization_utils.py` - Circuit serialization

---

## Version History

- **v0.0.29** (Current)
  - Added SSE streaming with automatic fallback to HTTP polling
  - Fixed counts format handling (hex/binary auto-detect)
  - Added `use_streaming` and `poll_interval` parameters
  - Code cleanup: removed legacy devices (16 files)
  - **Code modularization**: Refactored into utils/ folder structure
    - Created `utils/http_client.py` for HTTP communication
    - Created `utils/result_formatter.py` for result processing
    - Moved `serialization_utils.py` to `utils/`
    - Reduced `kq_cloudv2_device.py` from 736 lines to 253 lines (65% reduction)
  - Added type hints to all utility modules
  - Updated setup.py to only register kq.cloudv2

- **v0.0.28**
  - Fixed SSE URL paths
  - Fixed API submission endpoint
  - Implemented retry logic with exponential backoff
  - Improved counts format handling

- **v0.0.27** and earlier
  - Legacy versions (deprecated)

---

## Related Documentation

- **Cloud API v2**: `/Users/ino/Work/kisti/quantum/2025/api_v4/cloud_v2/CLAUDE.md`
- **Emulator API**: `/Users/ino/Work/kisti/quantum/2025/api_v4/emulator_api/CLAUDE.md`
- **Project Root**: `/Users/ino/Work/kisti/quantum/2025/api_v4/CLAUDE.md`

---

**Package**: pennylane-kq
**Version**: 0.0.29
**Organization**: KISTI (Korea Institute of Science and Technology Information)
**Last Updated**: 2025-11-06
