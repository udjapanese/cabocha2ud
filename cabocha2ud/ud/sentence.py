# -*- coding: utf-8 -*-

"""
Universal Dependencies sentence class
"""
from __future__ import annotations
from typing import Optional

from .word import Word


class Header:
    """ Header class for Universal Dependencies

    Args:
        key (str): key
        value (str): value
    """

    def __init__(self, key: Optional[str]=None, value: Optional[str]=None, cont: str=None):
        self.key = ""
        self.value = ""
        if cont is not None:
            assert cont.startswith("# ")
            self.key, self.value = cont.replace("# ", "").split(" = ")
        elif isinstance(key, str) and isinstance(value, str):
            self.key = key
            self.value = value
        else:
            raise KeyError("please set key and value or cont")

    def get_key(self) -> str:
        return self.key

    def get_value(self) -> str:
        return self.value

    def __str__(self) -> str:
        return "# {} = {}".format(self.key, self.value)


class Sentence(list[Word]):
    """ Sentence class for Universal Dependencies

    Args:
        content: Optional[List[str]]: setence text list
    """

    def __init__(self, content: Optional[list[str]]=None):
        super(Sentence, self).__init__()
        self.headers: list[Header] = []
        self.header_map: dict[str, Header] = {}
        if content is not None:
            self.load(content)

    def words(self) -> list[Word]:
        return self

    def word(self, id_: int) -> Word:
        assert 0 < id_ <= len(self.words()), "must be word id 0 < {} <= {}".format(id_, len(self.words()))
        return self[id_ - 1]

    def get_header_keys(self) -> list[str]:
        return list(self.header_map.keys())

    def get_header(self, key: str) -> Optional[Header]:
        return self.header_map.get(key, None)

    def __str__(self) -> str:
        sss: list[str] = []
        sss.extend([str(h) for h in self.headers])
        for ccc in self:
            sss.append(str(ccc))
        return "\n".join(sss) + "\n"

    def load(self, content: list[str]) -> None:
        count = 0
        while content[count].startswith("# "):
            header = Header(cont=content[count])
            self.headers.append(header)
            self.header_map[header.get_key()] = header
            count += 1
        for cont in content[count:]:
            self.append(Word(content=cont.split("\t")))

    @staticmethod
    def load_from_string(sent_str: str) -> Sentence:
        sent_lst = sent_str.rstrip("\n").split("\n")
        return Sentence(content=sent_lst)

    @staticmethod
    def load_from_list(sent_lst: list[str]) -> Sentence:
        return Sentence(content=sent_lst)