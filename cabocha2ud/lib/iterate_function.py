# -*- coding: utf-8 -*-

"""
iterator functions for cabocha format
"""

import re
from typing import Iterator, Tuple, Optional


RE_DOC_HEADER = re.compile(r'^#! DOC\s+[0-9]+$')
ATTR_NAMES = [
    "SEGMENT", "SEGMENT_S", "LINK", "GROUP", "GROUP_S"
]


def separate_information_from_excabocha(doc: list[str]) -> Tuple[list[str], list[str], list[str]]:
    """ 拡張Cabochaの特定範囲から情報を抽出する
        参照： https://ja.osdn.net/projects/chaki/wiki/%E6%8B%A1%E5%BC%B5Cabocha%E3%83%95%E3%82%A9%E3%83%BC%E3%83%9E%E3%83%83%E3%83%88%E3%81%B8%E3%81%AE%E3%82%A8%E3%82%AF%E3%82%B9%E3%83%9D%E3%83%BC%E3%83%88
        prefix, cont, suffix に分解する
    """
    prefix: list[str] = []
    suffix: list[str] = []
    pos = 0
    line = doc[pos]
    while line.startswith("#! "):
        prefix.append(line)
        pos += 1
        line = doc[pos]
    doc = doc[pos:]
    pos = -1
    line = doc[pos]
    while line.startswith("#! "):
        suffix.insert(0, line)
        pos += -1
        line = doc[pos]
    if pos != -1:
        # 末尾の述語情報などがついていた場合ずらす
        doc = doc[:pos+1]
    return (prefix, doc, suffix)


def iterate_document(lines: list[str], separate_info: bool=True, strip_end=True) -> Iterator[Tuple[Optional[list[str]], list[str], Optional[list[str]]]]:
    """
        Create iterate per document
    Args:
        lines (list[str]): cabocha text
        separate_info (bool, optional): [description]. Defaults to True.

    Raises:
        TypeError: [description]

    Yields:
        Iterator[Tuple[Optional[list[str]], list[str], Optional[list[str]]]]:
            the first values: prefix information or None
            the second values: content
            the first values: suffix information or None
    """
    doc: list[str] = []
    if strip_end:
        if lines[-1] == "":
            # 下に空行があるとエラーになるため空行を除く
            pos = -1
            while lines[pos] == "":
                pos = pos - 1
            lines = lines[:pos + 1]
    for line in lines:
        if RE_DOC_HEADER.match(line) and len(doc) > 0:
            if separate_info:
                yield separate_information_from_excabocha(doc)
            else:
                yield (None, doc, None)
            doc = [line]
        else:
            doc.append(line)
    if len(doc) > 0:
        if not RE_DOC_HEADER.match(doc[0]):
            raise TypeError("parse Error: first line must be `#! DOC`")
        if separate_info:
            yield separate_information_from_excabocha(doc)
        else:
            yield (None, doc, None)


def iterate_sentence(lines: list[str], separate_info: bool=True) -> Iterator[Tuple[list[str], Optional[list[str]]]]:
    """
        iterate sentence
    """
    sent: list[str] = []
    for line in lines:
        if line.startswith("EOS"):
            if separate_info:
                _, cont, suffix = separate_information_from_excabocha(sent)
                yield cont, suffix
            else:
                yield (sent, None)
            sent = []
        else:
            sent.append(line)
    if len(sent) > 0:
        raise TypeError("parse Error: last line must be `EOS`")


def iterate_bunsetu(lines: list[str]) -> Iterator[list[str]]:
    """
        iterate bunsetu
    """
    if not lines[0].startswith("* "):
        raise TypeError("parse Error: first line must be `* `")
    sent = [lines[0]]
    for line in lines[1:]:
        if line.startswith("* "):
            yield sent
            sent = [line]
        else:
            sent.append(line)
    yield sent


def iterate_seg_and_link(lines: list[str]) -> Iterator[list[list[str]]]:
    """
        iterate seg and link
    """
    if len(lines) == 0:
        return []
    lineit = iter(lines)
    tmp = [next(lineit)]
    try:
        while True:
            line = next(lineit)
            if any([tmp[-1].startswith("#! " + name) for name in ATTR_NAMES]):
                while line.startswith("#! ATTR"):
                    tmp.append(line)
                    line = next(lineit)
                yield [t.split(" ") for t in tmp]
                tmp = []
            else:
                raise TypeError("do not recognize the line", tmp)
            tmp.append(line)
    except StopIteration:
        yield [t.split(" ") for t in tmp]
