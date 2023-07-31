class MsgSign:
    GET_USERNAME = "Getting artist's display name"
    SCRAPE = "Scraping {}"
    ACTUAL_HANDLE = "Which one is the actual artist of the artwork(s)?"
    VALIDATE_LINKS = "Validating social links"
    MORE_HASHTAGS = "More hashtags"
    COMPOSE = "Composing message"
    SEND = "Sending to Telegram"


class Msg:
    ZERO_2_CANCEL = "Type 0 to cancel the process at any time"
    DEBUG_ENABLED = "Debug mode is enabled, scraper will not send any message to telegram"
    ENTER_POST_URL = "Enter post url or [/login example.com] "
    CLOSING_SESSION = "Closing session..."
    DOESNT_MATCH_PATTERN = "The url doesn't match pattern for a post"

    MORE_HASHTAGS = "# not included (separated by a space): "
    SELECT_HANDLE = "Enter the index, <username>, <username where_to_find.com> or leave empty to use {}: "


class MsgErr:
    INVALID_INDEX = "Invalid index"
    BLACKLISTED_ACCOUNT = "This account is blacklisted"
    CANNOT_GET_USERNAME = "Cannot get artist username"
    ARTIST_NOT_FOUND = "Artist not found in database"
    FOUND_INVALID_LINKS = "Found invalid social media links"
    BOT_API_KEY_NOT_SET = "Bot API key not set"
