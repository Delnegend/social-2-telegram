class Config:
    DEBUG_MODE = False
    DUMP_SCRAPED_POST_TO_JSON = False
    DUMP_TELEGRAM_RESPOND_TO_JSON = False
    DUMP_DATA_GOING_TO_BE_SENT_TO_TELEGRAM = False

    MSEDGE_DRIVER_PATH = ""
    EXTENSIONS_DIR = ""
    COOKIES_DIR = ""
    USER_DATA_DIR = ""
    WAIT_ELEM_TIMEOUT = 10

    BOT_API_KEY = ""
    CHAT_ID = ""
    DISABLE_NOTIFICATION = True
    IGNORE_LINK_VALIDATION: list[str] = []
    BLACKLIST_ACCOUNTS: list[str] = []

    ARTISTS_INFO_FILE = "artists_info.yaml"
    ARTISTS_ALT_HANDLES_FILE = "artists_alt_handles.yaml"
