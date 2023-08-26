import re
from dataclasses import dataclass, field

from option import Option, Some

from helpers.insensitive_match import insensitive_match  # type: ignore
from variables.Message import NewArtistMsg


@dataclass
class ArtistInfoData:
    country_flag: str
    hashtag_represent: str
    social_media: dict[str, str] = field(default_factory=dict)


class NewArtist:
    def __init__(
        self,
        twitter_username: str,
        artists_info: dict[str, ArtistInfoData],
        artists_alt_handles: dict[str, set[str]],
    ) -> None:
        self.__artist_handle = twitter_username
        self.__artists_info = artists_info
        self.__artists_alt_handles = artists_alt_handles

    def __parse_represent_hashtags(self, in_hashtag_str: str) -> str:
        hashtags = set(
            [hashtag.replace("#", "").strip() for hashtag in in_hashtag_str.split(" ")] + [self.__artist_handle]
        )
        hashtags.discard("")
        hashtags = " ".join(hashtags)
        return hashtags

    def __parse_social_media_links(self, _input: str) -> dict[str, str]:
        unprocessed_links = [
            link
            for link in _input.split(",")
            if link.strip() and len(link.split(":")) >= 2 and link.split(":")[0].strip() and link.split(":")[1].strip()
        ]
        processed_links: dict[str, str] = {}
        for _link in unprocessed_links:
            link = _link.split(":")
            processed_links[link[0].strip()] = ":".join(link[1:]).strip()
        return processed_links

    def process_alt_handles(self, social_media: dict[str, str]) -> set[str]:
        alt_handles: set[str] = set()

        def helper(pattern: str, val: str, match_group: int = 1):
            nonlocal alt_handles
            if match := re.search(pattern, val):
                alt_handles.add(match.group(match_group))

        for _, link in social_media.items():
            match link:
                case link if "twitter.com" in link.lower():
                    helper(r"twitter.com\/([^/]+)\/?", link)
                case link if "instagram.com" in link.lower():
                    helper(r"instagram.com\/([^/]+)\/?", link)
                case link if "furaffinity.net" in link.lower():
                    helper(r"furaffinity.net\/user\/([^/]+)\/?", link)
                case link if "patreon.com" in link.lower():
                    helper(r"patreon.com\/([^/]+)\/?", link)
                case link if "gumroad.com" in link.lower():
                    helper(r"(?:https?:\/\/)?(?:www\.)?([^\/]+)\.gumroad\.com\/?", link)
                case link if "skeb.jp" in link.lower():
                    helper(r"skeb\.jp\/@([^/]+)\/?", link)
                case link if "ko-fi.com" in link.lower():
                    helper(r"ko-fi\.com\/([^/]+)\/?", link)
                case link if "linktr.ee" in link.lower():
                    helper(r"linktr\.ee\/([^/]+)\/?", link)
                case link if "t.me" in link.lower():
                    helper(r"t\.me\/([^/]+)\/?", link)
                case link if "fanbox.cc" in link.lower():
                    helper(r"(?:https?:\/\/)?(?:www\.)?([^\/]+)\.fanbox\.cc\/?", link)
                case link if "itaku.ee" in link.lower():
                    helper(r"itaku\.ee\/profile\/([^/]+)\/?", link)
                case link if "picarto.tv" in link.lower():
                    helper(r"picarto\.tv\/([^/]+)\/?", link)
                case _:
                    pass
        if match := insensitive_match(self.__artist_handle, self.__artists_alt_handles.keys()):
            alt_handles.update(self.__artists_alt_handles[match.value])
        alt_handles.discard("")
        alt_handles.discard(self.__artist_handle)
        return self.__rm_dupl_handles(alt_handles)

    def __rm_dupl_handles(self, alt_handles: set[str]) -> set[str]:
        """Set is case sensitive, this will make it case insensitive"""
        lowered: set[str] = set()
        result: set[str] = set()
        for handle in alt_handles:
            if handle.lower() not in lowered:
                lowered.add(handle.lower())
                result.add(handle)
        return result

    def new(self) -> Option[str]:
        """Return 0 if user wants to exit"""
        handle = self.__artist_handle

        if (hashtag_represent := input(NewArtistMsg.HASHTAG_REPRESENT.format(handle)).strip()).startswith("0"):
            return Some("0")
        hashtag_represent = self.__parse_represent_hashtags(hashtag_represent)

        if (social_media := input(NewArtistMsg.SOCIAL_MEDIA.format(handle)).strip()).startswith("0"):
            return Some("0")
        social_media = self.__parse_social_media_links(social_media)

        self.__artists_alt_handles[handle] = self.process_alt_handles(social_media)

        if (country_flag := input(NewArtistMsg.COUNTRY.format(handle)).strip()).startswith("0"):
            return Some("0")

        self.__artists_info[self.__artist_handle] = ArtistInfoData(
            country_flag=country_flag, hashtag_represent=hashtag_represent, social_media=social_media
        )
        return Some("")
