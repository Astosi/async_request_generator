import logging
import time

class CoolFormatter(logging.Formatter):
    # ANSI color codes
    COLOR_CODES = {
        "MAGENTA": "\033[95m",
        "BLUE": "\033[94m",
        "GREEN": "\033[92m",
        "YELLOW": "\033[93m",
        "RED": "\033[91m",
        "BOLD": "\033[1m",
        "UNDERLINE": "\033[4m",
        "END": "\033[0m",
        "GREY": "\033[37m"
    }

    # Mapping from logging levels to colors
    LEVEL_TO_COLOR = {
        "DEBUG": COLOR_CODES["BLUE"],
        "INFO": COLOR_CODES["GREEN"],
        "WARNING": COLOR_CODES["YELLOW"],
        "ERROR": COLOR_CODES["RED"],
        "CRITICAL": COLOR_CODES["BOLD"] + COLOR_CODES["RED"]
    }

    def format(self, record):
        level_name = record.levelname
        colored_level_name = self.LEVEL_TO_COLOR.get(level_name, "") + level_name + self.COLOR_CODES["END"]
        colored_name = self.COLOR_CODES["MAGENTA"] + record.name + self.COLOR_CODES["END"]

        message = super().format(record)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(record.created))

        return f"{self.COLOR_CODES['GREY']}{timestamp}{self.COLOR_CODES['END']} - {colored_level_name} - {colored_name} - {message}"
