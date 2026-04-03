"""
The initialization of the `pennylane-kq` module
"""

from .kq_devices import KQCloudV2Device, KQEmulatorDevice
from ._version import __version__

__all__ = [
    "KQCloudV2Device",
    "KQEmulatorDevice",
    "__version__",
]
