"""Cloud simulator/emulator examples: Bell counts or a three-circuit batch.

Set API_KEY below, then run in JupyterLab:
    %run test/example_emulator.py --target kisti.sim1
    %run test/example_emulator.py --target kisti.emulator --mode batch

Importing this module does not submit jobs. Calling main() submits remote jobs.
"""

import argparse
from math import pi

import pennylane as qml
from pennylane.tape import QuantumScript

API_KEY = "your-api-key"
TARGET = "kisti.emulator"  # Or "kisti.sim1" for the cloud-local simulator.
SHOTS = 1024
MODE = "counts"  # "counts" or "batch"
VERIFY_SSL = False


def positive_int(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def run_counts(dev):
    @qml.qnode(dev)
    def bell():
        qml.Hadamard(0)
        qml.CNOT([0, 1])
        return qml.counts()

    counts = bell()
    print("Bell counts:", counts)
    return counts


def run_batch(dev):
    shots = dev.shots.total_shots
    tapes = [
        QuantumScript(
            [qml.Hadamard(0), qml.CNOT([0, 1])],
            [qml.expval(qml.Z(0))], shots=shots,
        ),
        QuantumScript([qml.X(0)], [qml.expval(qml.Z(0))], shots=shots),
        QuantumScript([qml.RY(pi / 3, wires=0)],
                      [qml.expval(qml.Z(0))], shots=shots),
    ]
    results = dev.execute(tapes)
    for number, (result, expected) in enumerate(zip(results, (0.0, -1.0, 0.5)), 1):
        print(f"Circuit {number}: {result:.4f} (ideal: {expected:.1f})")
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", default=TARGET,
                        choices=("kisti.sim1", "kisti.emulator"))
    parser.add_argument("--mode", default=MODE, choices=("counts", "batch"))
    parser.add_argument("--shots", type=positive_int, default=SHOTS)
    args = parser.parse_args(argv)
    if not API_KEY.strip() or API_KEY.strip() == "your-api-key":
        parser.error("Set API_KEY in this script to your cloud service API key first")

    dev = qml.device(
        "kq.emulator", wires=2 if args.mode == "counts" else 3,
        shots=args.shots, api_key=API_KEY, target=args.target,
        verify_ssl=VERIFY_SSL, use_streaming=False,
    )
    print(f"Submitting {args.mode} job(s) to {args.target}", flush=True)
    return run_counts(dev) if args.mode == "counts" else run_batch(dev)


if __name__ == "__main__":
    main()
