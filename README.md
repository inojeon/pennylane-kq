# PennyLane Korea Quantum Plugin

The PennyLane-KQ plugin integrates the KQ quantum computing library.

[PennyLane](https://pennylane.readthedocs.io) is a cross-platform Python library for quantum machine learning, automatic differentiation, and optimization of hybrid quantum-classical computations.

This PennyLane plugin allows to use both the software and hardware backends of KQ as devices for PennyLane.

# Features

- Provides three devices to be used with PennyLane: `kq.emulator`, and `kq.hardware`. These provide access to the respective KQ backends.

- Supports a wide range of PennyLane operations and observables across the devices.

- Combine KQ high performance simulator and hardware backend support with PennyLane's automatic differentiation and optimization.

## Installation

This plugin requires Python version 3.9 and above, as well as PennyLane and KQ. Installation of this plugin, as well as all dependencies, can be done using pip:

```python
python -m pip install pennylane_kq
```

## Authors

KISTI

## Support

-[**Source Code:**](https://github.com/inojeon/pennylane-kq)

-[**Issue Tracker:**](https://github.com/inojeon/pennylane-kq/issues)

If you are having issues, please let us know by posting the issue on our Github issue tracker, or
by asking a question in the forum.

## pypi 업데이트 방법

\_version.py 에서 버전 변경,

```
python setup.py sdist bdist_wheel
python -m twine upload  --skip-existing  dist/*
```

```
python setup.py sdist bdist_wheel
```

에러시 wheel 설치

```
pip install wheel
```
