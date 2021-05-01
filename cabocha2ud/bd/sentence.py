# -*- coding: utf-8 -*-

""" sentence.py
"""

from typing import Optional, Union, TYPE_CHECKING, cast
if TYPE_CHECKING:
    from .document import Document

from ..lib.iterate_function import iterate_seg_and_link, iterate_bunsetu

from .word import Word
from .bunsetu import Bunsetu
from .annotation import (
    get_annotation_object, AnnotationList
)



class Sentence(list):

    """Sentence class: sentence class is Bunsetu List

    """

    def __init__(
            self, data_type, sent_pos, sentence_lines, suffix,
            doc, base_file_name=None,
            word_unit="suw", space_marker="　", debug=False
    ):
        self.base_file_name: Optional[str] = base_file_name
        self.data_type: str = data_type
        self.word_unit: str = word_unit
        self.debug: bool = debug
        self.doc = doc  # sentence's document
        self.sent_pos = sent_pos
        self.sent_id = None
        self.attributes_list = []
        self.annotation_list = None
        self._flatten: Optional[list[Word]] = None
        self.bunsetu_dep = []
        self.word_dep_child = None
        # abs_pos_* represent abstract position (begin1, end1), (begin2, end2), ...
        self.abs_pos_list: list[tuple[int, int]] = []
        self.abs_pos_dict = {}
        self.space_marker = space_marker
        self.__parse(sentence_lines, suffix)

    def __str__(self) -> str:
        org = "\n".join([
            str(bun) for bun in self
        ])
        if len(self.annotation_list) > 0:
            org = org + "\n" + str(self.annotation_list)
        org = org + "\n" + "EOS"
        return org

    def get_ud_children(self, word, is_reconst=False):
        """
            get UD child position
        """
        if self.word_dep_child is None or is_reconst:
            word_dep_child = {}
            for tword in self.flatten():
                if tword.dep_num not in word_dep_child:
                    word_dep_child[tword.dep_num] = set([])
                word_dep_child[tword.dep_num].add(tword.token_pos)
            self.word_dep_child = word_dep_child.copy()
        if word.token_pos in self.word_dep_child:
            return self.word_dep_child[word.token_pos]
        else:
            return set([])

    def bunsetues(self) -> list[Bunsetu]:
        """
            return bunsetu list
        """
        return list(self)

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
        if self._flatten is not None:
            return self._flatten[tok_pos]
        else:
            raise KeyError

    def flatten(self, is_update=False) -> list[Word]:
        """
            flatten word list
        """
        # print self._flatten, is_update
        if self._flatten is None or is_update:
            self._flatten = [
                word for bunsetu in self.bunsetues()
                for word in bunsetu.words()
            ]
        return self._flatten

    def __parse(self, sentence_lines, annotation_list) ->  None:
        self.annotation_list = AnnotationList([
            get_annotation_object(seg)
            for seg in iterate_seg_and_link(list(reversed(annotation_list)))
        ])
        bunsetu_list = [bunsetu for bunsetu in iterate_bunsetu(sentence_lines)]
        prev_bunsetu = None
        for bunsetu in bunsetu_list:
            self.append(
                Bunsetu(
                    self.data_type, self.sent_pos, bunsetu,
                    base_file_name=self.base_file_name, debug=self.debug,
                    word_unit=self.word_unit, prev_bunsetu=prev_bunsetu
                )
            )
            prev_bunsetu = self[-1]
        self.set_document(self.doc)
        # 文節の掛かり先を決める
        for bunsetu in self.bunsetues():
            self.bunsetu_dep.append(bunsetu.dep_pos)
        # 単語の位置を決める
        for pos, word in enumerate(self.flatten()):
            word.token_pos = pos + 1
            if len(self.abs_pos_list) == 0:
                self.abs_pos_list.append((0, len(word.surface)))
            else:
                last = self.abs_pos_list[-1]
                self.abs_pos_list.append((last[1], last[1] + len(word.surface)))
        self.abs_pos_dict = {s: p for p, s in enumerate(self.abs_pos_list)}
        # detect_dep_inbunsetu(self)

    def get_header(self) -> str:
        """
            get header for sent
        """
        if len(self.doc) > 1:
            self.sent_id = self.doc.doc_id + "-" + str(self.sent_pos + 1)
        else:
            self.sent_id = self.doc.doc_id
        header = []
        header.append(("sent_id", self.sent_id))
        header.append(("text", "".join([
                w.get_surface() + self.space_marker if w.ud_misc["SpaceAfter"] == "Yes"
                else w.get_surface()
                for bun in self for w in bun
        ]).strip(self.space_marker)))
        if self.doc.doc_attrib_xml is not None and self.doc.doc_attrib_xml.find('english_text') is not None:
            eng_txt = self.doc.doc_attrib_xml.find('english_text').text.replace("# english_text = ", "")
            header.append(("text_en", eng_txt))
        return "\n".join(["# {} = {}".format(t, i) for t, i in header]) + "\n"

    def convert(self, sep="\t", is_skip_space=True) -> str:
        return self.get_header() + "\n".join([
            ww.convert(sep=sep) for ww in self.flatten()
        ])

