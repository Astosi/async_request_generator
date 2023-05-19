import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler


from logs.CustomFormatter import CoolFormatter
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

ROOT_DIR = os.getenv('ROOT_DIR')
LOG_DIR = os.path.join(ROOT_DIR, 'logs')

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOG_FILE = os.path.join(LOG_DIR, 'log_history/logs.log')

FILE_FORMATTER = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
FORMATTER = CoolFormatter()


class LoggerSingleton:
    __instance = None

    @classmethod
    def get_instance(cls):
        if cls.__instance is None:
            cls.__instance = cls()
        return cls.__instance

    def __init__(self):
        self.loggers = {}

    def get_console_handler(self):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(FORMATTER)
        return console_handler

    def get_file_handler(self):
        file_handler = TimedRotatingFileHandler(LOG_FILE, when='midnight')
        file_handler.setFormatter(FILE_FORMATTER)
        return file_handler

    def get_logger(self, logger_name):
        if logger_name in self.loggers:
            return self.loggers[logger_name]

        logger = logging.getLogger(logger_name)

        #logger.setLevel(logging.DEBUG)  # better to have too much log than not enough
        logger.setLevel(logging.WARNING)  # better to have too much log than not enough

        logger.addHandler(self.get_console_handler())
        logger.addHandler(self.get_file_handler())

        # with this pattern, it's rarely necessary to propagate the error up to parent
        logger.propagate = False

        self.loggers[logger_name] = logger
        return logger


def get_logger(logger_name):
    return LoggerSingleton.get_instance().get_logger(logger_name)
