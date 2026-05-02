import platform
from datetime import datetime

from rich.table import Table


def fmt_delta(time: float | datetime) -> str:
    """Display the age of a timestamp or datetime in the past, formatted with colors.

    :param time: The event to calculate for.
    :return: The pretty printed age.
    """
    match time:
        case float():
            delta = datetime.now() - datetime.fromtimestamp(time)
        case datetime():
            delta = datetime.now() - time
        case _:
            raise TypeError()

    if (days := delta.days) < 7:
        color = "green"
    elif days < 31:
        color = "cyan"
    else:
        color = "red"
    return f"[{color}]{str(delta).split('.')[0]}[/{color}]"


def fmt_table(name: str) -> Table:
    return Table(
        box=None,
        padding=(0, 0, 0, 2),
        show_header=False,
        title=f"{name}:",
        title_justify="left",
        title_style="",
    )


def os_version() -> str:
    if (system := platform.system()) == "Linux":
        return platform.freedesktop_os_release()["PRETTY_NAME"]
    elif system == "Darwin":
        return f"macOS {platform.mac_ver()[0]}"
    else:
        return "Unknown"


def sizeof_fmt(num: float, suffix="B") -> str:
    """Parse a number (of bytes) and return a human-readable version.

    :param num: The number to parse.
    :return: A string of the formatted number.
    """
    for unit in ("", "K", "M", "G", "T", "P", "E", "Z"):
        if abs(num) < 1000.0:
            return f"{num:3.1f} {unit}{suffix}"
        num /= 1000.0
    return f"{num:.1f} Y{suffix}"
