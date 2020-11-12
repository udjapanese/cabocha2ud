# -*- coding: utf-8 -*-

"""
Document class
"""

import os
import re
import xml.etree.ElementTree as ET

from lib.iterate_function import (
    iterate_seg_and_link, iterate_sentence
)
from rule.dep import detect_ud_label
from rule.bunsetu import detect_dep_inbunsetu
from rule.remove_space import skip_jsp_token_from_sentence
from rule.swap_dep import (
    swap_dep_without_child_from_sent, swap_dep_unsubj_from_sent
)
from rule.remove_multi_subj import adapt_nsubj_to_dislocated_rule
from base.component import Component
from base.sentence import Sentence
from base.annotation import (
    get_annotation_object, AnnotationList
)


def get_doc_id(doc):
    """
        get doc id
    """
    if doc.data_type == "chj":
        return os.path.splitext(os.path.basename(doc.base_file_name))[0].split(".")[0]
    elif doc.data_type == "bccwj":
        return doc.doc_attributes[1].split("\t")[2]
    elif doc.data_type == "gsd":
        return doc.doc_attrib_xml.find('sent_id').text.replace('# sent_id = ', '')


RE_SAHEN_MATCH = re.compile("^名詞.*サ変.*")
def __replace_pos_and_label(sent):
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
            word.dep_num = parent.dep_num
        if word.get_origin() == "する" and RE_SAHEN_MATCH.match(parent.get_xpos()):
            parent.en_pos[0] = "VERB"
        if (word.en_pos[0] == "ADP" and word.dep_label == 'fixed'
                and word.token_pos < parent.token_pos):
            if parent.dep_label != "case":
                word.dep_label = 'case'
                continue
            if word.token_pos == 1:
                continue
            # わりと特殊  B024n_PM25_00027-131
            word.dep_num = 'case'



def post_proceeing_function(doc):
    """
        hook function
    """
    for sent in doc.sentences():
        # swap_dep_without_child_from_sent(sent)
        # swap_dep_unsubj_from_sent(sent)
        adapt_nsubj_to_dislocated_rule(sent)
        __replace_pos_and_label(sent)


class Document(Component, list):
    """
     document object
    """
    def __init__(
            self, data_type, text=None, base_file_name="doc", bunsetu_func="none",
            word_unit="suw", space_marker="　"
    ):
        super(Document, self).__init__(
            data_type, base_file_name=base_file_name, word_unit=word_unit,
            bunsetu_func=bunsetu_func
        )
        # 先頭の情報
        self.doc_attributes = []
        self.doc_attrib_xml = None
        # 末尾の注釈
        self.doc_annotation = []
        # 文書上での絶対位置
        self.abs_pos_list = []
        self.abs_pos_dict = {}
        self.is_use_bunsetu_num = bool(self.bunsetu_func == "none")
        self.space_marker = space_marker
        if text is not None:
            self.__parse(text)
        else:
            with open(self.base_file_name, "r") as btext:
                self.__parse(btext)
        # パース後に取得
        if self.data_type == "gsd":
            doc_attrs = self.doc_attributes[1].split("\t")[1]
            self.doc_attrib_xml = ET.fromstring('<root>' + doc_attrs.replace('&', '&amp;') + '</root>')
        self.doc_id = get_doc_id(self)

    def convert(self, is_skip_space=True, sep="\n"):
        """
            convert to ud
        """
        # UD掛かり先ラベルを付与
        for sent in self.sentences():
            for word in sent.flatten():
                detect_ud_label(word, debug=self.debug)
        # スペースの除去をする
        if is_skip_space:
            skip_jsp_token_from_sentence(self)
        for sent in self:
            sent.sent_id = self.doc_id + "-" + str(sent.sent_pos + 1)
        # UD確定の後処理
        post_proceeing_function(self)
        return sep.join([
            sent.convert() + sep for sent in self.sentences()
        ])

    def __unicode__(self):
        org = "\n".join([
            str(sent) for sent in self.sentences()
        ])
        org = "\n".join(self.doc_attributes) + "\n" + org
        if len(self.doc_annotation) > 0:
            org = org + "\n" + str(self.doc_annotation)
        return org

    def get_pos_from_word(self, word):
        """
            word の位置を返す
        """
        return self.abs_pos_list[word.sent_pos][word.token_pos-1]

    def sentences(self):
        """
            get sentences
        """
        return self

    def __parse(self, text):
        org_sentences = [
            line.rstrip() for line in text
        ]
        if org_sentences[-1] == "":
            # 下に空行があるとエラーになるため空行を除く
            pos = -1
            while org_sentences[pos] == "":
                pos = pos - 1
            org_sentences = org_sentences[:pos + 1]
        pos = 0
        line = org_sentences[pos]
        while line.startswith("#! "):
            self.doc_attributes.append(line)
            pos += 1
            line = org_sentences[pos]
        org_sentences = org_sentences[pos:]
        pos = -1
        line = org_sentences[pos]
        while line.startswith("#! "):
            self.doc_annotation.append(line)
            pos += -1
            line = org_sentences[pos]
        self.doc_annotation = AnnotationList([
            get_annotation_object(seg)
            for seg in iterate_seg_and_link(list(reversed(self.doc_annotation)))
        ])
        if pos != -1:
            # 末尾の述語情報などがついていた場合ずらす
            org_sentences = org_sentences[:pos+1]
        for pos, sent in enumerate(iterate_sentence(org_sentences)):
            self.append(
                Sentence(
                    self.data_type, pos, sent, self,
                    base_file_name=self.base_file_name,
                    is_use_bunsetu_num=self.is_use_bunsetu_num,
                    bunsetu_func=self.bunsetu_func,
                    word_unit=self.word_unit,
                    space_marker=self.space_marker
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
            detect_dep_inbunsetu(sent)
