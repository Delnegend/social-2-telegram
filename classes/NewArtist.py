import re
from dataclasses import dataclass, field

from option import Option, Some

from variables import Colors


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
        artists_alt_account: dict[str, str],
    ) -> None:
        self.__twitter_username = twitter_username
        self.__artists_info = artists_info
        self.__artists_alt_accounts = artists_alt_account

    def __process_representing_hashtags(self, _input: str) -> str:
        hashtags = " ".join([hashtag.replace("#", "").strip() for hashtag in _input.split(" ") if hashtag.strip()])
        hashtags = hashtags or self.__twitter_username
        return hashtags

    def __process_social_media_links(self, _input: str) -> dict[str, str]:
        # unprocessed_links = _input.split(",")
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

    def __update_alt_accounts_list(self, social_media: dict[str, str]) -> None:
        # if there are 2 or more social_media_name.lower() starting with "twitter" then
        # add
        # - account_alt_1: account_main
        # - account_alt_2: account_main
        # - ...
        # to self.__artists_alt_accounts
        artist_twitter_links = [
            link
            for social_media_title, link in social_media.items()
            if social_media_title.lower().startswith("twitter")
        ]
        if len(artist_twitter_links) < 2:
            return
        original_twitter_username = re.sub(r"https://twitter.com/|/$", "", artist_twitter_links[0])
        for link in artist_twitter_links[1:]:
            link = re.sub(r"https://twitter.com/|/$", "", link)
            self.__artists_alt_accounts[link] = original_twitter_username

    def new(self) -> Option[str]:
        """Return 0 if user wants to exit"""
        hashtag_representing_artist = input(
            f"Enter hashtag(s) representing artist ({Colors.YELLOW}{self.__twitter_username}{Colors.END}): "
        ).strip()
        if hashtag_representing_artist.startswith("0"):
            return Some("0")
        hashtag_representing_artist = self.__process_representing_hashtags(hashtag_representing_artist)

        social_media = input("Enter artist's social media links (format: <name>: <link>, ...): ").strip()
        if social_media.startswith("0"):
            return Some("0")
        social_media = self.__process_social_media_links(social_media)

        self.__update_alt_accounts_list(social_media)

        country_flag = input("Enter artist's country flag (format: emoji): ").strip()
        if country_flag.startswith("0"):
            return Some("0")

        self.__artists_info[self.__twitter_username] = ArtistInfoData(
            country_flag=country_flag, hashtag_represent=hashtag_representing_artist, social_media=social_media
        )
        return Some("")
