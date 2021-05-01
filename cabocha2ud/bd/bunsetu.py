# -*- coding: utf-8 -*-

"""
Bunsetu class
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING
import bisect

if TYPE_CHECKING:
    from .word import Word
from .word import SUW, CHJSUW


class Bunsetu(list):
    """
        bunsetu class: bunsetu class is word list
    """
    self: list["Word"]

    EX_WORD_CLASS = {
        ("bccwj", "suw"): SUW,
        ("chj", "suw"): CHJSUW, ("chj", "luw"): CHJSUW,
        ("gsd", "suw"): SUW
    }
    def __init__(
            self, data_type: str, sent_pos: int, bunsetu,
            base_file_name: Optional[str]=None, debug=False,
            word_unit="suw", prev_bunsetu=None
    ):
        super().__init__(self)
        self.base_file_name: Optional[str] = base_file_name
        self.data_type: str = data_type
        self.word_unit: str = word_unit
        self.debug: bool = debug
        self.bunsetu_pos: Optional[int] = None
        self.bunsetu_type: Optional[str] = None
        self.dep_type: Optional[str] = None
        self.dep_pos: Optional[int] = None
        self.subj_pos: int = -1
        self.func_pos: int = -1
        self.is_loop = False
        self.prev_bunsetu: Optional[Bunsetu] = prev_bunsetu
        self.__parse(bunsetu, sent_pos)

    def get_header(self) -> str:
        """
            get the bunsetu's header
        """
        if self.data_type == "bccwj":
            dep_num = "0.000000"
        else:
            dep_num = "0"
        org = "* {} {}{} {}/{} {}".format(
            self.bunsetu_pos, self.dep_pos, self.dep_type,
            self.subj_pos + 1, self.func_pos + 1, dep_num
        )
        return org

    def __str__(self) -> str:
        return self.get_header() + "\n" + "\n".join([
            str(word) for word in self.words()
        ])

    def words(self) -> list[Word]:
        """
            get words
        """
        return self

    def is_inner_brank_word(self, pos: int) -> bool:
        """
        文節のなかで位置tはカッコ内部かどうか
        あくまで文節の中なので、文節外までみて確認しない

        Args:
            pos (int): カッコ内部なのか確認したい位置

        Returns:
            bool: 文節からみてカッコ内部である
        """
        kakko_res = [
            (wpos, wrd.get_xpos().replace("補助記号-括弧", ""))
            for wpos, wrd in enumerate(self.words())
            if wrd.get_xpos().startswith("補助記号-括弧")
        ]
        assert all([c in ["開", "閉"] for _, c in kakko_res])
        if len(kakko_res) == 0:  # かっこがないので
            return False
        tpos = bisect.bisect(kakko_res, (pos, "対"))
        if tpos == 0:
            # 「？, ）」で並んでいるならカッコ内部
            return kakko_res[0][1] == "閉"
        elif tpos == len(kakko_res):
            # 「（, ？」で並んでいるならカッコ内部
            return kakko_res[len(kakko_res)-1][1] == "開"
        else:
            tem_pos = tpos
            while tem_pos > 0:
                if kakko_res[tem_pos][1] == "開":
                    return True
                tem_pos = tem_pos - 1
            tem_pos = tpos
            while tem_pos < len(kakko_res):
                if kakko_res[tem_pos][1] == "閉":
                    return True
                tem_pos = tem_pos + 1
            return False

    def __parse(self, bunsetu_lines: list[str], sent_pos) -> None:
        from ..rule.bunsetu_rule import detect_bunsetu_pos, NUM_RE
        nbunsetu_lines = bunsetu_lines[:]
        # dep info
        if (attributes := NUM_RE.match(nbunsetu_lines[0])):
            self.bunsetu_pos = int(attributes.group(1))
            self.dep_pos = int(attributes.group(2))
            self.dep_type = attributes.group(3)
        if self.dep_pos == self.bunsetu_pos:
            # ループ、NO_HEAD
            self.is_loop = True
        for pos, token in enumerate(nbunsetu_lines[1:]):
            if (self.data_type, self.word_unit) not in self.EX_WORD_CLASS:
                raise NotImplementedError(self.data_type, self.word_unit)
            wrd_cls = self.EX_WORD_CLASS[(self.data_type, self.word_unit)]
            self.append(wrd_cls(
                base_file_name=self.base_file_name,
                data_type=self.data_type, sent_pos=sent_pos,
                bunsetu_pos=self.bunsetu_pos, word_pos=pos, token=token,
                bunsetu=self, word_unit=self.word_unit
            ))
        detect_bunsetu_pos(self)
        if self.subj_pos == -1 and self.func_pos == -1:
            for word in self.words():
                word.set_bunsetsu_info(None, None)
        elif self.subj_pos == -1 or self.func_pos == -1:
            # NO_HEADかも怪しいのでほぼ強制的に文節を付与
            detect_bunsetu_pos(self)
            for word in self.words():
                word.set_bunsetsu_info(
                    self.subj_pos == word.word_pos, self.func_pos == word.word_pos
                )
        else:
            for word in self.words():
                word.set_bunsetsu_info(
                    self.subj_pos == word.word_pos, self.func_pos == word.word_pos
                )


