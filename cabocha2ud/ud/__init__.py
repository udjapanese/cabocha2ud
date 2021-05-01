# -*- coding: utf-8 -*-

"""

Universal Dependency class
"""


from typing import Optional, List, Union, Iterator, cast
import xml.etree.ElementTree as ET

from ..lib.text_object import TextObject
from ..lib.yaml_dict import YamlDict
from ..bd import BunsetsuDependencies
from .sentence import Sentence, Header


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
        options (:obj:`YamlDict`): options
    """

    def __init__(self, file_name: Optional[str]=None, options: YamlDict=YamlDict()):
        self.file_name: Optional[str] = file_name
        self.file_obj: Optional[TextObject] = None
        self.options: YamlDict = options
        self.content: list[Sentence] = []
        if self.file_name is not None:
            self.file_obj = TextObject(file_name=self.file_name)
            self.read_ud_file()

    def __len__(self) -> int:
        return len(self.content)

    def __str__(self) -> str:
        return "\n".join([str(s) for s in self.content])

    def sentences(self) -> list[Sentence]:
        return self.content

    def read_ud_file(self, file_name: Optional[str]=None) -> None:
        if file_name is not None:
            self.file_name = file_name
            self.file_obj = TextObject(file_name=self.file_name)
        if self.file_obj is None:
            raise KeyError
        for sent in iterate_ud_sentence(cast(TextObject, self.file_obj).read()):
            self.content.append(Sentence.load_from_list(sent))

    def write_ud_file(self, file_name: str) -> None:
        writer = TextObject(file_name=file_name, mode="w")
        writer.write([str(s) for s in self.content])

    def fit(self, bobj: BunsetsuDependencies) -> None:
        """
        Args:
            bobj (BunsetsuDependencies): [description]
        """
        prev_text: Optional[str] = None
        target_text: Optional[str] = None
        tmp_content: list[Union[str, Sentence]] = []
        for doc_id, doc in enumerate(bobj):
            sentences = doc.convert_ud(is_skip_space=self.options.get("is_skip_space", False))
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
            return
        # new doc の処理をする
        tmp_lst: list[str] = []
        self.content = []
        for ccc in tmp_content:
            if isinstance(ccc, str):
                tmp_lst.append(ccc)
            else:
                sent: Sentence = ccc
                if len(tmp_lst) > 0:  # 統合する
                    for hhh in tmp_lst:
                        sent.headers.insert(0, Header(cont=hhh))
                    tmp_lst = []
                self.content.append(sent)
