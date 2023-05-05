# -*- coding: utf-8 -*-

"""
Filed for UD
"""

from enum import IntEnum, auto

COLCOUNT = 10
ID, FORM, LEMMA, UPOS, XPOS, FEATS, HEAD, DEPREL, DEPS, MISC = range(COLCOUNT)


class Field(IntEnum):
    # pylint: disable=invalid-name
    """
    Instance for UD field
    """
    ID = 0
    FORM = auto()
    LEMMA = auto()
    UPOS = auto()
    XPOS = auto()
    FEATS = auto()
    HEAD = auto()
    DEPREL = auto()
    DEPS = auto()
    MISC = auto()
