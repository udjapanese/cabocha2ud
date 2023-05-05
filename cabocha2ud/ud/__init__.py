# -*- coding: utf-8 -*-

"""

Universal Dependency class
"""

import copy
from typing import Iterator, Optional, Union, cast

from cabocha2ud.bd import BunsetsuDependencies
from cabocha2ud.lib.logger import Logger
from cabocha2ud.lib.text_object import TextObject
from cabocha2ud.lib.yaml_dict import YamlDict
from cabocha2ud.rule import dep
from cabocha2ud.ud.sentence import Header, Sentence
from cabocha2ud.ud.util import Field as UField
from cabocha2ud.ud.word import Misc


def iterate_ud_sentence(lines: Union[list[str], Iterator[str]]) -> Iterator[list[str]]:
    """ Iterator sentence list """
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
        sentences (:obj:`list[Sentence]`) list of `list[Sentence]`
        options (:obj:`YamlDict`): options
    """

    def __init__(
        self, file_name: Optional[str]=None, sentences: Optional[list[Sentence]]=None,
        logger: Optional[Logger]=None,
        options: YamlDict=YamlDict()
    ):
        self.file_name: Optional[str] = file_name
        self.file_obj: Optional[TextObject] = None
        self.options: YamlDict = options
        self._sentences: list[Sentence] = []
        self.sentence_ids: list[str] = []
        self.logger: Logger
        if logger:
            self.logger = logger
        else:
            self.logger = self.options.get("logger") or Logger()
        if self.file_name is not None:
            self.file_obj = TextObject(file_name=self.file_name)
            self.read_ud_file()
        elif sentences is not None:
            self._sentences = sentences

    def __len__(self) -> int:
        return len(self._sentences)

    def __str__(self) -> str:
        return "\n".join([str(s) for s in self._sentences])

    def sentences(self) -> list[Sentence]:
        """ return sentences list """
        return self._sentences

    def get_sentence(self, index: int) -> Sentence:
        """ return one sentence for index """
        return self._sentences[index]

    def remove_sentence_from_index(self, index: list[int]) -> None:
        """ Remove sentence by index list """
        ncontent: list[Sentence] = []
        sids: list[str] = []
        for spos, nsent in enumerate(self._sentences):
            if spos not in index:
                ncontent.append(nsent)
                sent_id = nsent.get_header("sent_id")
                assert sent_id is not None
                sids.append(sent_id.get_value())
        self._sentences = copy.deepcopy(ncontent)
        self.sentence_ids = copy.deepcopy(sids)
        assert len(self.sentence_ids) == len(self._sentences)

    def remove_sentence_from_sentid(self, sent_id_list: list[str]) -> None:
        """ remove sentence by sent_id's list """
        self.remove_sentence_from_index([
            self.sentence_ids.index(sent_id) for sent_id in sent_id_list
        ])

    def update_sentence_of_index(self, index: int, sent: Sentence) -> None:
        """ update sentence by index """
        if index < 0:
            assert KeyError("`index` must be greater than or equal to 0")
        sent_id = sent.get_header("sent_id")
        if len(self._sentences) < index:
            self._sentences.append(sent)
            if sent_id is not None:
                self.sentence_ids.append(sent_id.get_value())
            else:
                self.sentence_ids.append("sent-{:02}".format(len(self._sentences)))
        else:
            self._sentences[index] = sent
            if sent_id is not None:
                self.sentence_ids[index] = sent_id.get_value()
            else:
                self.sentence_ids[index] = "sent-{:02}".format(len(self._sentences))
        assert len(self.sentence_ids) == len(self._sentences)

    def update_sentence_of_sentid(self, sent_id: str, sent: Sentence) -> None:
        """ update sentence of sent_id """
        self.update_sentence_of_index(self.sentence_ids.index(sent_id), sent)

    def read_ud_file(self, file_name: Optional[str]=None) -> None:
        """ read UD file """
        if file_name is not None:
            self.file_name = file_name
            self.file_obj = TextObject(file_name=self.file_name)
        if self.file_obj is None:
            raise KeyError("must give file-like content")
        self.load(self.file_obj.read())

    def load(self, str_content: Union[list[str], Iterator[str]]):
        """ load UD from str list """
        for sent_pos, sent in enumerate(iterate_ud_sentence(str_content)):
            sent_obj = Sentence.load_from_list(sent, logger=self.logger)
            self._sentences.append(sent_obj)
            sent_id = sent_obj.get_header("sent_id")
            if sent_id is not None:
                self.sentence_ids.append(sent_id.get_value())
            else:
                self.sentence_ids.append("sent-{:02}".format(sent_pos))
        assert len(self.sentence_ids) == len(self._sentences)

    def write_ud_file(self, file_name: str) -> None:
        """ write UD file to `file_name` """
        writer = TextObject(file_name=file_name, mode="w")
        writer.write([str(s) for s in self._sentences])

    def fit(
        self, bobj: BunsetsuDependencies,
        pos_rule: list, dep_rule: list[tuple[list[dep.SubRule], str]]
    ) -> None:
        """
        Convert BD to UD

        Args:
            bobj (BunsetsuDependencies): converted BunsetsuDependencies
        """
        prev_text: Optional[str] = None
        target_newdoc_text: Optional[str] = None
        tmp_content: list[Union[str, Sentence]] = []
        for doc_id, doc in enumerate(bobj):
            sentences = doc.convert_ud(
                pos_rule, dep_rule, skip_space=self.options.get("skip_space", False)
            )
            if doc.doc_attrib_xml is None or len(list(doc.doc_attrib_xml.iter("newdoc_id"))) == 0:
                tmp_content.extend([Sentence.load_from_string(sent) for sent in sentences])
                continue
            target_newdoc_text = list(doc.doc_attrib_xml.iter("newdoc_id"))[0].text
            if doc_id == 0 and target_newdoc_text is not None:
                tmp_content.append(target_newdoc_text)
                prev_text = target_newdoc_text
            elif target_newdoc_text is not None and prev_text != target_newdoc_text:
                tmp_content.append(target_newdoc_text)
                prev_text = target_newdoc_text
            tmp_content.extend([Sentence.load_from_string(sent) for sent in sentences])
        if all(isinstance(c, Sentence) for c in tmp_content):
            self._sentences = cast(list[Sentence], tmp_content[:])
            for cpos, cont in enumerate(self._sentences):
                sent_id = cont.get_header("sent_id")
                if sent_id is not None:
                    self.sentence_ids.append(sent_id.get_value())
                else:
                    self.sentence_ids.append("sent-{:02}".format(cpos))
            assert len(self.sentence_ids) == len(self._sentences)
            return
        # new doc の処理をする
        tmp_lst: list[str] = []
        self._sentences = []
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
                self._sentences.append(sent)
                sent_id = self._sentences[-1].get_header("sent_id")
                if sent_id is not None:
                    self.sentence_ids.append(sent_id.get_value())
                else:
                    self.sentence_ids.append("sent-{:02}".format(len(self._sentences)))
        assert len(self.sentence_ids) == len(self._sentences)
        spos_lst: list[int] = []
        for spos, sent in enumerate(self.sentences()):
            header_keys = sent.get_header_keys()
            if spos == len(self.sentences()) - 1:
                spos_lst.append(spos)
            if "newdoc id" not in header_keys:
                continue
            if spos > 0:
                spos_lst.append(spos - 1)
        for spos in spos_lst:
            sent = self.sentences()[spos]
            misc = cast(Misc, sent.words()[-1][UField.MISC])
            misc.remove("SpaceAfter")
