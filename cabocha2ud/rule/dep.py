# -*- coding: utf-8 -*-

"""
BCCWJ DepParaPAS rule function
"""

import functools
from collections.abc import Callable
from typing import Generator, Optional, Union, cast, TypedDict, NamedTuple

import ruamel.yaml

from ..bd.word import Word
from . import dep_rule_func

class Rule(NamedTuple):
    func_name: str
    elem_arg: Union[int, str, list, set]

class SubRule(NamedTuple):
    ifunc: functools.partial[bool]
    iargs: Callable[[Optional[Word]], Union[None, list[Word]]]
    str_func: str

class RuleInst(TypedDict):
    res: str
    rule: list[Rule]

class RuleBase(TypedDict):
    func: list[str]
    args: list[str]
    elements: list[str]
    order_rule: list[RuleInst]


SELECT_TARGET_WORD_POSITION: dict[str, Callable[[Optional[Word]], Union[None, list[Word]]]] = {
    # 必ずリストになるように
    "word": lambda x: [x] if x is not None else None,
    "parent": lambda x: [cast(Word, x.parent_word)] if x is not None else None,
    "child": lambda x: x.child_words if x is not None else None,
    "parentchild": lambda x: x.parent_word.get_child_words() if x is not None and x.parent_word is not None else None,
    "semhead": lambda x: [cast(Word, x.sem_head_word)] if x is not None else None,
    "synhead": lambda x: [cast(Word, x.syn_head_word)] if x is not None else None
}


def check_funcname(func_name: str, rule_set: RuleBase) -> list[str]:
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


def load_dep_rule(file_name: str) -> list[tuple[list[SubRule], str]]:
    """
        load rule file
    """
    yaml = ruamel.yaml.YAML()
    rule_set: RuleBase = yaml.load(open(file_name).read().replace('\t', '    '))
    full_rule_set: list[tuple[list[SubRule], str]] = []
    for rule_pair in rule_set["order_rule"]:
        sub_rules: list[SubRule] = []
        for func_name, elem_arg in rule_pair["rule"]:
            func, args, elements = check_funcname(func_name, rule_set)
            # _func_name: (func, args, elements)
            # elementsをifuncに適応
            if func == "include":
                assert isinstance(elem_arg, list)
                elem_arg = set(elem_arg)
            # ifunc: Callable[[Word, Any, Any], bool] = dep_rule_func.DEP_RULE_FUNC_LIST[(func, elements)]
            ifunc: functools.partial[bool] = functools.partial(
                dep_rule_func.DEP_RULE_FUNC_LIST[(func, elements)], **{elements: elem_arg}
            )
            iargs: Callable[[Optional[Word]], Union[None, list[Word]]] = SELECT_TARGET_WORD_POSITION[args]
            str_func = "_".join([func, args, elements]) + "(" + str(elem_arg) + ")"
            sub_rules.append(SubRule(ifunc, iargs, str_func))
        full_rule_set.append((sub_rules, rule_pair["res"]))
    return full_rule_set


def select_target_word(word: Word, target_label: str) -> Optional[list[Word]]:
    assert target_label in SELECT_TARGET_WORD_POSITION
    return SELECT_TARGET_WORD_POSITION[target_label](word)


def detect_ud_label(word: Word, target_dep_rule: list[tuple[list[SubRule], str]]) -> None:
    """
        detect ud label
    """
    word.dep_label = "_undef_"
    # word
    word.parent_word = word.get_parent_word()
    word.child_words = word.get_child_words()
    word.sem_head_word = word.get_bunsetu_position_word("SEM_HEAD")
    word.syn_head_word = word.get_bunsetu_position_word("SYN_HEAD")
    for rule_pos, rule_data in enumerate(target_dep_rule):
        rule_list, en_rel = rule_data
        flag_lst: Generator[bool, None, None] = (
            functools.partial(ifunc, self=word, word=iargs(word))()
            for ifunc, iargs, _ in rule_list
        )
        if all(flag_lst):
            word.dep_label = en_rel
            if word.debug:
                rule_name_str: list[str] = [
                    str_func for _, _, str_func in rule_list
                ]
                word.logger.debug("\n")
                word.logger.debug("{}\n".format(str(word)))
                word.logger.debug("{}:{} -> {}\n".format(rule_pos, rule_name_str, en_rel))
                word.logger.debug("\n")
            break
    if word.dep_label == "_undef_":
        word.dep_label = "dep"
