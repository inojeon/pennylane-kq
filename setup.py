from setuptools import setup


with open("pennylane_kq/_version.py") as f:
    version = f.readlines()[-1].split()[-1].strip("\"'")


pennylane_devices_list = [
    "kq.emulator = pennylane_kq:KoreaQuantumEmulator",
    "kq.emulator.mpi = pennylane_kq:KoreaQuantumMPIEmulator",
    "kq.emulator.fast = pennylane_kq:KoreaQuantumFastEmulator",
    "kq.hardware = pennylane_kq:KoreaQuantumHardware",
    "kq.local_emulator = pennylane_kq:KoreaQuantumLocalEmulator",
    "kq.remote_emulator = pennylane_kq:KoreaQuantumRemoteEmulator",
    "kq.emulator.aws = pennylane_kq:KoreaQuantumEmulatorAWS",
]

# requirements = ["pennylane>=0.19,<0.30"]

setup(
    name="pennylane-kq",
    version=version,
    description="A Pennylane plugin for KQ Cloud System",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://www.github.com/inojeon/pennylane-kq",
    author="Inho Jeon",
    author_email="inojeon@kisti.re.kr",
    license="BSD-2",
    packages=["pennylane_kq"],
    zip_safe=False,
    # install_requires=requirements,
    entry_points={
        "pennylane.plugins": pennylane_devices_list
    },  # for registering the pennylane device(s)
    install_requires=[
        "pennylane >= 0.31",
        "numpy",
    ],
    provides=["pennylane_kq"],
)
