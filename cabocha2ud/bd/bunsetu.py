# -*- coding: utf-8 -*-

"""
Bunsetu class
"""

from __future__ import annotations

import bisect
import copy
import re
from typing import TYPE_CHECKING, Any, Optional, Pattern, cast

if TYPE_CHECKING:
    from .word import Word
    from .sentence import Sentence

from cabocha2ud.rule.bunsetu_rule import detect_bunsetu_pos

from ..lib.logger import Logger
from .word import Word

NUM_RE: Pattern[str] = re.compile(r"\* (\d+) (-?\d+)([A-Z][A-Z]?) (\d+)/(\d+)( (.+))?$")


class Bunsetu(list["Word"]):
    """
        bunsetu class: bunsetu class is word list
    """

    def __init__(
            self, sent_pos: int, bunsetu: list[str],
            base_file_name: Optional[str]=None, debug=False,
            prev_bunsetu=None, parent_sent=None, logger: Optional[Logger]=None,
            word_unit_mode: str="suw"
    ):
        super().__init__(self)
        self.base_file_name: Optional[str] = base_file_name
        self.debug: bool = debug
        self.logger: Logger = logger or Logger()
        self.word_unit_mode = word_unit_mode

        self.sent_pos = sent_pos
        self.bunsetu_pos: Optional[int] = None
        self.bunsetu_append_info: Optional[str] = None
        self.bunsetu_type: Optional[str] = None
        self.dep_type: Optional[str] = None
        self.dep_pos: Optional[int] = None
        self.subj_pos: int = -1
        self.func_pos: int = -1
        self.is_loop = False
        self.parent_sent: Optional[Sentence] = parent_sent
        self.prev_bunsetu: Optional[Bunsetu] = prev_bunsetu
        self.__parse(bunsetu, sent_pos)

    def set_sent(self, parent_sent: Sentence):
        """ set sentence parent """
        self.parent_sent = parent_sent

    def get_header(self) -> str:
        """
            get the bunsetu's header
        """
        org = "* {} {}{} {}/{}{}".format(
            self.bunsetu_pos, self.dep_pos, self.dep_type,
            self.subj_pos, self.func_pos,
            " " + self.bunsetu_append_info if self.bunsetu_append_info is not None else ""
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
        return list(self)

    def is_inner_brank_word(self, pos: int) -> bool:
        """
        文節のなかで位置tはカッコ内部かどうか
        あくまで文節の中なので、文節外までみて確認しない

        Args:
            pos (int): カッコ内部なのか確認したい位置

        Returns:
            bool: 文節からみてカッコ内部である
        """
        kakko_res: list[tuple[int, str]] = [
            (wpos, wrd.get_xpos().replace("補助記号-括弧", ""))
            for wpos, wrd in enumerate(self.words())
            if wrd.get_xpos().startswith("補助記号-括弧")
        ]
        assert all(c in ["開", "閉"] for _, c in kakko_res)
        if len(kakko_res) == 0:  # かっこがないので
            return False
        tpos = bisect.bisect(kakko_res, (pos, "対"))
        if tpos == 0:
            # 「？, ）」で並んでいるならカッコ内部
            return kakko_res[0][1] == "閉"
        if tpos == len(kakko_res):
            # 「（, ？」で並んでいるならカッコ内部
            return kakko_res[len(kakko_res)-1][1] == "開"
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

    def __parse(self, bunsetu_lines: list[str], sent_pos: int) -> None:
        """ parse bunsetu line """
        nbunsetu_lines = bunsetu_lines[:]
        # dep info
        if (attributes := NUM_RE.match(nbunsetu_lines[0])):
            self.bunsetu_pos = int(attributes.group(1))
            self.dep_pos = int(attributes.group(2))
            self.dep_type = attributes.group(3)
            self.subj_pos = int(attributes.group(4))
            self.func_pos = int(attributes.group(5))
            self.bunsetu_append_info = attributes.group(7)
        if self.dep_pos == self.bunsetu_pos:
            # ループ、NO_HEAD
            self.is_loop = True
        for pos, token in enumerate(nbunsetu_lines[1:]):
            _ddd: dict[str, Any] = {
                "base_file_name": self.base_file_name,
                "sent_pos": sent_pos,
                "bunsetu_pos": self.bunsetu_pos,
                "word_pos": pos, "token": token,
                "word_unit_mode": self.word_unit_mode,
                "bunsetu": self, "logger": self.logger
            }
            self.append(Word(**_ddd))

    def update_bunsetu_pos(self):
        """ update bunset position """
        detect_bunsetu_pos(self)
        if self.subj_pos == -1 and self.func_pos == -1:
            for word in self.words():
                word.set_bunsetsu_info(None, None)
        else:
            for word in self.words():
                word.set_bunsetsu_info(
                    self.subj_pos == word.word_pos, self.func_pos == word.word_pos
                )

    def build_luw_unit(self):
        """ 最初の文節の単語だけを抜いて長単位とする
        """
        assert self.word_unit_mode == "luw", "differ mode: " + self.word_unit_mode
        new_lst: list[Word] = []
        for _, luw_unit in enumerate(self.get_luw_list()):
            assert len(luw_unit) > 0
            first_wrd, _ = luw_unit[0], luw_unit[-1]
            first_wrd.word_unit_mode = "luw"
            first_wrd.build_luw_unit(luw_unit=luw_unit)
            new_lst.append(first_wrd)
        self.update_word_list(new_lst)

    def get_luw_list(self) -> list[list[Word]]:
        """ get luw list """
        luw_lst: list[list[Word]] = []
        for wrd in self.words():
            if wrd.word_pos == 0:
                luw_lst.append([wrd])
            elif wrd.luw_label == "B":
                luw_lst.append([])
                luw_lst[-1].append(wrd)
            else:
                luw_lst[-1].append(wrd)
        return luw_lst

    def update_word_list(self, wrd_lst:list[Word]) -> None:
        """ update word list """
        self.clear()
        for wpos, wrd in enumerate(wrd_lst):
            wrd.word_pos = wpos
            wrd.bunsetu_pos = cast(int, self.bunsetu_pos)
            self.append(wrd)
            if self.parent_sent is not None:
                wrd.sent_pos = self.parent_sent.sent_pos
                self.parent_sent.update_word_pos()

    def update_word(self, position: int, wrd:Word) -> None:
        """ update one word """
        assert 0 < position < len(self)
        self[position] = copy.deepcopy(wrd)
        if self.parent_sent is not None:
            wrd.sent_pos = self.parent_sent.sent_pos
            self.parent_sent.update_word_pos()

    def remove_word(self, position: int) -> None:
        """ remove one word """
        assert 0 < position < len(self)
        _ = self.pop(position)
        for wpos, wrd in enumerate(self.words()):
            wrd.word_pos = wpos
