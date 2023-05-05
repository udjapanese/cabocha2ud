# -*- coding: utf-8 -*-

"""

Word class for UD

"""


import bisect
from typing import Optional, Union, cast

from cabocha2ud.ud.util import Field


class Content:
    """
        UD content class
    """

    def __init__(self, id_: int, content: Optional[str]):
        self.id_: int = id_
        self.field: int = Field(self.id_)
        self.content: str = content if content is not None else "_"

    def __eq__(self, __value: object) -> bool:
        assert isinstance(__value, Content)
        return self.id_ == __value.id_ and self.content == __value.content

    def __str__(self) -> str:
        return self.get_content()

    def get_id(self) -> int:
        """ get ID """
        return self.id_

    def get_content(self) -> str:
        """ get content """
        return self.content

    def set_content(self, content: str):
        """ set content """
        self.content = content


class Misc(Content):
    """
        Misc content class
    """

    def __init__(self, id_: int, content: Optional[str]):
        super().__init__(id_, content)
        self.keys: list[str] = []
        self.dcont: dict[str, str] = {}
        if content is not None:
            self._load(content.split("|"))

    def __str__(self) -> str:
        return str(self.content)

    @staticmethod
    def split_data(content: str):
        """ split data """
        data = content.split("=")
        return data[0], "=".join(data[1:])

    def _load(self, content: list[str]) -> None:
        _content = sorted([Misc.split_data(c) for c in content])
        self.keys = [k for k, _ in _content]
        self.dcont = dict((k, v) for k, v in _content)

    def get_content_from_key(self, key: str) -> str:
        """ get from key """
        if key in self.dcont:
            return self.dcont[key]
        return "_"

    def remove(self, key: str) -> None:
        """ remove by str """
        assert key in self.keys, "cant't remove {} because {} not contained in MISC"
        self.keys.remove(key)
        del self.dcont[key]
        super().set_content("|".join(["{}={}".format(k, self.dcont[k]) for k in self.keys]))

    def update(self, key: str, value: str) -> None:
        """ update the value by key """
        if key not in self.keys:
            bisect.insort_left(self.keys, value)
        self.dcont[key] = value
        super().set_content("|".join(["{}={}".format(k, self.dcont[k]) for k in self.keys]))

    def set_content(self, content: str) -> None:
        if content is not None:
            self._load(content.split("|"))
        super().set_content(content)


class Word(list[Content]):
    """
    Word class object

    1: ID: Word index, integer starting at 1 for each new sentence;
        may be a range for multiword tokens; 
            may be a decimal number for empty nodes 
            (decimal numbers can be lower than 1 but must be greater than 0).
    2: FORM: Word form or punctuation symbol.
    3: LEMMA: Lemma or stem of word form.
    4: UPOS: Universal part-of-speech tag.
    5: XPOS: Language-specific part-of-speech tag; underscore if not available.
    6: FEATS: List of morphological features from the universal feature inventory
        or from a defined language-specific extension; underscore if not available.
    7: HEAD: Head of the current word, which is either a value of ID or zero (0).
    8: DEPREL: Universal dependency relation to the HEAD (root iff HEAD = 0)
        or a defined language-specific subtype of one.
    9: DEPS: Enhanced dependency graph in the form of a list of head-deprel pairs.
    10: MISC: Any other annotation.

    """

    def __init__(self, content: Optional[Union[str, list[str]]]=None):
        super().__init__()
        if content is not None:
            if isinstance(content, str):
                self.set_by_str(content)
            else:
                self.set_by_list(content)
        else:
            for id_ in range(len(Field)):
                self.append(Content(id_, "_"))

    def __str__(self):
        return "\t".join([c.get_content() for c in self])

    def is_spaceafter(self) -> bool:
        """ 
            if MISC SpaceAfter="Yes" or not include return True 
        """
        misc = cast(Misc, self.get(Field.MISC))
        res = misc.get_content_from_key("SpaceAfter")
        return res != "No"

    def set_by_str(self, content: str):
        """ alias to set by str to list """
        self.set_by_list(content=content.split("\t"))

    def set_by_list(self, content: list[str]):
        """ set by str list """
        assert len(content) == len(Field), "must set filed size " + str(len(Field))
        self.clear()
        self.extend([
            Misc(id_, cont) if id_ == Field.MISC else Content(id_, cont)
            for id_, cont in enumerate(content)
        ])

    def get(self, position: Union[Field, str, int]) -> Content:
        """ get content by position """
        if isinstance(position, str):
            return self[Field[position]]
        return self[position]

    def set(self, pos: Union[Field, str, int], content: Union[str, int]):
        """ set content by position """
        pos = Field[pos].value if isinstance(pos, str) else pos
        if pos == Field.MISC:
            self[pos] = Misc(pos, str(content))
        else:
            self[pos] = Content(pos, str(content))

    def get_value_str_list(self) -> list[str]:
        """ get value """
        return [str(content) for content in self]
