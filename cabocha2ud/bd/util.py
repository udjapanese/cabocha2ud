"""Util function or module for Bunsetu Depenedencies."""

import csv
from enum import IntEnum
from io import StringIO
from typing import Any


class DoNotExceptSizeError(Exception):
    """Exception raised for errors in the input size."""

    def __init__(self, msg:str|None=None, *args: tuple[Any,...], **kwargs: dict) -> None:
        """Init message."""
        if not msg:
            msg = "期待通りのサイズではありません"
        super().__init__(msg, *args, **kwargs)


class SUWFeaField(IntEnum):
    # pylint: disable=invalid-name
    """Items.

    (0): pos1
    (1): pos2
    (2): pos3
    (3): pos4
    (4): cType
    (5): cForm
    (6): lForm
    (7): lemma
    (8): orth
    (9): pron
    (10): orthBase
    (11): pronBase
    (12): goshu
    (13): iType
    (14): iForm
    (15): fType
    (16): fForm
    (17): iConType
    (18): fConType
    (19): type
    (20): kana
    (21): kanaBase
    (22): form
    (23): formBase
    (24): aType
    (25): aConType
    (26): aModType
    (27): lid
    (28): lemma_id

    """

    pos1 = 0
    pos2 = 1
    pos3 = 2
    pos4 = 3
    cType = 4
    cForm = 5
    lForm = 6
    lemma = 7
    orth = 8
    pron = 9
    orthBase = 10
    pronBase = 11
    goshu = 12
    iType = 13
    iForm = 14
    fType = 15
    fForm = 16
    iConType = 17
    fConType = 18
    type = 19
    kana = 20
    kanaBase = 21
    form = 22
    formBase = 23
    aType = 24
    aConType = 25
    aModType = 26
    lid = 27
    lemma_id = 28


class LUWFeaField(IntEnum):
    # pylint: disable=invalid-name
    # ruff: noqa: N815
    """LUWFeat.

    (0): l_pos1
    (1): l_pos2
    (2): l_pos3
    (3): l_pos4
    (4): l_cType
    (5): l_cForm
    (6): l_reading  <->  orthBase
    (7): l_lemma

    """

    l_pos1 = 0
    l_pos2 = 1
    l_pos3 = 2
    l_pos4 = 3
    l_cType = 4
    l_cForm = 5
    l_reading = 6
    l_lemma = 7


def csv_split(
    csv_str: str, delimiter: str=",", expect_size: int|None=None
) -> list[str]:
    """Csv split."""
    # ruff: noqa: RUF001
    if csv_str == "補助記号,読点,*,*,,,,，,,,,,,,記号,,,,,,,,,,,,,,,13752552530432,50":
        # GSDの例外
        csv_str = '補助記号,読点,*,*,,,,，,",",,",",,記号,,,,,,,,,,,,,,,13752552530432,50'
    splited =  next(iter(csv.reader(StringIO(csv_str), delimiter=delimiter)))
    if expect_size is not None:
        try:
            assert len(splited) == expect_size, csv_str
        except AssertionError as e:
            msg = f"期待通りのサイズではありません: {expect_size} 「{csv_str}」"
            raise DoNotExceptSizeError(msg) from e
    return next(iter(csv.reader(StringIO(csv_str), delimiter=delimiter)))


def csv_join(cols: list[str], delimiter: str=",") -> str:
    """Csv join function."""
    gstr = StringIO()
    joiner = csv.writer(gstr, delimiter=delimiter, lineterminator="\n")
    joiner.writerow(cols)
    return gstr.getvalue().rstrip("\n")
