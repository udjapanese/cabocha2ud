# -*- coding: utf-8 -*-

"""
util logger object
"""

import logging
from enum import Enum
from typing import Optional, Union

import logzero
from logzero import logger


class LogLevel(Enum):
    INFO: int = logging.INFO
    DEBUG: int = logging.DEBUG
    ERROR: int = logging.ERROR
    WARN: int = logging.WARN


class Logger:

    def __init__(self, mode: Optional[Union[LogLevel, str, int]]=LogLevel.INFO, logfile: Optional[str]=None, debug=False):
        self.mode: Optional[LogLevel] = LogLevel(mode) if mode is not None else None
        self.logfile: Optional[str] = logfile
        self.set_mode(mode)
        if debug:
            self.set_mode(LogLevel.DEBUG)
        if self.logfile is not None:
            logzero.logfile(self.logfile, loglevel=self.mode)

    def get_mode(self):
        return self.mode

    def set_mode(self, mode: Optional[Union[LogLevel, str, int]]):
        self.mode = LogLevel(mode) if mode is not None else None
        if self.mode is None:
            logzero.loglevel(LogLevel.INFO.value)
        else:
            logzero.loglevel(self.mode.value)

    def info(self, *args):
        self.message(*args, mode=LogLevel.INFO)

    def debug(self, *args):
        self.message(*args, mode=LogLevel.DEBUG)

    def message(self, *args, mode: Optional[LogLevel]=LogLevel.INFO):
        if mode is None:
            logger.info(" ".join(str(a) for a in args))
        else:
            return {
                LogLevel.DEBUG: logger.debug,
                LogLevel.WARN: logger.warn,
                LogLevel.INFO: logger.info,
                LogLevel.ERROR: logger.error
            }[LogLevel(mode)](" ".join(str(a) for a in args))
