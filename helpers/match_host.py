from __future__ import annotations

import re
import sys

from option import Err, Ok, Result

from variables.hosts import hosts

if sys.version_info >= (3, 11):
    from typing import TYPE_CHECKING
else:
    from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    from classes.Browser import Browser
    from classes.PlatformBase import PlatformBase


def match_host(input_str: str, browser: Browser) -> Result[PlatformBase, str]:
    """Returns a PlatformBase object if the input string matches a host, otherwise returns an error message"""
    input_str = input_str.strip().replace("www.", "")
    if not (found_a_math := re.search(r"(https?:\/\/)?([A-Za-z0-9.-]+)", input_str)):
        return Err("Cannot parse the domain")
    if (domain := found_a_math.group(2)) not in hosts:
        return Err(f"{domain} is not supported yet")
    return Ok(hosts[domain](browser))
