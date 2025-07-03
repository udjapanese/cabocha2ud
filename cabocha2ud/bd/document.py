"""Bunsetu Dependencies document class."""

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import TYPE_CHECKING, Optional, cast

if TYPE_CHECKING:
    from .word import Word

from cabocha2ud.lib.iterate_function import iterate_seg_and_link, iterate_sentence
from cabocha2ud.lib.logger import Logger
from cabocha2ud.rule.bunsetu_rule import detect_bunsetu_jp_type, detect_dep_bunsetu
from cabocha2ud.rule.dep import SubRule, detect_ud_label
from cabocha2ud.rule.pos import detect_ud_pos
from cabocha2ud.rule.remove_multi_subj import adapt_nsubj_to_dislocated_rule
from cabocha2ud.rule.remove_space import skip_jsp_token_from_sentence

from .annotation import AnnotationList, DocAnnotation, generate_docannotation, get_annotation_object
from .sentence import Sentence

RE_SAHEN_MATCH = re.compile("^名詞.*サ変.*")


def replace_pos_and_label(sent: "Sentence") -> None:  # noqa: C901, PLR0912
    """後処理のPOSとDEPRELの置換.

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
            elif wrd.en_pos[0] == "AUX" and wrd.dep_label == "cc":
                wrd.en_pos[0] = "CCONJ"
            elif wrd.en_pos[0] == "NOUN" and wrd.get_luw_pos() == "助動詞":
                wrd.en_pos[0] = "AUX"
        parent = wrd.get_parent_word()
        if parent is None:
            continue
        if parent.dep_label == "fixed":
            # fixed -> fixed の場合
            wrd.dep_num = parent.dep_num
            continue
        if (wrd.token_pos < parent.token_pos and wrd.dep_label in ["compound", "dep"]
            and parent.dep_label == "det"):
            # compound/dep -> det の場合
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
    """Document object."""

    def __init__(
        # ruff: noqa: PLR0913
        self, text: Optional[list[str]]=None, prefix: Optional[list[str]]=None,
        suffix: Optional[list[str]]=None,
        base_file_name: Optional[str]="doc", word_unit_mode: str="suw",
        space_marker: str="　", debug: bool=False, logger: Optional[Logger]=None
    ) -> None:
        """Init."""
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
        """Document parse function."""
        if self.text is not None and self.prefix is not None and self.suffix is not None:
            self.__parse(self.text, self.prefix, self.suffix)
        else:
            raise NotImplementedError

    def convert_ud(
        self, pos_rule: list, dep_rule: list[tuple[list[SubRule], str]],
        skip_space: bool=True, sep: str="\n"
    ) -> list[str]:
        """Convert to UD format."""
        self.detect_ud_dependencies()
        # UD掛かり先ラベルを付与
        for sent in self.sentences():
            _loop_convud(sent, pos_rule, dep_rule)
        # スペースの除去をする
        if skip_space:
            skip_jsp_token_from_sentence(self)
        # UD確定の後処理
        post_proceeing_function(self, dep_rule)
        return [
            sent.convert() + sep for sent in self.sentences()
        ]

    def __str__(self) -> str:
        """Str."""
        org = "\n".join([
            str(sent) for sent in self.sentences()
        ])
        org = str(self.doc_attributes) + org
        if len(self.doc_annotation) > 0:
            org = org + "\n" + str(self.doc_annotation)
        return org

    def get_pos_from_word(self, word: "Word") -> tuple[int, int]:
        """Word の位置を返す."""
        return cast(tuple[int, int], self.abs_pos_list[word.sent_pos][word.token_pos-1])

    def sentences(self) -> list["Sentence"]:
        """Get sentences."""
        return list(self)

    def remove_sentence_pos(self, sent_pos: list[int]) -> None:
        """Remove the sentence pos."""
        if len(sent_pos) == 0:
            return
        nsents: list[Sentence] = []
        for spos, sent in enumerate(self):
            assert spos == sent.sent_pos
            if spos in sent_pos:
                continue
            nsents.append(sent)
        self.clear()
        self.extend(nsents)
        for nspos, sent in enumerate(self):
            sent.sent_pos = nspos
            for bpos, bun in enumerate(sent):
                for wpos, _ in enumerate(bun):
                    self[nspos][bpos][wpos].sent_pos = nspos

    def __parse(self, text: list[str], prefix: list[str], suffix: list[str]) -> None:
        self.doc_attributes = generate_docannotation(prefix)
        # パース後に取得
        self.logger.debug("debug: doc_attr = %s", self.doc_attributes.attrib)
        if self.doc_attributes.attrib is not None:
            doc_attrs = self.doc_attributes.attrib
            if doc_attrs is not None:
                self.doc_attrib_xml = ET.fromstring(
                    # ruff: noqa: S314
                    "<root>" + doc_attrs.replace("&", "&amp;") + "</root>"
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
                    wrd.ud_misc["SpacesAfter"] = "Yes"
                    if "SpaceAfter" in wrd.ud_misc["SpaceAfter"]:
                        assert wrd.ud_misc["SpaceAfter"] == "No"
                        del wrd.ud_misc["SpaceAfter"]
                        assert wrd.ud_misc.get("SpaceAfter") is None
                else:
                    wrd.ud_misc["SpaceAfter"] = "No"

    def detect_ud_dependencies(self) -> None:
        """Detect UD label."""
        for sent_b in self:
            for bun in sent_b:
                bun.update_bunsetu_pos()
            detect_dep_bunsetu(sent_b)
            for bun in sent_b.bunsetues():
                # このタイミングで決められる
                bun.bunsetu_type = detect_bunsetu_jp_type(bun)


def _loop_convud(
    sent: Sentence, pos_rule: list, dep_rule: list[tuple[list[SubRule], str]]) -> Sentence:
    """親から順に実行."""
    for word in sent.iterate_word_tree():
        detect_ud_pos(word, pos_rule)
    for word in sent.words():
        detect_ud_label(word, dep_rule)
    return sent


def get_doc_id(doc: Document) -> str:
    """Get doc id."""
    if doc.doc_attributes.bibinfo is not None:
        return cast(str, doc.doc_attributes.bibinfo)
    if doc.doc_attributes.attrib is not None:
        return cast(
            str, cast(ET.Element, doc.doc_attrib_xml.find("sent_id")).text
        ).replace("# sent_id = ", "")
    assert doc.base_file_name is not None
    return str(Path(doc.base_file_name).parent).split(".")[0]


def __replace_allfix_deps(sent: Sentence, dep_rule: list[tuple[list[SubRule], str]]) -> None:
    for bunsetu in sent:
        if not all(wrd.dep_label == "fixed" for wrd in bunsetu):
            continue
        if len(bunsetu) == 1:
            # reparandum
            bunsetu[0].dep_label = "reparandum"
            continue
        target_pos = bunsetu[0].token_pos
        for wrd_pos, wrd in enumerate(bunsetu):
            if wrd_pos == 0:
                continue
            wrd.dep_num = target_pos
        if bunsetu[0].en_pos[0] == "AUX":
            bunsetu[0].dep_label = "aux"
        else:
            detect_ud_label(bunsetu[0], dep_rule)


def __replace_allcase_deps(sent: Sentence) -> None:
    for wrd in sent.words():
        if wrd.dep_label in ["fixed", "punct"] or wrd.dep_num == 0:
            continue
        assert wrd.dep_num is not None
        twrd = sent.words()[wrd.dep_num-1]
        if twrd.dep_label in ["cc", "aux"]:
            wrd.dep_num = twrd.dep_num


def __replace_iiyodomi(sent: Sentence) -> None:
    print(sent)


def __replace_fixed_gap(sent: Sentence) -> None:
    """条件として上の語も同じかかり先であることが条件."""
    print(sent)


def post_proceeing_function(doc: Document, dep_rule: list[tuple[list[SubRule], str]]) -> None:
    """Proceeding hook function."""
    for sent in doc.sentences():
        adapt_nsubj_to_dislocated_rule(sent)
        replace_pos_and_label(sent)
        # 言い淀み __replace_iiyodomi(sent)
        # fixed
        __replace_allfix_deps(sent, dep_rule)
        __replace_allcase_deps(sent)
