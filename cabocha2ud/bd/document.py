# -*- coding: utf-8 -*-

"""
Bunsetu Dependencies document class
"""

import os
import re
import xml.etree.ElementTree as ET

from typing import Iterator, List, Tuple, Optional, Union, cast, TYPE_CHECKING

from ..lib.iterate_function import (
    iterate_seg_and_link, iterate_sentence
)
if TYPE_CHECKING:
    from .word import Word


from ..rule.dep import detect_ud_label
from ..rule.bunsetu_rule import detect_dep_inbunsetu
from ..rule.remove_space import skip_jsp_token_from_sentence
from ..rule.swap_dep import (
    swap_dep_without_child_from_sent, swap_dep_unsubj_from_sent
)
from ..rule.remove_multi_subj import adapt_nsubj_to_dislocated_rule

from .sentence import Sentence
from .annotation import (
    get_annotation_object, AnnotationList
)




RE_SAHEN_MATCH = re.compile("^名詞.*サ変.*")
def __replace_pos_and_label(sent: "Sentence"):
    for word in sent.flatten():
        if word.dep_label == "punct":
            word.en_pos = ["PUNCT"]
        if len(word.en_pos) == 0:
            continue
        if word.en_pos[0] == "AUX" and word.dep_label == "compound":
            word.dep_label = "aux"
        if word.en_pos[0] == "AUX" and word.dep_label == "cc":
            word.en_pos[0] = "CCONJ"
        if word.en_pos[0] == "NOUN" and word.luw_pos == "助動詞":
            word.en_pos[0] = "AUX"
        parent = word.get_parent_word()
        if parent is None:
            continue
        if parent.dep_label == 'fixed':
            # fixed -> fixed の場合
            word.dep_num = parent.dep_num
            continue
        if parent.dep_label == 'cc' and word.dep_label in ["aux", "mark"]:
            word.dep_label = "fixed"
            continue
        if parent.word_pos == 0 and parent.dep_label == 'case' and word.dep_label in ["aux", "mark"]:
            word.dep_label = "fixed"
            continue
        if (word.en_pos[0] == "ADP" and word.dep_label == 'fixed'
                and word.token_pos < parent.token_pos):
            if parent.dep_label != "case":
                word.dep_label = 'case'
                continue
            if word.token_pos == 1:
                continue
            # わりと特殊  B024n_PM25_00027-131
            word.dep_label = 'case'


class Document(list["Sentence"]):
    """
     document object
    """


    def __init__(
            self, data_type: str, text: Optional[List[str]]=None, prefix: Optional[List[str]]=None,
            suffix: Optional[List[str]]=None,
            base_file_name: Optional[str]="doc",
            word_unit: str="suw", space_marker: Optional[str]="　", debug: bool=False
    ):
        self.base_file_name: Optional[str] = base_file_name
        self.data_type: str = data_type
        self.word_unit: str = word_unit
        self.debug: bool = debug
        # 先頭の情報
        self.doc_attributes: List[str] = []
        self.doc_attrib_xml: ET.Element = ET.fromstring("<root></root>")
        # 末尾の注釈
        self.doc_annotation: AnnotationList = AnnotationList([])
        # 文書上での絶対位置
        self.abs_pos_list: List[List[Tuple[int, int]]] = []
        self.space_marker: Optional[str] = space_marker
        self.text: Optional[List[str]] = text
        self.prefix: Optional[List[str]] = prefix
        self.suffix: Optional[List[str]] = suffix

    def parse(self) -> None:
        if self.text is not None and self.prefix is not None and self.suffix is not None:
            self.__parse(self.text, self.prefix, self.suffix)
        else:
            raise NotImplementedError
        # パース後に取得
        if self.data_type == "gsd":
            doc_attrs = self.doc_attributes[1].split("\t")[1]
            self.doc_attrib_xml = ET.fromstring('<root>' + doc_attrs.replace('&', '&amp;') + '</root>')
        self.doc_id = get_doc_id(self)

    def convert_ud(self, is_skip_space: bool=True, sep: str="\n") -> List[str]:
        """
            convert to UD format
        """
        # UD掛かり先ラベルを付与
        for sent in self.sentences():
            for word in sent.flatten():
                if self.debug:
                    print(word.token_pos, str(word))
                detect_ud_label(word, debug=self.debug)
        # スペースの除去をする
        if is_skip_space:
            skip_jsp_token_from_sentence(self)
        for sent in self:
            sent.sent_id = self.doc_id + "-" + str(sent.sent_pos + 1)
        # UD確定の後処理
        post_proceeing_function(self)
        return [
            sent.convert() + sep for sent in self.sentences()
        ]

    def __str__(self) -> str:
        org = "\n".join([
            str(sent) for sent in self.sentences()
        ])
        org = "\n".join(self.doc_attributes) + "\n" + org
        if len(self.doc_annotation) > 0:
            org = org + "\n" + str(self.doc_annotation)
        return org

    def get_pos_from_word(self, word: "Word") -> Tuple[int, int]:
        """
            word の位置を返す
        """
        return self.abs_pos_list[word.sent_pos][word.token_pos-1]

    def sentences(self) -> List["Sentence"]:
        """
            get sentences
        """
        return list(self)

    def __parse(self, text: List[str], prefix: list[str], suffix: list[str]) -> None:
        from ..rule.bunsetu_rule import detect_bunsetu_jp_type
        self.doc_attributes = prefix
        doc_annotation = suffix
        self.doc_annotation = AnnotationList([
            get_annotation_object(seg)
            for seg in iterate_seg_and_link(list(doc_annotation))
        ])
        for pos, sent in enumerate(iterate_sentence(text)):
            sent_b, s_suffix = sent
            self.append(
                Sentence(
                    self.data_type, pos, sent_b, s_suffix, self,
                    base_file_name=self.base_file_name,
                    word_unit=self.word_unit,
                    space_marker=self.space_marker,
                    debug=self.debug
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
        for sent_b in self:
            detect_dep_inbunsetu(sent_b)
            for bun in sent_b.bunsetues():
                # このタイミングで決められる
                bun.bunsetu_type = detect_bunsetu_jp_type(bun)


def get_doc_id(doc: Document) -> str:
    """
        get doc id
    """
    if doc.data_type == "chj":
        assert doc.base_file_name is not None
        return os.path.splitext(os.path.basename(doc.base_file_name))[0].split(".")[0]
    elif doc.data_type == "bccwj":
        return doc.doc_attributes[1].split("\t")[2]
    elif doc.data_type == "gsd":
        return cast(str, cast(ET.Element, doc.doc_attrib_xml.find('sent_id')).text).replace('# sent_id = ', '')
    raise NotImplementedError


def post_proceeing_function(doc: Document) -> None:
    """
        hook function
    """
    for sent in doc.sentences():
        # swap_dep_without_child_from_sent(sent)
        # swap_dep_unsubj_from_sent(sent)
        adapt_nsubj_to_dislocated_rule(sent)
        __replace_pos_and_label(sent)
