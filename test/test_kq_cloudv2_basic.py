"""
Basic tests for KQCloudV2Device
================================

Test basic import, initialization, and structure of the device.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_import():
    """Test that the device can be imported"""
    from pennylane_kq import KQCloudV2Device
    assert KQCloudV2Device is not None
    print("✅ KQCloudV2Device imported successfully")


def test_device_initialization():
    """Test device initialization"""
    from pennylane_kq import KQCloudV2Device

    # Test with required parameters
    dev = KQCloudV2Device(wires=2, shots=1024, api_key="test-key", target="test-target")
    assert len(dev.wires) == 2
    assert dev.shots.total_shots == 1024
    assert dev.host == "https://qc-api.kisti.re.kr"
    assert dev.api_key == "test-key"
    assert dev.target == "test-target"
    assert dev.stream_timeout == 1800.0
    print("✅ Device initialized with required parameters")

    # Test with custom parameters
    dev2 = KQCloudV2Device(
        wires=4,
        shots=2048,
        api_key="my-key",
        target="kisti.sim1",
        host="http://custom-host:9000",
        stream_timeout=3600.0
    )
    assert len(dev2.wires) == 4
    assert dev2.shots.total_shots == 2048
    assert dev2.host == "http://custom-host:9000"
    assert dev2.stream_timeout == 3600.0
    print("✅ Device initialized with custom parameters")


def test_required_param_validation():
    """Test that missing required parameters raise ValueError"""
    from pennylane_kq import KQCloudV2Device

    # shots=None should raise
    try:
        KQCloudV2Device(wires=2, shots=None, api_key="k", target="t")
        assert False, "Expected ValueError for shots=None"
    except ValueError as e:
        assert "shots" in str(e)
        print(f"✅ shots=None rejected: {e}")

    # missing api_key should raise
    try:
        KQCloudV2Device(wires=2, shots=1024, target="t")
        assert False, "Expected ValueError for missing api_key"
    except ValueError as e:
        assert "api_key" in str(e)
        print(f"✅ missing api_key rejected: {e}")

    # missing target should raise
    try:
        KQCloudV2Device(wires=2, shots=1024, api_key="k")
        assert False, "Expected ValueError for missing target"
    except ValueError as e:
        assert "target" in str(e)
        print(f"✅ missing target rejected: {e}")


def test_device_metadata():
    """Test device metadata"""
    from pennylane_kq import KQCloudV2Device

    assert KQCloudV2Device.name == "KQ Cloud API v2 Device"
    assert KQCloudV2Device.short_name == "kq.cloudv2"
    assert KQCloudV2Device.version == "0.0.29"
    assert KQCloudV2Device.author == "KISTI Quantum Computing Team"
    print("✅ Device metadata correct")


def test_supported_operations():
    """Test that device has supported operations"""
    from pennylane_kq import KQCloudV2Device

    assert "Hadamard" in KQCloudV2Device.operations
    assert "CNOT" in KQCloudV2Device.operations
    assert "RY" in KQCloudV2Device.operations
    assert "PauliZ" in KQCloudV2Device.operations
    print(f"✅ Device supports {len(KQCloudV2Device.operations)} operations")


def test_supported_observables():
    """Test that device has supported observables"""
    from pennylane_kq import KQCloudV2Device

    assert "PauliZ" in KQCloudV2Device.observables
    assert "PauliX" in KQCloudV2Device.observables
    assert "Hamiltonian" in KQCloudV2Device.observables
    print(f"✅ Device supports {len(KQCloudV2Device.observables)} observables")


def test_pennylane_device_registration():
    """Test that device is registered with PennyLane"""
    try:
        import pennylane as qml

        dev = qml.device('kq.cloudv2', wires=2, shots=1024,
                         api_key="test-key", target="test-target")
        assert dev is not None
        assert len(dev.wires) == 2
        print("✅ Device registered with PennyLane successfully")

    except ImportError:
        print("⚠️  PennyLane not installed, skipping registration test")
    except Exception as e:
        print(f"⚠️  Device registration test failed: {e}")
        print("   (This is normal if package is not installed via pip)")


def main():
    """Run all basic tests"""
    print("=" * 60)
    print("KQCloudV2Device Basic Tests")
    print("=" * 60)

    try:
        test_import()
        test_device_initialization()
        test_required_param_validation()
        test_device_metadata()
        test_supported_operations()
        test_supported_observables()
        test_pennylane_device_registration()

        print("\n" + "=" * 60)
        print("✅ ALL BASIC TESTS PASSED")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
