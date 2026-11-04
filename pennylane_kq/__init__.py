"""
The initialization of the `pennylane-kq` module
"""

from .kq_devices import KQEmulatorDevice, KQQPUDevice
from ._version import __version__

__all__ = [
    "KQEmulatorDevice",
    "KQQPUDevice",
    "__version__",
]
