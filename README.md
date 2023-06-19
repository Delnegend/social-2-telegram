# twt-2-tele

A CLI tool for reposting artworks from Twitter to Telegram

![](assets\demo.png)

## Features:
- `TwitterScraper`: scrape (mostly) everything in a tweet
  - Username
  - Display name
  - Profile picture (low resolution)
  - Content
  - Images/video/GIF
  - Like/reply/retweet/bookmark count
  - Timestamp
- Private Twitter account
- Artists w/ multiple Twitter accounts
- Multiple images from one tweet
- Additional hashtags


## Requirements:
- [Python 3.10+](https://www.python.org/)
- `pipenv`
- [Microsft Edge WebDriver](https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/)

## Installation:
- Clone this repository
- Install `pipenv` if you haven't
   ```bash
   pip install pipenv
   ```
- Install dependencies
   ```bash
   pipenv install
   ```
- Download Microsoft Edge WebDriver, extract and place `msedgedriver.exe` in this directory.

- <details>
  <summary>Configure Telegram bot API first</summary>

  - If you haven't had a bot, create one using [BotFather](https://t.me/botfather)

    <video controls>
      <source src="assets\get_bot_api.mp4" type="video/mp4">
    </video>

  - If you already have one, here's how to get the API

    <video controls>
      <source src="assets\get_bot_api_existing.mp4" type="video/mp4">
    </video>

  - Place the API in `telegram_config > api_key` in `config.yaml`, ignore the `chat_id` for now (we'll get to that in the next step)

</details>

- <details>
  <summary>Configure Telegram chat ID</summary>

  - Chat id between `you` and the `bot`
    - Spin up the application, assuming you have already configured the bot API
      ```bash
      pipenv run py main.py --get-chat-id
      ```
    - Send a message to your bot
    - The chat id will be messaged back to you

  - Chat id between `a channel` and the `bot`: use the channel's username directly
    ```yaml
    telegram_config:
      chat_id: "@your_channel_username"
    ```

</details>

## Usage:
```bash
$ python3 main.py --help
usage: main.py [-h] [--tweet-to-telegram] [--get-chat-id] [--force-update-alt-accounts] [--validate-social-links USERNAME]

options:
  -h, --help            show this help message and exit
  --tweet-to-telegram   Reposting mode (default if no option is passed)
  --get-chat-id         Spin up the bot to listen for direct messages and return the chat id
  --force-update-alt-accounts
                        Force update artists alt accounts in the database
  --validate-social-links USERNAME
                        Pass in a username to validate social links in the database
```