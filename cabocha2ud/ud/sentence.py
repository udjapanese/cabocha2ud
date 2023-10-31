# -*- coding: utf-8 -*-

"""
Universal Dependencies sentence class
"""

from __future__ import annotations

from typing import Optional, Union

from cabocha2ud.lib.list_based_key import ListBasedKey
from cabocha2ud.lib.logger import Logger
from cabocha2ud.ud.util import Field
from cabocha2ud.ud.word import Content, Misc, Word


class Header:
    """ Header class for Universal Dependencies
        # {key} = {value}
    Args:
        key (str): key
        value (str): value
    """

    def __init__(
        self, key: Optional[str]=None, value: Optional[str]=None, cont: Optional[str]=None
    ):
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

    def __eq__(self, __value: object) -> bool:
        assert isinstance(__value, Header)
        return self.key == __value.key and self.value == __value.value

    def __str__(self) -> str:
        """ return str """
        return "# {} = {}".format(self.key, self.value)

    def get_key(self) -> str:
        """ get key """
        return self.key

    def get_value(self) -> str:
        """ get value """
        return self.value

    def set_value(self, value: str):
        """ set value """
        self.value = value


class Sentence(list[Word]):
    """
        Sentence class for Universal Dependencies

    Args:
        content: Optional[List[str]]: setence text list
    """

    def __init__(
        self, content: Optional[list[str]]=None, spt: str=" ",
        logger: Optional[Logger]=None
    ):
        super().__init__()
        self.logger: Logger = logger or Logger()
        self.headers: ListBasedKey[Header] = ListBasedKey()
        self.sentence_text: str = ""
        self._sp: Optional[str] = spt
        if content is not None:
            self.load(content)

    def __str__(self) -> str:
        return "\n".join(self.get_str_list(mode="full")) + "\n"

    def get_sentence_text(self) -> str:
        """ get sentence """
        self.update_sentence()
        return self.sentence_text

    def update_sentence(self) -> None:
        """ update sentence text """
        assert self._sp is not None
        self.sentence_text = "".join([
            wrd.get(Field.FORM).get_content() + (
                self._sp if wrd.is_spaceafter() else ""
            )
            for wrd in self
        ]).rstrip(self._sp)
        self.fix_header_by_key("text", self.sentence_text)

    def words(self) -> list[Word]:
        """ return words of self """
        return list(self)

    def word(self, id_: int) -> Word:
        """ return word for _id """
        assert 0 < id_ <= len(self.words()), f"must be word id 0 < {id_} <= {len(self.words())}"
        return self[id_ - 1]

    def set_word_content(self, id_: int, _field: Union[int, Field], cnt: Union[str, int]) -> None:
        """
            Set word content id_: Word
        """
        assert 0 < id_ <= len(self.words()), f"must be word id 0 < {id_} <= {len(self.words())}"
        self[id_ - 1].set(_field, cnt)

    def get_header_keys(self) -> list[str]:
        """ get header's key """
        return self.headers.keys()

    def get_header(self, key: str) -> Optional[Header]:
        """ get header for key """
        return self.headers.get_item(key)

    def get_headers(self) -> list[Header]:
        """ get headers """
        return self.headers

    def fix_header_by_key(self, key: str, value: str) -> None:
        """ alias to str key """
        assert self.headers.include_key(key)
        hdr_ = self.headers.get_item(key)
        assert hdr_ is not None
        hdr_.set_value(value)
        self.headers.set_item(key, hdr_)

    def set_header(self, position: int, header: Header) -> None:
        """ set header for position """
        self.headers.insert_with_key(position, header.get_key(), header)

    def remove_header(self, key: str) -> None:
        """ remove header """
        assert key in self.headers
        self.headers.remove_obj_by_key(key)

    def get_str_list(self, mode: str="full") -> list[str]:
        """ get str list """
        if mode == "full":
            return [str(h) for h in self.headers] + [str(ccc) for ccc in self]
        if mode == "header":
            return [str(h) for h in self.headers]
        if mode == "body":
            return [str(ccc) for ccc in self]
        raise KeyError("`mode` must be full, header, body")

    def get_colmuns(self, field: Field) -> list[Content]:
        """ get columns for the filed (一列抜き取ってくる) """
        return [w.get(field) for w in self]

    def load(self, content: list[str]) -> None:
        """ load content list[str] """
        count = 0
        while content[count].startswith("# "):
            header = Header(cont=content[count])
            self.set_header(count, header)
            count += 1
        for cont in content[count:]:
            self.append(Word(content=cont.split("\t")))
        self.update_sentence()

    def get_bunsetsu_list(self) -> list[list[Word]]:
        """
            get splited list by bunsetsu
        """
        nlist: list[list[Word]] = []
        for word in self.words():
            misc_info = word[Field.MISC]
            assert isinstance(misc_info, Misc)
            if misc_info.get_content_from_key("BunsetuBILabel") == "B":
                nlist.append([])
            nlist[-1].append(word)
        return nlist

    @staticmethod
    def load_from_string(sent_str: str, spt: str=" ") -> Sentence:
        """ load Sentence object from string """
        return Sentence(
            content=sent_str.rstrip("\n").split("\n"),
            spt=spt
        )

    @staticmethod
    def load_from_list(
        sent_lst: list[str], spt: str=" ", logger: Optional[Logger]=None
    ) -> Sentence:
        """ load Sentence object from string list """
        return Sentence(content=sent_lst, spt=spt, logger=logger)
