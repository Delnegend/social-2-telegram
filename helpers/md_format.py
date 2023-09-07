import re


def md_format(content: str) -> str:
    """https://core.telegram.org/bots/api#markdownv2-style"""

    # replace [...](...) with @...@@...@
    for match in re.findall(r"\[(.*?)\]\((.*?)\)", content):
        content = content.replace(f"[{match[0]}]({match[1]})", f"@{match[0]}@@{match[1]}@")
    content = content.replace("SquareBracStart", "[").replace("SquareBracEnd", "]")

    # Add prefix "\" to special characters
    for char in "_*[]()~`>#-+={}.!|":
        content = content.replace(char, f"\\{char}")

    # replace @...@@...@ with [...](...)
    for match in re.findall(r"@(.*?)@@(.*?)@", content):
        content = content.replace(f"@{match[0]}@@{match[1]}@", f"[{match[0]}]({match[1]})")

    return content
