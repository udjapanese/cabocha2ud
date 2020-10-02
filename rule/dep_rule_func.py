# -*- coding: utf-8 -*-

"""
BCCWJ DepParaPAS rule function
"""

import re

BPOS_LIST = set([
    "SEM_HEAD", "SYN_HEAD", "CONT", "ROOT", "FUNC", "NO_HEAD"
])

DEP_RULE_FUNC_LIST = {}


def is_disfluency(word):
    """
        いいよどみがあるか？
    """
    s_seg = word.get_sent_segment()
    return s_seg != -1 and s_seg.name == "Disfluency"
DEP_RULE_FUNC_LIST["is_disf"] = is_disfluency


def is_appos(word, parent_word):
    """
        かかり関係であるかどうか
    """
    if word is None or parent_word is None:
        return False
    sent = word.get_sentence()
    word1_pos = sent.get_pos_from_word(word)
    word2_pos = sent.get_pos_from_word(parent_word)
    res = sent.annotation_list.get_appos(word1_pos, word2_pos)
    return res != -1
DEP_RULE_FUNC_LIST["appos"] = is_appos


def is_conj(word, parent_word):
    """
        conj関係なのか？
    """
    if word is None or parent_word is None:
        return False
    sent = word.get_sentence()
    word1_pos = sent.get_pos_from_word(word)
    word2_pos = sent.get_pos_from_word(parent_word)
    res = sent.annotation_list.get_conj(word1_pos, word2_pos)
    return res != -1
DEP_RULE_FUNC_LIST["conj"] = is_conj


def check_dep_num(word, dep_num):
    """
         その単語のdep_numであるかどうか
    """
    if word is None:
        return False
    return word.dep_num == dep_num
DEP_RULE_FUNC_LIST["check_dep"] = check_dep_num


def is_katuyo(word, target_katuyo):
    """
         その単語はその活用形を持つ
    """
    if word is None:
        return False
    return target_katuyo in word.get_katuyo()
DEP_RULE_FUNC_LIST["katuyo"] = is_katuyo


def is_match_xpos(word, target_xpos):
    """
        その単語はXPOSを持っている
    """
    if word is None:
        return False
    return re.match(target_xpos, word.get_xpos())
DEP_RULE_FUNC_LIST["match_xpos"] = is_match_xpos


def is_match_luwpos(word, target_xpos):
    """
        その単語は長単位品詞を持っている
    """
    if word is None:
        return False
    return re.match(target_xpos, word.luw_pos)
DEP_RULE_FUNC_LIST["match_luwpos"] = is_match_luwpos


def include_bpos(word, target_bpos):
    """
        その単語はそのBPOSの範囲である
    """
    assert set(target_bpos).issubset(BPOS_LIST)
    if word is None:
        return False
    return word.ud_misc["BunsetuPositionType"] in target_bpos
DEP_RULE_FUNC_LIST["include_bpos"] = include_bpos


def include_upos(word, target_upos):
    """
       その単語はUPOSを持っている
    """
    if word is None:
        return False
    return word.get_ud_pos() in target_upos
DEP_RULE_FUNC_LIST["include_upos"] = include_upos


def include_child_xpos(word, xpos):
    """
        かかられている単語の中にxposを持つ単語があるか否か
    """
    if word is None:
        return False
    for child_pos in word.doc[word.sent_pos].get_ud_children(word):
        cword = word.doc[word.sent_pos].get_word_from_tokpos(child_pos - 1)
        if re.match(xpos, cword.get_xpos()):
            return True
    return False
DEP_RULE_FUNC_LIST["include_child_xpos"] = include_child_xpos


def include_child_upos(word, target_upos):
    """
        かかられている単語の中に該当UPOSを持つ単語があるか否か
    """
    if word is None:
        return False
    for child_pos in word.doc[word.sent_pos].get_ud_children(word):
        cword = word.doc[word.sent_pos].get_word_from_tokpos(child_pos - 1)
        if cword.get_ud_pos() in target_upos:
            return True
    return False
DEP_RULE_FUNC_LIST["include_child_upos"] = include_child_upos


def is_match_suffix_string(word, re_str):
    """
       その単語からの末尾がre_str表現である
    """
    if word is None:
        return False
    bunmatu_str = "".join([
        w.surface for w in word.bunsetu[word.word_pos+1:]
    ])
    return re.match(re_str, bunmatu_str)
DEP_RULE_FUNC_LIST["match_suffix_string"] = is_match_suffix_string


def is_include_link(word):
    """
        include link information ?
    """
    return word.link_label != -1
DEP_RULE_FUNC_LIST["include_link"] = is_include_link


def include_jp_origin(word, jp_origin_list):
    """
        その単語はjp_origin_listである
    """
    if word is None:
        return False
    return word.get_jp_origin() in jp_origin_list
DEP_RULE_FUNC_LIST["include_jp_origin"] = include_jp_origin


def include_child_case(word, target_case):
    """
        かかられている単語の中にcaseがあるか否か
    """
    case_set = word.case_set
    flag = False
    for case in target_case:
        if case in case_set:
            flag = True
    return flag
DEP_RULE_FUNC_LIST["include_child_case"] = include_child_case


def _main():
    for key, value in list(DEP_RULE_FUNC_LIST.items()):
        print("{}\t{}".format(key, value))


if __name__ == '__main__':
    _main()
