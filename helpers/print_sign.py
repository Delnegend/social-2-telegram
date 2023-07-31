from variables.Colors import Colors


def print_sign(
    message: str,
    message_2: str = "",
    message_3: str = "",
    start_line: str = "\n",
    end_line: str = "\n",
) -> None:
    message = Colors.BLUE + message.strip() + Colors.END

    if message_2 := message_2.strip():
        message_2 = " - " + Colors.GREEN + message_2 + Colors.END
    if message_3 := message_3.strip():
        message_3 = " - " + Colors.YELLOW + message_3 + Colors.END

    left_bar = Colors.RED + "|=====[" + Colors.END
    right_bar = Colors.RED + "]=====|" + Colors.END
    print(f"{start_line}{left_bar} {message}{message_2}{message_3} {right_bar}", end=end_line)
