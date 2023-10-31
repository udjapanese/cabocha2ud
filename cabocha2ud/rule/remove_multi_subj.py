# -*- coding: utf-8 -*-

"""
BCCWJ DepParaPAS remove multi subj
"""

import argparse
from dataclasses import dataclass
from typing import TypedDict, cast

import tomli

from cabocha2ud.bd.sentence import Sentence
from cabocha2ud.bd.word import Word

REPLACE_NSUBJ_RULE_FILE = "conf/rule_nsubjcase_list.toml"

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


REP_NSUBJ_RULES: list[Rule] = []
with open(REPLACE_NSUBJ_RULE_FILE, "r", encoding="utf-8") as rdr:
    REP_NSUBJ_RULES = [Rule.to_obj(jdict) for jdict in tomli.loads(rdr.read())["rule"]]


def is_case(toks: list[Word], tpos: int, case_lst: list[str]) -> bool:
    """ remove multi subject """
    if len(toks[tpos].get_surface_case()) != len(case_lst):
        return False
    return all(case in toks[tpos].get_surface_case() for case in case_lst)


def adapt_nsubj_to_dislocated_rule(sent: Sentence) -> None:
    """
        nsubj/csubjの中で指定のものをnsubj:outerに
    """
    parent_nsubj_pos: dict[int, list[int]] = {}
    for word in sent.words():
        # nsubj/csubjの数を調べる
        if word.dep_num is None:
            continue
        if word.dep_label in ["nsubj", "csubj"]:
            if not word.dep_num in parent_nsubj_pos:
                parent_nsubj_pos[word.dep_num] = []
            parent_nsubj_pos[word.dep_num].append(word.token_pos)
    if len(parent_nsubj_pos) == 0:
        return
    for _, ctok_pos_lst in list(parent_nsubj_pos.items()):
        toks: list[Word] = [cast(Word, sent.get_word_from_tokpos(ctok-1)) for ctok in ctok_pos_lst]
        cases: list[list[str]] = [list(ctok.get_surface_case()) for ctok in toks]
        nctok_pos_lst: list[int] = []
        for pos, (tok, case) in enumerate(zip(toks, cases)):
            if len(case) > 1:
                tok.dep_label = "obl"
                continue
            nctok_pos_lst.append(ctok_pos_lst[pos])
        ctok_pos_lst = sorted(nctok_pos_lst)
        toks = [cast(Word, sent.get_word_from_tokpos(ctok-1)) for ctok in ctok_pos_lst]
        for rep_rule in REP_NSUBJ_RULES:
            if rep_rule.adapt_rule(toks):
                break
        npos_lst = [t for t in toks if t.dep_label in ["nsubj", "csubj"]]
        if len(npos_lst) >= 2:  # toks確認
            for tok in npos_lst[:-1]:
                tok.dep_label = str(tok.dep_label) + ":outer"


def _main() -> None:
    """
        main function
    """
    parser = argparse.ArgumentParser(description='')
    _ = parser.parse_args()
    for rule in REP_NSUBJ_RULES:
        print(rule)


if __name__ == '__main__':
    _main()
