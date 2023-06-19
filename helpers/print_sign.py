from .COLORS import FCOLORS


def print_sign(
    message: str,
    message_2: str = "",
    start_line: str = "\n",
    end_line: str = "\n",
) -> None:
    message = FCOLORS.BLUE + message.strip() + FCOLORS.END
    message_2 = (" - " + message_2.strip()) if message_2 else ""
    message_2 = FCOLORS.GREEN + message_2 + FCOLORS.END
    left_bar = FCOLORS.RED + "|=====[" + FCOLORS.END
    right_bar = FCOLORS.RED + "]=====|" + FCOLORS.END
    print(f"{start_line}{left_bar} {message}{message_2} {right_bar}", end=end_line)
