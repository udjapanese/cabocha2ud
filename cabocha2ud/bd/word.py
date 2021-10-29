# -*- coding: utf-8 -*-

"""
BCCWJ DepParaPAS class
"""

from __future__ import annotations

import re
import string
from typing import Literal, Union, Optional, Tuple, cast, TYPE_CHECKING

from .util import SUWFeaField, LUWFeaField

from ..lib.logger import Logger
if TYPE_CHECKING:
    from .bunsetu import Bunsetu
    from .document import Document
    from .sentence import Sentence
    from .annotation import Segment, Annotation, AnnotationList


JP_SP_MARK = "[JSP]"
RE_CASE_MATH = re.compile("助詞-[係格副]助詞")
RE_PROP_MATH = re.compile(".*固有名詞.*")
RE_ASCII_MATH = re.compile('^[' + string.printable + ']+$')


UNIDIC_ORIGIN_CONV = {
    "ず": "ぬ",
    "為る": "する",
    "居る": "いる",
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
}


class Property:

    def __init__(self, **kwargs):
        pass


class Reference(Property):
    """
     Implementation of Reference object
    """
    attr_property: list[str] = ["doc", "bunsetu", "sent_pos", "bunsetu_pos"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__doc: Optional[Document] = kwargs.get("doc")
        self.__bunsetu: "Bunsetu" = kwargs.get("bunsetu")
        self.__sent_pos: int = kwargs.get("sent_pos")  # 文書中の文の位置
        self.__bunsetu_pos: int = kwargs.get("bunsetu_pos")  # 文中の文節の位置

    @property
    def doc(self):
        return self.__doc

    @doc.setter
    def doc(self, doc: Optional[Document]):
        self.__doc = doc

    @property
    def bunsetu(self):
        return self.__bunsetu

    @bunsetu.setter
    def bunsetu(self, bunsetu: "Bunsetu"):
        self.__bunsetu = bunsetu

    @property
    def sent_pos(self):
        return self.__sent_pos

    @sent_pos.setter
    def sent_pos(self, sent_pos: int):
        self.__sent_pos = sent_pos

    @property
    def bunsetu_pos(self):
        return self.__bunsetu_pos

    @bunsetu_pos.setter
    def bunsetu_pos(self, bunsetu_pos: int):
        self.__bunsetu_pos = bunsetu_pos

    def get_bunsetu_jp_type(self) -> Optional[str]:
        from .bunsetu import Bunsetu
        assert self.bunsetu is not None and isinstance(self.bunsetu, Bunsetu)
        return self.bunsetu.bunsetu_type

    def get_bunsetu_position_word(self, bpos: str) -> Optional[Word]:
        """
            get word has `bpos` type, the bunsetu position word
        """
        from .bunsetu import Bunsetu
        assert self.bunsetu is not None and isinstance(self.bunsetu, Bunsetu)
        for target_wrd in self.bunsetu:
            if bpos == target_wrd.get_bunsetu_position_type():
                return target_wrd
        return None

    def get_sentence(self) -> "Sentence":
        """
            get Sentence object
        """
        from .document import Document
        assert isinstance(self.doc, Document) and isinstance(self.sent_pos, int)
        return self.doc[self.sent_pos]

    def get_sent_segment(self) -> Union[Literal[-1], "Segment"]:
        """
            get segment for word
        """
        assert self.doc is not None
        sword_pos = self.doc[self.sent_pos].get_pos_from_word(self)
        if self.doc[self.sent_pos].annotation_list is not None:
            return cast("AnnotationList", self.doc[self.sent_pos].annotation_list).get_segment(sword_pos)
        raise KeyError

    def get_luw_units(self) -> list[Word]:
        """ 属しているLUWのリストを返す

        Raises:
            KeyError: 文節の中に自分自身がなかったらエラー

        Returns:
            list[Word]: 自身を含むLUW（Wordのリスト）
        """
        from .bunsetu import Bunsetu
        assert isinstance(self.bunsetu, Bunsetu)
        for luw_unit in self.bunsetu.get_luw_list():
            for wrd in luw_unit:
                if wrd == self:
                    return luw_unit
        raise KeyError("not found from bunsetu")


class SUW(Property):
    attr_property: list[str] = [
        "word_pos", "surface", "features", "jp_pos", "origin", "usage",
        "yomi", "katuyo"
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 文節中の語の位置（SUW）
        self.word_pos: int = kwargs.get("word_pos")
        # 表層系
        self.surface: str = kwargs.get("surface")
        # 特徴(2列目)
        self.features: list[str] = kwargs.get("features", [])
        # 品詞
        self.jp_pos: str = kwargs.get("jp_pos")
        # 原型
        self.origin: str = kwargs.get("origin")
        # 用法（BCCWJのみ）
        self.usage: str = kwargs.get("usage")
        # 読み
        self.yomi: str = kwargs.get("yomi")
        # 活用形
        self.katuyo: str = kwargs.get("katuyo")

    def parse_suw_part(self, token: list[str]):
        from .util import SUWFeaField as Field
        self.surface = token[0]
        self.features = token[1].split(",")
        self.jp_pos = self.features[Field.pos1]
        self.origin = self.features[Field.orthBase]
        if self.origin == "":
            self.origin = self.features[Field.lemma]
        if self.features[Field.pos2] == "数詞":
            self.origin = self.features[Field.lemma]
        self.usage = self.features[Field.iForm]
        self.yomi = self.features[Field.lForm]
        self.katuyo = self.features[Field.cForm]

    def get_surface(self) -> str:
        """
            get surface
        """
        return self.surface

    def get_katuyo(self) -> str:
        """
        活用形を返す
        """
        return self.katuyo

    def get_xpos(self) -> str:
        """
            get xpos
        """
        from .util import SUWFeaField as Field
        return "-".join([
            f for f in self.features[Field.pos1:Field.cForm] if f != "*" and f != ""
        ])

    def get_features(self) -> list[str]:
        return self.features

    def get_jp_origin(self) -> str:
        """
            get JP ORIGIN form
        """
        return self.origin

    def get_origin(self) -> str:
        """
            get origin
        """
        from .util import SUWFeaField as Field

        if RE_PROP_MATH.match(self.get_xpos()) or RE_ASCII_MATH.match(self.get_surface()):
            # 「固有名詞」か「英数字文字列」は表層を返す
            return self.get_surface()
        if self.origin == "":
            return "_"
        if self.origin in ["です", "デス"] or self.features[Field.lemma] == "です":
            return "だ"
        lemma_dic = {
            "ぽい": "ぽい", "臭い": "臭い", "辛い": "辛い", "無い": "ない"
        }
        if self.features[Field.lemma] in lemma_dic:
            return lemma_dic[self.features[Field.lemma]]
        if self.jp_pos == "助動詞":
            if self.features[Field.orthBase] in ["です", "デス", "ダ", "ノ", "の"]:
                return "だ"
            if self.features[Field.orthBase] in UNIDIC_ORIGIN_CONV:
                return UNIDIC_ORIGIN_CONV[self.features[Field.orthBase]]
            if self.features[Field.lemma] in UNIDIC_ORIGIN_CONV:
                return UNIDIC_ORIGIN_CONV[self.features[Field.lemma]]
            return self.features[Field.lemma]
        if self.origin in UNIDIC_ORIGIN_CONV:
            return UNIDIC_ORIGIN_CONV[self.origin]
        if self.origin == "　":
            return "[SP]"
        return self.origin


class LUW(Property):
    attr_property: list[str] = [
        "luw_pos", "luw_label", "luw_origin", "luw_yomi", "luw_katuyo",
        "luw_form", "luw_features"
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 長単位品詞
        self.luw_pos: str = kwargs.get("luw_pos", None)
        # 長単位（範囲）ラベル
        self.luw_label: str = kwargs.get("luw_label", None)
        # 長単位原形
        self.luw_origin: str = kwargs.get("luw_origin", None)
        # 長単位読み
        self.luw_yomi: str = kwargs.get("luw_yomi", None)
        # 長単位活用
        self.luw_katuyo: str = kwargs.get("luw_katuyo", None)
        # 長単位表層
        self.luw_form: str = kwargs.get("luw_form", None)
        # 長単位品詞特徴
        self.luw_features: list[str] = kwargs.get("luw_features", [])
        # 前の単語
        self.l_bunsetu: Optional[Bunsetu] = None

    def get_surface(self) -> str:
        return self.luw_form

    def get_origin(self) -> str:
        if RE_PROP_MATH.match(self.get_xpos()) or RE_ASCII_MATH.match(self.get_surface()):
            # 「固有名詞」か「英数字文字列」は表層を返す
            return self.get_surface()
        if self.luw_origin == "":
            return "_"
        if self.luw_origin in ["です", "デス"] or self.luw_features[LUWFeaField.l_lemma] == "です":
            return "だ"
        lemma_dic = {
            "ぽい": "ぽい", "臭い": "臭い", "辛い": "辛い", "無い": "ない"
        }
        if self.luw_features[LUWFeaField.l_lemma] in lemma_dic:
            return lemma_dic[self.luw_features[LUWFeaField.l_lemma]]
        if self.luw_features[LUWFeaField.l_pos1] == "助動詞":
            if self.luw_features[LUWFeaField.l_lemma] in UNIDIC_ORIGIN_CONV:
                return UNIDIC_ORIGIN_CONV[self.luw_features[LUWFeaField.l_lemma]]
            return self.luw_features[LUWFeaField.l_lemma]
        if self.luw_origin in UNIDIC_ORIGIN_CONV:
            return UNIDIC_ORIGIN_CONV[self.luw_origin]
        if self.luw_origin == "　":
            return "[SP]"
        return self.luw_origin

    def get_katuyo(self) -> str:
        """
        活用形を返す
        """
        return self.luw_katuyo

    def get_xpos(self) -> str:
        return self.luw_pos
        #pos = 0
        #for pos, fff in enumerate(self.luw_features):
        #    if fff == "*" or pos >= 4:
        #        break
        #return "-".join(self.luw_features[:pos])

    def get_features(self) -> list[str]:
        return self.luw_features

    def parse_luw_part(self, token: list[str], luw_info: Optional[Word], bunsetu: Bunsetu) -> None:
        from .util import LUWFeaField as Field
        self.l_bunsetu = bunsetu
        if token[2] == "":
            target = None
            if isinstance(luw_info, Word):
                self.luw_label = "I"
                self.luw_form = luw_info.luw_form
                self.luw_features = luw_info.luw_features
                self.luw_origin = luw_info.luw_features[Field.l_lemma]
                self.luw_yomi = luw_info.luw_features[Field.l_reading]
                self.luw_pos = "-".join([
                    f for f in self.luw_features[Field.l_pos1:Field.l_cForm] if f != "*" and f != ""
                ])
                self.luw_katuyo = luw_info.luw_features[Field.l_cForm]
                return
            if len(self.l_bunsetu) > 0:
                target = self.l_bunsetu[-1]
            elif self.l_bunsetu.prev_bunsetu is not None and len(self.l_bunsetu.prev_bunsetu) > 0:
                target = self.l_bunsetu.prev_bunsetu[-1]
            else:
                raise ValueError
            # bunsetu情報を前の単語から引き継ぐ
            self.luw_label = "I"
            self.luw_form = target.luw_form
            self.luw_origin = target.luw_origin
            self.luw_yomi = target.luw_yomi
            self.luw_pos = target.luw_pos
            self.luw_katuyo = target.luw_katuyo
            self.luw_features = target.luw_features
        else:
            self.luw_label = "B"
            self.luw_features = token[3].split(",")
            self.luw_form = token[2]
            if len(self.luw_features) < 8:
                print("WARNING: {} size small".format(self.luw_features))
                self.luw_features.insert(3, '*')
            self.luw_origin = self.luw_features[Field.l_lemma]
            self.luw_yomi = self.luw_features[Field.l_reading]
            self.luw_pos = "-".join([f for f in self.luw_features[Field.l_pos1:Field.l_cForm] if f != "*" and f != ""])
            self.luw_katuyo = self.luw_features[Field.l_cForm]


class BunDepInfo(Property):
    attr_property: list[str] = [
        "dep_num", "is_subj_val", "is_func_val", "link_label", "case_set",
        "parent_word", "child_words", "sem_head_word", "syn_head_word", "bunsetu_position_type"
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dep_num: Optional[int] = kwargs.get("dep_num", None)
        self.is_subj_val: Optional[bool] = kwargs.get("is_subj_val", None)  # 主辞か？ None
        self.is_func_val: Optional[bool] = kwargs.get("is_func_val", None) # 機能語か？ None
        self.link_label: Union[None, int, str] = kwargs.get("link_label", None)
        self.case_set: Optional[dict[str, None]] = kwargs.get("case_set", None)
        self.parent_word: Optional[Word] = kwargs.get("parent_word", None)
        self.child_words: Optional[list[Word]] = kwargs.get("child_words", None)
        self.sem_head_word: Optional[Word] = kwargs.get("sem_head_word", None)
        self.syn_head_word: Optional[Word] = kwargs.get("syn_head_word", None)
        self.bunsetu_position_type: Optional[str] = kwargs.get("bunsetu_position_type", None)

    def set_bunsetsu_info(self, subj: Optional[bool], func: Optional[bool]) -> None:
        """
            set bunsetu info
        """
        self.is_func_val = func
        self.is_subj_val = subj

    def is_func(self) -> bool:
        """
            is function the word?
        """
        return self.is_func_val is not None and self.is_func_val

    def is_subj(self) -> bool:
        """
            is subject the word?
        """
        return self.is_subj_val is not None and self.is_subj_val


class UD(Property):
    attr_property: list[str] = ["token_pos", "ud_misc", "ud_feat", "en_pos", "dep_label"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # UDでの単語位置
        self.token_pos: int = kwargs.get("token_pos")
        # MISC
        self.ud_misc: dict[str, str] = kwargs.get("ud_misc", {"SpaceAfter": "No"})
        # FEAT
        self.ud_feat: dict = kwargs.get("ud_feat", {})
        # 英語の品詞
        self.en_pos: list[str] = kwargs.get("en_pos", [])
        # 掛かりラベル
        self.dep_label: Optional[str] = kwargs.get("dep_label")

    def get_udfeat(self) -> str:
        """
            return ud feat text
        """
        if len(self.ud_feat) == 0:
            return "_"
        return "|".join(["{}={}".format(k, v) for k, v in list(self.ud_feat.items())])

    def is_neg(self) -> bool:
        """
            NEGが入っているか？
        """
        return "NEG" in self.en_pos

    def get_ud_pos(self) -> str:
        """
            get UD POS
        """
        assert len(self.en_pos) > 0, "must do `detect_ud_pos` function "
        return ",".join(self.en_pos)

    def get_bunsetu_position_type(self) -> str:
        assert "BunsetuPositionType" in self.ud_misc
        return self.ud_misc["BunsetuPositionType"]


class Word(Reference, SUW, LUW, BunDepInfo, UD):

    """
        word class
    """

    def __init__(self, **kwargs):
        assert kwargs.get("bunsetu") is not None

        # 機能的なものは通常定義
        self.logger: Logger = kwargs.get("logger") or Logger()
        self.base_file_name: Optional[str] = kwargs.get("base_file_name")
        self.debug: bool = kwargs.get("debug", True)
        self.word_unit_mode: str = kwargs.get("word_unit_mode", "suw")
        self._token: list[str] = []

        super(Word, self).__init__(**kwargs)

        if kwargs.get("token") is not None:
            self._token: list[str] = kwargs.get("token").split("\t")
        self.parse(luw_info=kwargs.get("luw_info", None))

    def parse(self, luw_info: Optional[Word]) -> None:
        self.parse_suw_part(self._token)
        if len(self._token) == 2:
            # 長単位情報がない
            return
        self.parse_luw_part(self._token, luw_info, self.bunsetu)

    def __str__(self) -> str:
        org = "\t".join(self._token)
        return org

    def get_instance_for_pos(self) -> dict[str, str]:
        from .document import Document
        assert isinstance(self.dep_num, int) and isinstance(self.doc, Document)
        parent_word = self.get_parent_word()
        return {
            "pos": self.get_xpos(),
            "base_lexeme": self.get_origin(),
            "luw": self.get_luw_pos(),
            "bpos": self.get_bunsetu_position_type(),
            "parent_upos": parent_word.get_ud_pos() if parent_word is not None else "THIS_ROOT"
        }

    def get_link(self, aword: Word) -> Union[Literal[-1], Tuple["Annotation", "Segment", "Segment"]]:
        """
            get link for aword
        """
        from .document import Document
        assert self.doc is not None and isinstance(self.doc, Document)
        sword_pos = self.doc.get_pos_from_word(self)
        aword_pos = self.doc.get_pos_from_word(aword)
        return self.doc.doc_annotation.get_link(sword_pos, aword_pos)

    def get_parent_word(self) -> Optional[Word]:
        """
            get parent word from doc
        """
        assert self.doc is not None
        if self.dep_num is not None:
            self.parent_word = self.doc[self.sent_pos].get_word_from_tokpos(self.dep_num - 1)
        return self.parent_word

    def get_surface_case(self) -> dict[str, None]:
        """
            get surface case (表層格)
        """
        assert self.doc is not None
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

    def get_semhead_link_label(self) -> Union[str, Literal[-1]]:
        """
            selfがSEM_HEADだとして親と述語項関係にあるならそのラベルを返す
            selfと親自身にラベルがあるとは限らないので長単位から探す
        Returns:
                str: ga, o, ni のどれか
        Literal[-1]: リンクなかった
        """
        from .annotation import Segment, Annotation
        if self.ud_misc["BunsetuPositionType"] != "SEM_HEAD":
            return -1
        parent_word = self.get_parent_word()
        if parent_word is None:
            return -1
        for wrd in self.get_luw_units():
            _link_label: Union[Tuple[Annotation, Segment, Segment], Literal[-1]] = parent_word.get_link(wrd)
            if _link_label != -1:
                # 格情報を抽出 (ga, o, ni)]
                return cast(Tuple[Annotation, Segment, Segment], _link_label)[0].name.split(":")[-1]
        return -1

    def get_link_label(self) -> Union[str, Literal[-1]]:
        from .annotation import Segment, Annotation
        """
        自分と親とのリンクを確認して返す
        Returns:
                str: ga, o, ni のどれか
        Literal[-1]: リンクなかった
        """
        parent_word = self.get_parent_word()
        if parent_word is not None:
            _link_label: Union[Tuple[Annotation, Segment, Segment], Literal[-1]] = parent_word.get_link(self)
            if _link_label != -1:
                # 格情報を抽出 (ga, o, ni)]
                return cast(Tuple[Annotation, Segment, Segment], _link_label)[0].name.split(":")[-1]
        return -1

    def get_child_words(self) -> list[Word]:
        assert self.doc is not None
        if self.child_words is not None:
            return self.child_words
        self.child_words = []
        for child_pos in self.doc[self.sent_pos].get_ud_children(self):
            cword = self.doc[self.sent_pos].get_word_from_tokpos(child_pos - 1)
            if cword is None:
                raise KeyError
            self.child_words.append(cword)
        return self.child_words

    def has_space_after(self) -> bool:
        from .annotation import Segment
        sent = self.doc[self.sent_pos]
        wrd_pos = sent.get_pos_from_word(self)
        res = sent.annotation_list.get_segment(wrd_pos)
        if isinstance(res, Segment) and res.get_name() == "space-after:seg":
            value = res.get_attr("space-after:value")
            return value is not None
        return False

    def get_udmisc(self) -> str:
        """
            return ud misc text
        """
        self.ud_misc["BunsetuBILabel"] = "B" if self.word_pos == 0 else "I"
        if self.luw_label is not None:
            self.ud_misc["LUWBILabel"] = self.luw_label
            self.ud_misc["LUWPOS"] = self.get_luw_pos()
        if self.has_space_after():
            self.ud_misc["SpaceAfter"] = "Yes"
            # comment: BCCWJなどのYesを上書きする可能性があるのでNoにはしないこと
        return "|".join([
            "{}={}".format(k, v) for k, v in sorted(self.ud_misc.items())
            if self.word_unit_mode == "suw" or (self.word_unit_mode == "luw" and k not in ["LUWPOS", "LUWBILabel"])
        ])

    def convert(self, sep: str="\t") -> str:
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

    def build_luw_unit(self):
        assert self.word_unit_mode == "luw", "differ mode: " + self.word_unit_mode
        self._token[0] = self.get_surface()
        self._token[1] = ",".join(self.get_features())

    def get_surface(self) -> str:
        if self.word_unit_mode == "luw":
            return LUW.get_surface(self)
        if self.word_unit_mode == "suw":
            return SUW.get_surface(self)
        raise NotImplementedError

    def get_origin(self):
        if self.word_unit_mode == "luw":
            return LUW.get_origin(self)
        if self.word_unit_mode == "suw":
            return SUW.get_origin(self)
        raise NotImplementedError

    def get_xpos(self):
        if self.word_unit_mode == "luw":
            return LUW.get_xpos(self)
        if self.word_unit_mode == "suw":
            return SUW.get_xpos(self)
        raise NotImplementedError

    def get_luw_pos(self) -> str:
        if self.luw_pos is not None:
            return self.luw_pos
        else:
            return self.get_xpos()

    def get_katuyo(self) -> str:
        if self.word_unit_mode == "luw":
            return LUW.get_katuyo(self)
        if self.word_unit_mode == "suw":
            return SUW.get_katuyo(self)
        raise NotImplementedError

    def get_features(self) -> list[str]:
        if self.word_unit_mode == "luw":
            return LUW.get_features(self)
        if self.word_unit_mode == "suw":
            return SUW.get_features(self)
        raise NotImplementedError
