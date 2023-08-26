from __future__ import annotations

import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from option import Option, Some

from variables.Colors import Colors
from variables.Config import Config

if sys.version_info >= (3, 11):
    from typing import TYPE_CHECKING
else:
    from typing_extensions import TYPE_CHECKING
if TYPE_CHECKING:
    from classes.Browser import Browser


def __print_link(name: str, link: str, status: str) -> None:
    """Print the link with a status"""
    match status:
        case _ if status.startswith("2") or status == "valid":
            status = Colors.GREEN + status + Colors.END
        case _ if status == "invalid":
            status = Colors.RED + status + Colors.END
        case _:
            status = Colors.YELLOW + status + Colors.END
    link = Colors.CYAN + link + Colors.END
    print(f"- {name} ({link}): {status}")


def __check_request(urL: str) -> bool:
    """Check if the provided url is valid using requests"""
    try:
        response = requests.get(urL)
    except Exception as e:
        print(f"Exception: {e}")
        return False
    else:
        return str(response.status_code)[0] == "2"


def __check_selenium_uname_in_title(url: str, uname: str, browser: Browser) -> bool:
    """Check if the website's title contains the artist's username"""
    browser.driver.get(url)
    valid = False
    timer = time.time()
    while not valid:
        try:
            title = browser.get_inner_html(browser.driver, "title")
        except:
            continue
        valid = uname.lower() in title.lower()
        if time.time() - timer > Config.WAIT_ELEM_TIMEOUT:
            break
    return valid


def __check_selenium_pixiv(url: str, browser: Browser) -> bool:
    """Check if the pixiv page contains the follow button"""
    browser.driver.get(url)
    return browser.get_elem(browser.driver, '[data-click-label="follow"]').is_some


def check_invalid_links(_input_links: dict[str, str], browser: Browser) -> Option[dict[str, str]]:
    """Validate social media links and return invalid links"""
    links_to_check: dict[str, str] = {}
    for name, link in _input_links.items():
        ignored = False
        for ignored_link in Config.IGNORE_LINK_VALIDATION:
            if ignored_link in link:
                __print_link(name, link, "ignored")
                ignored = True
                break
        if ignored:
            continue
        if not link.startswith("http"):
            link = f"https://{link}"
        links_to_check[name] = link

    invalid_links: dict[str, str] = {}
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(__check_request, link): name for name, link in links_to_check.items()}
        for future in as_completed(futures):
            is_valid, url = future.result(), links_to_check[futures[future]]
            if not is_valid:
                invalid_links[futures[future]] = url
            else:
                __print_link(futures[future], url, "200")

    if invalid_links:
        for name, link in zip(list(invalid_links.keys()).copy(), list(invalid_links.values()).copy()):
            if "pixiv.net" in link:
                if __check_selenium_pixiv(link, browser):
                    print(f"- {name} ({Colors.CYAN}{link}{Colors.END}): {Colors.GREEN}valid{Colors.END}")
                    del invalid_links[name]
                    continue
                else:
                    print(f"- {name} ({Colors.CYAN}{link}{Colors.END}): {Colors.RED}invalid{Colors.END}")

            uname: str = ""
            match link:
                case _ if "ko-fi.com" in link:
                    if (match := re.search(r"(?<=ko-fi.com\/)[^\/]+", link)) is not None:
                        uname = match.group(0)
                case _ if "subscribestar.adult" in link:
                    if (match := re.search(r"(?<=subscribestar.adult\/)[^\/]+", link)) is not None:
                        uname = match.group(0)
                case _ if "skeb.jp" in link:
                    if (match := re.search(r"(?<=skeb.jp\/)[^\/]+", link)) is not None:
                        uname = match.group(0)
                case _ if "picarto.tv" in link:
                    if (match := re.search(r"(?<=picarto.tv\/)[^\/]+", link)) is not None:
                        uname = match.group(0)
                case _ if "linktr.ee" in link:
                    if (match := re.search(r"(?<=linktr.ee\/)[^\/]+", link)) is not None:
                        uname = match.group(0)
                case _:
                    pass

            if not uname:
                __print_link(name, link, "cannot parse username from link")
                continue

            if __check_selenium_uname_in_title(link, uname, browser):
                __print_link(name, link, "valid")
                del invalid_links[name]
            else:
                __print_link(name, link, "invalid")

    return Some(invalid_links) if invalid_links else Option.NONE()  # type: ignore


def handle_invalid_links(links: dict[str, str], invalid_links: dict[str, str]) -> Option[str]:
    for invalid_link_name, _ in invalid_links.items():
        print(f"{Colors.RED}Invalid link: {Colors.END}{invalid_link_name}")
        fixed = False
        while not fixed:
            msg = "[/remove] [/new <url>] [/replace <name> <url>] [/ignore (default)]"
            msg = msg.replace("[", f"{Colors.BLUE}[{Colors.END}").replace("]", f"{Colors.BLUE}]{Colors.END}")
            match input(f"{msg}: ").strip():
                case "0":
                    return Some("0")
                case "/remove":
                    del links[invalid_link_name]
                    fixed = True
                case foo if foo.startswith("/new"):
                    input_new_url = re.sub(r"\s+", " ", foo[4:]).strip()
                    if not input_new_url:
                        print("Invalid parameters")
                        continue
                    respond = requests.get(input_new_url, headers={"User-Agent": "Mozilla/5.0"})
                    if not respond.ok:
                        print("Invalid link")
                        continue
                    links[invalid_link_name] = input_new_url
                    fixed = True
                case foo if foo.startswith("/replace"):
                    input_replace_url = re.sub(r"\s+", " ", foo[9:]).strip()
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
                case foo if foo.startswith("/ignore") or foo == "":
                    fixed = True
                case _:
                    print("Invalid command")
    return Some("")
