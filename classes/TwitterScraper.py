from __future__ import annotations

import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html import unescape

import yaml
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from classes.Config import Config

if sys.version_info >= (3, 11):
    from typing import TYPE_CHECKING
else:
    from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional

config = Config()


@dataclass
class Tweet:
    url: str = ""
    profile_picture: str = ""
    username: str = ""
    display_name: str = ""
    content: str = ""
    media_type: str = ""
    media: list[str] = field(default_factory=list)
    date: str = ""
    views: int = 0
    retweets: int = 0
    quotes: int = 0
    likes: int = 0
    bookmarks: int = 0
    mentions: list[tuple[str, str]] = field(default_factory=list)
    hashtags: list[tuple[str, str]] = field(default_factory=list)
    just_links: list[tuple[str, str]] = field(default_factory=list)

    @property
    def dict(self) -> dict[str, str | dict[str, str | int | list[str] | list[tuple[str, str]]] | list[str]]:
        return {
            "tweet_url": self.url,
            "account_info": {
                "profile_picture": self.profile_picture,
                "username": self.username,
                "display_name": self.display_name,
            },
            "content": self.content,
            "media_type": self.media_type,
            "media": self.media,
            "date": self.date,
            "metrics": {
                "views": self.views,
                "retweets": self.retweets,
                "quotes": self.quotes,
                "likes": self.likes,
                "bookmarks": self.bookmarks,
            },
            "urls": {
                "mentions": self.mentions,
                "hashtags": self.hashtags,
                "just_links": self.just_links,
            },
        }


"""A tweet's html structure inside <article> tag
div
    div
        div -> _
        div -> small profile picture, username, and display name
            - to get profile picture
                - find element div(data-testid="Tweet-User-Avatar")
                - find element img(data-testid="tweetPhoto")
        div -> content
            div -> content
            div
                div
                    div -> images/video/gif
            div -> _
            div -> dates, views
            div -> retweets, quotes, likes, bookmarks count
"""


class TwitterScraper:
    """Twitter Scraper class
    Parameters
    ----------
    tweet_id (str): Tweet's id
    twitter_username (str): Twitter's username, this is only used to get the display name of the account, in cases that the author of the artwork is not the owner of the tweet

    Attributes
    -----------------
    tweet_url (str): Tweet's url
    tweet_id (str): Tweet's id

    Methods
    --------------
    scrape(): Scrape the tweet and return Tweet object

    Returns
    -------
    TwitterScraper: Tweet object, convert it to dict using .dict

    Raises
    ------
    Exception: If cannot access the tweet
    """

    def __init__(self, tweet_id: str = "", twitter_username: str = "") -> None:
        self.__cookies: list[dict[str, str | int | bool]] = []
        self.tweet_url: str = f"https://twitter.com/i/web/status/{tweet_id}"
        self.tweet_id: str = tweet_id
        self.driver: Optional[webdriver.Edge] = None
        self.__twitter_username: str = twitter_username

        self.__is_original_twt = False
        self.__cookies_file_path = config.twitter_scraper_config.cookies_file_path
        self.__validate_cookies = config.twitter_scraper_config.validate_cookies
        self.__poll_frequency = config.twitter_scraper_config.poll_frequency
        self.__timeout = config.twitter_scraper_config.timeout
        self.__headless = config.debug.headless_driver
        self.__press_enter_to_continue_scrape = config.debug.press_enter_to_scrape

        self.__blacklist_scrape_elem = config.twitter_scraper_config.blacklist_element
        self.__whitelist_scrape_elem = config.twitter_scraper_config.whitelist_element
        self.__trigger_whitelist = True if len(self.__whitelist_scrape_elem) > 0 else False

    # region: cookies related stuffs

    def __cookies__inject(self, driver: webdriver.Edge) -> None:
        """
        Inject cookies to the webdriver
        Source: https://stackoverflow.com/a/63220249
        """
        driver.execute_cdp_cmd("Network.enable", {})
        for cookie in self.__cookies:
            driver.execute_cdp_cmd("Network.setCookie", cookie)
        driver.execute_cdp_cmd("Network.disable", {})

    def __cookies__check_valid(self) -> bool:
        """Check if cookies is valid or not"""
        options = webdriver.EdgeOptions()
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_argument("--headless")

        driver = webdriver.Edge(service=EdgeService("./msedgedriver.exe"), options=options)
        self.__cookies__inject(driver)
        driver.get("https://twitter.com")

        try:
            WebDriverWait(driver, self.__timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="AppTabBar_Profile_Link"]'))
            )
            return True
        except:
            return False

    def __cookies__generate(self) -> None:
        """Generate cookies and save it to cookies.json"""
        options = webdriver.EdgeOptions()
        options.add_experimental_option("excludeSwitches", ["enable-logging"])

        driver = webdriver.Edge(service=EdgeService("./msedgedriver.exe"), options=options)
        driver.get("https://twitter.com")

        input("Press enter after you logged in to twitter")

        self.__cookies = driver.get_cookies()
        with open("cookies.json", "w") as f:
            json.dump(self.__cookies, f)

        driver.quit()

    def __cookies__main(self) -> None:
        """Generate and validate cookies"""
        if os.path.exists(self.__cookies_file_path):
            with open(self.__cookies_file_path, "r") as f:
                self.__cookies = json.load(f)
            if self.__validate_cookies and not self.__cookies__check_valid():
                self.__cookies__generate()
        else:
            self.__cookies__generate()

    # endregion

    # region: helper functions

    def __driver__main(self, scrape_display_name: bool = False) -> None:
        options = webdriver.EdgeOptions()
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        if self.__headless:
            options.add_argument("--headless")
        self.__driver = webdriver.Edge(service=EdgeService("./msedgedriver.exe"), options=options)
        self.__cookies__inject(self.__driver)
        if not scrape_display_name:
            self.__driver.get(self.tweet_url)
        else:
            self.__driver.get(f"https://twitter.com/{self.__twitter_username}")

    def __find_tweet_container__main(self) -> None:
        try:
            WebDriverWait(self.__driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "article")))
        except:
            self.__driver.quit()
            raise Exception("Tweet not found, invalid tweet url/id or the internet is too slow to load the tweet")

        # the (container of the) tweet/reply tweet intended to be scraped
        # is the <article> tag that
        # has the date+view counts element (the selector below)
        for index, article in enumerate(self.__driver.find_elements(by=By.TAG_NAME, value="article")):
            try:
                article.find_element(by=By.CSS_SELECTOR, value="div > div > div:nth-child(3) > div:nth-child(5) a")
                self.__tweet_container = article
                self.__is_original_twt = True if index == 0 else False
                break
            except:
                pass
        self.__split_sub_elements()

    def __split_sub_elements(self) -> None:
        """Split a tweet <article> element into subelements
        - personal info: profile picture, username, display name
        - content: tweet's content
        - media: images, videos, gifs
        - dates: tweet's dates, views
        - stats: retweets, quotes, likes, bookmarks count
        """

        def helper(selector: str) -> WebElement:
            nonlocal self
            return self.__tweet_container.find_element(by=By.CSS_SELECTOR, value=selector)

        if self.__is_original_twt:
            self.__twt_account_info_ctn = helper("div > div > div:nth-child(2)")
        else:
            self.__twt_account_info_ctn = self.__tweet_container.find_elements(
                by=By.CSS_SELECTOR, value="div > div > div:nth-child(2)"
            )[1]
        self.__twt_content_ctn = helper("div > div > div:nth-child(3) > div:nth-child(1)")
        self.__twt_media_ctn = helper("div > div > div:nth-child(3) > div:nth-child(2) > div > div")
        self.__twt_date_view_ctn = helper("div > div > div:nth-child(3) > div:nth-child(4)")
        self.__twt_stats_ctn = helper("div > div > div:nth-child(3) > div:nth-child(5)")

    def __click_show_sensitive__main(self):
        """Click the "show" button of sensitive content"""
        try:
            timer = time.time()
            while True:
                if time.time() - timer > self.__timeout:
                    raise Exception("Timeout, can't click the show button")
                try:
                    self.__twt_content_ctn.find_element(by=By.CSS_SELECTOR, value="[role='button']").click()
                except:
                    break

        except:
            pass

    def __process_stat(self, stat: str) -> int:
        """Convert abbreviated stats to int"""
        if stat.endswith("K"):
            return int(float(stat[:-1]) * 1_000)
        elif stat.endswith("M"):
            return int(float(stat[:-1]) * 1_000_000)
        else:
            return int(re.sub(r"[^\d]", "", stat))

    # endregion

    # region: scrapers

    def __scrape_account_info(self) -> dict[str, str]:
        """Get profile picture, username, and display name"""
        links = self.__twt_account_info_ctn.find_elements(by=By.TAG_NAME, value="a")

        profile_picture = links[0].find_element(by=By.TAG_NAME, value="img").get_attribute("src")

        display_name = links[1].find_element(by=By.CSS_SELECTOR, value="div > div > span").get_attribute("innerHTML")
        for pattern, replace_with in zip((r"<span.*?>|</span>|<svg.*?/svg>", r"<img.*?alt=\"(.*?)\".*?>"), ("", r"\1")):
            display_name = re.sub(pattern, replace_with, display_name)

        username = links[2].find_element(by=By.CSS_SELECTOR, value="div > span").text.replace("@", "")

        return {
            "username": unescape(username),
            "display_name": unescape(display_name),
            "profile_picture": unescape(profile_picture),
        }

    def __scrape_content(self) -> str:
        """Get tweet's content"""
        try:
            parsed_tweet = self.__twt_content_ctn.find_element(
                by=By.CSS_SELECTOR, value='[data-testid="tweetText"]'
            ).get_attribute("innerHTML")
            for pattern, replace_with in zip(
                (
                    r"<span.*?>|</span>|<div.*?>|</div>",
                    r"<img.*?alt=\"(.*?)\".*?>",
                    r"<a.*?href=\"(.*?)\".*?>(.*?)</a>",
                ),
                ("", r"\1", r"[\2](\1)"),
            ):
                parsed_tweet = re.sub(pattern, replace_with, parsed_tweet)

            # for each [...](...)
            # [...]: remove https:// and http://
            # (...): add https://twitter.com if it starts with /
            for hyperlink in re.findall(r"\[(.*?)\]\((.*?)\)", parsed_tweet):
                text = hyperlink[0].strip().replace("https://", "").replace("http://", "")
                link = "https://twitter.com" + hyperlink[1] if hyperlink[1].startswith("/") else hyperlink[1]
                parsed_tweet = parsed_tweet.replace(f"[{hyperlink[0]}]({hyperlink[1]})", f"[{text}]({link})")
            return unescape(parsed_tweet.strip())
        except NoSuchElementException:
            return ""

    def __scrape_images(self) -> list[str]:
        """Get images url"""
        parsed_img_container = self.__twt_media_ctn.find_elements(
            by=By.CSS_SELECTOR, value='[data-testid="tweetPhoto"]'
        )

        def parse_img_src(x: WebElement) -> str:
            src = x.find_element(by=By.TAG_NAME, value="img").get_attribute("src")
            url, params = src.split("?")
            param_dict: dict[str, str] = {}
            for param in params.split("&"):
                key, value = param.split("=")
                param_dict[key] = value
            return (
                url
                + "?name=orig"
                + "&"
                + "&".join([f"{key}={value}" for key, value in param_dict.items() if key != "name"])
            )

        return [parse_img_src(tweet_image_elem) for tweet_image_elem in parsed_img_container]

    def __scrape_media__video_ytdl(self) -> str:
        """Get stream url using youtube-dl"""
        import youtube_dl

        try:
            with youtube_dl.YoutubeDL({"quiet": True}) as ydl:
                info = ydl.extract_info(self.tweet_url, download=False)
                return info["formats"][-1]["url"] if info is not None else ""
        except:
            return ""

    def __scrape_media__video_custom(self) -> str:
        """Catching network requests to get video url"""

        video_tag_exist = False
        parsed_video_tag = WebElement("", "")
        timer = time.time()
        while not video_tag_exist:
            if time.time() - timer > self.__timeout:
                raise TimeoutError("Timeout while clicking and waiting for video tag to appear")
            try:
                parsed_video_tag = self.__twt_media_ctn.find_element(by=By.TAG_NAME, value="video")
                video_tag_exist = True
            except NoSuchElementException:
                self.__twt_media_ctn.click()
                time.sleep(self.__poll_frequency)

        if (url := parsed_video_tag.get_attribute("src")).endswith(".mp4"):
            return url

        found_video_url = False
        requests_log = self.__driver.execute_script("return window.performance.getEntriesByType('resource')")
        timer = time.time()
        while not found_video_url:
            if time.time() - timer > self.__timeout:
                raise TimeoutError("Timeout while waiting for requests to get video url")
            for request in requests_log:
                type_a = re.search(r"https://video.twimg.com/ext_tw_video/.*?", request["name"])
                type_b = re.search(r"https://video.twimg.com/amplify_video/.*?", request["name"])
                if (type_a is not None) or (type_b is not None):
                    return request["name"]
            time.sleep(self.__poll_frequency)
            requests_log = self.__driver.execute_script("return window.performance.getEntriesByType('resource')")

        return ""

    def __scrape_date_and_views(self) -> dict[str, str]:
        """Get date and views of tweet
        returns:
            dict: {
                "date": str (%Y-%m-%d %H:%M:%S %Z)
                "views": str(int) (so pylance doesn't yell at me)
            }
        """
        parsed_date_str = self.__twt_date_view_ctn.find_element(by=By.TAG_NAME, value="time").get_attribute("datetime")
        parsed_date_obj = datetime.strptime(parsed_date_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
        parsed_date_str = datetime.strftime(parsed_date_obj.astimezone(), "%Y-%m-%d %H:%M:%S %Z")

        try:
            parsed_views = self.__twt_date_view_ctn.find_element(
                by=By.CSS_SELECTOR, value='[data-testid="app-text-transition-container"] > span > span'
            ).text
        except NoSuchElementException:
            parsed_views = "0"

        return {
            "date": parsed_date_str,
            "views": str(self.__process_stat(parsed_views)),
        }

    def __scrape_metrics(self) -> dict[str, int]:
        parsed_stats = self.__twt_stats_ctn.find_elements(
            by=By.CSS_SELECTOR, value='[data-testid="app-text-transition-container"]'
        )
        variables = {
            "retweets": 0,
            "quotes": 0,
            "likes": 0,
            "bookmarks": 0,
        }
        for stat, key in zip(parsed_stats, ["retweets", "quotes", "likes", "bookmarks"]):
            # hover on stat to get full count in [data-testid="HoverLabel"] -> span
            if stat.text[-1].isdigit():
                variables[key] = self.__process_stat(stat.text)
                continue
            hover_label = ""
            hover_label_exist = False
            timer = time.time()
            while not hover_label_exist:
                if time.time() - timer > self.__timeout:
                    raise TimeoutError("Timeout while hovering over the stat")
                ActionChains(self.__driver).move_to_element(stat).perform()
                hover_label_elems = self.__driver.find_elements(by=By.CSS_SELECTOR, value='[data-testid="HoverLabel"]')
                if len(hover_label_elems) > 0:
                    hover_label = hover_label_elems[0].find_element(by=By.TAG_NAME, value="span").text
                    hover_label_exist = True
                time.sleep(self.__poll_frequency)
            variables[key] = self.__process_stat(hover_label)

        return variables

    def __scrape_urls(self, scraped_content) -> dict[str, list[tuple[str, str]]]:
        urls = re.findall(r"\[.*?\]\(.*?\)", scraped_content)
        mentions: list[tuple[str, str]] = []
        hashtags: list[tuple[str, str]] = []
        just_links: list[tuple[str, str]] = []

        def split_md_links_into_tuple(md_link: str) -> tuple[str, str]:
            """[text](url) -> (text, url)"""
            _text = re.search(r"\[(.*?)\]", md_link)
            text = _text.group(1) if _text is not None else ""
            _url = re.search(r"\((.*?)\)", md_link)
            url = _url.group(1) if _url is not None else ""
            return (text, url)

        with ThreadPoolExecutor(max_workers=10) as executor:
            # from the list of urls ([...](...)), organize them into 3 lists: mentions, hashtags, just_links
            # - mentions: [@...](...)
            # - hashtags: [#...](...)
            # - just_links: [...](...)
            futures = [executor.submit(split_md_links_into_tuple, md_link) for md_link in urls]
            for future in as_completed(futures):
                text, url = future.result()
                if text.startswith("@"):
                    mentions.append(tuple([text, url]))
                elif text.startswith("#"):
                    hashtags.append(tuple([text, url]))
                else:
                    just_links.append(tuple([text.replace("https://", "").replace("http://", ""), url]))

        return {
            "mentions": mentions,
            "hashtags": hashtags,
            "just_links": just_links,
        }

    def __scrape_media__main(self) -> tuple[list[str], str]:
        """Scrape media from tweet, return list of media urls and media type"""
        media: list[str] = []
        exist_play_button = self.__twt_media_ctn.find_elements(by=By.CSS_SELECTOR, value="[data-testid='playButton']")
        if not exist_play_button:
            media += self.__scrape_images()
            media_type = "image"
        else:
            tweet_video_url = self.__scrape_media__video_ytdl() or self.__scrape_media__video_custom()
            media.append(tweet_video_url)
            media_type = "video"
        media_type = media_type if len(media) > 0 else ""
        return media, media_type

    # endregion

    def scrape(self) -> Tweet:
        self.__cookies__main()
        self.__driver__main()
        if self.__press_enter_to_continue_scrape:
            input("Press Enter to continue...")
        self.__find_tweet_container__main()
        self.__click_show_sensitive__main()

        def allow_scrape(elem: str) -> bool:
            nonlocal self
            if self.__trigger_whitelist:
                return elem in self.__whitelist_scrape_elem
            else:
                return elem not in self.__blacklist_scrape_elem

        media, media_type = self.__scrape_media__main() if allow_scrape("media") else ([], "")
        tweet_content = self.__scrape_content() if allow_scrape("content") else ""
        tweet_account_info = (
            self.__scrape_account_info()
            if allow_scrape("account_info")
            else {"profile_picture": "", "username": "", "display_name": ""}
        )
        tweet_metrics = (
            self.__scrape_metrics()
            if allow_scrape("metrics")
            else {"retweets": 0, "quotes": 0, "likes": 0, "bookmarks": 0}
        )
        tweet_date_views = (
            self.__scrape_date_and_views() if allow_scrape("date_and_views") else {"date": datetime.now(), "views": 0}
        )
        tweet_urls = (
            self.__scrape_urls(tweet_content)
            if allow_scrape("urls")
            else {"mentions": [], "hashtags": [], "just_links": []}
        )

        scraped_data = Tweet(
            url=self.tweet_url,
            profile_picture=tweet_account_info["profile_picture"],
            username=tweet_account_info["username"],
            display_name=tweet_account_info["display_name"],
            content=tweet_content,
            media_type=media_type,
            media=media,
            mentions=tweet_urls["mentions"],
            hashtags=tweet_urls["hashtags"],
            just_links=tweet_urls["just_links"],
            date=tweet_date_views["date"],
            views=int(tweet_date_views["views"]),
            retweets=tweet_metrics["retweets"],
            quotes=tweet_metrics["quotes"],
            likes=tweet_metrics["likes"],
            bookmarks=tweet_metrics["bookmarks"],
        )
        self.__driver.quit()

        return scraped_data

    def get_display_name(self) -> str:
        selector = '[data-testid="UserName"] > div > div > div > div > div > span'
        self.__cookies__main()
        self.__driver__main(scrape_display_name=True)

        WebDriverWait(self.__driver, self.__timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        if self.__press_enter_to_continue_scrape:
            input("Press Enter to continue...")
        username = self.__driver.find_element(by=By.CSS_SELECTOR, value=selector).get_attribute("innerHTML")
        self.__driver.quit()

        for pattern, replace_with in zip(
            (
                r"<span.*?>|</span>|<div.*?>|</div>|<svg.*?/svg>",
                r"<img.*?alt=\"(.*?)\".*?>",
            ),
            ("", r"\1"),
        ):
            username = re.sub(pattern, replace_with, username)
        return unescape(username)


def main():
    # --- Input tweet id/url ---
    tweet_input = sys.argv[1:]
    tweet_input = re.search(r"(\d+)$", sys.argv[1:][0])
    if tweet_input is None:
        print("Invalid input")
        exit(1)

    # --- Scrape ---
    scraper = TwitterScraper(tweet_input[0])
    result: Tweet = scraper.scrape()
    print(yaml.dump(result.dict, indent=4, allow_unicode=True, sort_keys=False))


if __name__ == "__main__":
    try:
        start = time.time()
        main()
        print(f"\nTime elapsed: {time.time() - start:.2f} seconds")
    except KeyboardInterrupt:
        print("\nExiting...")
        exit(0)
