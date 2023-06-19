import json

import requests

from classes.Config import Config

config = Config()


def send_telegram_message(content: str, media: list[str] | None = None) -> int:
    if media is None:
        respond = requests.post(
            f"https://api.telegram.org/bot{config.telegram_config.api_key}/sendMessage",
            data={
                "chat_id": config.telegram_config.chat_id,
                "text": content,
                "parse_mode": "MarkdownV2",
                "disable_notification": config.telegram_config.disable_notification,
            },
        )
    else:
        # add tweet.content to the first image
        media_processed = [
            {
                "type": "photo",
                "media": media[0],
                "caption": content,
                "parse_mode": "MarkdownV2",
            }
        ]
        # add the rest of the images
        media_processed.extend([{"type": "photo", "media": image} for image in media[1:]])

        respond = requests.post(
            f"https://api.telegram.org/bot{config.telegram_config.api_key}/sendMediaGroup",
            data={
                "chat_id": config.telegram_config.chat_id,
                "media": json.dumps(media_processed),
                "disable_notification": config.telegram_config.disable_notification,
            },
        )

    if config.debug.dump_telegram_respond_to_json:
        with open("debug_telegram_response.json", "w") as f:
            json.dump(respond.json(), f, indent=4)

    return respond.status_code
