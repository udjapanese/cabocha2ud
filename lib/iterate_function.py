# -*- coding: utf-8 -*-

"""
iterator functions for cabocha format
"""

import re

RE_DOC_HEADER = re.compile(r'^#! DOC\s+[0-9]+$')
ATTR_NAMES = [
    "SEGMENT", "SEGMENT_S", "LINK", "GROUP", "GROUP_S"
]

def iterate_document(lines):
    """
        iterate sentence
    """
    doc = []
    for line in lines:
        if RE_DOC_HEADER.match(line) and len(doc) > 0:
            yield doc
            doc = [line]
        else:
            doc.append(line)
    if len(doc) > 0:
        if not RE_DOC_HEADER.match(doc[0]):
            raise TypeError("parse Error: first line must be `#! DOC`")
        yield doc


def iterate_sentence(lines):
    """
        iterate sentence
    """
    sent = []
    for line in lines:
        if line.startswith("EOS"):
            yield sent
            sent = []
        else:
            sent.append(line)
    if len(sent) > 0:
        raise TypeError("parse Error: last line must be `EOS`")


def iterate_bunsetu(lines):
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


def iterate_seg_and_link(lines):
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
