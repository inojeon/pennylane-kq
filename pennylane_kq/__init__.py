"""
The initialization of the `pennylane-kq` module
"""

from .kq_cloudv2_device import KQCloudV2Device
from ._version import __version__

__all__ = [
    "KQCloudV2Device",
    "__version__",
]
