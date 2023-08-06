import json

import requests
from option import Err, Ok, Option, Result, Some

from variables.Config import Config


def __compose_message(content: str) -> Option[dict[str, str | bool]]:
    data = {
        "chat_id": Config.CHAT_ID,
        "text": content,
        "parse_mode": "MarkdownV2",
        "disable_notification": Config.DISABLE_NOTIFICATION,
    }
    return Some(data)


def __compose_media_message(
    content: str, media_urls: list[str], media_type: str = "photo"
) -> Option[dict[str, str | bool]]:
    media_processed: list[dict[str, str | bool]] = [
        {
            "type": media_type,
            "media": media_urls[0],
            "caption": content,
            "parse_mode": "MarkdownV2",
        }
    ]
    if media_type == "video":
        media_processed[0]["supports_streaming"] = True
    media_processed.extend(
        [
            {"type": media_type, "media": media_url, "supports_streaming": True}
            if media_type == "video"
            else {"type": media_type, "media": media_url}
            for media_url in media_urls[1:]
        ]
    )

    data = {
        "chat_id": Config.CHAT_ID,
        "media": json.dumps(media_processed),
        "disable_notification": Config.DISABLE_NOTIFICATION,
    }
    return Some(data)


def send_telegram_message(
    content: str, media_urls: list[str] | None = None, media_type: str = "photo"
) -> Result[None, str]:
    """
    Send a message to telegram chat
    - content (str): message content
    - media (list[str] | None, optional): list of media url. Defaults to None.
    - media_type (str, optional): type of media, "photo" or "video". Defaults to "photo".
    """

    api = "sendMessage" if media_urls is None else "sendMediaGroup"
    data = (
        __compose_message(content) if media_urls is None else __compose_media_message(content, media_urls, media_type)
    )

    if Config.DUMP_DATA_GOING_TO_BE_SENT_TO_TELEGRAM:
        with open("debug_data_going_to_be_sent_to_telegram.json", "w") as f:
            json.dump(data.unwrap(), f, indent=4)

    respond = requests.post(
        f"https://api.telegram.org/bot{Config.BOT_API_KEY}/{api}",
        data=data.unwrap(),
    )

    if Config.DUMP_TELEGRAM_RESPOND_TO_JSON:
        with open("debug_telegram_response.json", "w") as f:
            json.dump(respond.json(), f, indent=4)

    if str(respond.status_code).startswith("2"):
        return Ok(None)
    return Err(f"Telegram response: {respond.status_code} {respond.reason}")
