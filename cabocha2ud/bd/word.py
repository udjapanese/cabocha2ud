"""BCCWJ DepParaPAS class."""

from __future__ import annotations

import re
import string
from typing import TYPE_CHECKING, Any, ClassVar, Literal, Union, cast

from cabocha2ud.bd.util import DoNotExceptSizeError, LUWFeaField, SUWFeaField, csv_join, csv_split
from cabocha2ud.lib.logger import Logger

if TYPE_CHECKING:
    # ruff: noqa: TCH004
    from cabocha2ud.bd.annotation import Annotation, AnnotationList, Segment
    from cabocha2ud.bd.bunsetu import Bunsetu
    from cabocha2ud.bd.document import Document
    from cabocha2ud.bd.sentence import Sentence

from cabocha2ud.bd.annotation import Annotation, AnnotationList, Segment

JP_SP_MARK = "[JSP]"
RE_CASE_MATH = re.compile("助詞-[係格副]助詞")
RE_PROP_MATH = re.compile(".*固有名詞.*")
RE_ASCII_MATH = re.compile("^[" + string.printable + "]+$")


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


def conv_v29_lemma(
    origin: str, features: list[str], pos1_pos: int, lemma_pos: int, orthbase_pos: int
) -> str:
    """Convert old lemma."""
    lemma_dic = {"ぽい": "ぽい", "臭い": "臭い", "辛い": "辛い"}
    if features[lemma_pos] in lemma_dic:
        return lemma_dic[features[lemma_pos]]
    if features[pos1_pos] == "助動詞":
        # ruff: noqa: RUF001
        if features[orthbase_pos] in ["です", "デス", "ダ", "ノ", "の"]:
            return "だ"
        if features[lemma_pos] in UNIDIC_ORIGIN_CONV:
            return UNIDIC_ORIGIN_CONV[features[lemma_pos]]
        return features[lemma_pos]
    if origin in UNIDIC_ORIGIN_CONV:
        return UNIDIC_ORIGIN_CONV[origin]
    return origin


class Property:
    """Base Object."""

    attr_property: list[str]

    def __init__(self, **kwargs: dict[str, object]) -> None:
        """Init."""
        self.logger: Logger = cast(Logger, kwargs.get("logger")) or Logger()

    def __str__(self) -> str:
        """Get String."""
        raise NotImplementedError


class Reference(Property):
    """Implementation of Reference object."""

    attr_property: ClassVar[list[str]] = ["doc", "bunsetu", "sent_pos", "bunsetu_pos"]

    def __init__(self, **kwargs: dict[str, object]) -> None:
        """Init."""
        super().__init__(**kwargs)
        self.__doc: Document| None = cast("Document", kwargs.get("doc"))
        self.__bunsetu: Bunsetu = cast("Bunsetu", kwargs.get("bunsetu"))
        self.__sent_pos: int = cast(int, kwargs.get("sent_pos"))
        self.__bunsetu_pos: int = cast(int, kwargs.get("bunsetu_pos"))

    def __str__(self) -> str:
        """Get string."""
        raise NotImplementedError

    @property
    def doc(self) -> Document | None:
        """Getter Document object."""
        return self.__doc

    @doc.setter
    def doc(self, doc: Document | None) -> None:
        """Settter Document object."""
        self.__doc = doc

    @property
    def bunsetu(self) -> Bunsetu:
        """Getter Bunsetu object."""
        return self.__bunsetu

    @bunsetu.setter
    def bunsetu(self, bunsetu: Bunsetu) -> None:
        """Setter Bunsetu object."""
        self.__bunsetu = bunsetu

    @property
    def sent_pos(self) -> int:
        """"Getter sent pos."""
        return self.__sent_pos

    @sent_pos.setter
    def sent_pos(self, sent_pos: int) -> None:
        """Setter sent pos."""
        self.__sent_pos = sent_pos

    @property
    def bunsetu_pos(self) -> int:
        """"Getter bunsetu pos."""
        return self.__bunsetu_pos

    @bunsetu_pos.setter
    def bunsetu_pos(self, bunsetu_pos: int) -> None:
        """"Setter bunsetu pos."""
        self.__bunsetu_pos = bunsetu_pos

    def get_bunsetu_jp_type(self) -> str | None:
        """Get JP Bunsetu Type."""
        assert isinstance(self.bunsetu.bunsetu_type, str) or self.bunsetu.bunsetu_type is None
        return self.bunsetu.bunsetu_type

    def get_bunsetu_position_word(self, bpos: str) -> Word | None:
        """Get word has `bpos` type, the bunsetu position word."""
        for target_wrd in self.bunsetu:
            if bpos == target_wrd.get_bunsetu_position_type():
                assert isinstance(target_wrd, Word)
                return target_wrd
        return None

    def get_sentence(self) -> Sentence:
        """Get Sentence object."""
        assert isinstance(self.doc, Document)
        assert isinstance(self.sent_pos, int)
        return self.doc[self.sent_pos]

    def get_luw_units(self) -> list[Word]:
        """属しているLUWのリストを返す.

        Raises:
            KeyError: 文節の中に自分自身がなかったらエラー

        Returns:
            list[Word]: 自身を含むLUW（Wordのリスト）

        """
        for luw_unit in self.bunsetu.get_luw_list():
            for wrd in luw_unit:
                if wrd == self:
                    assert isinstance(luw_unit, list)
                    return luw_unit
        msg = "not found from bunsetu"
        raise KeyError(msg)


class SUW(Property):
    """Implementation of SUW."""

    attr_property: ClassVar[list[str]] = [
        "word_pos", "surface", "features", "jp_pos", "origin", "usage",
        "yomi", "katuyo"
    ]

    def __init__(self, **kwargs: dict[str, object]) -> None:
        """Init."""
        super().__init__(**kwargs)
        # 文節中の語の位置（SUW）
        self.word_pos: int = cast(int, kwargs.get("word_pos"))
        # 表層系
        self.surface: str = cast(str, kwargs.get("surface"))
        # 品詞
        self.jp_pos: str = cast(str, kwargs.get("jp_pos"))
        # 原型
        self.origin: str = cast(str, kwargs.get("origin"))
        # 用法（BCCWJのみ）
        self.usage: str = cast(str, kwargs.get("usage"))
        # 読み
        self.yomi: str = cast(str, kwargs.get("yomi"))
        # 活用形
        self.katuyo: str = cast(str, kwargs.get("katuyo"))
        # 特徴(2列目)
        self.features: list[str] = cast(list[str], kwargs.get("features", []))

    def __str__(self) -> str:
        """Get string."""
        raise NotImplementedError

    def parse_suw_part(self, token: list[str]) -> None:
        """Parse SUW part."""
        self.surface = token[0]
        try:
            self.features = csv_split(token[1], expect_size=len(SUWFeaField))
        except DoNotExceptSizeError:
            features = csv_split(token[1])
            full_size = len(SUWFeaField)
            if len(features) < full_size:
                min_trusted_size = SUWFeaField.goshu + 1
                if len(features) < min_trusted_size:
                    features.extend([""] * (min_trusted_size - len(features)))
                if len(features) < full_size:
                    features.extend([""] * (full_size - len(features)))
            else:
                trusted_limit = SUWFeaField.iConType + 1
                if len(features) > trusted_limit:
                    features = features[:trusted_limit]
                if len(features) < full_size:
                    features.extend([""] * (full_size - len(features)))
            self.features = features[:len(SUWFeaField)]
        assert len(self.features) == len(SUWFeaField)
        self.jp_pos = self.features[SUWFeaField.pos1]
        self.origin = self.features[SUWFeaField.lemma]
        if self.origin == "":
            self.origin = self.features[SUWFeaField.lemma]
        if self.features[SUWFeaField.pos2] == "数詞":
            self.origin = self.features[SUWFeaField.lemma]
        self.usage = self.features[SUWFeaField.iForm]
        self.yomi = self.features[SUWFeaField.lForm]
        self.katuyo = self.features[SUWFeaField.cForm]

    def get_surface(self) -> str:
        """Get surface."""
        return self.surface

    def get_katuyo(self) -> str:
        """活用形を返す."""
        return self.katuyo

    def get_xpos(self) -> str:
        """Get xpos."""
        return "-".join(
            f for f in self.features[SUWFeaField.pos1:SUWFeaField.cForm] if f not in ["*", ""]
        )

    def get_features(self) -> list[str]:
        """Get Features."""
        return self.features

    def get_jp_origin(self) -> str:
        """Get JP ORIGIN form."""
        return self.origin

    def get_origin(self, do_conv29:bool=False) -> str:
        """Get origin."""
        if RE_PROP_MATH.match(self.get_xpos()) or RE_ASCII_MATH.match(self.get_surface()):
            # 「固有名詞」か「英数字文字列」は表層を返す
            return self.get_surface()
        if self.origin == "":
            return "_"
        if self.origin == "　":
            return "[SP]"
        goiso_del_c = 2
        if len(self.origin.split("-")) == goiso_del_c:
            # 語彙素細分類がまざっているので、除く
            return self.origin.split("-")[0]
        if do_conv29:
            return conv_v29_lemma(
                self.origin, self.features,
                SUWFeaField.pos1, SUWFeaField.lemma, SUWFeaField.orthBase
            )
        return self.origin

    def get_unidic_info(self, delimiter: str=",") -> str:
        """UniDic 情報を返す.

        Returns:
            str: UniDic情報、
            「lForm 語彙素読み」「lemma 語彙素」「orth 書字形出現形」「pron 発音形出現形」
            「orthBase 書字形基本形」「pronBase 発音形基本形」「form 語形出現形」
            「formBase  語形基本形」

        """
        usize = 8
        unidic_info: list[str] = [
            SUW.get_features(self)[SUWFeaField.lForm],
            SUW.get_features(self)[SUWFeaField.lemma],
            SUW.get_features(self)[SUWFeaField.orth],
            SUW.get_features(self)[SUWFeaField.orthBase],
            SUW.get_features(self)[SUWFeaField.pron],
            SUW.get_features(self)[SUWFeaField.pronBase],
            SUW.get_features(self)[SUWFeaField.form],
            SUW.get_features(self)[SUWFeaField.formBase]
        ]
        res = csv_join(unidic_info, delimiter=delimiter)
        csv_split(res, expect_size=usize)  # サイズチェック
        return res


class LUW(Property):
    """LUW property."""

    attr_property: ClassVar[list[str]] = [
        "luw_pos", "luw_label", "luw_origin", "luw_yomi", "luw_katuyo",
        "luw_form", "luw_features"
    ]

    def __init__(self, **kwargs: dict[str, object]) -> None:
        """Init."""
        super().__init__(**kwargs)
        # 長単位品詞
        self.luw_pos: str = cast(str, kwargs.get("luw_pos"))
        # 長単位（範囲）ラベル
        self.luw_label: str = cast(str, kwargs.get("luw_label"))
        # 長単位原形
        self.luw_origin: str = cast(str, kwargs.get("luw_origin"))
        # 長単位読み
        self.luw_yomi: str = cast(str, kwargs.get("luw_yomi"))
        # 長単位活用
        self.luw_katuyo: str = cast(str, kwargs.get("luw_katuyo"))
        # 長単位表層
        self.luw_form: str = cast(str, kwargs.get("luw_form"))
        # 長単位品詞特徴
        self.luw_features: list[str] = cast(list[str], kwargs.get("luw_features", []))
        # 前の単語
        self.l_bunsetu: Bunsetu | None = None

    def __str__(self) -> str:
        """Get string."""
        raise NotImplementedError

    def get_surface(self) -> str:
        """Get Surface (Form)."""
        return self.luw_form

    def get_origin(self, do_conv29:bool=False) -> str:
        """Get Origin."""
        if RE_PROP_MATH.match(self.get_xpos()) or RE_ASCII_MATH.match(self.get_surface()):
            # 「固有名詞」か「英数字文字列」は表層を返す
            return self.get_surface()
        if self.luw_origin == "":
            return "_"
        if self.luw_origin == "　":
            return "[SP]"
        if do_conv29:
            return conv_v29_lemma(
                self.luw_origin, self.luw_features,
                LUWFeaField.l_pos1, LUWFeaField.l_lemma, LUWFeaField.l_lemma
            )
        return self.luw_origin

    def get_unidic_info(self, delimiter: str=",") -> str:
        """UniDic 情報を返す.

        Returns:
            str: UniDic情報、語彙素（l_lemma） 読み（l_reading）

        """
        lsize = 2
        luw_features = LUW.get_features(self)
        if len(luw_features) == 0:
            return "_"
        unidic_info: list[str] = [
            LUW.get_features(self)[LUWFeaField.l_reading],
            LUW.get_features(self)[LUWFeaField.l_lemma]
        ]
        res = csv_join(unidic_info, delimiter=delimiter)
        csv_split(res, expect_size=lsize)  # サイズチェック
        return res

    def get_katuyo(self) -> str:
        """活用形を返す."""
        return self.luw_katuyo

    def get_xpos(self) -> str:
        """Get XPOS for LUW POS."""
        return self.luw_pos

    def get_features(self) -> list[str]:
        """Get LUW features."""
        return self.luw_features

    def parse_luw_part(self, token: list[str], luw_info: Word | None, bunsetu: Bunsetu) -> None:
        """Parse LUW Part."""
        self.l_bunsetu = bunsetu
        if token[2] == "":
            target = None
            if isinstance(luw_info, Word):
                self.luw_label = "I"
                self.luw_form = luw_info.luw_form
                self.luw_features = luw_info.luw_features
                self.luw_origin = luw_info.luw_features[LUWFeaField.l_lemma]
                self.luw_yomi = luw_info.luw_features[LUWFeaField.l_reading]
                self.luw_pos = "-".join(
                    f for f in self.luw_features[LUWFeaField.l_pos1:LUWFeaField.l_cForm]
                    if f not in ["*", ""]
                )
                self.luw_katuyo = luw_info.luw_features[LUWFeaField.l_cForm]
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
            try:
                self.luw_features = csv_split(token[3], expect_size=len(LUWFeaField))
            except DoNotExceptSizeError:
                self.luw_features = ["" for _ in range(len(LUWFeaField))]
            assert len(self.luw_features) == len(LUWFeaField)
            self.luw_form = token[2]
            self.luw_origin = self.luw_features[LUWFeaField.l_lemma]
            self.luw_yomi = self.luw_features[LUWFeaField.l_reading]
            self.luw_pos = "-".join(
                f for f in self.luw_features[LUWFeaField.l_pos1:LUWFeaField.l_cForm]
                if f not in ["*", ""]
            )
            self.luw_katuyo = self.luw_features[LUWFeaField.l_cForm]


class BunDepInfo(Property):
    """Bunsetu Dependencies Info."""

    attr_property: ClassVar[list[str]] = [
        "dep_num", "is_subj_val", "is_func_val", "link_label", "case_set",
        "parent_word", "child_words", "sem_head_word", "syn_head_word", "bunsetu_position_type"
    ]

    def __init__(self, **kwargs: dict[str, object]) -> None:
        """Init."""
        super().__init__(**kwargs)
        self.dep_num: int | None = cast(int, kwargs.get("dep_num"))
        self.is_subj_val: bool | None = cast(bool, kwargs.get("is_subj_val"))  # 主辞か？ None
        self.is_func_val: bool | None = cast(bool, kwargs.get("is_func_val")) # 機能語か？ None
        self.link_label: None | int | str = cast(int|str, kwargs.get("link_label"))
        self.case_set: dict[str, None] | None = cast(dict,kwargs.get("case_set"))
        self.parent_word: Word | None = cast(Word, kwargs.get("parent_word"))
        self.child_words: list[Word] | None = cast(list[Word], kwargs.get("child_words"))
        self.sem_head_word: Word | None = cast(Word,kwargs.get("sem_head_word"))
        self.syn_head_word: Word | None = cast(Word,kwargs.get("syn_head_word"))
        self.bunsetu_position_type: str | None = cast(str, kwargs.get("bunsetu_position_type"))

    def __str__(self) -> str:
        """Get string, but not implemented."""
        raise NotImplementedError

    def set_bunsetsu_info(self, subj: bool | None, func: bool | None) -> None:
        """Set bunsetu info."""
        self.is_func_val = func
        self.is_subj_val = subj

    def is_func(self) -> bool:
        """"Is function the word."""
        return self.is_func_val is not None and self.is_func_val

    def is_subj(self) -> bool:
        """Is subject the word."""
        return self.is_subj_val is not None and self.is_subj_val


class UD(Property):
    """UD property object class."""

    attr_property: ClassVar[list[str]] = ["token_pos", "ud_misc", "ud_feat", "en_pos", "dep_label"]

    def __init__(self, **kwargs: dict[str, object]) -> None:
        """Init."""
        super().__init__(**kwargs)
        # UDでの単語位置
        self.token_pos: int = cast(int, kwargs.get("token_pos"))
        # MISC
        self.ud_misc: dict[str, str] = cast(dict, kwargs.get("ud_misc", {"SpaceAfter": "No"}))
        # FEAT
        self.ud_feat: dict = cast(dict, kwargs.get("ud_feat", {}))
        # 英語の品詞
        self.en_pos: list[str] = cast(list[str], kwargs.get("en_pos", []))
        # 掛かりラベル
        self.dep_label: str | None = cast(str, kwargs.get("dep_label"))

    def __str__(self) -> str:
        """Get string."""
        raise NotImplementedError

    def get_udfeat(self) -> str:
        """Return ud feat text."""
        if len(self.ud_feat) == 0:
            return "_"
        return "|".join([f"{k}={v}" for k, v in list(self.ud_feat.items())])

    def is_neg(self) -> bool:
        """NEGが入っているか."""
        return "NEG" in self.en_pos

    def get_ud_pos(self) -> str:
        """Get UD POS."""
        assert len(self.en_pos) > 0, "must do `detect_ud_pos` function "
        return ",".join(self.en_pos)

    def get_bunsetu_position_type(self) -> str:
        """Return Bunsetu position type."""
        assert "BunsetuPositionType" in self.ud_misc
        return self.ud_misc["BunsetuPositionType"]


class Word(Reference, SUW, LUW, BunDepInfo, UD):
    """Word class."""

    def __init__(self, **kwargs: dict[str, Any]) -> None:
        """機能的なものは通常定義."""
        self.logger: Logger = cast(Logger, kwargs.get("logger")) or Logger()
        self.base_file_name: str | None = cast(str, kwargs.get("base_file_name"))
        self.debug: bool = cast(bool, kwargs.get("debug", True))
        self.word_unit_mode: str = cast(str, kwargs.get("word_unit_mode", "suw"))
        self._token: list[str] = []

        super().__init__(**kwargs)

        if kwargs.get("token") is not None:
            if isinstance(kwargs.get("token"), str):
                tok = cast(str, kwargs.get("token"))
                self._token = tok.split("\t")
            if isinstance(kwargs.get("token"), list):
                self._token = cast(list[str], kwargs.get("token"))
        self.parse(luw_info=cast(Word, kwargs.get("luw_info")))

    def parse(self, luw_info: Word | None) -> None:
        """Parse WORD line."""
        self.parse_suw_part(self._token)
        noluw_column_size = 2
        if len(self._token) == noluw_column_size:
            # 長単位情報がないためnoluw_column_size解析をしない
            return
        self.parse_luw_part(self._token, luw_info, self.bunsetu)

    def __str__(self) -> str:
        """Get string."""
        return "\t".join(self._token)

    def get_tokens(self) -> list[str]:
        """Get base token str list."""
        return self._token

    def get_token(self, pos: int) -> str:
        """Get base token by position."""
        return self._token[pos]

    def set_token(self, pos: int, token_s: str) -> None:
        """Set token overwrite."""
        assert pos <= len(self._token)
        self._token[pos] = token_s

    def get_instance_for_pos(self) -> dict[str, str]:
        """Instance for POS."""
        assert isinstance(self.dep_num, int)
        assert self.doc is not None
        parent_word = self.get_parent_word()
        return {
            "pos": self.get_xpos(),
            "base_lexeme": self.get_origin(),
            "luw": self.get_luw_pos(),
            "bpos": self.get_bunsetu_position_type(),
            "parent_upos": parent_word.get_ud_pos() if parent_word is not None else "THIS_ROOT"
        }

    def get_link(self, awrd: Word) -> Literal[-1] | tuple[Annotation, Segment, Segment]:
        """Get link for aword."""
        # mypy: disable=warn-return-any
        assert self.doc is not None
        sword_pos = self.doc.get_pos_from_word(self)
        aword_pos = self.doc.get_pos_from_word(awrd)
        return cast(
            Union[Literal[-1], tuple["Annotation", "Segment", "Segment"]],
            self.doc.doc_annotation.get_link(sword_pos, aword_pos)
        )

    def get_parent_word(self) -> Word | None:
        """Get parent word from doc."""
        assert self.doc is not None
        if self.dep_num is not None:
            self.parent_word = self.doc[self.sent_pos].get_word_from_tokpos(self.dep_num - 1)
        return self.parent_word

    def get_surface_case(self) -> dict[str, None]:
        """Get surface case (表層格)."""
        assert self.doc is not None
        self.case_set = {}
        for child_pos in self.doc[self.sent_pos].get_ud_children(self, is_reconst=True):
            cword = self.doc[self.sent_pos].get_word_from_tokpos(child_pos - 1)
            if cword is None:
                raise ValueError
            if RE_CASE_MATH.match(cword.get_xpos()):
                self.case_set[cword.get_jp_origin()] = None
        return self.case_set

    def get_semhead_link_label(self) -> str | Literal[-1]:
        """selfがSEM_HEADだとして親と述語項関係にあるならそのラベルを返す.

        selfと親自身にラベルがあるとは限らないので長単位から探す

        Returns:
                str: ga, o, ni のどれか
                    Literal[-1]: リンクなかった

        """
        if self.ud_misc["BunsetuPositionType"] != "SEM_HEAD":
            return -1
        parent_word = self.get_parent_word()
        if parent_word is None:
            return -1
        for wrd in self.get_luw_units():
            _link_label = parent_word.get_link(wrd)
            if _link_label != -1:
                # 格情報を抽出 (ga, o, ni)]
                assert isinstance(_link_label, tuple)
                return _link_label[0].name.split(":")[-1]
        return -1

    def get_link_label(self) -> str | Literal[-1]:
        """自分と親とのリンクを確認して返す.

        Returns:
                str: ga, o, ni のどれか  or Literal[-1]: リンクなかった

        """
        parent_word = self.get_parent_word()
        if parent_word is not None:
            _link_label = parent_word.get_link(self)
            if _link_label != -1:
                # 格情報を抽出 (ga, o, ni)]
                assert isinstance(_link_label, tuple)
                return _link_label[0].name.split(":")[-1]
        return -1

    def get_child_words(self) -> list[Word]:
        """Get children words."""
        assert self.doc is not None
        self.child_words = []
        for child_pos in self.doc[self.sent_pos].get_ud_children(self):
            cword = self.doc[self.sent_pos].get_word_from_tokpos(child_pos - 1)
            if cword is None:
                raise KeyError
            self.child_words.append(cword)
        return self.child_words

    def has_space_after(self) -> bool:
        """Has space after."""
        assert self.doc is not None
        sent = self.doc[self.sent_pos]
        wrd_pos = sent.get_pos_from_word(self)
        res = sent.annotation_list.get_segment(wrd_pos)
        if isinstance(res, Segment) and res.get_name() == "space-after:seg":
            value = res.get_attr_value("space-after:value")
            return value is not None
        return False

    def get_udmisc(self, add_unidic_info:bool=True) -> str:
        """Return ud misc text."""
        self.ud_misc["BunsetuBILabel"] = "B" if self.word_pos == 0 else "I"
        if self.luw_label is not None:
            self.ud_misc["LUWBILabel"] = self.luw_label
            self.ud_misc["LUWPOS"] = self.get_luw_pos()
        if self.has_space_after():
            self.ud_misc["SpacesAfter"] = "Yes"
            if "SpaceAfter" in self.ud_misc:
                assert self.ud_misc["SpaceAfter"] == "No"
                del self.ud_misc["SpaceAfter"]
                assert self.ud_misc.get("SpaceAfter") is None
                # SpaceAfter Noを取り除く
            # BCCWJなどのYesを上書きする可能性があるのでNoにはしないこと
        else:
            self.ud_misc["SpaceAfter"] = "No"
            if "SpacesAfter" in self.ud_misc:
                assert self.ud_misc["SpacesAfter"] == "Yes"
                del self.ud_misc["SpacesAfter"]
                assert self.ud_misc.get("SpacesAfter") is None
                # SpacesAfter Yesを取り除く
        if add_unidic_info:
            if self.get_origin() != self.get_origin(do_conv29=True):
                self.ud_misc["PrevUDLemma"] = self.get_origin(do_conv29=True)
            #  lexemes, forms, and orth forms
            self.ud_misc["UnidicInfo"] = self.get_unidic_info()
        return "|".join([
            f"{k}={v}" for k, v in sorted(self.ud_misc.items())
            if self.word_unit_mode == "suw" or (
                self.word_unit_mode == "luw" and k not in ["LUWPOS", "LUWBILabel"]
            )
        ])

    def get_unidic_info(self, delimiter: str=",") -> str:
        """Get Unidic info."""
        return re.sub(r"　　+", "　",
            f"{SUW.get_unidic_info(self, delimiter=delimiter)}"
                    f"{delimiter}{LUW.get_unidic_info(self, delimiter=delimiter)}"
        ).rstrip()

    def get_sent_segment(self) -> Literal[-1] | Segment:
        """Get segment for word."""
        assert self.doc is not None
        sword_pos = self.doc[self.sent_pos].get_pos_from_word(self)
        if self.doc[self.sent_pos].annotation_list is not None:
            return cast("AnnotationList",
                        self.doc[self.sent_pos].annotation_list).get_segment(sword_pos)
        raise KeyError

    def convert(self, sep: str="\t") -> str:
        """Convert word line."""
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

    def build_luw_unit(self, luw_unit: list[Word], suw_delimter: str=";") -> None:
        """Build LUW Unit."""
        assert self.word_unit_mode == "luw", "differ mode: " + self.word_unit_mode
        self._token[0] = self.get_surface()
        if luw_unit is None:
            self._token[1] = ",".join(self.get_features())
        else:
            self._token[1] = ",".join([
                suw_delimter.join([f.replace(suw_delimter, "\\"+suw_delimter) for f in fes])
                for fes in zip(*[SUW.get_features(suw) for suw in luw_unit])
            ])
            self.features = self._token[1].split(",")

    def get_surface(self) -> str:
        """Get Surface."""
        if self.word_unit_mode == "luw":
            return LUW.get_surface(self)
        if self.word_unit_mode == "suw":
            return SUW.get_surface(self)
        raise NotImplementedError

    def get_origin(self, do_conv29:bool=False) -> str:
        """Get Origin."""
        if self.word_unit_mode == "luw":
            return LUW.get_origin(self, do_conv29=do_conv29)
        if self.word_unit_mode == "suw":
            return SUW.get_origin(self, do_conv29=do_conv29)
        raise NotImplementedError

    def get_xpos(self) -> str:
        """Get XPOS."""
        if self.word_unit_mode == "luw":
            return LUW.get_xpos(self)
        if self.word_unit_mode == "suw":
            return SUW.get_xpos(self)
        raise NotImplementedError

    def get_luw_pos(self) -> str:
        """Get LUW POS."""
        if self.luw_pos is not None:
            return self.luw_pos
        return self.get_xpos()

    def get_katuyo(self) -> str:
        """Get katuyo."""
        if self.word_unit_mode == "luw":
            return LUW.get_katuyo(self)
        if self.word_unit_mode == "suw":
            return SUW.get_katuyo(self)
        raise NotImplementedError

    def get_features(self) -> list[str]:
        """Get features."""
        if self.word_unit_mode == "luw":
            return LUW.get_features(self)
        if self.word_unit_mode == "suw":
            return SUW.get_features(self)
        raise NotImplementedError
