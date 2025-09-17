# -*- coding: utf-8 -*-

"""
BCCWJ DepParaPAS remove multi obj
"""

import argparse
from dataclasses import dataclass
from typing import TypedDict, cast

import tomli

from cabocha2ud.bd.sentence import Sentence
from cabocha2ud.bd.word import Word

REPLACE_OBJ_RULE_FILE = "conf/rule_objcase_list.toml"

class IsCase(TypedDict):
    """ is case 
    [[rule.condition.is_case]]
    pos = 0
    case = ["は"]
    """
    pos: int
    case: list[str]


class Condition(TypedDict):
    """ condition 
    [[rule.condition]]
    size = 3
    [[rule.condition.is_case]]
    pos = 1
    case = ["も"]
    """
    size: int
    is_case: list[IsCase]


class Eval(TypedDict):
    """ eval 
    [[rule.eval]]
    pos = 2
    dep = "obj"
    """
    pos: int
    dep: str


@dataclass
class Rule:
    """ rule """
    condition: Condition
    eval: list[Eval]

    @classmethod
    def to_obj(cls, dic: dict) -> "Rule":
        """ rule """
        rrs = cls(
            condition=Condition(
                size=dic["condition"]["size"],
                is_case=[IsCase(pos=c["pos"], case=c["case"]) for c in dic["condition"]["is_case"]]
            ),
            eval=[Eval(pos=e["pos"], dep=e["dep"]) for e in dic["eval"]]
        )
        assert rrs.check_valid_rule()
        return rrs

    def check_valid_rule(self) -> bool:
        """ check valid rule """
        return all(isc["pos"] < self.condition["size"] for isc in self.condition["is_case"])

    def adapt_rule(self, wrd: list[Word]) -> bool:
        """ Wordにたいして結果を返す """
        if len(wrd) != self.condition["size"]:
            return False
        if not all(is_case(wrd, isc["pos"], isc["case"]) for isc in self.condition["is_case"]):
            return False
        for evl in self.eval:
            assert wrd[evl["pos"]].dep_label is not None
            wrd[evl["pos"]].dep_label = evl["dep"] if evl["dep"] != ":outer"\
                else cast(str, wrd[evl["pos"]].dep_label) + ":outer"
        return True


REP_OBJ_RULES: list[Rule] = []
with open(REPLACE_OBJ_RULE_FILE, "r", encoding="utf-8") as rdr:
    REP_OBJ_RULES = [Rule.to_obj(jdict) for jdict in tomli.loads(rdr.read())["rule"]]


def is_case(toks: list[Word], tpos: int, case_lst: list[str]) -> bool:
    """ remove multi object """
    # print(toks[tpos].get_surface_case(), case_lst)
    if len(toks[tpos].get_surface_case()) != len(case_lst):
        return False
    return all(case in toks[tpos].get_surface_case() for case in case_lst)


def adapt_obj_to_dislocated_rule(sent: Sentence) -> None:
    """
        objの中で指定のものをiobjに
    """
    parent_obj_pos: dict[int, list[int]] = {}
    for word in sent.words():
        # nsubj/csubjの数を調べる
        if word.dep_num is None:
            continue
        if word.dep_label in ["obj"]:
            if not word.dep_num in parent_obj_pos:
                parent_obj_pos[word.dep_num] = []
            parent_obj_pos[word.dep_num].append(word.token_pos)
    if len(parent_obj_pos) == 0:
        return
    #print(sent.sent_id, parent_obj_pos)
    for _, ctok_pos_lst in list(parent_obj_pos.items()):
        toks = [cast(Word, sent.get_word_from_tokpos(ctok-1)) for ctok in ctok_pos_lst]
        for rep_rule in REP_OBJ_RULES:
            if rep_rule.adapt_rule(toks):
                break


def _main() -> None:
    """
        main function
    """
    parser = argparse.ArgumentParser(description='')
    _ = parser.parse_args()
    for rule in REP_OBJ_RULES:
        print(rule)


if __name__ == '__main__':
    _main()
