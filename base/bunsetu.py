# -*- coding: utf-8 -*-

"""
Bunsetu class
"""

from base.component import Component
from base.word import SUW, CHJSUW, LUW, CHJLUW, GSDSUW
from rule.bunsetu import detect_bunsetu_pos_each, NUM_RE


EX_WORD_CLASS = {
    ("bccwj", "suw"): SUW, ("bccwj", "luw"): LUW,
    ("chj", "suw"): CHJSUW, ("chj", "luw"): CHJLUW,
    ("gsd", "suw"): GSDSUW
}


def convert_wordunit(data_type, word_unit, bunsetu_lines, luw_sep=";"):
    """
        文節のテキストラインを変換する
        これは 入力フォーマットがSUWでかつ、LUWに変換するときだけ使う
        LUWはluw_sep(";")で区切る
    """
    if word_unit == "luw":
        luw_line_num = -1
        # 文節 ⊃ LUWのはずなので先頭はBのはず
        # chjとbccjwで見る列番号が違う
        if data_type == "bccwj":
            luw_line_num = 2
        elif data_type == "chj":
            raise NotImplementedError
            # 問題点; 3にはLUW情報がない？
            # luw_line_num = 3
        else:
            raise NotImplementedError
        print(bunsetu_lines[1].split("\t"))
        assert luw_line_num != -1 and bunsetu_lines[1].split("\t")[luw_line_num] == "B"
        nlst = [bunsetu_lines[1]]
        for line in bunsetu_lines[2:]:
            bst = line.split("\t")
            assert bst[luw_line_num] in ["B", "I"]
            if bst[luw_line_num] == "B":
                nlst.append(line)
            else:
                nlst[-1] = nlst[-1] + luw_sep + line
        return [bunsetu_lines[0]] + nlst
    return bunsetu_lines[:]


class Bunsetu(Component, list):
    """
        bunsetu class: bunsetu class is word list
    """

    def __init__(
            self, data_type, sent_pos, bunsetu,
            base_file_name=None,
            is_use_bunsetu_num=False, bunsetu_func="none",
            word_unit="suw", prev_bunsetu=None
    ):
        super(Bunsetu, self).__init__(
            data_type, base_file_name=base_file_name,
            bunsetu_func=bunsetu_func, word_unit=word_unit
        )
        self.is_use_bunsetu_num = is_use_bunsetu_num
        self.bunsetu_pos = None
        self.dep_type = None
        self.dep_pos = None
        self.subj_pos = None
        self.func_pos = None
        self.is_loop = False
        self.prev_bunsetu = prev_bunsetu
        self.__parse(bunsetu, sent_pos)

    def get_header(self):
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

    def __unicode__(self):
        return self.get_header() + "\n" + "\n".join([
            str(word) for word in self.words()
        ])

    def convert(self, sep="", is_skip_space=True):
        raise NotImplementedError

    def words(self):
        """
            get words
        """
        return self

    def __detect_for_bunsetu_pos(self):
        if self.bunsetu_func == "none":
            detect_bunsetu_pos_each(self, "type2")
        else:
            detect_bunsetu_pos_each(self, func_type=self.bunsetu_func)

    def __parse(self, bunsetu_lines, sent_pos):
        nbunsetu_lines = convert_wordunit(
            self.data_type, self.word_unit, bunsetu_lines
        )
        # dep info
        attributes = NUM_RE.match(nbunsetu_lines[0]).groups()
        self.bunsetu_pos = int(attributes[0])
        self.dep_pos = int(attributes[1])
        self.dep_type = attributes[2]
        if self.dep_pos == self.bunsetu_pos:
            # ループ、NO_HEAD
            self.is_loop = True
        for pos, token in enumerate(nbunsetu_lines[1:]):
            if (self.data_type, self.word_unit) not in EX_WORD_CLASS:
                raise NotImplementedError(self.data_type, self.word_unit)
            wrd_cls = EX_WORD_CLASS[(self.data_type, self.word_unit)]
            self.append(wrd_cls(
                base_file_name=self.base_file_name,
                data_type=self.data_type, sent_pos=sent_pos,
                bunsetu_pos=self.bunsetu_pos, word_pos=pos, token=token,
                bunsetu=self, word_unit=self.word_unit
            ))
        if self.is_use_bunsetu_num and self.word_unit == "suw":
            if self.data_type == "bccwj":
                self.subj_pos = int(attributes[3]) - 1
                self.func_pos = int(attributes[4]) - 1
            elif self.data_type == "gsd":
                self.subj_pos = int(attributes[3])
                self.func_pos = int(attributes[4])
        else:
            self.__detect_for_bunsetu_pos()
        if self.subj_pos == -1 and self.func_pos == -1:
            for word in self.words():
                word.set_bunsetsu_info(None, None)
        elif self.subj_pos == -1 or self.func_pos == -1:
            # NO_HEADかも怪しいのでほぼ強制的に文節を付与
            detect_bunsetu_pos_each(self, func_type="type2")
            for word in self.words():
                word.set_bunsetsu_info(
                    self.subj_pos == word.word_pos, self.func_pos == word.word_pos
                )
        else:
            for word in self.words():
                word.set_bunsetsu_info(
                    self.subj_pos == word.word_pos, self.func_pos == word.word_pos
                )
