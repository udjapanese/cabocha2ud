# -*- coding: utf-8 -*-

"""
BCCWJ DepParaPAS remove multi subj
"""
from typing import cast

from ..bd.word import Word
from ..bd.sentence import Sentence


def is_case(tok: Word, case_lst: list[str]) -> bool:
    if len(tok.get_surface_case()) != len(case_lst):
        return False
    return all([case in tok.get_surface_case() for case in case_lst])


def adapt_nsubj_to_dislocated_rule(sent: Sentence) -> None:
    """
        nsubj/csubjの中で指定のものをdislocatedに
    """
    parent_nsubj_pos: dict[int, list[int]] = {}
    for word in sent.flatten():
        # nsubjの数を調べる
        if word.dep_num is None:
            continue
        if word.dep_label == "nsubj" or word.dep_label == "csubj":
            if not word.dep_num in parent_nsubj_pos:
                parent_nsubj_pos[word.dep_num] = []
            parent_nsubj_pos[word.dep_num].append(word.token_pos)
    if len(parent_nsubj_pos) > 0:
        for _, ctok_pos_lst in list(parent_nsubj_pos.items()):
            ctok_pos_lst = sorted(ctok_pos_lst)
            toks = [cast(Word, sent.get_word_from_tokpos(ctok-1)) for ctok in ctok_pos_lst]
            cases = [[c for c in ctok.get_surface_case()] for ctok in toks]
            if sent.debug and len(ctok_pos_lst) >= 3:
                print(sent.sent_id, " aaaaaa ", ctok_pos_lst)
                for ccc, case in enumerate(cases):
                    print("tok{} ->".format(ccc), "/".join([k for k in case]), end=" ")
                print()
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
            cases = [[c for c in ctok.get_surface_case()] for ctok in toks]
            if sent.debug and len(ctok_pos_lst) >= 3:
                print(sent.sent_id, " bbbbb ", ctok_pos_lst)
                for ccc, case in enumerate(cases):
                    print("tok{} ->".format(ccc), "/".join([k for k in case]), end=" ")
                print()
            if len(ctok_pos_lst) == 3:
                # 一つの語に nsubj の子が3つあって
                tok_1 = toks[0]
                tok_2 = toks[1]
                tok_3 = toks[2]
                if is_case(tok_2, ["も"]) and is_case(tok_3, ["も"]):
                    #
                    tok_2.dep_label = "obj"
                    tok_3.dep_label = "obj"
                elif is_case(tok_1, ["も"]) and is_case(tok_2, ["は"]) and is_case(tok_3, ["も"]):
                    #
                    tok_1.dep_label = "obl"
                    tok_3.dep_label = "obl"
                elif is_case(tok_1, ["も"]) and is_case(tok_2, ["も"]) and is_case(tok_3, ["が"]):
                    #
                    tok_1.dep_label = "obl"
                    tok_2.dep_label = "obl"
                elif is_case(tok_1, ["は"]) and is_case(tok_3, ["が"]):
                    # 1つめが「は」、3つめが「が」の場合：1つめを dislocated に
                    tok_1.dep_label = "dislocated"
                elif is_case(tok_1, ["など", "は"]) and is_case(tok_3, ["は"]):
                    # 1つめが「などは」、3つめが「が」の場合：1つめを dislocated に
                    tok_1.dep_label = "dislocated"
                elif is_case(tok_1, ["は"]) and is_case(tok_3, ["は"]):
                    # 1つめが「は」、3つめが「は」の場合：1つめを dislocated に
                    tok_1.dep_label = "dislocated"
                elif is_case(tok_1, ["は"]) and is_case(tok_2, ["は"]) and is_case(tok_3, ["の"]):
                    # 1つめが「は」、3つめが「は」の場合：1つめを dislocated に
                    tok_3.dep_label = "nmod"
                elif is_case(tok_1, ["の"]) and is_case(tok_2, ["は"]) and is_case(tok_3, ["の"]):
                    # 1つめが「は」、3つめが「は」の場合：1つめを dislocated に
                    tok_1.dep_label = "nmod"
                    tok_2.dep_label = "nmod"
                    tok_3.dep_label = "nmod"
                elif is_case(tok_1, ["が"]) and is_case(tok_3, ["が"]):
                    # 1つめが「が」、3つめが「が」の場合：1つめを dislocated に
                    tok_1.dep_label = "dislocated"
                elif is_case(tok_1, ["の"]) and is_case(tok_2, ["の"]) and is_case(tok_3, ["の"]):
                    tok_1.dep_label = "nmod"
                    tok_2.dep_label = "nmod"
                    tok_3.dep_label = "nmod"
                elif is_case(tok_2, ["の"]) and is_case(tok_3, ["の"]):
                    tok_2.dep_label = "nmod"
                    tok_3.dep_label = "nmod"
                elif is_case(tok_1, ["は"]) and is_case(tok_2, ["が"]) and is_case(tok_3, ["の"]):
                    tok_1.dep_label = "dislocated"
                    tok_3.dep_label = "nmod"
                elif is_case(tok_1, ["の"]) and is_case(tok_2, ["が"]) and is_case(tok_3, ["の", "から"]):
                    # D068p_PB37_00050-50
                    tok_3.dep_label = "obl"
                elif is_case(tok_1, ["も"]) and is_case(tok_2, ["が"]) and is_case(tok_3, ["が"]):
                    tok_1.dep_label = "obl"
                elif is_case(tok_1, ["は"]) and is_case(tok_2, ["が"]) and is_case(tok_3, ["も"]):
                    #
                    tok_1.dep_label = "dislocated"
                    tok_3.dep_label = "obl"
                elif is_case(tok_1, ["は"]) and is_case(tok_2, ["は"]) and is_case(tok_3, ["も"]):
                    tok_3.dep_label = "obl"
                    tok_1.dep_label = "dislocated"
                elif is_case(tok_1, ["も"]) and is_case(tok_2, ["は"]) and is_case(tok_3, ["が"]):
                    tok_2.dep_label = "dislocated"
                    tok_1.dep_label = "obl"
                elif is_case(tok_1, ["も"]) and is_case(tok_2, ["は"]) and is_case(tok_3, ["は"]):
                    tok_1.dep_label = "dislocated"
                elif is_case(tok_1, ["も"]) and is_case(tok_2, ["も"]) and is_case(tok_3, ["は"]):
                    tok_1.dep_label = "dislocated"
                    tok_2.dep_label = "dislocated"
                elif is_case(tok_1, ["は"]) and is_case(tok_2, ["も"]) and is_case(tok_3, ["は"]):
                    tok_1.dep_label = "dislocated"
                elif is_case(tok_2, ["が"]) and is_case(tok_3, ["も"]):
                    tok_1.dep_label = "dislocated"
                    tok_3.dep_label = "obl"
                elif is_case(tok_2, ["は"]) and is_case(tok_3, ["も"]):
                    tok_1.dep_label = "dislocated"
                    tok_3.dep_label = "obl"
                elif is_case(tok_1, ["が"]) and is_case(tok_2, ["も"]):
                    tok_1.dep_label = "dislocated"
                    tok_2.dep_label = "obl"
                elif is_case(tok_1, ["が"]) and is_case(tok_2, ["も"]):
                    tok_1.dep_label = "dislocated"
                    tok_2.dep_label = "obl"
                elif is_case(tok_1, ["も"]) and is_case(tok_2, ["も"]) and is_case(tok_3, ["が"]):
                    tok_1.dep_label = "obj"
                    tok_2.dep_label = "obj"
                elif is_case(tok_1, ["が"]) and is_case(tok_2, ["は"]) and is_case(tok_3, ["は"]):
                    tok_1.dep_label = "obl"
                    tok_2.dep_label = "dislocated"
            elif len(ctok_pos_lst) == 2:
                # 一つの語に nsubj の子が2つあって、1つめが「は」、2つめが「が」の場合：1つめを dislocated に
                if is_case(toks[0], ["は"]) and is_case(toks[1], ["が"]):
                    toks[0].dep_label = "dislocated"
            elif len(ctok_pos_lst) == 4:
                tok_1 = toks[0]
                tok_2 = toks[1]
                tok_3 = toks[2]
                tok_4 = toks[3]
                if is_case(tok_1, ["は"]) and is_case(tok_2, ["が"]) and is_case(tok_3, ["は"]) and is_case(tok_4, ["が"]):
                    tok_1.dep_label = "dislocated"
                    tok_3.dep_label = "dislocated"
                elif is_case(tok_1, ["は"]) and is_case(tok_2, ["は"]) and is_case(tok_4, ["が"]):
                    tok_1.dep_label = "dislocated"
                    tok_2.dep_label = "dislocated"
                elif is_case(tok_1, ["が"]) and is_case(tok_2, ["は"]) and is_case(tok_3, ["も"]) and is_case(tok_4, ["が"]):
                    tok_3.dep_label = "obl"
                    tok_2.dep_label = "dislocated"
                elif is_case(tok_2, ["の"]) and is_case(tok_3, ["の"]) and is_case(tok_4, ["の"]):
                    tok_2.dep_label = "nmod"
                    tok_3.dep_label = "nmod"
                    tok_4.dep_label = "nmod"
                elif is_case(tok_2, ["も"]) and is_case(tok_4, ["も"]):
                    tok_3.dep_label = "obj"
                    tok_4.dep_label = "obj"
                elif is_case(tok_2, ["は"]) and is_case(tok_3, ["も"]) and is_case(tok_4, ["も"]):
                    tok_3.dep_label = "obl"
                    tok_4.dep_label = "obl"
                elif is_case(tok_1, ["が"]) and is_case(tok_2, ["も"]) and is_case(tok_3, ["も"]) and is_case(tok_4, ["が"]):
                    tok_1.dep_label = "dislocated"
                    tok_2.dep_label = "obj"
                    tok_3.dep_label = "obj"
                elif is_case(tok_2, ["も"]) and is_case(tok_3, ["も"]) and is_case(tok_4, ["が"]):
                    tok_2.dep_label = "obj"
                    tok_3.dep_label = "obj"
