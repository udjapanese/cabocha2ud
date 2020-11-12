# -*- coding: utf-8 -*-

"""
BCCWJ DepParaPAS rule function
"""

import re

BPOS_LIST = set([
    "SEM_HEAD", "SYN_HEAD", "CONT", "ROOT", "FUNC", "NO_HEAD"
])

DEP_RULE_FUNC_LIST = {}

"""
(include|match|regex)(word|parent|child|semhead|synhead)(pos|xpos|lemma|...)
include=複数候補のどれかに一致、match=完全一致、regex=正規表現
word... はターゲットの語からみてどの単語の情報を見るか
pos... は属性名
"""

def register_function(target_func):
    """
        関数名をそのままルール名として登録
    """
    funcname = target_func.__name__.split("_")
    assert len(funcname) == 2
    DEP_RULE_FUNC_LIST[(funcname[0], funcname[1])] = target_func


@register_function
def match_segment(self, word, segment):
    """
        いいよどみがあるか？  match_word_segment("Disfluency")
    """
    if word is None:
        return False
    for wrd in word:
        if wrd is None:
            return False
        s_seg = wrd.get_sent_segment()
        if s_seg != -1 and s_seg.name == segment:
            return True
    return False


def match_groups(self, word, groups):
    """
        基本word=parentしか取らないこととする
    """
    if self is None or word is None:
        return False
    sent = self.get_sentence()
    word1_pos = sent.get_pos_from_word(self)
    word2_pos = sent.get_pos_from_word(word)
    res = sent.get_group(groups, word1_pos, word2_pos)
    return res != -1


# @register_function
def is_appos(self, word, parent_word):
    """
        かかり関係であるかどうか ?
    """
    if word is None or parent_word is None:
        return False
    sent = word.get_sentence()
    word1_pos = sent.get_pos_from_word(word)
    word2_pos = sent.get_pos_from_word(parent_word)
    res = sent.annotation_list.get_appos(word1_pos, word2_pos)
    return res != -1


# @register_function
def is_conj(self, word, parent_word):
    """
        conj関係なのか？  ?
    """
    if word is None or parent_word is None:
        return False
    sent = word.get_sentence()
    word1_pos = sent.get_pos_from_word(word)
    word2_pos = sent.get_pos_from_word(parent_word)
    res = sent.annotation_list.get_conj(word1_pos, word2_pos)
    return res != -1


@register_function
def match_depnum(self, word, depnum):
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
def regex_katuyo(self, word, katuyo):
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
def regex_xpos(self, word, xpos):
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
def match_luwpos(self, word, luwpos):
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
def regex_luwpos(self, word, luwpos):
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
def include_bpos(self, word, bpos):
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
def include_upos(self, word, upos):
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
def regex_suffixstring(self, word, suffixstring):
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
def is_include_link(word):
    """
        include link information ?
    """
    if word is None:
        return False
    return word.link_label != -1


@register_function
def match_lemma(self, word, lemma):
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
def regex_lemma(self, word, lemma):
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
def include_lemma(self, word, lemma):
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
def include_case(self, word, case):
    """
        指定したcaseがwordに含まれているか（基本的にinclude_child_caseでしか使わない）
    """
    assert word is None or isinstance(word, list)
    if word is None:
        return False
    for wrd in word:
        if wrd is None:
            return False
        if RE_CASE_MATCH.match(wrd.get_xpos()):
            if wrd.get_jp_origin() in case:
                return True
    return False


def _main():
    for key, value in list(DEP_RULE_FUNC_LIST.items()):
        print("{}\t{}".format(key, value))


if __name__ == '__main__':
    _main()
