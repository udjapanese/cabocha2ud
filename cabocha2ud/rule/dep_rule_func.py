# -*- coding: utf-8 -*-

"""
BCCWJ DepParaPAS rule function
"""

import re
from collections.abc import Callable
from typing import Optional, List, Any, cast
from ..bd.word import Word
from ..bd.annotation import Segment

BPOS_LIST = set([
    "SEM_HEAD", "SYN_HEAD", "CONT", "ROOT", "FUNC", "NO_HEAD"
])

DEP_RULE_FUNC_LIST: dict[tuple[str, str], Callable[[Word, Any, Any], bool]] = {}

"""
(include|match|regex)(word|parent|child|semhead|synhead)(pos|xpos|lemma|...)
include=複数候補のどれかに一致、match=完全一致、regex=正規表現
word... はターゲットの語からみてどの単語の情報を見るか
pos... は属性名
"""

def register_function(target_func: Callable[[Word, Any, Any], bool]) -> None:
    """
        関数名をそのままルール名として登録
    """
    funcname = target_func.__name__.split("_")
    assert len(funcname) == 2
    DEP_RULE_FUNC_LIST[(funcname[0], funcname[1])] = target_func


@register_function
def match_segment(self: Word, word: Optional[List[Word]], segment: str) -> bool:
    """
        いいよどみがあるか？  match_word_segment("Disfluency")
    """
    if word is None:
        return False
    for wrd in word:
        if wrd is None:
            return False
        s_seg = wrd.get_sent_segment()
        if s_seg == -1:
            return False
        if cast(Segment, s_seg).name == segment:
            return True
    return False


# @register_function
def is_appos(self: Word, word: Word, parent_word: Word) -> bool:
    """
        かかり関係であるかどうか ?
    """
    if word is None or parent_word is None:
        return False
    sent = word.get_sentence()
    word1_pos = sent.get_pos_from_word(word)
    word2_pos = sent.get_pos_from_word(parent_word)
    res: int = sent.annotation_list.get_appos(word1_pos, word2_pos)
    return res != -1


# @register_function
def is_conj(self: Word, word: Word, parent_word: Word) -> bool:
    """
        conj関係なのか？  ?
    """
    if word is None or parent_word is None:
        return False
    sent = word.get_sentence()
    word1_pos = sent.get_pos_from_word(word)
    word2_pos = sent.get_pos_from_word(parent_word)
    res: int = sent.annotation_list.get_conj(word1_pos, word2_pos)
    return res != -1


@register_function
def match_depnum(self: Word, word: Optional[List[Word]], depnum: int) -> bool:
    """
         その単語のdepnumであるかどうか
    """
    assert word is None or isinstance(word, list)
    if word is None:
        return False
    for wrd in word:
        if wrd is None:
            return False
        if wrd.dep_num == depnum:
            return True
    return False


@register_function
def regex_katuyo(self: Word, word: Optional[List[Word]], katuyo: str) -> bool:
    """
         その単語はその活用形を持つ   match_word_katuyou(target_katuyo)
    """
    assert word is None or isinstance(word, list)
    if word is None:
        return False
    for wrd in word:
        if wrd is None:
            return False
        if re.match(katuyo, wrd.get_katuyo()):
            return True
    return False


@register_function
def regex_xpos(self: Word, word: Optional[List[Word]], xpos: str) -> bool:
    """
        その単語はXPOSを持っている   regex_word_xpos(xpos)
    """
    assert word is None or isinstance(word, list)
    if word is None:
        return False
    for wrd in word:
        if wrd is None:
            return False
        if re.match(xpos, wrd.get_xpos()):
            return True
    return False


@register_function
def match_luwpos(self: Word, word: Optional[List[Word]], luwpos: str) -> bool:
    """
        その単語は長単位品詞を持っている   regex_word_luwpos(target_xpos)
    """
    assert word is None or isinstance(word, list)
    if word is None:
        return False
    for wrd in word:
        if wrd is None:
            return False
        if wrd.luw_pos == luwpos:
            return True
    return False


@register_function
def regex_luwpos(self: Word, word: Optional[List[Word]], luwpos: str) -> bool:
    """
        その単語は長単位品詞を持っている   regex_word_luwpos(target_xpos)
    """
    assert word is None or isinstance(word, list)
    if word is None:
        return False
    for wrd in word:
        if wrd is None:
            return False
        if re.match(luwpos, wrd.luw_pos):
            return True
    return False

@register_function
def match_bpos(self: Word, word: Optional[List[Word]], bpos: str) -> bool:
    """
        その単語はそのBPOSの範囲である   include_word_bpos(target_bpos)
    """
    assert word is None or isinstance(word, list)
    if word is None:
        return False
    for wrd in word:
        if wrd is None:
            return False
        if wrd.ud_misc["BunsetuPositionType"] == bpos:
            return True
    return False


@register_function
def include_bpos(self: Word, word: Optional[List[Word]], bpos: List[str]) -> bool:
    """
        その単語はそのBPOSの範囲である   include_word_bpos(target_bpos)
    """
    assert word is None or isinstance(word, list)
    assert set(bpos).issubset(BPOS_LIST)
    if word is None:
        return False
    for wrd in word:
        if wrd is None:
            return False
        if wrd.ud_misc["BunsetuPositionType"] in bpos:
            return True
    return False


@register_function
def include_upos(self, word, upos) -> bool:
    """
       その単語はUPOSを持っている   include_word_upos(target_upos)
    """
    assert word is None or isinstance(word, list)
    if word is None:
        return False
    for wrd in word:
        if wrd is None:
            return False
        if wrd.get_ud_pos() in upos:
            return True
    return False


@register_function
def regex_suffixstring(self, word, suffixstring) -> bool:
    """
       その単語からの末尾がre_str表現である
    """
    assert word is None or isinstance(word, list)
    if word is None:
        return False
    for wrd in word:
        if wrd is None:
            return False
        bunmatu_str = "".join([
            w.surface for w in wrd.bunsetu[wrd.word_pos+1:]
        ])
        if re.match(suffixstring, bunmatu_str):
            return True
    return False


# @register_function
def is_include_link(word: Word) -> bool:
    """
        include link information ?
    """
    if word is None:
        return False
    return word.link_label != -1


@register_function
def match_lemma(self: Word, word: Optional[List[Word]], lemma: str) -> bool:
    """
        その単語の日本語原型はjp_origin_listにある  match_word_lemma()
    """
    assert word is None or isinstance(word, list)
    if word is None:
        return False
    for wrd in word:
        if wrd is None:
            return False
        if wrd.get_origin() == lemma:
            return True
    return False


@register_function
def regex_lemma(self: Word, word: Optional[List[Word]], lemma: str) -> bool:
    """
        その単語の日本語原型はjp_origin_listにある  regex_word_lemma()
    """
    assert word is None or isinstance(word, list)
    if word is None:
        return False
    for wrd in word:
        if wrd is None:
            return False
        if re.match(lemma, wrd.get_origin()):
            return True
    return False


@register_function
def include_lemma(self: Word, word: Optional[List[Word]], lemma: str) -> bool:
    """
        その単語の日本語原型はjp_origin_listにある  include_word_lemma()
    """
    assert word is None or isinstance(word, list)
    if word is None:
        return False
    for wrd in word:
        if wrd is None:
            return False
        if wrd.get_origin() in lemma:
            return True
    return False


RE_CASE_MATCH = re.compile("助詞-[係格副]助詞")
@register_function
def include_case(self: Word, word: Optional[list[Word]], case: list[str]) -> bool:
    """
        指定したcaseがwordに含まれているか（基本的にinclude_child_caseでしか使わない）
        case
    """
    assert word is None or isinstance(word, list)
    if word is None:
        return False
    check_case = [c.split(":") for c in case]
    assert all([1 <= len(c) <=2 for c in check_case]) and all([RE_CASE_MATCH.match(c[1]) for c in check_case if len(c)==2])
    cword = [wrd for wrd in word if wrd.bunsetu_pos == self.bunsetu_pos and self.word_pos < wrd.word_pos]
    for wrd in cword:
        if wrd is None:
            return False
        for ccc in check_case:
            if len(ccc) == 1:
                if RE_CASE_MATCH.match(wrd.get_xpos()) and ccc[0] == wrd.get_jp_origin():
                    return True
            elif len(ccc) == 2:
                if re.match(ccc[1], wrd.get_xpos()) and ccc[0] == wrd.get_jp_origin():
                    return True
    return False


@register_function
def match_busetutype(self: Word, word: Optional[list[Word]], busetutype: str) -> bool:
    assert word is None or isinstance(word, list)
    if word is None:
        return False
    for wrd in word:
        if wrd is None:
            return False
        if wrd.get_bunsetu_jp_type() == busetutype:
            return True
    return False


@register_function
def include_busetutype(self: Word, word: Optional[list[Word]], busetutype: list[str]) -> bool:
    assert word is None or isinstance(word, list)
    if word is None:
        return False
    for wrd in word:
        if wrd is None:
            return False
        if wrd.get_bunsetu_jp_type() in busetutype:
            return True
    return False


FORMULA_LIST: dict[str, Callable[[int, int, int], bool]] = {
    "==": lambda x, y, n: x-y==n,
    ">": lambda x, y, n: x-y>n,
    "<": lambda x, y, n: x-y<n,
    ">=": lambda x, y, n: x-y>=n,
    "<=": lambda x, y, n: x-y<=n,
}
NUM_VRE = re.compile(".*?(\-?[0-9]+)$")
@register_function
def match_disformula(self: Word, word: Optional[list[Word]], disformula: str) -> bool:
    """
    disformula: "X-Y==n"みたいなフォーマット、Xが対象の語、Yが比較の語
        nが正の数なら右主辞であり、負の数なら左主辞
    word: 比較する語のリスト
    """
    assert word is None or isinstance(word, list)
    if word is None:
        return False
    if len(word) > 2:  # 現状parentぐらいしか利用用途がないので
        return False
    rem = NUM_VRE.match(disformula)
    assert(rem is not None)
    target_num_r = rem.groups()[0]
    assert(target_num_r.isdigit())
    disformula = disformula.replace(target_num_r, "")
    assert(disformula.replace("X-Y", "") in FORMULA_LIST)
    formula = disformula.replace("X-Y", "")
    target_num = int(target_num_r, base=10)
    wrd, y_pos = word[0], self.token_pos
    x_pos = wrd.token_pos
    return FORMULA_LIST[formula](x_pos, y_pos, target_num)


def _main() -> None:
    for key, value in list(DEP_RULE_FUNC_LIST.items()):
        print("{}\t{}".format(key, value))


if __name__ == '__main__':
    _main()
