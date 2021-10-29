# -*- coding: utf-8 -*-

""" sentence.py
"""

import copy
import xml.etree.ElementTree as ET

from typing import Optional, TYPE_CHECKING, cast
if TYPE_CHECKING:
    from .document import Document
from ..lib.iterate_function import iterate_seg_and_link, iterate_bunsetu
from ..lib.logger import Logger

from .word import Word
from .bunsetu import Bunsetu

from .annotation import (
    Segment, get_annotation_object, AnnotationList
)



class Sentence(list["Bunsetu"]):

    """Sentence class: sentence class is Bunsetu List

    """

    def __init__(
            self, sent_pos: int, sentence_lines, suffix,
            doc: "Document", base_file_name=None,
            word_unit_mode: str="suw",
            space_marker: str="　", debug: bool=False, logger: Optional[Logger]=None
    ):
        self.base_file_name: Optional[str] = base_file_name
        self.debug: bool = debug
        self.logger: Logger = logger or Logger()
        self.word_unit_mode = word_unit_mode
        self.doc: Document = doc  # sentence's document
        self.sent_pos: int = sent_pos
        self.sent_id: Optional[str] = None
        self.attributes_list: list = []
        self.annotation_list: Optional[AnnotationList] = None
        self._flatten: Optional[list[Word]] = None
        self.bunsetu_dep: list[Optional[int]] = []
        self.word_dep_child: Optional[dict[int, set[int]]] = None
        # abs_pos_* represent abstract position (begin1, end1), (begin2, end2), ...
        self.abs_pos_list: list[tuple[int, int]] = []
        self.abs_pos_dict: dict[tuple[int, int], int] = {}
        self.space_marker: str = space_marker
        self.__parse(sentence_lines, suffix)

    def __str__(self) -> str:
        org = "\n".join([
            str(bun) for bun in self
        ])
        if self.annotation_list is not None and len(self.annotation_list) > 0:
            org = org + "\n" + str(self.annotation_list)
        org = org + "\n" + "EOS"
        return org

    def get_text(self) -> str:
        return "".join([w.get_surface() for w in self.flatten()])

    def get_ud_children(self, word: Word, is_reconst: bool=False) -> set[int]:
        """
            get UD child position
        """
        if self.word_dep_child is None or is_reconst:
            word_dep_child: dict[int, set[int]] = {}
            for tword in self.flatten():
                assert isinstance(tword.dep_num, int)
                if tword.dep_num not in word_dep_child:
                    word_dep_child[tword.dep_num] = set([])
                word_dep_child[tword.dep_num].add(tword.token_pos)
            self.word_dep_child = word_dep_child.copy()
        assert self.word_dep_child is not None
        if word.token_pos in self.word_dep_child:
            return self.word_dep_child[word.token_pos]
        else:
            return set([])

    def bunsetues(self) -> list[Bunsetu]:
        """
            return bunsetu list
        """
        return list(self)

    def update_bunsetu(self, position: int, bun:Bunsetu) -> None:
        assert 0 < position < len(self)
        self[position] = bun

    def set_sent_pos(self, sent_pos: int) -> None:
        """
            set sent_pos
        """
        self.sent_pos = sent_pos
        for word in self.flatten():
            word.sent_pos = sent_pos

    def set_document(self, doc: "Document") -> None:
        """
            wordにdocumentをlinkする
        """
        for word in self.flatten():
            word.doc = doc

    def get_pos_from_word(self, word: Word) -> tuple[int, int]:
        """
            return word's pos
        """
        return self.abs_pos_list[word.token_pos-1]

    def get_word_from_tokpos(self, tok_pos: int) -> Optional[Word]:
        """
            extract word by token pos
        """
        if tok_pos < 0:
            return None
        assert all([len(bun) > 0 for bun in self])
        return self.flatten()[tok_pos]

    def iterate_word_tree(self) -> list[Word]:
        from collections import deque
        # self.update_word_pos()
        _tree: dict[int, set[int]] = {}
        root_num: Optional[int] = None
        _flat_lst = self.flatten()
        for word in _flat_lst:
            assert word.dep_num is not None
            if word.dep_num not in _tree:
                _tree[word.dep_num] = set()
            assert word.token_pos is not None
            _tree[word.dep_num].add(word.token_pos)
        assert len(_tree[0]) > 0
        norder: list[int] = []
        qlst: deque[int] = deque()
        for root_num in _tree[0]:
            qlst.append(root_num)
        while len(qlst) > 0:
            now_tokenpos = qlst.popleft()
            norder.append(now_tokenpos-1)
            if now_tokenpos not in _tree:
                continue
            stree = _tree[now_tokenpos]
            for near in stree:
                qlst.append(near)
        assert len(self.flatten()) == len(norder)
        return [_flat_lst[n] for n in norder]

    def flatten(self) -> list[Word]:
        """
            flatten word list
        """
        return [
            word for bunsetu in self.bunsetues()
            for word in bunsetu.words()
        ]

    def words(self):
        return self.flatten()

    def __parse(self, sentence_lines, annotation_list) ->  None:
        self.annotation_list = AnnotationList([
            get_annotation_object(seg)
            for seg in iterate_seg_and_link(list(annotation_list))
        ])
        bunsetu_list = [bunsetu for bunsetu in iterate_bunsetu(sentence_lines)]
        prev_bunsetu = None
        for bunsetu in bunsetu_list:
            self.append(
                Bunsetu(
                    self.sent_pos, bunsetu,
                    base_file_name=self.base_file_name, debug=self.debug,
                    prev_bunsetu=prev_bunsetu, parent_sent=self,
                    logger=self.logger, word_unit_mode=self.word_unit_mode
                )
            )
            prev_bunsetu = self[-1]
            self[-1].set_sent(self)
        self.set_document(self.doc)
        self.bunsetu_dep = [bun.dep_pos for bun in self.bunsetues()]
        self.update_word_pos()

    def update_word_pos(self) -> None:
        # 単語の位置を決める
        self.abs_pos_list = []
        for pos, word in enumerate(self.flatten()):
            word.sent_pos = self.sent_pos
            word.token_pos = pos + 1
            if len(self.abs_pos_list) == 0:
                self.abs_pos_list.append((0, len(word.surface)))
            else:
                last = self.abs_pos_list[-1]
                self.abs_pos_list.append((last[1], last[1] + len(word.surface)))
        self.abs_pos_dict = {s: p for p, s in enumerate(self.abs_pos_list)}

    def get_ud_header(self) -> str:
        """
            get header for sent
        """
        if len(self.doc) > 1:
            self.sent_id = self.doc.doc_id + "-" + str(self.sent_pos + 1)
        else:
            self.sent_id = self.doc.doc_id
        header = [("sent_id", self.sent_id)]
        header.append(("text", "".join([
            w.get_surface() + self.space_marker if w.ud_misc["SpaceAfter"] == "Yes"
            else w.get_surface()
            for bun in self for w in bun
        ]).strip(self.space_marker)))
        if self.doc.doc_attrib_xml is not None and self.doc.doc_attrib_xml.find('english_text') is not None:
            txt = self.doc.doc_attrib_xml.find('english_text')
            eng_txt = cast(str, cast(ET.Element, txt).text).replace("# english_text = ", "")
            header.append(("text_en", eng_txt))
        return "\n".join(["# {} = {}".format(t, i) for t, i in header]) + "\n"

    def convert(self, sep="\t") -> str:
        """
            ww.convert() ``update ud_misc``, so code order do not changed
        """
        self.update_word_pos()
        body = "\n".join([
            ww.convert(sep=sep) for ww in self.flatten()
        ])
        return self.get_ud_header() + body

