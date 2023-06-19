import re


def telegram_md_format(tweet_content: str) -> str:
    """https://core.telegram.org/bots/api#markdownv2-style"""

    # replace [...](...) with @...@@...@
    for match in re.findall(r"\[(.*?)\]\((.*?)\)", tweet_content):
        tweet_content = tweet_content.replace(f"[{match[0]}]({match[1]})", f"@{match[0]}@@{match[1]}@")

    # Add prefix "\" to special characters
    for char in "_*[]()~`>#-+={}.!|":
        tweet_content = tweet_content.replace(char, f"\\{char}")

    # replace @...@@...@ with [...](...)
    for match in re.findall(r"@(.*?)@@(.*?)@", tweet_content):
        tweet_content = tweet_content.replace(f"@{match[0]}@@{match[1]}@", f"[{match[0]}]({match[1]})")

    return tweet_content
