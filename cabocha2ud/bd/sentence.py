# -*- coding: utf-8 -*-

"""
Bunsetsu Sentence Object
"""

import xml.etree.ElementTree as ET
from collections import deque
from typing import TYPE_CHECKING, Optional, cast

if TYPE_CHECKING:
    from .document import Document

from cabocha2ud.bd.annotation import AnnotationList, get_annotation_object
from cabocha2ud.bd.bunsetu import Bunsetu
from cabocha2ud.bd.word import Word
from cabocha2ud.lib.dependency import get_caused_nonprojectivities
from cabocha2ud.lib.iterate_function import (iterate_bunsetu,
                                             iterate_seg_and_link)
from cabocha2ud.lib.logger import Logger


class Sentence(list["Bunsetu"]):
    """
        Sentence class: sentence class is Bunsetu List
    """

    def __init__(
            self, sent_pos: int, sentence_lines: list[str], suffix: Optional[list[str]],
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
        self.annotation_list: AnnotationList
        self.word_dep_child: Optional[dict[int, set[int]]] = None
        # abs_pos_* represent abstract position (begin1, end1), (begin2, end2), ...
        self.abs_pos_list: list[tuple[int, int]] = []
        self.abs_pos_dict: dict[tuple[int, int], int] = {}
        self.space_marker: str = space_marker
        self.__parse(sentence_lines, [] if suffix is None else suffix)

    def __str__(self) -> str:
        org = "\n".join([str(bun) for bun in self])
        if self.annotation_list is not None and len(self.annotation_list) > 0:
            org = org + "\n" + str(self.annotation_list)
        org = org + "\n" + "EOS"
        return org

    def get_text(self) -> str:
        """ get text for Sentence

        Returns:
            str: return str
        """
        return "".join([
            w.get_surface() + self.space_marker
            if w.has_space_after() else w.get_surface()
            for bun in self for w in bun
        ])

    def get_ud_children(self, word: Word, is_reconst: bool=False) -> set[int]:
        """
            get UD child position
        """
        if self.word_dep_child is None or is_reconst:
            self._update_ud_children()
        assert self.word_dep_child is not None
        if word.token_pos in self.word_dep_child:
            return self.word_dep_child[word.token_pos]
        return set([])

    def _update_ud_children(self):
        word_dep_child: dict[int, set[int]] = {}
        for tword in self.words():
            assert isinstance(tword.dep_num, int)
            if tword.dep_num not in word_dep_child:
                word_dep_child[tword.dep_num] = set([])
            word_dep_child[tword.dep_num].add(tword.token_pos)
        self.word_dep_child = word_dep_child.copy()

    def bunsetues(self) -> list[Bunsetu]:
        """
            return bunsetu list
        """
        return list(self)

    def update_bunsetu(self, position: int, bun: Bunsetu) -> None:
        """ update bunsetu """
        assert 0 <= position < len(self)
        self[position] = bun

    def set_sent_pos(self, sent_pos: int) -> None:
        """
            set sent_pos
        """
        self.sent_pos = sent_pos
        for word in self.words():
            word.sent_pos = sent_pos

    def set_document(self, doc: "Document") -> None:
        """
            wordにdocumentをlinkする
        """
        for word in self.words():
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
        assert all(len(bun) > 0 for bun in self)
        return self.words()[tok_pos]

    def iterate_word_tree(self) -> list[Word]:
        """ return word tree iterator """
        _tree: dict[int, set[int]] = {}
        root_num: Optional[int] = None
        for word in self.words():
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
        assert len(self.words()) == len(norder)
        return [self.words()[n] for n in norder]

    def words(self) -> list[Word]:
        """ get word's list """
        return [
            word for bunsetu in self.bunsetues()
            for word in bunsetu.words()
        ]

    def __parse(self, sentence_lines: list[str], annotation_list: list[str]) ->  None:
        self.annotation_list = AnnotationList([
            get_annotation_object(seg)
            for seg in iterate_seg_and_link(list(annotation_list))
        ])
        prev_bunsetu = None
        for bunsetu in iterate_bunsetu(sentence_lines):
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
        self.update_word_pos()
        try:
            self.validate_bunsetu_dependencies()
        except KeyError as _:
            self.set_sent_id()
            self.logger.debug("The sentence has invalid tree: {}, skip".format(self.sent_id))

    def validate_bunsetu_dependencies(self, strict=False) -> bool:
        """ 文節間の依存関係にエラーがないか確認する

        Returns:
            bool: 問題なければTrue、問題があるならFalse
        """
        # 文節木の構築
        _bunsetu_dep: list[int] = [-1]
        prev_pos: int = -1
        for bunsetu in self.bunsetues():
            assert isinstance(bunsetu.bunsetu_pos, int)
            assert isinstance(bunsetu.dep_pos, int), "must be set integer number"
            assert bunsetu.bunsetu_pos == prev_pos + 1, "`bunsetu_pos` must be sequential"
            assert bunsetu.dep_pos in list(range(0, len(self.bunsetues()))) + [-1], \
                "`bunsetu.dep_pos`: {} must be range: {}".format(
                    bunsetu.dep_pos, list(range(0, len(self.bunsetues()))) + [-1]
            )
            _bunsetu_dep.append(bunsetu.dep_pos + 1)
            prev_pos = bunsetu.bunsetu_pos
        if not strict:
            return True
        # 文節間で交差があるか確認をする
        nonprojectives = {}
        for bunsetu in self.bunsetues():
            assert isinstance(bunsetu.bunsetu_pos, int) and isinstance(bunsetu.dep_pos, int)
            res = [
                r - 1 for r in get_caused_nonprojectivities(bunsetu.bunsetu_pos+1, _bunsetu_dep)
            ]
            if len(res) > 0:
                # 部分並列になるものはDXと表現されるため、そのものは除外
                if bunsetu.dep_type == "DX":
                    continue
                if all(self.bunsetues()[r].dep_type == "DX" for r in res):
                    continue
                nonprojectives[bunsetu.bunsetu_pos] = res
        if len(nonprojectives) > 0:
            raise KeyError(f"has non-projective bunsetu: {self.sent_id} {nonprojectives}")
        return True

    def update_word_pos(self) -> None:
        """ 単語の位置を決める """
        self.abs_pos_list = []
        for pos, word in enumerate(self.words()):
            word.sent_pos = self.sent_pos
            word.token_pos = pos + 1
            if len(self.abs_pos_list) == 0:
                self.abs_pos_list.append((0, len(word.get_surface())))
            else:
                last = self.abs_pos_list[-1]
                self.abs_pos_list.append((last[1], last[1] + len(word.get_surface())))
        self.abs_pos_dict = {s: p for p, s in enumerate(self.abs_pos_list)}

    def set_sent_id(self):
        """ set sent_id
            if doc_id is set: with doc_id
        """
        if self.annotation_list.find_key_annotations("sent-id"):
            sent_attr = self.annotation_list.find_key_annotations("sent-id")[0]
            self.sent_id = sent_attr.get_attr_value("sent-id")
        else:
            if self.doc.doc_id is not None:
                self.sent_id = self.doc.doc_id
                if len(self.doc.sentences()) > 1:
                    self.sent_id += "-" + str(self.sent_pos + 1)
            else:
                self.sent_id = "sent" + "-" + str(self.sent_pos + 1)

    def get_ud_header(self) -> str:
        """
            get header for sent
        """
        self.set_sent_id()
        header = [("sent_id", self.sent_id)]
        header.append(("text", self.get_text().strip(self.space_marker)))
        if self.doc.doc_attrib_xml and self.doc.doc_attrib_xml.find('english_text'):
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
            ww.convert(sep=sep) for ww in self.words()
        ])
        return self.get_ud_header() + body
