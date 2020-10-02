# -*- coding: utf-8 -*-

"""
BCCWJ DepParaPAS rule function
"""

import re
import json
from rule import dep_rule_func

TARGET_RULE = {"pos": None, "dep": None}
DEP_RULE_FILE = {
    # word unit mapping
    "bccwj_suw": "conf/bccwj_dep_suw_rule.json",
    "bccwj_luw": "conf/bccwj_dep_luw_rule.json",
    "chj_suw": "conf/bccwj_dep_suw_rule.json",
    "gsd_suw": "conf/bccwj_dep_suw_rule.json"
}


def load_dep_rule(data_type, word_unit):
    """
        load rule file
    """
    rule_set = json.load(open(DEP_RULE_FILE[data_type + "_" + word_unit]))
    full_rule_set = []
    for rule_pair in rule_set["rule"]:
        rrr = [
            (dep_rule_func.DEP_RULE_FUNC_LIST[func], arg)
            for func, arg in rule_pair["rule"]
        ]
        full_rule_set.append((rrr, rule_pair["res"]))
    return full_rule_set


def _get_link_label(word, parent_word):
    link_label = -1
    if parent_word is not None:
        link_label = parent_word.get_link(word)
    if link_label != -1:
        # 格情報を抽出 (ga, o, ni)]
        link_label = link_label[0].name.split(":")[-1]
    return link_label


def _get_surface_case(word):
    case = {}
    for child_pos in word.doc[word.sent_pos].get_ud_children(word):
        cword = word.doc[word.sent_pos].get_word_from_tokpos(child_pos - 1)
        if re.match("助詞-[係格副]助詞", cword.get_xpos()):
            case[cword.get_jp_origin()] = None
    return case


def detect_ud_label(word):
    """
        TODO: make_udep_label見ながら実装
    """
    word.dep_label = "_undef_"
    parent_word = word.get_parent_word()
    word.link_label = _get_link_label(word, parent_word)
    word.case_set = _get_surface_case(word)
    if TARGET_RULE["dep"] is None:
        TARGET_RULE["dep"] = list(load_dep_rule(word.data_type, word.word_unit))
    for rule, en_rel in list(TARGET_RULE["dep"]):
        flag_lst = []
        for func, args in rule:
            aaa = []
            for arg in args:
                if arg == "word":
                    aaa.append(word)
                elif arg == "parent_word":
                    aaa.append(parent_word)
                else:
                    aaa.append(arg)
            flag_lst.append(func(*aaa))
        if all(flag_lst):
            word.dep_label = en_rel
            break
    if word.dep_label == "_undef_":
        word.dep_label = "dep"
