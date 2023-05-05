# -*- coding: utf-8 -*-

"""
Bunsetu Dependencies document class
"""

import os
import re
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING, Optional, cast

from ..lib.iterate_function import iterate_seg_and_link, iterate_sentence
from ..lib.logger import Logger
from ..rule.bunsetu_rule import detect_bunsetu_jp_type

if TYPE_CHECKING:
    from .word import Word

from ..rule.bunsetu_rule import detect_dep_bunsetu
from ..rule.dep import SubRule, detect_ud_label
from ..rule.pos import detect_ud_pos
from ..rule.remove_multi_subj import adapt_nsubj_to_dislocated_rule
from ..rule.remove_space import skip_jsp_token_from_sentence
from .annotation import (AnnotationList, DocAnnotation, generate_docannotation,
                         get_annotation_object)
from .sentence import Sentence
from .word import Word

RE_SAHEN_MATCH = re.compile("^名詞.*サ変.*")


def __replace_pos_and_label(sent: "Sentence"):
    """
    後処理のPOSとDEPRELの置換

    Args:
        sent (Sentence): 対象の文
    """
    for wrd in sent.words():
        # UPOSについての置換
        if wrd.dep_label == "punct":
            wrd.en_pos = ["PUNCT"]
        if len(wrd.en_pos) > 0:
            if wrd.en_pos[0] == "AUX" and wrd.dep_label == "compound":
                wrd.dep_label = "aux"
            if wrd.en_pos[0] == "AUX" and wrd.dep_label == "cc":
                wrd.en_pos[0] = "CCONJ"
            if wrd.en_pos[0] == "NOUN" and wrd.get_luw_pos() == "助動詞":
                wrd.en_pos[0] = "AUX"
        parent = wrd.get_parent_word()
        if parent is None:
            continue
        if parent.dep_label == "fixed":
            # fixed -> fixed の場合
            wrd.dep_num = parent.dep_num
            continue
        if parent.dep_label == "cc" and wrd.dep_label in ["aux", "mark"]:
            wrd.dep_label = "fixed"
            continue
        if parent.dep_label == "aux" and wrd.dep_label in ["case", "mark"]:
            wrd.dep_label = "fixed"
            continue
        if parent.word_pos == 0 and parent.dep_label == "case" and wrd.dep_label in ["aux", "mark"]:
            wrd.dep_label = "fixed"
            continue
        if (
            wrd.en_pos[0] == "ADP" and wrd.dep_label in ["fixed"]
                and wrd.token_pos < parent.token_pos
        ):
            if parent.dep_label != "case":
                wrd.dep_label = "case"
                continue
            if wrd.token_pos == 1:
                continue
            wrd.dep_label = "case" # わりと特殊  B024n_PM25_00027-131


class Document(list["Sentence"]):
    """
     Document object
    """

    def __init__(
            self, text: Optional[list[str]]=None, prefix: Optional[list[str]]=None,
            suffix: Optional[list[str]]=None,
            base_file_name: Optional[str]="doc", word_unit_mode: str="suw",
            space_marker: str="　", debug: bool=False, logger: Optional[Logger]=None
    ):
        self.base_file_name: Optional[str] = base_file_name
        self.debug: bool = debug
        self.logger: Logger = logger or Logger()
        # モードオプション   suw or luw
        self.word_unit_mode = word_unit_mode
        # 先頭の情報
        self.doc_attributes: DocAnnotation
        self.doc_attrib_xml: ET.Element = ET.fromstring("<root></root>")
        self.doc_id: Optional[str]
        # 末尾の注釈
        self.doc_annotation: AnnotationList = AnnotationList([])
        # 文書上での絶対位置
        self.abs_pos_list: list[list[tuple[int, int]]] = []
        self.space_marker: str = space_marker
        self.text: Optional[list[str]] = text
        self.prefix: Optional[list[str]] = prefix
        self.suffix: Optional[list[str]] = suffix

    def parse(self) -> None:
        """ Document parse function """
        if self.text is not None and self.prefix is not None and self.suffix is not None:
            self.__parse(self.text, self.prefix, self.suffix)
        else:
            raise NotImplementedError

    def convert_ud(
        self, pos_rule: list, dep_rule: list[tuple[list[SubRule], str]],
        skip_space: bool=True, sep: str="\n"
    ) -> list[str]:
        """
            convert to UD format
        """
        self.detect_ud_dependencies()
        # UD掛かり先ラベルを付与
        for sent in self.sentences():
            _loop_convud(sent, pos_rule, dep_rule)
        # スペースの除去をする
        if skip_space:
            skip_jsp_token_from_sentence(self)
        # UD確定の後処理
        post_proceeing_function(self)
        return [
            sent.convert() + sep for sent in self.sentences()
        ]

    def __str__(self) -> str:
        org = "\n".join([
            str(sent) for sent in self.sentences()
        ])
        org = str(self.doc_attributes) + org
        if len(self.doc_annotation) > 0:
            org = org + "\n" + str(self.doc_annotation)
        return org

    def get_pos_from_word(self, word: "Word") -> tuple[int, int]:
        """
            word の位置を返す
        """
        return cast(tuple[int, int], self.abs_pos_list[word.sent_pos][word.token_pos-1])

    def sentences(self) -> list["Sentence"]:
        """
            get sentences
        """
        return list(self)

    def __parse(self, text: list[str], prefix: list[str], suffix: list[str]) -> None:
        self.doc_attributes = generate_docannotation(prefix)
        # パース後に取得
        if self.doc_attributes.attrib is not None:
            doc_attrs = self.doc_attributes.attrib
            if doc_attrs is not None:
                self.doc_attrib_xml = ET.fromstring(
                    '<root>' + doc_attrs.replace('&', '&amp;') + '</root>'
                )
        self.doc_id = get_doc_id(self)
        doc_annotation = suffix
        self.doc_annotation = AnnotationList([
            get_annotation_object(seg)
            for seg in iterate_seg_and_link(list(doc_annotation))
        ])
        for pos, psent in enumerate(iterate_sentence(text)):
            sent_b, s_suffix = psent
            self.append(
                Sentence(
                    pos, sent_b, s_suffix, self,
                    base_file_name=self.base_file_name,
                    space_marker=self.space_marker,
                    word_unit_mode=self.word_unit_mode,
                    debug=self.debug, logger=self.logger
                )
            )
            self[-1].set_document(self)
            if len(self.sentences()) == 1:
                self.abs_pos_list = [self[-1].abs_pos_list]
            else:
                last_pos = self.abs_pos_list[-1][-1][-1]
                self.abs_pos_list.append([
                    (pos[0] + last_pos, pos[1] + last_pos)
                    for pos in self[-1].abs_pos_list
                ])
        for sent in self:
            sent.set_sent_id()
            for wrd in sent.words():
                if wrd.has_space_after():
                    wrd.ud_misc["SpaceAfter"] = "Yes"

    def detect_ud_dependencies(self):
        """ Detect UD label """
        for sent_b in self:
            for bun in sent_b:
                bun.update_bunsetu_pos()
            detect_dep_bunsetu(sent_b)
            for bun in sent_b.bunsetues():
                # このタイミングで決められる
                bun.bunsetu_type = detect_bunsetu_jp_type(bun)


def _loop_convud(sent: Sentence, pos_rule: list, dep_rule: list[tuple[list[SubRule], str]]):
    """
    親から順に実行
    """
    for word in sent.iterate_word_tree():
        detect_ud_pos(word, pos_rule)
    for word in sent.words():
        detect_ud_label(word, dep_rule)
    return sent


def get_doc_id(doc: Document) -> str:
    """
        get doc id
    """
    if doc.doc_attributes.bibinfo is not None:
        return cast(str, doc.doc_attributes.bibinfo)
    if doc.doc_attributes.attrib is not None:
        return cast(
            str, cast(ET.Element, doc.doc_attrib_xml.find('sent_id')).text
        ).replace('# sent_id = ', '')
    assert doc.base_file_name is not None
    return os.path.splitext(os.path.basename(doc.base_file_name))[0].split(".")[0]


def post_proceeing_function(doc: Document) -> None:
    """
        hook function
    """
    for sent in doc.sentences():
        # swap_dep_without_child_from_sent(sent)
        adapt_nsubj_to_dislocated_rule(sent)
        __replace_pos_and_label(sent)
