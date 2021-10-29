# -*- coding: utf-8 -*-

# from . import document

""" bunsetsu_dependencies.py

Cabocha Bunsetu Dependency class
"""

import collections

from typing import Optional, List
from ..lib.logger import Logger
from ..lib.iterate_function import iterate_document
from ..lib.text_object import TextObject
from ..lib.yaml_dict import YamlDict

from .document import Document
from .sentence import Sentence


class BunsetsuDependencies(collections.UserList[Document]):
    """
    Attributes:
        file_name (str): file name, if the parameter set, load cabocha file
        file_obj (:obj:`TextObject`): file object class.
    """

    def __init__(self, file_name: Optional[str]=None, options: YamlDict=YamlDict()):
        super(BunsetsuDependencies, self).__init__()
        self.file_name: Optional[str] = file_name
        self.file_obj: TextObject = TextObject()
        self.options: YamlDict = options
        self.logger: Logger = self.options.get("logger", None) or Logger()
        self.word_unit_mode = "suw"
        if self.file_name is not None:
            self.file_obj = TextObject(file_name=self.file_name)
            self.read_cabocha_file()

    def __str__(self) -> str:
        return "\n".join([str(doc) for doc in self.documents()])

    def documents(self) -> collections.UserList[Document]:
        return self

    def sentences(self) -> list[Sentence]:
        return [s for doc in self for s in doc.sentences()]

    def get_sentence(self, spos: int) -> Sentence:
        return self.sentences()[spos]

    def read_cabocha_file(self, file_name: Optional[str]=None) -> bool:
        try:
            if file_name is not None:
                self.file_name = file_name
                self.file_obj = TextObject(file_name=self.file_name)
            doc_text = [line for line in self.file_obj.read()]
            for text in iterate_document(doc_text, separate_info=True):
                prefix, ddoc, suffix = text
                doc: Document = Document(
                    text=ddoc, prefix=prefix, suffix=suffix, base_file_name=None,
                    space_marker=self.options.get("space_marker", "　"),
                    debug=self.options.get("debug", False),
                    word_unit_mode=self.options.get("word_unit", "suw"),
                    logger=self.logger
                )
                doc.parse()
                self.append(doc)
        except Exception as e:
            raise e
        return True

    def write_cabocha_file(self, file_name: str="-") -> None:
        self.file_name = file_name
        wrt_obj = TextObject(file_name=self.file_name, mode="w")
        wrt_obj.write([str(self)])

