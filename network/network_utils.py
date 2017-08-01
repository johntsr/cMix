import logging
import sys


class Status:
    OK = 0
    ERROR = 1


class Callback:
    KEY_SHARE = 0
    PRE_FOR_PREPROCESS = 1
    PRE_FOR_MIX = 2
    PRE_FOR_POSTPROCESS = 3
    PRE_RET_MIX = 4
    PRE_RET_POSTPROCESS = 5
    KEY_USER = 6
    USER_MESSAGE = 7
    USER_RESPONSE = 8
    REAL_FOR_PREPROCESS = 9
    REAL_FOR_MIX = 10
    REAL_FOR_MIX_COMMIT = 11
    REAL_FOR_POSTPROCESS = 12
    REAL_RET_MIX = 13
    REAL_RET_MIX_COMMIT = 14
    REAL_RET_POSTPROCESS = 15

class Message:

    def __init__(self, callback, payload):
        self.callback = callback
        self.payload = payload

    def __str__(self):
        return "\nCallback: " + str(self.callback) + "\nPayload: " + str(self.payload)


class NetworkError(RuntimeError):
    def __init__(self, arg):
        self.args = arg


def handleError(error):
    logging.exception(error)
    sys.exit(error[0])
