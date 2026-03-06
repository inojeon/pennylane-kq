"""
Integration tests for KQCloudV2Device
======================================

Test full integration with Cloud API v2 and SSE streaming.

PREREQUISITES:
1. Cloud API v2 must be running at http://localhost:8080
2. Emulator API must be running at http://localhost:8000
3. RabbitMQ must be running

To start services:
    # Terminal 1 - Emulator API
    cd /Users/ino/Work/kisti/quantum/2025/api_v4/emulator_api
    uvicorn src.main:app --port 8000

    # Terminal 2 - Cloud API v2
    cd /Users/ino/Work/kisti/quantum/2025/api_v4/cloud_v2
    uvicorn main:app --port 8080
"""

import sys
import os
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_cloud_api_health():
    """Test that Cloud API v2 is running"""
    import requests

    try:
        response = requests.get("http://localhost:8080/api/health", timeout=5.0)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Cloud API v2 is running: {data}")
            return True
        else:
            print(f"❌ Cloud API v2 returned status {response.status_code}")
            return False
    except requests.ConnectionError:
        print("❌ Cannot connect to Cloud API v2 at http://localhost:8080")
        print("   Please start Cloud API v2 first:")
        print("   cd /Users/ino/Work/kisti/quantum/2025/api_v4/cloud_v2")
        print("   uvicorn main:app --port 8080")
        return False
    except Exception as e:
        print(f"❌ Error checking Cloud API v2: {e}")
        return False


def test_simple_circuit_execution():
    """Test simple circuit execution with expectation value"""
    try:
        import pennylane as qml
        from pennylane_kq import KQCloudV2Device

        print("\n🔬 Test 1: Simple Bell state circuit (expval)")

        # Create device
        dev = KQCloudV2Device(wires=2, shots=None, host="http://localhost:8080")

        # Define circuit
        @qml.qnode(dev)
        def circuit():
            qml.Hadamard(wires=0)
            qml.CNOT(wires=[0, 1])
            return qml.expval(qml.PauliZ(0))

        # Execute
        print("   Executing circuit...")
        result = circuit()

        print(f"   Result: {result}")
        print(f"   Type: {type(result)}")

        # Validate
        assert isinstance(result, (float, np.number)), f"Expected float, got {type(result)}"
        assert -1 <= result <= 1, f"Expectation value out of range: {result}"

        print("✅ Simple circuit execution passed")
        return True

    except Exception as e:
        print(f"❌ Simple circuit execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sampling_circuit():
    """Test circuit execution with sampling"""
    try:
        import pennylane as qml
        from pennylane_kq import KQCloudV2Device

        print("\n🔬 Test 2: Bell state with sampling")

        # Create device with shots
        dev = KQCloudV2Device(wires=2, shots=1024, host="http://localhost:8080")

        # Define circuit
        @qml.qnode(dev)
        def circuit():
            qml.Hadamard(wires=0)
            qml.CNOT(wires=[0, 1])
            return qml.sample(qml.PauliZ(0))

        # Execute
        print("   Executing circuit with 1024 shots...")
        result = circuit()

        print(f"   Result shape: {result.shape}")
        print(f"   First 10 samples: {result[:10]}")

        # Validate
        assert isinstance(result, np.ndarray), f"Expected numpy array, got {type(result)}"
        assert len(result) == 1024, f"Expected 1024 samples, got {len(result)}"

        print("✅ Sampling circuit execution passed")
        return True

    except Exception as e:
        print(f"❌ Sampling circuit execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_batch_circuit_execution():
    """Test batch execution of multiple circuits"""
    try:
        import pennylane as qml
        from pennylane_kq import KQCloudV2Device

        print("\n🔬 Test 3: Batch execution (5 circuits)")

        # Create device
        dev = KQCloudV2Device(wires=2, shots=None, host="http://localhost:8080")

        # Define circuits with different parameters
        @qml.qnode(dev)
        def circuit(theta):
            qml.RY(theta, wires=0)
            return qml.expval(qml.PauliZ(0))

        # Execute multiple times
        print("   Executing 5 circuits with different parameters...")
        params = [0.0, np.pi/4, np.pi/2, 3*np.pi/4, np.pi]
        results = [circuit(p) for p in params]

        print(f"   Results: {results}")

        # Validate
        assert len(results) == 5, f"Expected 5 results, got {len(results)}"
        for i, result in enumerate(results):
            assert isinstance(result, (float, np.number)), f"Result {i} not a float"
            assert -1 <= result <= 1, f"Result {i} out of range"

        # Check that results vary (RY rotation should change expectation value)
        assert not all(r == results[0] for r in results), "All results are identical"

        print("✅ Batch circuit execution passed")
        return True

    except Exception as e:
        print(f"❌ Batch circuit execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_vqe_workflow():
    """Test VQE-like workflow with optimization"""
    try:
        import pennylane as qml
        from pennylane_kq import KQCloudV2Device

        print("\n🔬 Test 4: VQE workflow (simple optimization)")

        # Create device
        dev = KQCloudV2Device(wires=2, shots=None, host="http://localhost:8080")

        # Define Hamiltonian (simple H = Z0)
        H = qml.PauliZ(0)

        # Define ansatz
        @qml.qnode(dev)
        def circuit(params):
            qml.RY(params[0], wires=0)
            qml.RY(params[1], wires=1)
            return qml.expval(H)

        # Test a few parameter values
        print("   Testing 3 different parameter sets...")
        test_params = [
            [0.0, 0.0],
            [np.pi/2, 0.0],
            [np.pi, 0.0]
        ]

        energies = []
        for i, params in enumerate(test_params):
            energy = circuit(params)
            energies.append(energy)
            print(f"   Params {params}: Energy = {energy:.4f}")

        # Validate
        assert len(energies) == 3
        for energy in energies:
            assert isinstance(energy, (float, np.number))
            assert -1 <= energy <= 1

        print("✅ VQE workflow passed")
        return True

    except Exception as e:
        print(f"❌ VQE workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handling():
    """Test error handling for invalid inputs"""
    try:
        import requests
        from pennylane_kq import KQCloudV2Device

        print("\n🔬 Test 5: Error handling")

        # Test 1: Invalid host
        print("   Testing connection to invalid host...")
        dev = KQCloudV2Device(wires=2, host="http://invalid-host:9999")

        try:
            # This should fail with connection error
            dev._submit_batch({"jobs": []})
            print("❌ Expected connection error, but succeeded")
            return False
        except RuntimeError as e:
            if "Cannot connect" in str(e):
                print("   ✅ Connection error handled correctly")
            else:
                print(f"   ⚠️  Unexpected error message: {e}")

        print("✅ Error handling passed")
        return True

    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all integration tests"""
    print("=" * 70)
    print("KQCloudV2Device Integration Tests")
    print("=" * 70)

    # Check prerequisites
    print("\n📋 Checking prerequisites...")
    if not test_cloud_api_health():
        print("\n❌ Prerequisites not met. Please start Cloud API v2.")
        return 1

    # Run tests
    tests = [
        test_simple_circuit_execution,
        test_sampling_circuit,
        test_batch_circuit_execution,
        test_vqe_workflow,
        test_error_handling,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ Test {test_func.__name__} crashed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    # Summary
    print("\n" + "=" * 70)
    print(f"Test Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 70)

    if failed == 0:
        print("✅ ALL INTEGRATION TESTS PASSED")
        return 0
    else:
        print(f"❌ {failed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    exit(main())
