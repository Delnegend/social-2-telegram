from option import Option, Some


def insensitive_match(input_str: str, iteratable) -> Option[str]:
    """Just like <key in dict.keys()> but case insensitive"""
    match = [key for key in iteratable if input_str.lower() == key.lower()]
    return Option.NONE() if not match else Some(match[0])
