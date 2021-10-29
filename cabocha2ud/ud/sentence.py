# -*- coding: utf-8 -*-

"""
Universal Dependencies sentence class
"""
from __future__ import annotations
from typing import Optional

from ..lib.logger import Logger
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

    def set_value(self, value: str):
        self.value = value

    def __str__(self) -> str:
        return "# {} = {}".format(self.key, self.value)


class Sentence(list[Word]):
    """ Sentence class for Universal Dependencies

    Args:
        content: Optional[List[str]]: setence text list
    """

    def __init__(self, content: Optional[list[str]]=None, logger: Optional[Logger]=None):
        super(Sentence, self).__init__()
        self.logger: Logger = logger or Logger()
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

    def set_header(self, position: int, header: Header) -> None:
        self.headers.insert(position, header)
        self.header_map[header.get_key()] = header

    def get_headers(self) -> list[Header]:
        return self.headers

    def get_str_list(self, mode: str="full") -> list[str]:
        if mode == "full":
            return [str(h) for h in self.headers] + [str(ccc) for ccc in self]
        elif mode == "header":
            return [str(h) for h in self.headers]
        elif mode == "body":
            return [str(ccc) for ccc in self]
        raise KeyError("`mode` must be full, header, body")

    def __str__(self) -> str:
        return "\n".join(self.get_str_list(mode="full")) + "\n"

    def load(self, content: list[str]) -> None:
        count = 0
        while content[count].startswith("# "):
            header = Header(cont=content[count])
            self.set_header(count, header)
            count += 1
        for cont in content[count:]:
            self.append(Word(content=cont.split("\t")))

    @staticmethod
    def load_from_string(sent_str: str) -> Sentence:
        return Sentence(content=sent_str.rstrip("\n").split("\n"))

    @staticmethod
    def load_from_list(sent_lst: list[str]) -> Sentence:
        return Sentence(content=sent_lst)
