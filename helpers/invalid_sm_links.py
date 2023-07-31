import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from option import Option, Some

from variables.Colors import Colors
from variables.Config import Config


def check_invalid_links(_input_links: dict[str, str]) -> Option[dict[str, str]]:
    """Validate social media links and return invalid links"""

    links_to_check = {}
    for name, link in _input_links.items():
        ignored = False
        for ignored_link in Config.IGNORE_LINK_VALIDATION:
            if ignored_link in link:
                status = Colors.YELLOW + "ignored" + Colors.END
                link = Colors.CYAN + link + Colors.END
                print(f"- {name} ({link}): {status}")
                ignored = True
                break
        if ignored:
            continue
        if not link.startswith("http"):
            link = f"https://{link}"
        links_to_check[name] = link

    invalid_links = {}
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(requests.get, link): name for name, link in links_to_check.items()}
        for future in as_completed(futures):
            name = futures[future]
            try:
                response = future.result()
            except Exception as e:
                print(f"Exception: {e}")
                invalid_links[name] = links_to_check[name]
            else:
                status_code_range = str(response.status_code)[0]
                color_code = ""
                url = Colors.CYAN + response.url + Colors.END
                match status_code_range:
                    case "2":
                        color_code = Colors.GREEN
                    case "3":
                        color_code = Colors.YELLOW
                    case _:
                        color_code = Colors.RED
                print(f"- {name} ({url}): {color_code}{response.status_code}{Colors.END}")
                if status_code_range != "2":
                    invalid_links[name] = links_to_check[name]

    return Some(invalid_links) if invalid_links else Option.NONE()


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
