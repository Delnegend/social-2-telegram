import json
import os
import sys
import time

import yaml
from option import Err, Ok, Option, Result, Some

from classes import ArtistInfoData, Browser, NewArtist, PlatformBase, Post
from helpers import (
    artists_info_load,
    artists_info_save,
    check_invalid_links,
    handle_invalid_links,
    insensitive_match,
    match_host,
    md_format,
    overwrite_sm_name,
    print_sign,
    send_telegram_message,
    telegram_listen,
)
from variables import Config, Msg, MsgErr, MsgSign


@lambda _: _(Config)
def load_config(Config: type[Config]) -> None:
    for config_key in Config.__dict__.keys():
        if config_key.startswith("__"):
            continue
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
            if (key := insensitive_match(config_key, config.keys())).is_some:
                setattr(Config, config_key, config[key.value])


class MainMenu:
    def __init__(self) -> None:
        if not Config.BOT_API_KEY:
            print(MsgErr.BOT_API_KEY_NOT_SET)
            sys.exit(1)

        if not Config.CHAT_ID:
            telegram_listen()
            sys.exit(0)

        self.__artists_info: dict[str, ArtistInfoData] = {}
        self.__artists_alt_handles: dict[str, str] = {}  # key: alt handle, value: main handle
        self.__artists_info, self.__artists_alt_handles = artists_info_load()

        self.browser = Browser()
        self.platform_to_get_username: PlatformBase

        print(Msg.ZERO_2_CANCEL)
        if Config.DEBUG_MODE:
            print(Msg.DEBUG_ENABLED)

        while True:
            print_sign(Msg.ENTER_POST_URL)
            input_url: str = input("🍨 ").strip()

            if input_url == "0":
                print("Closing session...")
                self.browser.driver.quit()
                sys.exit(0)

            if input_url.startswith("/login "):
                url = input_url.split(" ")[1].strip().replace("https://", "").replace("http://", "").replace("/", "")
                self.browser.cookies_create(url, os.path.join(Config.COOKIES_DIR, url), "")
                continue

            if (platform := match_host(input_url, self.browser)).is_ok:
                self.platform = platform.unwrap()
                self.platform_to_get_username = platform.unwrap()
            else:
                print_sign("Error", platform.unwrap_err())
                continue

            if (res := self.platform.has_the_pattern(input_url)).is_none:
                print(Msg.DOESNT_MATCH_PATTERN)
                continue

            if (res := self.scraping_and_sending(input_url)).is_err:
                print_sign("Error", res.unwrap_err())
                continue

    # region: load/save artist info into yaml file

    # endregion

    # region: steps

    def __step__ask_more_hashtags(self) -> Option[str]:
        """Return additional hashtags for post"""
        input_more_hashtags = input(Msg.MORE_HASHTAGS).strip()
        if input_more_hashtags == "0":
            return Some("0")
        hashtag_list = [
            f"#{hashtag.strip()}" if not hashtag.strip().startswith("#") else hashtag.strip()
            for hashtag in input_more_hashtags.split(" ")
            if hashtag.strip()
        ]
        hashtag_str = " ".join(hashtag_list)
        return Some(hashtag_str)

    def __step__ask_artist_handle(self, all_handles: list[str]) -> Option[str]:
        for index, username in enumerate(all_handles):
            print(f"{index + 1}. {username}")
        while True:
            match input(Msg.SELECT_HANDLE.format(all_handles[0])).strip():
                case "":
                    return Some(all_handles[0])
                case "0":
                    return Some("0")
                case foo if not foo.isdigit():
                    data = foo.split(" ")
                    if len(data) == 2:
                        if (matched_host := match_host(data[1].strip(), self.browser)).is_ok:
                            self.platform_to_get_username = matched_host.unwrap()
                    return Some(data[0].strip())
                case foo if int(foo) not in range(1, len(all_handles) + 1):
                    print(MsgErr.INVALID_INDEX)
                    continue
                case foo if insensitive_match(all_handles[int(foo) - 1], Config.BLACKLIST_ACCOUNTS).is_some:
                    print(MsgErr.BLACKLISTED_ACCOUNT)
                    continue
                case foo:
                    return Some(all_handles[int(foo) - 1])

    def __step__get_artist_username(
        self, artist_handle: str, post_er_handle: str, post_er_uname: str
    ) -> Result[str, str]:
        if artist_handle == post_er_handle:
            return Ok(post_er_uname)
        print_sign(MsgSign.GET_USERNAME, end_line="\r")

        artist_uname = ""
        if (artist_uname_ := self.platform_to_get_username.get_username(artist_handle)).is_none:
            print_sign(MsgSign.GET_USERNAME, "Error", start_line="")
            artist_uname = input(Msg.ENTER_USERNAME.format(artist_handle)).strip()
            if artist_uname == "0":
                return Ok("0")
        else:
            artist_uname = artist_uname_.value
        print_sign(MsgSign.GET_USERNAME, artist_uname, start_line="")
        return Ok(artist_uname)

    def __step_composing(
        self, post: Post, artist_uname: str, artist_handle: str, all_handles: list[str], more_hashtags: list[str]
    ) -> Option[str]:
        artist_obj = self.__artists_info[artist_handle]

        post.content = md_format(post.content)
        post.url = md_format(post.url)
        _delimeter = ("\n`" + "—" * 20 + "`") if post.content else ""

        if artist_obj.country_flag not in artist_uname:
            artist_uname += " " + artist_obj.country_flag
        artist_uname = md_format(artist_uname).strip()

        social_media_links = ", ".join(
            f"[{md_format(overwrite_sm_name(name))}]({md_format(link)})"
            for name, link in artist_obj.social_media.items()
        )
        video_hashtag = "#ANI " if post.media_type == "video" else ""

        artist_hashtag_list = [hashtag for hashtag in artist_obj.hashtag_represent.split(" ")]
        artist_hashtag_list.append(artist_handle) if artist_handle not in artist_hashtag_list else None
        artist_hashtag_list.extend(key for key, value in self.__artists_alt_handles.items() if artist_handle in value)

        mention_hashtags_list = [handle for handle in all_handles if handle.strip() and handle != artist_handle]

        post_hashtags_list = [hashtag[0] for hashtag in post.hashtag_link if hashtag[0].strip()]

        # can't use set() because it will change the order
        hashtags_list = []
        for hashtag in artist_hashtag_list + mention_hashtags_list + more_hashtags + post_hashtags_list:
            if hashtag.strip() and hashtag not in hashtags_list:
                hashtags_list.append(hashtag.strip())
        hashtags = " ".join(f"#{hashtag}" if not hashtag.startswith("#") else hashtag for hashtag in hashtags_list)

        message = f"""\
            {post.content}{_delimeter}
            [Sauce]({post.url}) \\| {artist_uname}
            {social_media_links}
            _{md_format(video_hashtag)}{md_format(hashtags)}_
        """
        return Some("\n".join(line.strip() for line in message.split("\n")))

    # endregion

    def scraping_and_sending(self, post_url: str) -> Result[None, str]:
        print_sign(MsgSign.SCRAPE.format(self.platform.post), end_line="\r")
        start_time = time.time()
        post = self.platform.scrape(post_url).value
        print_sign(
            MsgSign.SCRAPE.format(self.platform.post),
            f"{round(time.time() - start_time, 2)} seconds",
            self.platform.title,
            start_line="",
        )

        if Config.DUMP_SCRAPED_POST_TO_JSON:
            with open(file=f"debug_scraped_post_{post_url}.json", mode="w", encoding="utf-8") as f:
                json.dump(post.dict, f, indent=4)

        if Config.DEBUG_MODE:
            print(yaml.dump(post.dict, sort_keys=False, indent=4, allow_unicode=True))
            return Ok(None)

        print_sign(MsgSign.ACTUAL_HANDLE)
        all_handles = [post.handle] + [mention[0] for mention in post.mention_link if mention[0] != post.handle]
        if (artist_handle := self.__step__ask_artist_handle(all_handles).unwrap()) == "0":
            return Ok(None)
        if (artist_uname_res := self.__step__get_artist_username(artist_handle, post.handle, post.username)).is_err:
            return Err(artist_uname_res.unwrap_err())
        elif (artist_uname := artist_uname_res.unwrap()) == "0":
            return Ok(None)

        print_sign(MsgSign.MORE_HASHTAGS)
        if (more_hashtags := self.__step__ask_more_hashtags().unwrap()) == "0":
            return Ok(None)

        if (foo := insensitive_match(artist_handle, self.__artists_alt_handles)).is_some:
            artist_handle = self.__artists_alt_handles[foo.value]

        if (insensitive_match(artist_handle, self.__artists_info)).is_none:
            print_sign(MsgErr.ARTIST_NOT_FOUND)
            if NewArtist(artist_handle, self.__artists_info, self.__artists_alt_handles).new().unwrap() == "0":
                return Ok(None)
            artists_info_save(self.__artists_info, self.__artists_alt_handles)

        artist_handle = insensitive_match(artist_handle, self.__artists_info).value
        artist_obj = self.__artists_info[artist_handle]

        print_sign(MsgSign.VALIDATE_LINKS)
        if (invalid_links := check_invalid_links(artist_obj.social_media)).is_some:
            print_sign(MsgErr.FOUND_INVALID_LINKS)
            if handle_invalid_links(artist_obj.social_media, invalid_links.unwrap()).unwrap() == "0":
                return Ok(None)
            artists_info_save(self.__artists_info, self.__artists_alt_handles)

        print_sign(MsgSign.COMPOSE)
        message = self.__step_composing(post, artist_uname, artist_handle, all_handles, more_hashtags.split()).unwrap()

        print_sign(MsgSign.SEND, end_line="\r")
        timer = time.time()
        if (res := send_telegram_message(message, post.media, post.media_type)).is_ok:
            print_sign(MsgSign.SEND, f"{round(time.time() - timer, 2)} seconds", start_line="")
            return Ok(None)
        else:
            print_sign(MsgSign.SEND, "Error", start_line="")
            return Err(res.unwrap_err())


def main():
    MainMenu()


if __name__ == "__main__":
    main()
