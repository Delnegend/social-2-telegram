from __future__ import annotations

import sys
from abc import ABC, abstractmethod

from option import Option

from classes.Post import Post

if sys.version_info >= (3, 11):
    from typing import TYPE_CHECKING
else:
    from typing_extensions import TYPE_CHECKING
if TYPE_CHECKING:
    from classes.Browser import Browser


class PlatformBase(ABC):
    """Base class for platform plugins"""

    @abstractmethod
    def __init__(self, browser: Browser) -> None:
        self.title = "⚠️"  # the social media name
        self.post = "⚠️"  # what's a post called
        raise NotImplementedError

    @abstractmethod
    def scrape(self, input_url: str) -> Option[Post]:
        """Scrape the website"""
        raise NotImplementedError

    @abstractmethod
    def has_the_pattern(self, url: str) -> Option[str]:
        """Check if the url has the pattern of a post"""
        raise NotImplementedError

    @abstractmethod
    def get_username(self, handle: str) -> Option[str]:
        """Get the username of a handle"""
        raise NotImplementedError
