"""Cabocha Bunsetu Dependency class."""

import collections
from pathlib import Path
from typing import Optional

from cabocha2ud.bd.document import Document
from cabocha2ud.bd.sentence import Sentence
from cabocha2ud.lib.iterate_function import iterate_document
from cabocha2ud.lib.logger import Logger
from cabocha2ud.lib.text_object import TextObject
from cabocha2ud.lib.yaml_dict import YamlDict


class BunsetsuDependencies(collections.UserList[Document]):
    """BD object.

    Attributes:
        file_name (str): file name, if the parameter set, load cabocha file
        file_obj (:obj:`TextObject`): file object class.

    """

    def __init__(
        self, file_name: Optional[str]=None, options: YamlDict|None=None,
        logger: Optional[Logger]=None
    ) -> None:
        """Init."""
        super().__init__()
        self.options: YamlDict
        if options is not None:
            self.options = options
        else:
            self.options = YamlDict()
        self.file_name: Optional[str] = file_name
        self.file_obj: TextObject = TextObject()
        self.logger: Logger
        if logger:
            self.logger = logger
        else:
            self.logger = self.options.get("logger") or Logger()
        self.word_unit_mode = "suw"
        if self.file_name is not None:
            self.file_obj = TextObject(file_name=self.file_name)
            self.read_cabocha_file()

    def __str__(self) -> str:
        """Return string."""
        return "\n".join([str(doc) for doc in self.documents()])

    def documents(self) -> collections.UserList[Document]:
        """Return documents."""
        return self

    def sentences(self) -> list[Sentence]:
        """Return sentence list."""
        return [s for doc in self for s in doc.sentences()]

    def get_sentence(self, spos: int) -> Sentence:
        """Return sentence."""
        return self.sentences()[spos]

    def read_cabocha_file(self, file_name: Optional[str]=None) -> bool:
        """Read cabocha file."""
        if file_name is not None:
            self.file_name = file_name
            self.file_obj = TextObject(file_name=self.file_name)
        doc_name = "doc"
        if self.file_name and self.file_name not in {"-"}:
            doc_name = Path(self.file_name).name or "doc"
        for text in iterate_document(
            list(self.file_obj.read()), separate_info=True,
            default_doc_name=doc_name,
        ):
            prefix, ddoc, suffix = text
            doc: Document = Document(
                text=ddoc, prefix=prefix, suffix=suffix, base_file_name=self.file_name,
                space_marker=self.options.get("space_marker", "　"),
                debug=self.options.get("debug", False),
                word_unit_mode=self.options.get("word_unit", "suw"),
                logger=self.logger
            )
            doc.parse()
            self.append(doc)
        return True

    def write_cabocha_file(self, file_name: str="-") -> None:
        """Write Cabocha file."""
        self.file_name = file_name
        wrt_obj = TextObject(file_name=self.file_name, mode="w")
        wrt_obj.write([str(self)])
