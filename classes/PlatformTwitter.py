from __future__ import annotations

import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from html import unescape

from option import Option, Some
from selenium.webdriver.common.by import By

from classes.PlatformBase import PlatformBase
from classes.Post import Post

if sys.version_info >= (3, 11):
    from typing import TYPE_CHECKING
else:
    from typing_extensions import TYPE_CHECKING
if TYPE_CHECKING:
    from selenium.webdriver.remote.webelement import WebElement

    from classes.Browser import Browser


class PlatformTwitter(PlatformBase):
    def __init__(self, browser: Browser) -> None:
        self.title = "𝕏"
        self.post = "x's"
        self.__driver = browser.driver
        self.__get_inner_html = browser.get_inner_html
        self.__get_elem = browser.get_elem

    def has_the_pattern(self, url: str) -> Option[str]:
        """Check if the provided url contains the pattern /<username>/status/<tweet_id>"""
        if match := re.match(r".*\/([a-zA-Z0-9_]{1,15})\/status\/(\d+)", url):
            username, tweet_id = match.groups()
            return Some(f"https://twitter.com/{username}/status/{tweet_id}")
        return Option.NONE()

    def get_username(self, handle: str) -> Option[str]:
        """Return (is_handle_valid: bool, username: str)"""
        self.__driver.get(f"https://twitter.com/{handle}")
        if self.__get_inner_html(self.__driver, "#loading-box-error") != "":
            return Option.NONE()
        if (username := self.__get_inner_html(self.__driver, "#profile-name")) == "":
            return Option.NONE()
        return Some(self.__cleanup_username(username))

    # region: helpers

    def __cleanup_username(self, username: str) -> str:
        username = re.sub(r"<span.*?>|</span>|<div.*?>|</div>|<svg.*?/svg>", "", username)
        username = re.sub(r"<img.*?alt=\"(.*?)\".*?>", r"\1", username)
        return unescape(username)

    def __scrape_media(self, tweet: WebElement) -> tuple[str, list[str]]:
        """Return (content_type: str, content_list: list[str])"""
        media: list[str] = []
        if len(tweet.find_elements(By.CSS_SELECTOR, ".tweet-media")) == 0:
            return "", media

        media_container = tweet.find_element(By.CSS_SELECTOR, ".tweet-media")
        images = media_container.find_elements(By.TAG_NAME, "img")

        if len(images) > 0:
            for image in images:
                if src := image.get_attribute("src"):
                    media.append(src)
            return "photo", media

        # return the src attribute of the source tag
        video = media_container.find_element(By.TAG_NAME, "video")
        media.append(video.find_element(By.TAG_NAME, "source").get_attribute("src") or "")
        return "video", media

    # endregion

    # region: post-processing

    def __process_content(self, content: str) -> str:
        """HTML -> Markdown + clean up"""

        content = re.sub(r"<span.*?>|</span>|<div.*?>|</div>", "", content)
        content = re.sub(r"<img.*?alt=\"(.*?)\".*?>", r"\1", content)
        content = re.sub(r"<a.*?href=\"(.*?)\".*?>(.*?)</a>", r"[\2](\1)", content)
        content = re.sub(r"<br>", "\n", content)

        # for each [...](...)
        # [...]: remove https:// and http://
        # (...): add https://twitter.com if it starts with /
        for hyperlink in re.findall(r"\[(.*?)\]\((.*?)\)", content):
            text = hyperlink[0].strip().replace("https://", "").replace("http://", "")
            link = "https://twitter.com" + hyperlink[1] if hyperlink[1].startswith("/") else hyperlink[1]
            content = content.replace(f"[{hyperlink[0]}]({hyperlink[1]})", f"[{text}]({link})")
        return unescape(content.strip())

    def __process_links(self, content) -> dict[str, list[tuple[str, str]]]:
        urls = re.findall(r"\[.*?\]\(.*?\)", content)
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
            futures = [executor.submit(split_md_links_into_tuple, md_link) for md_link in urls]
            for future in as_completed(futures):
                text, url = future.result()
                if text.startswith("@"):
                    mentions.append(tuple([text.replace("@", ""), url]))
                elif text.startswith("#"):
                    hashtags.append(tuple([text.replace("#", ""), url]))
                else:
                    just_links.append(tuple([text.replace("https://", "").replace("http://", ""), url]))

        return {"mentions": mentions, "hashtags": hashtags, "just_links": just_links}

    def __process_stats(self, stats: str) -> int:
        return int(stats.replace(",", "")) if stats != "" else 0

    # endregion

    def scrape(self, input_url: str) -> Option[Post]:
        self.__driver.get(self.has_the_pattern(input_url).value)

        render_timeout: float = 1.2
        if (tweet_ := self.__get_elem(self.__driver, ".tweet-main")).is_none:
            return Option.NONE()
        tweet = tweet_.value

        url = self.has_the_pattern(input_url).value
        pfp = tweet.find_element(By.CSS_SELECTOR, ".tweet-avatar").get_attribute("src") or ""
        handle = self.__get_inner_html(tweet, ".tweet-header-handle", render_timeout).replace("@", "")
        username = self.__cleanup_username(self.__get_inner_html(tweet, ".tweet-header-name", render_timeout))

        content = self.__process_content(self.__get_inner_html(tweet, ".tweet-body-text", render_timeout))
        media_type, media = self.__scrape_media(tweet)
        date = "" if (date_ := self.__get_elem(tweet, ".tweet-date")).is_none else date_.value.get_attribute("title") or ""

        repost, likes, quotes = (
            self.__process_stats(self.__get_inner_html(tweet, ".tweet-footer-stat-retweets", render_timeout)),
            self.__process_stats(self.__get_inner_html(tweet, ".tweet-footer-stat-favorites", render_timeout)),
            self.__process_stats(self.__get_inner_html(tweet, ".tweet-footer-stat-replies", render_timeout)),
        )

        links = self.__process_links(content)

        return Some(
            Post(
                url=url,
                profile_picture=pfp,
                handle=handle,
                username=username,
                content=content,
                media_type=media_type,
                media=media,
                date=date,
                repost=repost,
                likes=likes,
                quotes=quotes,
                mention_link=links["mentions"],
                hashtag_link=links["hashtags"],
                just_links=links["just_links"],
            )
        )
