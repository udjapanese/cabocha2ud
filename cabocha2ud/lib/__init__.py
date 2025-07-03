"""Utility Functions."""

import itertools
from typing import Iterable


def flatten(lst: Iterable) -> list:
    """Do flatten list.

    Args:
        lst (Iterable): list be flattend

    Returns:
        Iterable: of result flattened

    """
    return list(itertools.chain.from_iterable(lst))
