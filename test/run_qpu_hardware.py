"""Submit one Bell circuit to a real KRISS QPU through the cloud service.

JupyterLab:
    Set API_KEY below to your cloud service API key, then run:
    %run test/run_qpu_hardware.py --target kriss.hw_20q

Use --target kriss.hw_50q for the other device. Importing this module does
not submit a job. Executing it does. Client timeout does not cancel the job.
"""

import argparse
import time

import pennylane as qml

API_KEY = "your-api-key"  # 실행 전에 발급받은 API 키를 입력하세요.


def positive_int(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True,
                        choices=("kriss.hw_20q", "kriss.hw_50q"))
    parser.add_argument("--shots", type=positive_int, default=1024)
    parser.add_argument("--timeout", type=positive_int, default=1800,
                        help="Total result wait in seconds; does not cancel jobs")
    parser.add_argument("--host", default="https://qc-api.kisti.re.kr")
    args = parser.parse_args(argv)
    api_key = API_KEY.strip()
    if not api_key or api_key == "your-api-key":
        parser.error("Set API_KEY in this script to your cloud service API key first")

    dev = qml.device(
        "kq.qpu", wires=2, shots=args.shots, target=args.target,
        api_key=api_key, host=args.host, stream_timeout=args.timeout,
        use_streaming=False,
    )

    @qml.qnode(dev)
    def bell():
        qml.Hadamard(0)
        qml.CNOT([0, 1])
        return qml.counts(wires=[0, 1])

    print(f"Submitting one real QPU job: {args.target}, 2 wires, {args.shots} shots",
          flush=True)
    started = time.monotonic()
    counts = bell()
    print(f"Completed in {time.monotonic() - started:.1f} seconds")
    print("Counts:", dict(sorted(counts.items())))
    total = sum(counts.values())
    if total <= 0:
        raise RuntimeError("The server returned no measurement counts")
    print(f"Returned shots: {total} (requested: {args.shots})")
    if total != args.shots:
        print("Shot total differs; check server result processing.")
    for state in ("00", "01", "10", "11"):
        print(f"P({state}) = {counts.get(state, 0) / total:.4f}")
    print("Ideal: P(00) = P(11) = 0.5; P(01) = P(10) = 0.")
    print("Hardware noise and finite sampling cause deviations; this test does "
          "not certify entanglement or hardware fidelity.")
    return counts


if __name__ == "__main__":
    main()
