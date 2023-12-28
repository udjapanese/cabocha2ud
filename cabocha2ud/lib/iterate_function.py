
"""Iterator functions for cabocha format."""

import re
from typing import Iterator, Optional, Union

ATTR_NAMES = [
    "SEGMENT", "SEGMENT_S", "LINK", "GROUP", "GROUP_S"
]


def separate_information_from_excabocha(doc: list[str]) -> tuple[list[str], list[str], list[str]]:
    """拡張Cabochaの特定範囲から情報を抽出する.

    参照： https://00m.in/z1jkb
    prefix, cont, suffix に分解する.
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


def iterate_document(
    lines: list[str], separate_info: bool=True, strip_end: bool=True
) -> Iterator[tuple[Optional[list[str]], list[str], Optional[list[str]]]]:
    """Create iterate per document."""
    doc: list[str] = []
    if strip_end and lines[-1] == "":  # 下に空行があるとエラーになるため空行を除く
        pos = -1
        while lines[pos] == "":
            pos = pos - 1
        lines = lines[:pos + 1]

    target_header: Optional[re.Pattern] = None
    if lines[0].startswith("#! DOCID"):
        target_header = re.compile(r"^#! DOCID\s+.*")
    elif lines[0].startswith("#! DOC"):
        target_header = re.compile(r"^#! DOC\s+.*")
    else:
        msg = "parse Error: first line must be `#! DOC` or `#! DOCID`"
        raise TypeError(msg)

    for line in lines:
        if target_header.match(line) and len(doc) > 0:
            if separate_info:
                yield separate_information_from_excabocha(doc)
            else:
                yield (None, doc, None)
            doc = [line]
        else:
            doc.append(line)
    if len(doc) > 0:
        if not target_header.match(doc[0]):
            msg = "parse Error: first line must be `#! DOC`"
            raise TypeError(msg)
        if separate_info:
            yield separate_information_from_excabocha(doc)
        else:
            yield (None, doc, None)


def iterate_sentence(
    lines: list[str], separate_info: bool=True
) -> Iterator[tuple[list[str], Optional[list[str]]]]:
    """Iterate sentence."""
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
        msg = "parse Error: last line must be `EOS`"
        raise TypeError(msg)


def iterate_bunsetu(lines: list[str]) -> Iterator[list[str]]:
    """Iterate bunsetu."""
    if not lines[0].startswith("* "):
        msg = f"parse Error: first line must be `* ` {lines[0]}"
        raise TypeError(msg)
    sent = [lines[0]]
    for line in lines[1:]:
        if line.startswith("* "):
            yield sent
            sent = [line]
        else:
            sent.append(line)
    yield sent


def iterate_seg_and_link(lines: list[str]) -> Iterator[list[list[str]]]:
    """Iterate seg and link."""
    if len(lines) == 0:
        return
    lineit = iter(lines)
    tmp = []
    try:
        tmp.append(next(lineit))
        while True:
            line = next(lineit)
            if any(tmp[-1].startswith("#! " + name) for name in ATTR_NAMES):
                while line.startswith("#! ATTR"):
                    tmp.append(line)
                    line = next(lineit)
                yield [t.split(" ") for t in tmp]
                tmp = []
            else:
                msg = f"do not recognize the line {tmp}"
                raise TypeError(msg)
            tmp.append(line)
    except StopIteration:
        assert isinstance(tmp, list)
        yield [t.split(" ") for t in tmp]


def iterate_ud_sentence(lines: Union[list[str], Iterator[str]]) -> Iterator[list[str]]:
    """Iterate sentence list."""
    sent: list[str] = []
    for line in lines:
        if line == "":
            yield sent
            sent = []
        else:
            sent.append(line)
