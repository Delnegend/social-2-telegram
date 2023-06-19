import argparse
import asyncio
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import yaml

from classes.Config import Config
from classes.NewArtist import ArtistInfoData, NewArtist
from classes.TwitterScraper import TwitterScraper
from helpers.COLORS import FCOLORS
from helpers.print_sign import print_sign
from helpers.send_telegram_message import send_telegram_message
from helpers.telegram_md_format import telegram_md_format

config = Config()


class MainMenu:
    def __init__(self) -> None:
        self.__API_TOKEN = config.telegram_config.api_key
        if not self.__API_TOKEN:
            print("TELEGRAM_BOT_API_KEY not found in config.yaml")
            sys.exit(1)

        self.__BLACKLIST_ACCOUNTS = config.telegram_config.blacklist_accounts
        self.__IGNORE_LINKS_VALIDATION = config.telegram_config.ignore_link_validation

        self.__artists_info: dict[str, ArtistInfoData] = {}
        self.__artists_alt_account: dict[str, str] = {}  # key: alt account, value: main account

        self.__artists_info_load()

    # ========== LOAD/SAVE ARTISTS INFO ==========

    def __artists_info_load(self) -> None:
        if not os.path.isfile("artist_info.yaml"):
            with open(file="artist_info.yaml", mode="w", encoding="utf-8") as f:
                yaml.dump({}, f, sort_keys=False, allow_unicode=True, indent=4)
        else:
            with open(file="artist_info.yaml", mode="r", encoding="utf-8") as f:
                for artist_username, artist_info in yaml.load(f, Loader=yaml.FullLoader).items():
                    self.__artists_info[artist_username] = ArtistInfoData(
                        country_flag=artist_info["country_flag"],
                        hashtag_represent=artist_info["hashtag_represent"],
                        social_media=artist_info["social_media"],
                    )

        if not os.path.isfile("artist_alt_account.yaml"):
            with open(file="artist_alt_account.yaml", mode="w", encoding="utf-8") as f:
                yaml.dump({}, f, sort_keys=False, allow_unicode=True, indent=4)
        else:
            with open(file="artist_alt_account.yaml", mode="r", encoding="utf-8") as f:
                for alt_account, main_account in yaml.load(f, Loader=yaml.FullLoader).items():
                    self.__artists_alt_account[alt_account] = main_account

    def __artists_info_save(self) -> None:
        artists_info_yaml = {}
        for artist_username, artist_info in self.__artists_info.items():
            artists_info_yaml[artist_username] = {
                "country_flag": artist_info.country_flag,
                "hashtag_represent": artist_info.hashtag_represent,
                "social_media": artist_info.social_media,
            }
        with open(file="artist_info.yaml", mode="w", encoding="utf-8") as f:
            yaml.dump(artists_info_yaml, f, sort_keys=False, allow_unicode=True, indent=4)

        artists_alt_account_yaml = {}
        for alt_account, main_account in self.__artists_alt_account.items():
            artists_alt_account_yaml[alt_account] = main_account
        with open(file="artist_alt_account.yaml", mode="w", encoding="utf-8") as f:
            yaml.dump(artists_alt_account_yaml, f, allow_unicode=True, indent=4, sort_keys=True)

    # ========== MENU ==========

    def menu__get_chat_id(self):
        from telebot.async_telebot import AsyncTeleBot

        bot = AsyncTeleBot(self.__API_TOKEN)

        @bot.message_handler(commands=["help", "start"])
        async def send_welcome(message):
            await bot.reply_to(message, message.chat.id)

        asyncio.run(bot.polling())

    def menu__tweet_to_telegram(self, tweet_id_or_url: str = ""):
        """If tweet_id_or_url
        - empty: input() in while True loop, use when sending multiple tweets
        - not empty: use when sending single tweet
        """
        print("Note: type 0 to cancel the process at any time")

        while True:
            print_sign("Enter tweet id or url")
            input_tweet = tweet_id_or_url or input("🍆 ").strip()
            if input_tweet == "0":
                break
            tweet_id = re.search(r"(\d{15,})", input_tweet.split("?")[0])
            if tweet_id:
                tweet_id = tweet_id.group(1)
            else:
                print("Invalid tweet id or url")
                if tweet_id_or_url:
                    sys.exit(1)
                continue

            self.__scraping_and_sending(tweet_id)
            if tweet_id_or_url:
                break

    def menu__force_update_artist_alt_account(self):
        new_artist_obj = NewArtist("", artists_info=self.__artists_info, artists_alt_account=self.__artists_alt_account)
        new_artist_obj.force_update_alt_accounts()
        self.__artists_info_save()

    def menu__validate_social_media_links(self, uname: str = ""):
        if not uname or uname == "0" or uname not in self.__artists_info.keys():
            print_sign("Username not found in database")
            return
        self.__validate_social_media_links(self.__artists_info[uname].social_media)

    # ========== SUBMENU ==========

    def __validate_social_media_links(self, _input_links: dict[str, str]) -> dict[str, str]:
        """Validate social media links and return invalid links"""
        invalid_links = {}
        ignored_links = self.__IGNORE_LINKS_VALIDATION

        input_links = {}
        for name, link in _input_links.items():
            ignored = False
            for ignored_link in ignored_links:
                if ignored_link in link:
                    status = FCOLORS.YELLOW + "ignored" + FCOLORS.END
                    link = FCOLORS.CYAN + link + FCOLORS.END
                    print(f"- {name} ({link}): {status}")
                    ignored = True
                    break
            if ignored:
                continue
            if not link.startswith("http"):
                link = f"https://{link}"
            input_links[name] = link

        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(requests.get, link): name for name, link in input_links.items()}
            for future in as_completed(futures):
                name = futures[future]
                try:
                    response = future.result()
                except Exception as e:
                    print(f"Exception: {e}")
                    invalid_links[name] = input_links[name]
                else:
                    status_code_range = str(response.status_code)[0]
                    color_code = ""
                    url = FCOLORS.CYAN + response.url + FCOLORS.END
                    match status_code_range:
                        case "2":
                            color_code = FCOLORS.GREEN
                        case "3":
                            color_code = FCOLORS.YELLOW
                        case _:
                            color_code = FCOLORS.RED
                    print(f"- {name} ({url}): {color_code}{response.status_code}{FCOLORS.END}")
                    if status_code_range != "2":
                        invalid_links[name] = input_links[name]

        return invalid_links

    def __handle_invalid_social_media_links(self, links: dict[str, str], invalid_links: dict[str, str]) -> None:
        for invalid_link_name, _ in invalid_links.items():
            print(f"{FCOLORS.RED}Invalid link: {FCOLORS.END}{invalid_link_name}")
            fixed = False
            while not fixed:
                open = FCOLORS.BLUE + "[" + FCOLORS.END
                close = FCOLORS.BLUE + "]" + FCOLORS.END
                message = "{}/remmove{} {}/new <url>{} {}/replace <name> <url>{} {}/ignore (default){}: ".format(
                    open, close, open, close, open, close, open, close
                )
                input_fix_url = input(message).strip()
                if input_fix_url == "0":
                    sys.exit(1)
                elif input_fix_url.startswith("/remove"):
                    del links[invalid_link_name]
                    fixed = True
                elif input_fix_url.startswith("/new"):
                    input_new_url = re.sub(r"\s+", " ", input_fix_url[4:]).strip()
                    if not input_new_url:
                        print("Invalid parameters")
                        continue
                    respond = requests.get(input_new_url, headers={"User-Agent": "Mozilla/5.0"})
                    if not respond.ok:
                        print("Invalid link")
                        continue
                    links[invalid_link_name] = input_new_url
                    fixed = True
                elif input_fix_url.startswith("/replace"):
                    input_replace_url = re.sub(r"\s+", " ", input_fix_url[9:]).strip()
                    if not input_replace_url or len(input_replace_url.split(" ")) != 2:
                        print("Invalid parameters")
                        continue
                    new_name, new_url = input_replace_url.split(" ")
                    if not requests.get(new_url, headers={"User-Agent": "Mozilla/5.0"}).ok:
                        print("Invalid link")
                        continue
                    del links[invalid_link_name]
                    links[new_name] = new_url
                    fixed = True
                elif input_fix_url.startswith("/ignore") or input_fix_url == "":
                    fixed = True
                else:
                    print("Invalid command")
            self.__artists_info_save()

    def __scraping_and_sending(self, tweet_id: str) -> None:
        # region: ----- Scraping -----
        print_sign("Scraping tweet", end_line="\r")
        start_time = time.time()
        scraper = TwitterScraper(tweet_id)
        tweet = scraper.scrape()
        print_sign("Scraping tweet", f"{round(time.time() - start_time, 2)} seconds", start_line="")
        if config.debug.dump_scraped_tweet_to_json:
            with open(file=f"debug_scraped_tweet_{tweet_id}.json", mode="w", encoding="utf-8") as f:
                json.dump(tweet.dict, f, indent=4)
        # endregion

        # region: ----- Confirming tweet from artist -----
        print_sign("Which one is the actual artist of the artwork(s)?")
        _all_usernames: list[str] = [tweet.username] + [
            mention[0].replace("@", "") for mention in tweet.mentions if mention[0].replace("@", "") != tweet.username
        ]
        for index, username in enumerate(_all_usernames):
            print(f"{index + 1}. {username}")
        input_select_artist_uname = input(f"Default {FCOLORS.YELLOW}({_all_usernames[0]}){FCOLORS.YELLOW}: ").strip()
        selected_artist_uname = ""
        match input_select_artist_uname:
            case "":
                selected_artist_uname = _all_usernames[0]
            case "0":
                sys.exit(1)
            case _:
                if not input_select_artist_uname.isdigit():
                    respond = requests.get(f"https://twitter.com/{input_select_artist_uname}")
                    if respond.status_code != 200:
                        print("Invalid username")
                        return
                    selected_artist_uname = input_select_artist_uname
                elif int(input_select_artist_uname) > len(_all_usernames):
                    print("Invalid number")
                    return
                # check in blacklist
                elif _all_usernames[int(input_select_artist_uname) - 1] in self.__BLACKLIST_ACCOUNTS:
                    print("This account is in the blacklist")
                    return
                else:
                    selected_artist_uname = _all_usernames[int(input_select_artist_uname) - 1]
        # endregion

        # region: ----- Get artist twitter display name if tweet's author is not the artist -----
        artist_display_name = ""
        if selected_artist_uname != tweet.username:
            print_sign("Getting artist's display name", end_line="\r")
            tweet_scrape = TwitterScraper(twitter_username=selected_artist_uname)
            artist_display_name = tweet_scrape.get_display_name()
            print_sign("Getting artist's display name", f"{artist_display_name}", start_line="")
        else:
            artist_display_name = tweet.display_name
        # endregion

        # region: ----- Ask for additional hashtags -----
        print_sign("Additional hashtags")
        input_additional_hashtags = input("# not included (separated by a space): ").strip()
        if input_additional_hashtags == "0":
            return
        input_additional_hashtags = " ".join(
            [
                f"#{hashtag}" if not hashtag.startswith("#") else hashtag
                for hashtag in input_additional_hashtags.split(" ")
                if hashtag.strip()
            ]
        )
        # endregion

        # region: ----- Checking if the artist is in the database ------
        if selected_artist_uname in self.__artists_alt_account.keys():
            selected_artist_uname = self.__artists_alt_account[selected_artist_uname]

        if selected_artist_uname not in self.__artists_info.keys():
            print_sign("Artist not found in database")
            new_artist_obj = NewArtist(selected_artist_uname, self.__artists_info, self.__artists_alt_account)
            if not new_artist_obj.new():
                return
            self.__artists_info_save()

        _selected_artist = self.__artists_info[selected_artist_uname]
        # endregion

        # region: ----- Validate artists social links -----
        print_sign("Validating social links")
        social_media_links = _selected_artist.social_media
        invalid_social_media_links = self.__validate_social_media_links(social_media_links)

        if invalid_social_media_links:
            print_sign("Found invalid social media links")
            self.__handle_invalid_social_media_links(social_media_links, invalid_social_media_links)
        # endregion

        # region: ----- Composing message -----
        print_sign("Composing message")
        _content = telegram_md_format(tweet.content)
        _url = telegram_md_format(tweet.url)
        _delimeter = ("\n`" + "—" * 20 + "`") if tweet.content else ""
        if not _selected_artist.country_flag in artist_display_name:
            artist_display_name += " " + _selected_artist.country_flag
        _artist_display_name = telegram_md_format(artist_display_name).strip()
        _social_media_links = ", ".join(
            f"[{telegram_md_format(social_media_name)}]({telegram_md_format(social_media_link)})"
            for social_media_name, social_media_link in _selected_artist.social_media.items()
        )
        _artist_hashtag = telegram_md_format(
            " ".join(
                [
                    f"#{hashtag}" if not hashtag.startswith("#") else hashtag
                    for hashtag in _selected_artist.hashtag_represent.split(" ")
                    if hashtag.strip()
                ]
            )
        )
        _mention_hashtags = telegram_md_format(
            " ".join(
                [
                    f"#{hashtag}" if not hashtag.startswith("#") else hashtag
                    for hashtag in _all_usernames
                    if hashtag.strip() and hashtag != selected_artist_uname
                ]
            )
        )
        _mention_hashtags = (" " + _mention_hashtags) if _mention_hashtags else ""
        _additional_hashtags = telegram_md_format(input_additional_hashtags)
        _additional_hashtags = (" " + _additional_hashtags) if _additional_hashtags else ""
        message = f"""\
            {_content}{_delimeter}
            [Sauce]({_url}) \\| {_artist_display_name}
            {_social_media_links}
            _{_artist_hashtag}{_mention_hashtags}{_additional_hashtags}_
        """
        message = "\n".join(line.strip() for line in message.split("\n"))
        # endregion

        # region: ----- Sending tweet to telegram -----
        print_sign("Sending to Telegram", end_line="\r")
        timer = time.time()
        if send_telegram_message(message, tweet.media) != 200:
            # print("Error sending message to telegram")
            print_sign("Sending to Telegram", "Error", start_line="")
            return
        else:
            print_sign("Sending to Telegram", f"{round(time.time() - timer, 2)} seconds", start_line="")
        # endregion


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tweet-to-telegram",
        action="store_true",
        help="Reposting mode (default if no option is passed)",
    )
    parser.add_argument(
        "--get-chat-id",
        action="store_true",
        help="Spin up the bot to listen for direct messages and return the chat id",
    )
    parser.add_argument(
        "--force-update-alt-accounts",
        action="store_true",
        help="Force update artists alt accounts in the database",
    )
    parser.add_argument(
        "--validate-social-links",
        action="store",
        help="Pass in a username to validate social links in the database",
        default="",
        type=str,
        metavar="USERNAME",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    main_menu = MainMenu()
    if args.tweet_to_telegram or len(sys.argv) == 1:
        main_menu.menu__tweet_to_telegram()
    elif args.get_chat_id:
        main_menu.menu__get_chat_id()
    elif args.force_update_alt_accounts:
        main_menu.menu__force_update_artist_alt_account()
    elif args.validate_social_links != "":
        uname: str = args.validate_social_links
        main_menu.menu__validate_social_media_links(uname)


if __name__ == "__main__":
    main()
