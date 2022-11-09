# -*- coding: utf-8 -*-

"""

Universal Dependency class
"""

import copy
import xml.etree.ElementTree as ET
from typing import Iterator, Optional, Union, cast

from ..bd import BunsetsuDependencies
from ..lib.logger import Logger
from ..lib.text_object import TextObject
from ..lib.yaml_dict import YamlDict
from ..rule import dep
from .sentence import Header, Sentence


def iterate_ud_sentence(lines: Union[list[str], Iterator[str]]) -> Iterator[list[str]]:
    sent: list[str] = []
    for line in lines:
        if line == "":
            yield sent
            sent = []
        else:
            sent.append(line)

class UniversalDependencies:
    """
    Attributes:
        file_name (str): file name, if the parameter set, load cabocha file
        file_obj (:obj:`TextObject`): file object class.
        content (:obj:`list[Sentence]`) list of `list[Sentence]`
        options (:obj:`YamlDict`): options
    """

    def __init__(self, file_name: Optional[str]=None, content: Optional[list[Sentence]]=None, options: YamlDict=YamlDict()):
        self.file_name: Optional[str] = file_name
        self.file_obj: Optional[TextObject] = None
        self.options: YamlDict = options
        self.content: list[Sentence] = []
        self.sentence_ids: list[str] = []
        self.logger: Logger = self.options.get("logger") or Logger()
        if self.file_name is not None:
            self.file_obj = TextObject(file_name=self.file_name)
            self.read_ud_file()
        elif content is not None:
            self.content = content

    def __len__(self) -> int:
        return len(self.content)

    def __str__(self) -> str:
        return "\n".join([str(s) for s in self.content])

    def sentences(self) -> list[Sentence]:
        return self.content

    def get_sentence(self, index: int) -> Sentence:
        return self.content[index]

    def remove_sentence_from_index(self, index: list[int]) -> None:
        ncontent: list[Sentence] = []
        sids: list[str] = []
        for spos, nsent in enumerate(self.content):
            if spos not in index:
                ncontent.append(nsent)
                sent_id = nsent.get_header("sent_id")
                assert sent_id is not None
                sids.append(sent_id.get_value())
        self.content = copy.deepcopy(ncontent)
        self.sentence_ids = copy.deepcopy(sids)
        assert len(self.sentence_ids) == len(self.content)

    def remove_sentence_from_sentid(self, sent_id_list: list[str]) -> None:
        self.remove_sentence_from_index([
            self.sentence_ids.index(sent_id) for sent_id in sent_id_list
        ])

    def update_sentence_of_index(self, index: int, sent: Sentence) -> None:
        if index < 0:
            assert KeyError("`index` must be greater than or equal to 0")
        sent_id = sent.get_header("sent_id")
        if len(self.content) < index:
            self.content.append(sent)
            if sent_id is not None:
                self.sentence_ids.append(sent_id.get_value())
            else:
                self.sentence_ids.append("sent-{:02}".format(len(self.content)))
        else:
            self.content[index] = sent
            if sent_id is not None:
                self.sentence_ids[index] = sent_id.get_value()
            else:
                self.sentence_ids[index] = "sent-{:02}".format(len(self.content))
        assert len(self.sentence_ids) == len(self.content)

    def update_sentence_of_sentid(self, sent_id: str, sent: Sentence) -> None:
        self.update_sentence_of_index(self.sentence_ids.index(sent_id), sent)

    def read_ud_file(self, file_name: Optional[str]=None) -> None:
        if file_name is not None:
            self.file_name = file_name
            self.file_obj = TextObject(file_name=self.file_name)
        if self.file_obj is None:
            raise KeyError("must give file-like content")
        self.load(self.file_obj.read())

    def load(self, str_content: Union[list[str], Iterator[str]]):
        for sent_pos, sent in enumerate(iterate_ud_sentence(str_content)):
            sent_obj = Sentence.load_from_list(sent)
            self.content.append(sent_obj)
            sent_id = sent_obj.get_header("sent_id")
            if sent_id is not None:
                self.sentence_ids.append(sent_id.get_value())
            else:
                self.sentence_ids.append("sent-{:02}".format(sent_pos))
        assert len(self.sentence_ids) == len(self.content)

    def write_ud_file(self, file_name: str) -> None:
        writer = TextObject(file_name=file_name, mode="w")
        writer.write([str(s) for s in self.content])

    def fit(self, bobj: BunsetsuDependencies, pos_rule: list, dep_rule: list[tuple[list[dep.SubRule], str]]) -> None:
        """
        Args:
            bobj (BunsetsuDependencies): [description]
        """
        prev_text: Optional[str] = None
        target_text: Optional[str] = None
        tmp_content: list[Union[str, Sentence]] = []
        for doc_id, doc in enumerate(bobj):
            sentences = doc.convert_ud(pos_rule, dep_rule, is_skip_space=self.options.get("is_skip_space", False))
            if doc.doc_attrib_xml is None or doc.doc_attrib_xml.find('newdoc_id') is None:
                tmp_content.extend([Sentence.load_from_string(sent) for sent in sentences])
                continue
            target_text = cast(ET.Element, cast(ET.Element, doc.doc_attrib_xml).find('newdoc_id')).text
            if doc_id == 0 and target_text is not None:
                tmp_content.append(target_text)
                prev_text = target_text
            elif target_text is not None and prev_text != target_text:
                tmp_content.append(target_text)
                prev_text = target_text
            tmp_content.extend([Sentence.load_from_string(sent) for sent in sentences])
        if all([isinstance(c, Sentence) for c in tmp_content]):
            self.content = cast(list[Sentence], tmp_content[:])
            for cpos, cont in enumerate(self.content):
                sent_id = cont.get_header("sent_id")
                if sent_id is not None:
                    self.sentence_ids.append(sent_id.get_value())
                else:
                    self.sentence_ids.append("sent-{:02}".format(cpos))
            assert len(self.sentence_ids) == len(self.content)
            return
        # new doc の処理をする
        tmp_lst: list[str] = []
        self.content = []
        for ccc in tmp_content:
            if isinstance(ccc, str):
                tmp_lst.append(ccc)
            else:
                assert isinstance(ccc, Sentence)
                sent: Sentence = ccc
                if len(tmp_lst) > 0:  # 統合する
                    for hhh in tmp_lst:
                        sent.set_header(0, Header(cont=hhh))
                    tmp_lst = []
                self.content.append(sent)
                sent_id = self.content[-1].get_header("sent_id")
                if sent_id is not None:
                    self.sentence_ids.append(sent_id.get_value())
                else:
                    self.sentence_ids.append("sent-{:02}".format(len(self.content)))
        assert len(self.sentence_ids) == len(self.content)