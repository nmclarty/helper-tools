import platform
from datetime import datetime


def os_version() -> str:
    if (system := platform.system()) == "Linux":
        return platform.freedesktop_os_release()["PRETTY_NAME"]
    elif system == "Darwin":
        return f"macOS {platform.mac_ver()[0]}"
    else:
        return "Unknown"


def format_ts(ts: float) -> str:
    delta = datetime.now() - datetime.fromtimestamp(ts)
    if (days := delta.days) < 7:
        color = "green"
    elif days < 31:
        color = "cyan"
    else:
        color = "red"
    return f"[{color}]{str(delta)[:-7]}[/{color}]"


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
