# -*- coding: utf-8 -*-

"""
BCCWJ DepParaPAS remove multi subj
"""
from typing import cast

from ..bd.sentence import Sentence
from ..bd.word import Word


def is_case(tok: Word, case_lst: list[str]) -> bool:
    if len(tok.get_surface_case()) != len(case_lst):
        return False
    return all([case in tok.get_surface_case() for case in case_lst])


def adapt_nsubj_to_dislocated_rule(sent: Sentence) -> None:
    """
        nsubj/csubjの中で指定のものをnsubj:outerに
    """
    parent_nsubj_pos: dict[int, list[int]] = {}
    for word in sent.flatten():
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
        ctok_pos_lst = sorted(ctok_pos_lst)
        toks: list[Word] = [cast(Word, sent.get_word_from_tokpos(ctok-1)) for ctok in ctok_pos_lst]
        cases: list[list[str]] = [[c for c in ctok.get_surface_case()] for ctok in toks]
        nctok_pos_lst: list[int] = []
        if any([len(case) > 1 for case in cases]):
            for pos, (tok, case) in enumerate(zip(toks, cases)):
                if len(case) > 1:
                    tok.dep_label = "obl"
                else:
                    nctok_pos_lst.append(ctok_pos_lst[pos])
        else:
            nctok_pos_lst = ctok_pos_lst[:]
        ctok_pos_lst = sorted(nctok_pos_lst)
        toks = [cast(Word, sent.get_word_from_tokpos(ctok-1)) for ctok in ctok_pos_lst]
        sent.logger.debug(sent.sent_id, " bbbbb ", ctok_pos_lst)
        for ccc, case in enumerate([[c for c in ctok.get_surface_case()] for ctok in toks]):
            sent.logger.debug("tok {} ->".format(ccc), "/".join([k for k in case]))
        if len(ctok_pos_lst) == 2 and is_case(toks[0], ["は"]) and is_case(toks[1], ["が"]):
            # 一つの語に nsubj の子が2つあって、1つめが「は」、2つめが「が」の場合：1つめを nsubj:outer に
            toks[0].dep_label = str(toks[0].dep_label) + ":outer"
        elif len(ctok_pos_lst) == 3 and is_case(toks[1], ["も"]) and is_case(toks[2], ["も"]):
            # 2つめが「も」、3つめが「も」
            toks[1].dep_label = "obj"
            toks[2].dep_label = "obj"
        elif len(ctok_pos_lst) == 3 and is_case(toks[0], ["も"]) and is_case(toks[1], ["は"]) and is_case(toks[2], ["も"]):
            # 1つめ「も」、2つめ「は」、3つめ「も」
            toks[0].dep_label = "obl"
            toks[2].dep_label = "obl"
        elif len(ctok_pos_lst) == 3 and is_case(toks[0], ["も"]) and is_case(toks[1], ["も"]) and is_case(toks[2], ["が"]):
            # 1つめが「も」、2つめが「も」、３つめが「が」の場合：3つめをnsubj、他をobl
            toks[0].dep_label = "obl"
            toks[1].dep_label = "obl"
        elif len(ctok_pos_lst) == 3 and is_case(toks[0], ["は"]) and is_case(toks[2], ["が"]):
            # 1つめが「は」、3つめが「が」の場合：1つめを nsubj:outer に
            toks[0].dep_label = str(toks[0].dep_label) + ":outer"
        elif len(ctok_pos_lst) == 3 and is_case(toks[0], ["など", "は"]) and is_case(toks[2], ["は"]):
            # 1つめが「などは」、3つめが「が」の場合：1つめを nsubj:outer に
            toks[0].dep_label = str(toks[0].dep_label) + ":outer"
        elif len(ctok_pos_lst) == 3 and is_case(toks[0], ["は"]) and is_case(toks[2], ["は"]):
            # 1つめが「は」、3つめが「は」の場合：1つめを nsubj:outer に
            toks[0].dep_label = str(toks[0].dep_label) + ":outer"
        elif len(ctok_pos_lst) == 3 and is_case(toks[0], ["は"]) and is_case(toks[1], ["は"]) and is_case(toks[2], ["の"]):
            # 1つめが「は」、2つめが「は」、3つめ「の」の場合：1つめを nsubj:outer に
            toks[2].dep_label = "nmod"
        elif len(ctok_pos_lst) == 3 and is_case(toks[0], ["の"]) and is_case(toks[1], ["は"]) and is_case(toks[2], ["の"]):
            # 「の」「は」「の」
            toks[0].dep_label = "nmod"
            toks[1].dep_label = "nmod"
            toks[2].dep_label = "nmod"
        elif len(ctok_pos_lst) == 3 and is_case(toks[0], ["が"]) and is_case(toks[2], ["が"]):
            # 1つめが「が」、3つめが「が」の場合：1つめを nsubj:outer に
            toks[0].dep_label = str(toks[0].dep_label) + ":outer"
        elif len(ctok_pos_lst) == 3 and is_case(toks[0], ["の"]) and is_case(toks[1], ["の"]) and is_case(toks[2], ["の"]):
            toks[0].dep_label = "nmod"
            toks[1].dep_label = "nmod"
            toks[2].dep_label = "nmod"
        elif len(ctok_pos_lst) == 3 and is_case(toks[1], ["の"]) and is_case(toks[2], ["の"]):
            toks[1].dep_label = "nmod"
            toks[2].dep_label = "nmod"
        elif len(ctok_pos_lst) == 3 and is_case(toks[0], ["は"]) and is_case(toks[1], ["が"]) and is_case(toks[2], ["の"]):
            toks[0].dep_label = str(toks[0].dep_label) + ":outer"
            toks[2].dep_label = "nmod"
        elif len(ctok_pos_lst) == 3 and is_case(toks[0], ["の"]) and is_case(toks[1], ["が"]) and is_case(toks[2], ["の", "から"]):
            # D068p_PB37_00050-50
            toks[2].dep_label = "obl"
        elif len(ctok_pos_lst) == 3 and is_case(toks[0], ["も"]) and is_case(toks[1], ["が"]) and is_case(toks[2], ["が"]):
            toks[0].dep_label = "obl"
        elif len(ctok_pos_lst) == 3 and is_case(toks[0], ["は"]) and is_case(toks[1], ["が"]) and is_case(toks[2], ["も"]):
            # 1つめ「は」、2つめ「が」、3つめ「も」
            toks[0].dep_label = str(toks[0].dep_label) + ":outer"
            toks[2].dep_label = "obl"
        elif len(ctok_pos_lst) == 3 and is_case(toks[0], ["は"]) and is_case(toks[1], ["は"]) and is_case(toks[2], ["も"]):
            toks[2].dep_label = "obl"
            toks[0].dep_label = str(toks[0].dep_label) + ":outer"
        elif len(ctok_pos_lst) == 3 and is_case(toks[0], ["も"]) and is_case(toks[1], ["は"]) and is_case(toks[2], ["が"]):
            toks[1].dep_label = str(toks[0].dep_label) + ":outer"
            toks[0].dep_label = "obl"
        elif len(ctok_pos_lst) == 3 and is_case(toks[0], ["も"]) and is_case(toks[1], ["は"]) and is_case(toks[2], ["は"]):
            toks[0].dep_label = str(toks[0].dep_label) + ":outer"
        elif len(ctok_pos_lst) == 3 and is_case(toks[0], ["も"]) and is_case(toks[1], ["も"]) and is_case(toks[2], ["は"]):
            toks[0].dep_label = str(toks[0].dep_label) + ":outer"
            toks[1].dep_label = str(toks[1].dep_label) + ":outer"
        elif len(ctok_pos_lst) == 3 and is_case(toks[0], ["は"]) and is_case(toks[1], ["も"]) and is_case(toks[2], ["は"]):
            toks[0].dep_label = str(toks[0].dep_label) + ":outer"
        elif len(ctok_pos_lst) == 3 and is_case(toks[1], ["が"]) and is_case(toks[2], ["も"]):
            toks[0].dep_label = str(toks[0].dep_label) + ":outer"
            toks[2].dep_label = "obl"
        elif len(ctok_pos_lst) == 3 and is_case(toks[1], ["は"]) and is_case(toks[2], ["も"]):
            toks[0].dep_label = str(toks[0].dep_label) + ":outer"
            toks[2].dep_label = "obl"
        elif len(ctok_pos_lst) == 3 and is_case(toks[0], ["が"]) and is_case(toks[1], ["も"]):
            toks[0].dep_label = str(toks[0].dep_label) + ":outer"
            toks[1].dep_label = "obl"
        elif len(ctok_pos_lst) == 3 and is_case(toks[0], ["が"]) and is_case(toks[1], ["も"]):
            toks[0].dep_label = str(toks[0].dep_label) + ":outer"
            toks[1].dep_label = "obl"
        elif len(ctok_pos_lst) == 3 and is_case(toks[0], ["も"]) and is_case(toks[1], ["も"]) and is_case(toks[2], ["が"]):
            toks[0].dep_label = "obj"
            toks[1].dep_label = "obj"
        elif len(ctok_pos_lst) == 3 and is_case(toks[0], ["が"]) and is_case(toks[1], ["は"]) and is_case(toks[2], ["は"]):
            toks[0].dep_label = "obl"
            toks[1].dep_label = str(toks[1].dep_label) + ":outer"
        elif len(ctok_pos_lst) == 4 and is_case(toks[0], ["は"]) and is_case(toks[1], ["が"]) and is_case(toks[2], ["は"]) and is_case(toks[3], ["が"]):
            toks[0].dep_label = str(toks[0].dep_label) +  ":outer"
            toks[2].dep_label = str(toks[2].dep_label) + ":outer"
        elif len(ctok_pos_lst) == 4 and is_case(toks[0], ["は"]) and is_case(toks[1], ["は"]) and is_case(toks[3], ["が"]):
            toks[0].dep_label = str(toks[0].dep_label) + ":outer"
            toks[1].dep_label = str(toks[1].dep_label) + ":outer"
        elif len(ctok_pos_lst) == 4 and is_case(toks[0], ["が"]) and is_case(toks[1], ["は"]) and is_case(toks[2], ["も"]) and is_case(toks[3], ["が"]):
            toks[2].dep_label = "obl"
            toks[1].dep_label = str(toks[1].dep_label) + ":outer"
        elif len(ctok_pos_lst) == 4 and is_case(toks[1], ["の"]) and is_case(toks[2], ["の"]) and is_case(toks[3], ["の"]):
            toks[1].dep_label = "nmod"
            toks[2].dep_label = "nmod"
            toks[3].dep_label = "nmod"
        elif len(ctok_pos_lst) == 4 and is_case(toks[1], ["も"]) and is_case(toks[3], ["も"]):
            toks[2].dep_label = "obj"
            toks[3].dep_label = "obj"
        elif len(ctok_pos_lst) == 4 and is_case(toks[1], ["は"]) and is_case(toks[2], ["も"]) and is_case(toks[3], ["も"]):
            toks[2].dep_label = "obl"
            toks[3].dep_label = "obl"
        elif len(ctok_pos_lst) == 4 and is_case(toks[0], ["が"]) and is_case(toks[1], ["も"]) and is_case(toks[2], ["も"]) and is_case(toks[3], ["が"]):
            toks[0].dep_label = str(toks[0].dep_label) + ":outer"
            toks[1].dep_label = "obj"
            toks[2].dep_label = "obj"
        elif len(ctok_pos_lst) == 4 and is_case(toks[1], ["も"]) and is_case(toks[2], ["も"]) and is_case(toks[3], ["が"]):
            toks[1].dep_label = "obj"
            toks[2].dep_label = "obj"
        # toks確認
        npos_lst = [t for t in toks if t.dep_label in ["nsubj", "csubj"]]
        if len(npos_lst) >= 2:
            assert len(npos_lst) == 2
            npos_lst[0].dep_label = str(npos_lst[0].dep_label) + ":outer"
