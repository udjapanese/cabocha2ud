"""Util logger object."""

import logging
import re
from enum import Enum
from typing import Optional, TypeVarTuple

import logzero
from logzero import logger

Ts = TypeVarTuple("Ts")

class LogLevel(Enum):
    """Logger Level enum."""

    INFO = logging.INFO
    DEBUG = logging.DEBUG
    ERROR = logging.ERROR
    WARN = logging.WARNING


fmt_re = re.compile(r"%[-+#0 ]?\d*(\.\d+)?[sdxfegEG]")
def is_printf_format_string(s: str) -> bool:
    """与えられた文字列が printf 形式 (%s, %d など) の書式文字列かどうかを判定."""
    return bool(fmt_re.search(s))


class Logger:
    """Logger wrapper Object."""

    def __init__(
        self, mode: LogLevel | str | int | None=LogLevel.INFO,
        logfile: Optional[str]=None, debug:bool=False
    ) -> None:
        """Logger init."""
        self.mode: Optional[LogLevel] = None
        self.logfile: Optional[str] = logfile
        if debug:
            mode = LogLevel.DEBUG
        self.set_mode(mode)
        if self.logfile is not None:
            logzero.logfile(self.logfile, loglevel=self.mode)

    def get_mode(self) -> LogLevel | None:
        """Get logger mode."""
        return self.mode

    def set_mode(self, mode: LogLevel | str | int | None) -> None:
        """Set logger mode."""
        self.mode = LogLevel(mode) if mode is not None else None
        if self.mode is None:
            logzero.loglevel(LogLevel.INFO.value)
        else:
            logzero.loglevel(self.mode.value)

    def info(self, *args: *tuple[object,...]) -> None:
        """Info alias function."""
        self.message(*args, mode=LogLevel.INFO)

    def debug(self, *args: *tuple[object,...]) -> None:
        """Debug alias function."""
        self.message(*args, mode=LogLevel.DEBUG)

    def message(self, *args: *tuple[object,...], mode: LogLevel|None=LogLevel.INFO) -> None:
        """Logger message funciton."""
        if isinstance(args[0], str) and is_printf_format_string(args[0]):
            fmt_msg = args[0] % args[1:]
        else:
            fmt_msg = " ".join(str(a) for a in args)
        if mode is None:
            logger.info(fmt_msg)
        else:
            {
                LogLevel.DEBUG: logger.debug,
                LogLevel.WARN: logger.warning,
                LogLevel.INFO: logger.info,
                LogLevel.ERROR: logger.error
            }[LogLevel(mode)](fmt_msg)
