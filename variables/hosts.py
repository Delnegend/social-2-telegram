from __future__ import annotations

import sys

from classes.PlatformFA import PlatformFA
from classes.PlatformTwitter import PlatformTwitter

if sys.version_info >= (3, 11):
    from typing import TYPE_CHECKING
else:
    from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    from classes.PlatformBase import PlatformBase

hosts: dict[str, type[PlatformBase]] = {
    "furaffinity.net": PlatformFA,
    "twitter.com": PlatformTwitter,
}
