# -*- coding: utf-8 -*-

"""
Sentence class
"""

import xml.etree.ElementTree as ET
from lib.iterate_function import iterate_seg_and_link, iterate_bunsetu

from base.component import Component
from base.bunsetu import Bunsetu
from base.annotation import (
    get_annotation_object, AnnotationList
)



class Sentence(Component, list):
    """
        Sentence class: sentence class is Bunsetu List
    """

    def __init__(
            self, data_type, sent_pos, sentence_lines,
            doc, base_file_name=None, is_use_bunsetu_num=False, bunsetu_func="none",
            word_unit="suw", space_marker="　"
    ):
        super(Sentence, self).__init__(
            data_type, base_file_name=base_file_name, word_unit=word_unit,
            bunsetu_func=bunsetu_func
        )
        self.is_use_bunsetu_num = is_use_bunsetu_num
        self.doc = doc  # sentence's document
        self.sent_pos = sent_pos
        self.sent_id = None
        self.attributes_list = []
        self.annotation_list = None
        self._flatten = None
        self.bunsetu_dep = []
        self.word_dep_child = None
        # abs_pos_* represent abstract position (begin1, end1), (begin2, end2), ...
        self.abs_pos_list = []
        self.abs_pos_dict = {}
        self.space_marker = space_marker
        self.__parse(sentence_lines)

    def __unicode__(self):
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

    def bunsetues(self):
        """
            return bunsetu list
        """
        return self

    def set_sent_pos(self, sent_pos):
        """
            set sent_pos
        """
        self.sent_pos = sent_pos
        for word in self.flatten():
            word.sent_pos = sent_pos

    def set_document(self, doc):
        """
            wordにdocumentをlinkする
        """
        for word in self.flatten():
            word.doc = doc

    def get_pos_from_word(self, word):
        """
            return word's pos
        """
        return self.abs_pos_list[word.token_pos-1]

    def get_word_from_pos(self, pos):
        """
            get word by position
             if pos is int, return bunsetu
             if pos is list or tuple, return abs pos bunsetu
        """
        assert isinstance(pos, (int, list, tuple))
        if isinstance(pos, int):
            return self[pos]
        elif isinstance(pos, (list, tuple)) and len(pos) == 2:
            return self.abs_pos_dict[pos]
        else:
            raise TypeError("no type", pos)

    def get_word_from_tokpos(self, tok_pos):
        """
            extract word by token pos
        """
        if tok_pos < 0:
            return None
        return self._flatten[tok_pos]

    def flatten(self, is_update=False):
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

    def __parse(self, sentence_lines):
        pos = 0
        line = sentence_lines[pos]
        while line.startswith("#! "):
            self.attributes_list.append(line)
            pos += 1
            line = sentence_lines[pos]
        sentence_lines = sentence_lines[pos:]
        annotation_list = []
        if sentence_lines[-1].startswith("#! "):
            # 末尾に文のexcabochaあり
            pos = -1
            line = sentence_lines[pos]
            while line.startswith("#! "):
                annotation_list.append(line)
                pos += -1
                line = sentence_lines[pos]
            sentence_lines = sentence_lines[:pos+1]
            annotation_list = [
                get_annotation_object(seg)
                for seg in iterate_seg_and_link(list(reversed(annotation_list)))
            ]
        self.annotation_list = AnnotationList(annotation_list)
        bunsetu_list = [bunsetu for bunsetu in iterate_bunsetu(sentence_lines)]
        prev_bunsetu = None
        for bunsetu in bunsetu_list:
            self.append(
                Bunsetu(
                    self.data_type, self.sent_pos, bunsetu,
                    base_file_name=self.base_file_name,
                    is_use_bunsetu_num=self.is_use_bunsetu_num,
                    bunsetu_func=self.bunsetu_func,
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

    def get_header(self):
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

    def convert(self, sep="\t", is_skip_space=True):
        return self.get_header() + "\n".join([
            ww.convert(sep=sep) for ww in self.flatten()
        ])
