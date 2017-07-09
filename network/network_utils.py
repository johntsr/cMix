import logging
import sys


class Status:
    OK = 0
    ERROR = 1


class Callback:
    KEY_SHARE = 0


class NetworkError(RuntimeError):
    def __init__(self, arg):
        self.args = arg


def handleError(error):
    logging.exception(error)
    sys.exit(error[0])
