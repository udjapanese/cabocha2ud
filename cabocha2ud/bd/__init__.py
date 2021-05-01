# -*- coding: utf-8 -*-

# from . import document

""" bunsetsu_dependencies.py

Cabocha Bunsetu Dependency class
"""

import collections

from typing import Optional, List
from ..lib.iterate_function import iterate_document
from ..lib.text_object import TextObject
from ..lib.yaml_dict import YamlDict

from .document import Document


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
        if self.file_name is not None:
            self.file_obj = TextObject(file_name=self.file_name)
            self.read_cabocha_file()

    def __str__(self) -> str:
        return "\n".join([str(doc) for doc in self.documments()])

    def documments(self) -> collections.UserList[Document]:
        return self

    def read_cabocha_file(self, file_name: Optional[str]=None) -> bool:
        try:
            if file_name is not None:
                self.file_name = file_name
                self.file_obj = TextObject(file_name=self.file_name)
            doc_text = [line for line in self.file_obj.read()]
            for text in iterate_document(doc_text, separate_info=True):
                prefix, ddoc, suffix = text
                doc: Document = Document(
                    self.options.get("data_type", "gsd"),
                    text=ddoc, prefix=prefix, suffix=suffix, base_file_name=None,
                    word_unit=self.options.get("word_unit", "suw"),
                    space_marker=self.options.get("space_marker", "　"),
                    debug=self.options.get("debug", False)
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

