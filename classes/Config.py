from dataclasses import dataclass, field
from threading import Lock

import yaml


class ConfigMeta(type):
    _instances = {}
    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


@dataclass
class DebugConfig:
    dump_scraped_tweet_to_json: bool = False
    dump_telegram_respond_to_json: bool = False
    headless_driver: bool = False
    press_enter_to_scrape: bool = False


@dataclass
class TwitterScraperConfig:
    cookies_file_path: str = ""
    validate_cookies: bool = False
    poll_frequency: float = 0.0
    timeout: float = 0.0
    blacklist_element: list[str] = field(default_factory=list)
    whitelist_element: list[str] = field(default_factory=list)


@dataclass
class TelegramConfig:
    api_key: str = ""
    chat_id: str = ""
    disable_notification: bool = False
    ignore_link_validation: list[str] = field(default_factory=list)
    blacklist_accounts: list[str] = field(default_factory=list)


class Config(metaclass=ConfigMeta):
    def __init__(self) -> None:
        with open("config.yaml", "r") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)

        __debug = config["debug"]
        self.debug: DebugConfig = DebugConfig(
            dump_scraped_tweet_to_json=__debug["dump_scraped_tweet_to_json"],
            dump_telegram_respond_to_json=__debug["dump_telegram_respond_to_json"],
            headless_driver=__debug["headless_driver"],
            press_enter_to_scrape=__debug["press_enter_to_scrape"],
        )
        __twitter_scraper_config = config["twitter_scraper_config"]
        self.twitter_scraper_config: TwitterScraperConfig = TwitterScraperConfig(
            cookies_file_path=__twitter_scraper_config["cookies_file_path"],
            validate_cookies=__twitter_scraper_config["validate_cookies"],
            poll_frequency=__twitter_scraper_config["poll_frequency"],
            timeout=__twitter_scraper_config["timeout"],
            blacklist_element=__twitter_scraper_config["blacklist_element"],
            whitelist_element=__twitter_scraper_config["whitelist_element"],
        )
        __telegram_config = config["telegram_config"]
        self.telegram_config: TelegramConfig = TelegramConfig(
            api_key=__telegram_config["api_key"],
            chat_id=__telegram_config["chat_id"],
            disable_notification=__telegram_config["disable_notification"],
            ignore_link_validation=__telegram_config["ignore_link_validation"],
            blacklist_accounts=__telegram_config["blacklist_accounts"],
        )
