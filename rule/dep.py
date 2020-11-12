# -*- coding: utf-8 -*-

"""
BCCWJ DepParaPAS rule function
"""

import sys
import re
import functools

import ruamel.yaml

from rule import dep_rule_func

TARGET_DEP_RULE = None
DEP_RULE_FILE = {
    # word unit mapping
    "bccwj_suw": "conf/bccwj_dep_suw_rule.yaml",
    "bccwj_luw": "conf/bccwj_dep_suw_rule.yaml",
    "chj_suw": "conf/bccwj_dep_suw_rule.yaml",
    "gsd_suw": "conf/bccwj_dep_suw_rule.yaml"
}
SELECT_TARGET_WORD_POSITION = {
    # 必ずリストになるように
    "word": lambda x: [x] if x is not None else None,
    "parent": lambda x: [x.parent_word] if x is not None else None,
    "child": lambda x: x.child_words if x is not None else None,
    "parentchild": lambda x: x.parent_word.get_child_words() if x is not None and x.parent_word is not None else None,
    "semhead": lambda x: [x.sem_head_word] if x is not None else None,
    "synhead": lambda x: [x.syn_head_word] if x is not None else None
}


def check_funcname(func_name, rule_set):
    """
        check valid function name
    """
    _func_name = func_name.split("_")
    if len(_func_name) != 3:
        raise KeyError("{} is not valid name, function name is separated by `_`".format(func_name))
    if _func_name[0] not in rule_set["func"]:
        raise NotImplementedError("{} is not valid name, or not implemented {}".format(func_name, _func_name[0]))
    if _func_name[1] not in SELECT_TARGET_WORD_POSITION:
        raise NotImplementedError("{} is not valid name, or not implemented {}".format(func_name, _func_name[1]))
    if (_func_name[0], _func_name[2]) not in dep_rule_func.DEP_RULE_FUNC_LIST:
        raise NotImplementedError("{} is not valid name, or not implemented {}".format(func_name, (_func_name[0], _func_name[2])))
    return _func_name


def load_dep_rule(data_type, word_unit):
    """
        load rule file
    """
    yaml = ruamel.yaml.YAML()
    rule_set = yaml.load(open(DEP_RULE_FILE[data_type + "_" + word_unit]).read().replace('\t', '    '))
    full_rule_set = []
    for rule_pair in rule_set["order_rule"]:
        sub_rules = []
        for func_name, elem_arg in rule_pair["rule"]:
            func, args, elements = check_funcname(func_name, rule_set)
            # _func_name: (func, args, elements)
            ifunc = dep_rule_func.DEP_RULE_FUNC_LIST[(func, elements)]
            # elementsをifuncに適応
            ifunc = functools.partial(ifunc, **{elements: elem_arg})
            iargs = SELECT_TARGET_WORD_POSITION[args]
            str_func = "_".join([func, args, elements]) + "(" + str(elem_arg) + ")"
            sub_rules.append((ifunc, iargs, str_func))
        full_rule_set.append((sub_rules, rule_pair["res"]))
    return full_rule_set


def select_target_word(word, target_label):
    assert target_label in SELECT_TARGET_WORD_POSITION
    return SELECT_TARGET_WORD_POSITION[target_label](word)


def detect_ud_label(word, debug=False):
    """
        detect ud label
    """
    global TARGET_DEP_RULE
    if TARGET_DEP_RULE is None:
        TARGET_DEP_RULE = list(load_dep_rule(word.data_type, word.word_unit))
    word.dep_label = "_undef_"
    # word
    word.parent_word = word.get_parent_word()
    word.child_words = word.get_child_words()
    word.sem_head_word = word.get_bunsetu_position_word("SEM_HEAD")
    word.syn_head_word = word.get_bunsetu_position_word("SYN_HEAD")
    word.link_label = word.get_link_label()
    # word.case_set = word.get_surface_case()
    for rule_pos, rule_data in enumerate(list(TARGET_DEP_RULE)):
        rule_list, en_rel = rule_data
        flag_lst, rule_name_str = [], []
        for ifunc, iargs, str_func in rule_list:
            arg = iargs(word)
            flag_lst.append(functools.partial(ifunc, self=word, word=arg)())
            rule_name_str.append(str_func)
        if all(flag_lst):
            word.dep_label = en_rel
            if debug:
                sys.stdout.write("\n")
                sys.stdout.write("{}\n".format(str(word)))
                sys.stdout.write("{}:{} -> {}\n".format(rule_pos, rule_name_str, en_rel))
                sys.stdout.write("\n")
            break
    if word.dep_label == "_undef_":
        word.dep_label = "dep"
