# -*- coding: utf-8 -*-

from typing import Optional, Union
import bisect

from .util import Field

class Content:

    def __init__(self, id_: int, content: Optional[str]):
        self.id_: int = id_
        self.field: int = Field(self.id_)
        self.content: Optional[str] = content

    def get_id(self) -> int:
        return self.id_

    def get_content(self) -> Optional[str]:
        return self.content

    def set_content(self, content: Optional[str]):
        self.content = content

    def __str__(self) -> str:
        return str(self.content)

class Misc(Content):

    def __init__(self, id_: int, content: Optional[str]):
        super().__init__(id_, content)
        self.keys: list[str] = []
        self.dcont: dict[str, str] = {}
        if content is not None:
            self._load(content.split("|"))

    def _load(self, content: list[str]) -> None:
        _content = sorted([c.split("=") for c in content])
        self.keys = [k for k, _ in _content]
        self.dcont = dict([(k, v) for k, v in _content])

    def get_from_key(self, key: str) -> str:
        if key in self.dcont:
            return self.dcont[key]
        raise KeyError("Not Found: {} in MISC".format(key))

    def update(self, key: str, value: str) -> None:
        if key not in self.keys:
            bisect.insort_left(self.keys, value)
        self.dcont[key] = value
        super().set_content("|".join(["{}={}".format(k, self.dcont[k]) for k in self.keys]))

    def set_content(self, content: Optional[str]) -> None:
        if content is not None:
            self._load(content.split("|"))
        super().set_content(content)

    def __str__(self) -> str:
        return str(self.content)



class Word(list[Content]):
    """

1: ID: Word index, integer starting at 1 for each new sentence; may be a range for multiword tokens; may be a decimal number for empty nodes (decimal numbers can be lower than 1 but must be greater than 0).
2: FORM: Word form or punctuation symbol.
3: LEMMA: Lemma or stem of word form.
4: UPOS: Universal part-of-speech tag.
5: XPOS: Language-specific part-of-speech tag; underscore if not available.
6: FEATS: List of morphological features from the universal feature inventory or from a defined language-specific extension; underscore if not available.
7: HEAD: Head of the current word, which is either a value of ID or zero (0).
8: DEPREL: Universal dependency relation to the HEAD (root iff HEAD = 0) or a defined language-specific subtype of one.
9: DEPS: Enhanced dependency graph in the form of a list of head-deprel pairs.
10: MISC: Any other annotation.

    """
    def __init__(self, content: Optional[list[str]]=None):
        super(Word, self).__init__()
        if content is not None:
            self.__load(content)
        else:
            for id_ in range(len(Field)):
                self.append(Content(id_, "_"))

    def __str__(self):
        return "\t".join([str(c) for c in self])

    def __load(self, content: list[str]):
        for id_, cont in enumerate(content):
            if id_ == Field.MISC:
                self.append(Misc(id_, cont))
            else:
                self.append(Content(id_, cont))
        if len(self) != len(Field):
            raise ValueError("must set filed size " + str(len(Field)))

    def get(self, position: Union[Field, str]) -> Content:
        if isinstance(position, str):
            return self[Field[position]]
        return self[position]
