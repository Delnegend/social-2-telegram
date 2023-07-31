import time

import requests

from variables.Config import Config


def telegram_listen():
    print("Waiting for /id command...")

    while True:
        response = requests.post(
            "https://api.telegram.org/bot" + Config.BOT_API_KEY + "/getUpdates",
            json={"offset": -1, "limit": 1, "allowed_updates": "message_id", "timeout": 1},
        )
        if not str(response.status_code).startswith("2"):
            raise Exception("Error when sending message to telegram")
        try:
            if response.json()["result"][0]["message"]["text"] == "/id":
                Config.CHAT_ID = response.json()["result"][0]["message"]["chat"]["id"]
                break
        except:
            pass
        time.sleep(1)

    response = requests.post(
        "https://api.telegram.org/bot" + Config.BOT_API_KEY + "/sendMessage",
        json={"chat_id": Config.CHAT_ID, "text": Config.CHAT_ID},
    )
