from option import Option, Some


def insensitive_match(input_str: str, iteratable) -> Option[str]:  # type: ignore
    """Just like <key in dict.keys()> but case insensitive"""
    match = [item for item in iteratable if input_str.lower() == item.lower()]  # type: ignore
    return Option.NONE() if not match else Some(match[0])  # type: ignore
