import re

from variables.Colors import Colors


def highlight(content: str, color: str = Colors.YELLOW) -> str:
    # replace <...> with color
    for match in re.findall(r"<\|(.*?)\|>", content):
        content = content.replace(f"<|{match}|>", f"{color}{match}{Colors.END}")
    return content


class MsgSign:
    GET_USERNAME = "Getting artist's display name"
    SCRAPE = "Scraping {}"
    ACTUAL_HANDLE = "Which one is the actual artist of the artwork(s)?"
    VALIDATE_LINKS = "Validating social links"
    MORE_HASHTAGS = "More hashtags"
    COMPOSE = "Composing message"
    SEND = "Sending to Telegram"


class Msg:
    ZERO_2_CANCEL = highlight("Type <|0|> to cancel the process at any time")
    DEBUG_ENABLED = "Debug mode is enabled, scraper will not send any message to telegram"
    ENTER_POST_URL = highlight("<|<post>|> || <|/irl <post>>|> || <|/login <site>|>")
    CLOSING_SESSION = "Closing session..."
    DOESNT_MATCH_PATTERN = "The url doesn't match pattern for a post"

    MORE_HASHTAGS = "# not included (separated by a space): "
    SELECT_HANDLE = highlight(
        "Enter the <|index|>, <|<username>|>, <|<username where_to_find.com>|> or leave empty to use <|{}|>: "
    )
    ENTER_USERNAME = highlight("Cannot scrape username for <|{}|>, please enter manually: ")


class NewArtistMsg:
    HASHTAG_REPRESENT = highlight("Enter representing hashtag(s) (empty for <|{}|>): ")
    SOCIAL_MEDIA = highlight("Enter {}'s social media links (format: <|<name>: <link>|>, ...): ")
    COUNTRY = highlight("Enter {}'s country flag (format: <|emoji|>): ")


class MsgErr:
    INVALID_INDEX = "Invalid index"
    BLACKLISTED_ACCOUNT = "This account is blacklisted"
    CANNOT_GET_USERNAME = "Cannot get artist username"
    ARTIST_NOT_FOUND = "Artist not found in database"
    FOUND_INVALID_LINKS = "Found invalid social media links"
    BOT_API_KEY_NOT_SET = "Bot API key not set"
