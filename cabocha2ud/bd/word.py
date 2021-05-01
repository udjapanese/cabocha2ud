# -*- coding: utf-8 -*-

"""
BCCWJ DepParaPAS class
"""

from __future__ import annotations

import re
import string
from typing import Union, Optional, Tuple, cast, TYPE_CHECKING
if TYPE_CHECKING:
    from .bunsetu import Bunsetu
    from .document import Document
    from .sentence import Sentence
    from .annotation import Segment, Annotation, AnnotationList

from ..rule.pos import detect_ud_pos

JP_SP_MARK = "[JSP]"
RE_CASE_MATH = re.compile("助詞-[係格副]助詞")
RE_PROP_MATH = re.compile(".*固有名詞.*")
RE_ASCII_MATH = re.compile('^[' + string.printable + ']+$')


UNIDIC_ORIGIN_CONV = {
    "ず": "ぬ",
    '為る': 'する',
    '居る': 'いる',
    "出来る": "できる",
    "有る": "ある",
    "無い": "ない",
    "なかっ": "ない",
    "なく": "ない",
    "成る": "なる",
    "仕舞う": "しまう",
    "レる": "れる",
    "在る": "ある",
    "如し": "ごとし",
    "頂く": "いただく",
    "良い": "よい",
    "頂ける": "いただける",
    "貰う": "もらう",
    "下さる": "くださる",
    "欲しい": "ほしい",
    "過ぎる": "すぎる",
    "タ": "た",
    "様": "よう",
    "見る": "みる",
    "得る": "える",
    "チャウ": "ちゃう",
    "知れる": "しれる",
    "貰える": "もらえる",
    "致す": "いたす",
    "為さる": "なさる"
    # -------
}


class Word:

    """
        word class
    """

    sent_pos: int
    token_pos: int
    word_pos: int
    bunsetu_pos: int
    dep_num: Optional[int]
    _token: list[str]
    luw_pos: str
    surface: str
    doc: "Document"
    bunsetu: "Bunsetu"
    link_label: Union[None, int, str]
    dep_label: Optional[str]
    parent_word: Optional[Word]
    child_words: Optional[list[Word]]
    sem_head_word: Optional[Word]
    syn_head_word: Optional[Word]
    features: list[str]
    luw_label: str
    luw_origin: str
    luw_yomi: str
    luw_katuyo: str
    luw_form: str
    case_set: Optional[dict[str, None]]
    bunsetu_position_type: Optional[str]

    def __init__(self, **kwargs):
        valid_keys = [
            "sent_pos",  # 文書中の文の位置
            # 文中の文節の位置
            "bunsetu_pos",  # bunsetu_pos
            # 文節中の語の位置
            "word_pos",  # pos
            "_token",  # token.split("\t")
            # 表層系
            "surface",  # None
            # 原型
            "origin",  # None
            # 読み
            "yomi",  # None
            # 特徴
            "features",  # None
            # 日本語の品詞
            "jp_pos",  # None
            # 主辞か？
            "_is_subj",  # None
            # 機能語か？
            "_is_func",   # None
            # 用法　(bccwjのみ)
            "usage",  # None
            # 活用形
            "katuyo",   # None
            # UD用MISC
            "ud_misc",  #   {"SpaceAfter": "No"}
            "ud_feat",  # {}
            # 文中の単語の位置(UDでの単語位置)
            "token_pos",  # None
            # 英語の品詞
            "en_pos",  # []
            # 掛かり先
            "dep_num",  # None
            # 掛かりラベル
            "dep_label",  # None
            # doc, bunsetu ひっぱる用
            "doc",   # None
            "bunsetu",  # bunsetu
            # 長単位ラベル
            "luw_label",  # None
            # 長単位品詞
            "luw_pos",  # None
            # 長単位品詞特徴
            "luw_features",  # None
            # 長単位原形
            "luw_origin",  # None
            # 長単位読み
            "luw_yomi",  # None
            # 長単位活用
            "luw_katuyo",  # None
            # 長単位表層
            "luw_form",
            # for dependency information
            "link_label",  # None
            "case_set",   # None
            "parent_word",  # None == self.get_parent_word()
            "bunsetu_position_type",   #  None == self.ud_misc["BunsetuPositionType"]
            "child_words",  #  None
            "sem_head_word",   # None
            "syn_head_word"   # None
        ]
        self.base_file_name: Optional[str] = kwargs.get("base_file_name")
        self.data_type: str = kwargs.get("data_type")
        self.word_unit: str = kwargs.get("word_unit", "suw")
        self.debug: bool = kwargs.get("debug", True)
        for key in valid_keys:
            self.__dict__[key] = kwargs.get(key)
        if kwargs.get("token") is not None:
            self._token = kwargs.get("token").split("\t")
        # UD用
        self.ud_misc = kwargs.get("ud_misc", {"SpaceAfter": "No"})
        self.ud_feat = kwargs.get("ud_feat", {})
        # 英語の品詞
        self.en_pos = kwargs.get("en_pos", [])

    def __str__(self) -> str:
        org = "\t".join(self._token)
        if self.luw_label is not None:
            org = org + "\t" + "\t".join(
                [self.luw_label, self.luw_origin, self.luw_yomi, self.luw_pos, self.luw_katuyo]
            )
        return org

    def get_sentence(self) -> "Sentence":
        """
            get Sentence object
        """
        assert self.doc is not None and self.sent_pos is not None
        return self.doc[self.sent_pos]

    def set_bunsetsu_info(self, subj: Optional[bool], func: Optional[bool]) -> None:
        """
            set bunsetu info
        """
        self._is_func = func
        self._is_subj = subj

    def get_sent_segment(self) -> Union[int, "Segment"]:
        """
            get segment for word
        """
        sword_pos = self.doc[self.sent_pos].get_pos_from_word(self)
        if self.doc[self.sent_pos].annotation_list is not None:
            return cast("AnnotationList", self.doc[self.sent_pos].annotation_list).get_segment(sword_pos)
        else:
            raise KeyError

    def get_link(self, aword: Word) -> Union[int, Tuple["Annotation", "Segment", "Segment"]]:
        """
            get link for aword
        """
        sword_pos = self.doc.get_pos_from_word(self)
        aword_pos = self.doc.get_pos_from_word(aword)
        return self.doc.doc_annotation.get_link(sword_pos, aword_pos)

    def get_parent_word(self) -> Optional[Word]:
        """
            get parent word from doc
        """
        assert self.doc is not None
        if self.parent_word is None and self.dep_num is not None:
            self.parant_word = self.doc[self.sent_pos].get_word_from_tokpos(self.dep_num - 1)
        return self.parant_word

    def get_bunsetu_position_type(self) -> str:
        """
            get bunsetu_position_type
        """
        assert "BunsetuPositionType" in self.ud_misc
        if self.bunsetu_position_type is not None:
            return self.bunsetu_position_type
        self.bunsetu_position_type = self.ud_misc["BunsetuPositionType"]
        return self.bunsetu_position_type

    def get_bunsetu_jp_type(self):
        assert self.bunsetu is not None
        return self.bunsetu.bunsetu_type

    def get_bunsetu_position_word(self, bpos):
        """
            get word has `bpos` type, the bunsetu position word
        """
        assert self.bunsetu is not None
        for target_wrd in self.bunsetu:
            if bpos == target_wrd.get_bunsetu_position_type():
                return target_wrd
        return None

    def get_surface_case(self) -> dict[str, None]:
        """
            get surface case (表層格)
        """
        if self.case_set is not None:
            return self.case_set
        self.case_set = {}
        for child_pos in self.doc[self.sent_pos].get_ud_children(self, is_reconst=True):
            cword = self.doc[self.sent_pos].get_word_from_tokpos(child_pos - 1)
            if cword is None:
                raise ValueError
            if RE_CASE_MATH.match(cword.get_xpos()):
                self.case_set[cword.get_jp_origin()] = None
        return self.case_set

    def get_link_label(self):
        if self.link_label is not None:
            return self.link_label
        parent_word = self.get_parent_word()
        self.link_label = -1
        if parent_word is not None:
            self.link_label = self.parent_word.get_link(self)
        if self.link_label != -1:
            # 格情報を抽出 (ga, o, ni)]
            self.link_label = self.link_label[0].name.split(":")[-1]
        return self.link_label

    def get_child_words(self) -> list[Word]:
        if self.child_words is not None:
            return self.child_words
        self.child_words = []
        for child_pos in self.doc[self.sent_pos].get_ud_children(self):
            cword = self.doc[self.sent_pos].get_word_from_tokpos(child_pos - 1)
            if cword is None:
                raise KeyError
            self.child_words.append(cword)
        return self.child_words

    def is_func(self) -> bool:
        """
            is function the word?
        """
        return self._is_func is not None and self._is_func

    def is_subj(self) -> bool:
        """
            is subject the word?
        """
        return self._is_subj is not None and self._is_subj

    def token(self) -> list[str]:
        """
            get token
        """
        return self._token

    def __parse(self) -> None:
        raise NotImplementedError

    def get_katuyo(self) -> str:
        """
        活用形を返す
        """
        raise NotImplementedError

    def get_surface(self) -> str:
        """
            get surface
        """
        return self.surface

    def get_jp_origin(self) -> str:
        """
            get JP ORIGIN form
        """
        raise NotImplementedError

    def get_origin(self) -> str:
        """
            get origin
        """
        raise NotImplementedError

    def get_ud_pos(self) -> str:
        """
            get UD POS
        """
        if len(self.en_pos) == 0:
            detect_ud_pos(self)
        return ",".join(self.en_pos)

    def is_neg(self) -> bool:
        """
            NEGが入っているか？
        """
        return "NEG" in self.en_pos

    def get_udmisc(self) -> str:
        """
            return ud misc text
        """
        # if self.data_type != "gsd":
        self.ud_misc["BunsetuBILabel"] = "B" if self.word_pos == 0 else "I"
        if self.luw_label is not None:
            self.ud_misc["LUWBILabel"] = self.luw_label
            self.ud_misc["LUWPOS"] = self.luw_pos
        return "|".join(["{}={}".format(k, v) for k, v in sorted(self.ud_misc.items())])

    def get_udfeat(self) -> str:
        """
            return ud feat text
        """
        if len(self.ud_feat) == 0:
            return "_"
        return "|".join(["{}={}".format(k, v) for k, v in list(self.ud_feat.items())])

    def get_xpos(self) -> str:
        """
            get xpos
        """
        raise NotImplementedError

    def convert(self, is_skip_space=True, sep="\t") -> str:
        """
            convert word line.
        """
        templace: str = sep.join([
            "{id}", "{form}", "{lemma}", "{upos}", "{xpos}",
            "{feats}", "{head}", "{deprel}", "{deps}", "{misc}"
        ])
        return templace.format(
            id=self.token_pos, form=self.get_surface(),
            lemma=self.get_origin(),
            upos=self.get_ud_pos(), xpos=self.get_xpos(),
            feats=self.get_udfeat(),
            head=self.dep_num, deprel=self.dep_label,
            deps="_", misc=self.get_udmisc()
        )


class SUW(Word):
    """
        SUW class: bunsetu class is word list
    """

    def __init__(self, **kwargs):
        self.word_unit = "suw"
        super(SUW, self).__init__(**kwargs)
        self.__parse()

    def get_jp_origin(self) -> str:
        """
            get JP ORIGIN form
        """
        return self.origin

    def get_katuyo(self):
        """
        活用形を返す
        """
        return self.katuyo

    def get_xpos(self):
        """
            get xpos
        """
        items, pos = [], 0
        while self.features[pos] != "*" and pos < 4:
            items.append(self.features[pos])
            pos += 1
        return "-".join(items)

    def get_origin(self) -> str:
        """
            get origin
        """
        if RE_PROP_MATH.match(self.get_xpos()):
            # 固有名詞は表層を返す
            return self.surface
        if RE_ASCII_MATH.match(self.surface):
            # 英数字文字列は
            return self.surface
        if self.origin == "":
            return "_"
        if self.origin in ["です", "デス"] or self.features[7] == "です":
            return "だ"
        if self.features[7] == "ぽい":
            return "ぽい"
        if self.features[7] == "臭い":
            return "臭い"
        if self.features[7] == "辛い":
            return "辛い"
        if self.features[7] == "無い":
            return "ない"
        if self.jp_pos == "助動詞":
            if self.features[10] in ["です", "デス", "ダ"]:
                return "だ"
            if self.features[10] in ["ノ", "の"]:
                return "だ"
            if self.features[10] in UNIDIC_ORIGIN_CONV:
                return UNIDIC_ORIGIN_CONV[self.features[10]]
            if self.features[7] in UNIDIC_ORIGIN_CONV:
                return UNIDIC_ORIGIN_CONV[self.features[7]]
            return self.features[7]
        if self.origin in UNIDIC_ORIGIN_CONV:
            return UNIDIC_ORIGIN_CONV[self.origin]
        if self.origin == "　":  # and self.luw_pos == u"web誤脱":
            return "[SP]"
        return self.origin

    def __parse(self) -> None:
        self.surface = self._token[0]
        self.features = self._token[1].split(",")
        self.jp_pos = self.features[0]
        self.origin = self.features[10]
        if self.origin == "":
            self.origin = self.features[7]
        if self.features[1] == "数詞":
            self.origin = self.features[7]
        self.usage = self.features[14]
        self.yomi = self.features[6]
        self.katuyo = self.features[5]
        if self.word_unit == "suw":
            assert len(self._token) >= 3
            if self._token[2] == "":
                target = None
                if len(self.bunsetu) > 0:
                    target = self.bunsetu[-1]
                elif self.bunsetu.prev_bunsetu is not None and len(self.bunsetu.prev_bunsetu) > 0:
                    target = self.bunsetu.prev_bunsetu[-1]
                else:
                    raise ValueError
                # bunsetu情報を前の単語から引き継ぐ
                self.luw_label = "I"
                self.luw_form = target.luw_form
                self.luw_origin = target.luw_origin
                self.luw_yomi = target.luw_yomi
                self.luw_pos = target.luw_pos
                self.luw_katuyo = target.luw_katuyo
            else:
                self.luw_label = "B"
                self.luw_features = self._token[3].split(",")
                self.luw_form = self._token[2]
                if len(self.luw_features) < 8:
                    print("WARNING: {} size small".format(self.luw_features))
                    self.luw_features.insert(3, '*')
                self.luw_origin = self.luw_features[7]
                self.luw_yomi = self.luw_features[6]
                self.luw_pos = "-".join([f for f in self.luw_features[0:5] if f != "*" and f != ""])
                self.luw_katuyo = self.luw_features[5]


class CHJSUW(Word):
    """
        CHJ SUW
    """

    def __init__(self, **kwargs):
        self.word_unit = "suw"
        super(CHJSUW, self).__init__(**kwargs)
        self.__parse()

    def get_jp_origin(self) -> str:
        """
            get JP ORIGIN form
        """
        return self.origin

    def get_katuyo(self) -> str:
        """
        活用形を返す
        """
        return self.katuyo

    def _pos_disambiguation(self):
        self.en_pos = [self.en_pos[-1]]
        return

    def get_ud_pos(self) -> str:
        """
            get UD POS
        """
        if len(self.en_pos) == 0:
            detect_ud_pos(self)
        if len(self.en_pos) > 1:
            self._pos_disambiguation()
        return ",".join(self.en_pos)

    def __str__(self) -> str:
        """
            meiroku(CHJ)とBCCWJで表示する列が違うので_tokenを参照する
        """
        sss = ""
        if self.yomi is not None:
            tok = self._token[:]
            ttt = tok[1].split(",")
            ttt.append(self.yomi)
            sss += "\t".join([tok[0], ",".join(ttt)] + tok[2:])
        else:
            sss += "\t".join(self._token)
        if self.luw_label is not None:
            lst = [self.luw_label, self.luw_origin, self.luw_yomi, self.luw_pos, self.luw_katuyo]
            sss = sss + "\t" + "\t".join(lst)
        return sss

    def get_xpos(self):
        """
            get xpos
        """
        items, pos = [], 0
        while self.features[pos] != "*" and pos < 4:
            items.append(self.features[pos])
            pos += 1
        return "-".join(items)

    def get_origin(self) -> str:
        """
            get origin
        """
        if self.surface == "　":
            return JP_SP_MARK
        if self.origin == "":
            return "_"
        # 原形読みよりそのままのほうが有用なのでは？
        return self.origin

    def __parse(self) -> None:
        self.features = self._token[1].split(",")
        self.surface = self._token[0]
        self.jp_pos = self.features[0]
        self.origin = self.features[7]
        self.yomi = None
        self.katuyo = self.features[5]
        if len(self.features) > 9:
            self.yomi = self.features[9]
        if len(self._token) >= 4 and self.word_unit == "suw":
            # 長単位情報使う？
            self.luw_label = self._token[3]
            self.luw_origin = self._token[4]
            self.luw_pos = self._token[6]
            self.luw_katuyo = self._token[7]
            self.luw_yomi = self._token[5]
