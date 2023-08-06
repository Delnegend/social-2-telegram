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


class PlatformFA(PlatformBase):
    def __init__(self, browser: Browser) -> None:
        self.title = "FurAffinity"
        self.post = "submission"
        self.__driver = browser.driver
        self.__get_inner_html = browser.get_inner_html
        self.__get_elem = browser.get_elem
        self.__get_elems = browser.get_elems

    def has_the_pattern(self, url: str) -> Option[str]:
        if match := re.match(r".*\/view\/(\d+)", url):
            return Some(f"https://www.furaffinity.net/view/{match.groups()[0]}")
        return Option.NONE()

    def get_username(self, handle: str) -> Option[str]:
        return Some(handle)

    def __process_content(self, content: str) -> str:
        """HTML -> Markdown + clean up"""
        content = re.sub(r"<br>", "\n", content)
        content = re.sub(r"\n\n+", "\n\n", content)
        content = re.sub(r"<code.*?>|</code>", "", content)
        content = re.sub(r"<img.*?alt=\"(.*?)\".*?src=\"(.*?)\".*?>", r"[\1](\2)", content)

        # if <a> tag
        # - has <img> tag inside, replace with [<img alt attr>](<href attr>)
        # - doesn't have <img> tag inside, replace with [<text>](<href attr>)
        content = re.sub(
            r"<a.*?href=\"(.*?)\".*?>(.*?)<img.*?alt=\"(.*?)\".*?>.*?</a>",
            lambda match: f"[{match.groups()[2]}]({match.groups()[0]})",
            content,
        )
        content = re.sub(
            r"<a.*?href=\"(.*?)\".*?>(.*?)</a>",
            lambda match: f"[{match.groups()[1]}]({match.groups()[0]})",
            content,
        )

        # add https://www.furaffinity.net to links that start with /
        content = re.sub(r"\[(.*?)\]\((\/.*?)\)", r"[\1](https://www.furaffinity.net\2)", content)

        return unescape(content.strip())

    def __process_links(self, content: str) -> dict[str, list[tuple[str, str]]]:
        """Extract all links from content"""
        urls = re.findall(r"\[.*?\]\(.*?\)", content)
        mentions: list[tuple[str, str]] = []
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
                text, link = future.result()
                if link.startswith("https://www.furaffinity.net/user/"):
                    mentions.append(tuple([text, link]))
                else:
                    just_links.append(tuple([text.replace("https://", "").replace("http://", ""), link]))

        return {"mentions": mentions, "just_links": just_links}

    def __process_tags(self, tags: list[WebElement]) -> list[tuple[str, str]]:
        """Extract all tags from tags element"""

        def helper(link: str | None) -> str:
            """Extract tag from link"""
            if link is None:
                return ""
            if link.startswith("/"):
                return "https://www.furaffinity.net" + link
            return link

        return [(tag.get_attribute("innerHTML") or "", helper(tag.get_attribute("href"))) for tag in tags]

    def __scrape_image(self) -> str:
        """Scrape image from page"""
        # .favorite-nav > a.innerHTML == Download > a.href
        elems = self.__get_elems(self.__driver, ".favorite-nav > a")
        if len(elems) == 0:
            return ""
        for elem in elems:
            if elem.get_attribute("innerHTML") == "Download":
                return elem.get_attribute("href") or ""
        return ""

    def __scrape_tags(self) -> list[WebElement]:
        if len(elems := self.__driver.find_elements(By.CSS_SELECTOR, ".submission-sidebar .tags a")) == 0:
            return []
        return elems

    def scrape(self, url: str) -> Option[Post]:
        url = self.has_the_pattern(url).value
        self.__driver.get(url)
        if (submission_ := self.__get_elem(self.__driver, ".submission-content")).is_none:
            return Option.NONE()
        submission = submission_.value

        pfp = (
            ""
            if (pfp_ := self.__get_elem(submission, ".submission-user-icon")).is_none
            else pfp_.value.get_attribute("src") or ""
        )
        username = self.__get_inner_html(submission, ".submission-id-sub-container a strong")

        content = self.__process_content(self.__get_inner_html(submission, ".submission-description"))
        image = self.__scrape_image()
        date = (
            ""
            if (date_ := self.__get_elem(submission, ".popup_date")).is_none
            else date_.value.get_attribute("title") or ""
        )

        if (stats_ := self.__get_elem(self.__driver, ".submission-sidebar .stats-container")).is_none:
            stats = WebElement
            views, comments, favorites, rating = "", "", "", ""
        else:
            stats = stats_.value
            views, comments, favorites, rating = (
                self.__get_inner_html(stats, ".views > span"),
                self.__get_inner_html(stats, ".comments > span"),
                self.__get_inner_html(stats, ".favorites > span"),
                self.__get_inner_html(stats, ".rating > span").strip(),
            )
        links = self.__process_links(content)
        tags = self.__process_tags(self.__scrape_tags())

        return Some(
            Post(
                url=url,
                profile_picture=pfp,
                handle=username,
                username=username,
                content=self.__process_content(content),
                media_type="photo" if image != "" else "",
                media=[image],
                date=date,
                views=int(views) if views else 0,
                comments=int(comments) if comments else 0,
                likes=int(favorites) if favorites else 0,
                rating=rating,
                mention_link=links["mentions"],
                just_links=links["just_links"],
                hashtag_link=tags,
            )
        )
