"""Universal Dependency class."""

from typing import Iterator, Optional, Union, cast

from cabocha2ud.bd import BunsetsuDependencies
from cabocha2ud.lib.iterate_function import iterate_ud_sentence
from cabocha2ud.lib.logger import Logger
from cabocha2ud.lib.text_object import TextObject
from cabocha2ud.lib.yaml_dict import YamlDict
from cabocha2ud.rule import dep
from cabocha2ud.ud.sentence import Header, Sentence
from cabocha2ud.ud.util import Field as UField
from cabocha2ud.ud.word import Misc


class UniversalDependencies:
    """UniversalDependencies.

    Attributes:
        file_name (str): file name, if the parameter set, load cabocha file
        file_obj (:obj:`TextObject`): file object class.
        sentences (:obj:`list[Sentence]`) list of `list[Sentence]`
        options (:obj:`YamlDict`): options

    """

    def __init__(
        self, file_name: Optional[str]=None, sentences: Optional[list[Sentence]]=None,
        logger: Optional[Logger]=None,
        options: YamlDict|None=None
    ) -> None:
        """Init."""
        self.file_name: Optional[str] = file_name
        self.file_obj: Optional[TextObject] = None
        if options is None:
            options = YamlDict()
        self.options: YamlDict = options
        self._sp = None
        if self.options.get("space_marker") is not None:
            self._sp = self.options.get("space_marker")
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
        """Length."""
        return len(self._sentences)

    def __str__(self) -> str:
        """Get string."""
        return "\n".join([str(s) for s in self._sentences])

    def get_sp(self) -> str:
        """Get sp marker."""
        assert isinstance(self._sp, str)
        return self._sp

    def sentences(self) -> list[Sentence]:
        """Return sentences list."""
        return self._sentences

    def set_sentences(self, sents: list[Sentence]) -> None:
        """Return sentences list."""
        self._sentences = list(sents)

    def get_sentence(self, index: int) -> Sentence:
        """Return one sentence for index."""
        return self._sentences[index]

    def remove_sentence_from_index(self, index: list[int]) -> None:
        """Remove sentence by index list."""
        ncontent: list[Sentence] = []
        sids: list[str] = []
        for spos, nsent in enumerate(self._sentences):
            if spos not in index:
                ncontent.append(nsent)
                sent_id = nsent.get_header("sent_id")
                assert sent_id is not None
                sids.append(sent_id.get_value())
        self._sentences = list(ncontent)
        self.sentence_ids = list(sids)
        assert len(self.sentence_ids) == len(self._sentences)

    def remove_sentence_from_sentid(self, sent_id_list: list[str]) -> None:
        """Remove sentence by sent_id's list."""
        self.remove_sentence_from_index([
            self.sentence_ids.index(sent_id) for sent_id in sent_id_list
        ])

    def update_sentence_of_index(self, index: int, sent: Sentence) -> None:
        """Update sentence by index."""
        if index < 0:
            assert KeyError("`index` must be greater than or equal to 0")
        sent_id = sent.get_header("sent_id")
        if len(self._sentences) < index:
            self._sentences.append(sent)
            if sent_id is not None:
                self.sentence_ids.append(sent_id.get_value())
            else:
                self.sentence_ids.append(f"sent-{len(self._sentences):02}")
        else:
            self._sentences[index] = sent
            if sent_id is not None:
                self.sentence_ids[index] = sent_id.get_value()
            else:
                self.sentence_ids[index] = f"sent-{len(self._sentences):02}"
        assert len(self.sentence_ids) == len(self._sentences)

    def update_sentence_of_sentid(self, sent_id: str, sent: Sentence) -> None:
        """Update sentence of sent_id."""
        self.update_sentence_of_index(self.sentence_ids.index(sent_id), sent)

    def read_ud_file(self, file_name: Optional[str]=None) -> None:
        """Read UD file."""
        if file_name is not None:
            self.file_name = file_name
            self.file_obj = TextObject(file_name=self.file_name)
        if self.file_obj is None:
            msg = "must give file-like content"
            raise KeyError(msg)
        self.load(self.file_obj.read(), spt=self._sp)

    def load(self, str_content: Union[list[str], Iterator[str]], spt: Optional[str]=None) -> None:
        """Load UD from str list."""
        sent_datas = list(enumerate(iterate_ud_sentence(str_content)))
        # 一度スペースを決める必要がある
        if spt is None:
            for _, sent in sent_datas:
                sss = [s for s in sent if s.startswith("# text = ")]
                if len(sss) == 0:
                    continue
                for txt in sss:
                    if "　" in txt.split("=")[1].strip(" "):
                        spt = "　"
            if spt is None:
                spt = " "
            self._sp = spt
        assert self._sp is not None
        for sent_pos, sent in sent_datas:
            sent_obj = Sentence.load_from_list(sent, spt=self._sp, logger=self.logger)
            self._sentences.append(sent_obj)
            sent_id = sent_obj.get_header("sent_id")
            if sent_id is not None:
                self.sentence_ids.append(sent_id.get_value())
            else:
                self.sentence_ids.append(f"sent-{sent_pos:02}")
        assert len(self.sentence_ids) == len(self._sentences)

    def write_ud_file(self, file_name: str) -> None:
        """Write UD file to `file_name`."""
        writer = TextObject(file_name=file_name, mode="w")
        writer.write([str(s) for s in self._sentences])

def _generate_sentences(
    doc, pos_rule: list, dep_rule: list[tuple[list[dep.SubRule], str]], skip_space: bool
) -> Iterator[Sentence]:
    """BunsetsuDependencies から Sentence を生成する。"""
    sentences = doc.convert_ud(pos_rule, dep_rule, skip_space=skip_space)
    for sent in sentences:
        yield Sentence.load_from_string(sent, spt=doc.space_marker)


def _get_newdoc_text(doc) -> Optional[str]:
    """doc から newdoc のテキストを取得する。"""
    if doc.doc_attrib_xml is None:
        return None
    elem = next(doc.doc_attrib_xml.iter("newdoc_id"), None)
    return elem.text if elem is not None else None


def _should_add_newdoc(doc_id: int, newdoc_text: Optional[str], prev_text: Optional[str]) -> bool:
    """newdoc を切り替えるべきか判定する。"""
    return newdoc_text is not None and (doc_id == 0 or newdoc_text != prev_text)


def _iter_doc_contents(
    bobj: BunsetsuDependencies,
    pos_rule: list,
    dep_rule: list[tuple[list[dep.SubRule], str]],
    skip_space: bool,
) -> Iterator[Union[str, Sentence]]:
    """文書を巡回し newdoc と Sentence を順番に返すジェネレータ。"""
    prev_text: Optional[str] = None
    for doc_id, doc in enumerate(bobj):
        newdoc_text = _get_newdoc_text(doc)
        if _should_add_newdoc(doc_id, newdoc_text, prev_text):
            assert newdoc_text is not None
            prev_text = newdoc_text
            yield newdoc_text
        yield from _generate_sentences(doc, pos_rule, dep_rule, skip_space)


def _merge_newdoc_and_sentences(
    items: Iterator[Union[str, Sentence]]
) -> tuple[list[Sentence], bool]:
    """newdoc の文字列を直後の Sentence に統合する。"""
    headers: list[str] = []
    sentences: list[Sentence] = []
    has_newdoc = False
    for item in items:
        if isinstance(item, str):
            headers.append(item)
            has_newdoc = True
            continue
        for head in headers:
            item.set_header(0, Header(cont=head))
        headers = []
        sentences.append(item)
    return sentences, has_newdoc


def _remove_space_after(uobj: UniversalDependencies) -> None:
    """newdoc 境界の SpaceAfter を調整する。"""
    spos_lst: list[int] = []
    for spos, sent in enumerate(uobj.sentences()):
        header_keys = sent.get_header_keys()
        if spos == len(uobj.sentences()) - 1:
            spos_lst.append(spos)
        if "newdoc id" not in header_keys:
            continue
        if spos > 0:
            spos_lst.append(spos - 1)
    for spos in spos_lst:
        sent = uobj.sentences()[spos]
        misc = cast(Misc, sent.words()[-1][UField.MISC])
        if "SpaceAfter" in misc:
            misc.remove("SpaceAfter")


def fit(
    uobj: UniversalDependencies,
    bobj: BunsetsuDependencies,
    pos_rule: list,
    dep_rule: list[tuple[list[dep.SubRule], str]],
) -> None:
    """Convert BD to UD."""
    skip_space = uobj.options.get("skip_space", False)
    items = _iter_doc_contents(bobj, pos_rule, dep_rule, skip_space)
    sentences, has_newdoc = _merge_newdoc_and_sentences(items)
    uobj.set_sentences(sentences)
    for cpos, cont in enumerate(uobj.sentences()):
        sent_id = cont.get_header("sent_id")
        if sent_id is not None:
            uobj.sentence_ids.append(sent_id.get_value())
        else:
            uobj.sentence_ids.append(f"sent-{cpos:02}")
    assert len(uobj.sentence_ids) == len(uobj.sentences())
    if has_newdoc:
        _remove_space_after(uobj)
