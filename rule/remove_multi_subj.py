# -*- coding: utf-8 -*-

"""
BCCWJ DepParaPAS remove multi subj
"""


def is_case(tok, case_lst):
    if len(tok.get_surface_case()) != len(case_lst):
        return False
    return all([case in tok.get_surface_case() for case in case_lst])


def adapt_nsubj_to_dislocated_rule(sent):
    """
        nsubj/csubjの中で指定のものをdislocatedに
    """
    parent_nsubj_pos = {}
    for word in sent.flatten():
        # nsubjの数を調べる
        if word.dep_label == "nsubj" or word.dep_label == "csubj":
            if not word.dep_num in parent_nsubj_pos:
                parent_nsubj_pos[word.dep_num] = []
            parent_nsubj_pos[word.dep_num].append(word.token_pos)
    if len(parent_nsubj_pos) > 0:
        for prent_pos, ctok_pos_lst in list(parent_nsubj_pos.items()):
            ctok_pos_lst = sorted(ctok_pos_lst)
            if len(ctok_pos_lst) == 3:
                # 一つの語に nsubj の子が3つあって
                tok_1 = sent.get_word_from_tokpos(ctok_pos_lst[0]-1)
                tok_2 = sent.get_word_from_tokpos(ctok_pos_lst[1]-1)
                tok_3 = sent.get_word_from_tokpos(ctok_pos_lst[2]-1)
                if is_case(tok_1, ["は"]) and is_case(tok_3, ["が"]):
                    # 1つめが「は」、3つめが「が」の場合：1つめを dislocated に
                    tok_1.dep_label = "dislocated"
                elif is_case(tok_1, ["など", "は"]) and is_case(tok_3, ["は"]):
                    # 1つめが「などは」、3つめが「が」の場合：1つめを dislocated に
                    tok_1.dep_label = "dislocated"
                elif is_case(tok_1, ["は"]) and is_case(tok_3, ["は"]):
                    # 1つめが「は」、3つめが「は」の場合：1つめを dislocated に
                    tok_1.dep_label = "dislocated"
                elif is_case(tok_1, ["が"]) and is_case(tok_3, ["が"]):
                    # 1つめが「が」、3つめが「が」の場合：1つめを dislocated に
                    tok_1.dep_label = "dislocated"
                elif is_case(tok_1, ["の"]) and is_case(tok_2, ["の"]) and is_case(tok_3, ["の"]):
                    tok_1.dep_label = "nmod"
                    tok_2.dep_label = "nmod"
                    tok_3.dep_label = "nmod"
                elif is_case(tok_1, ["の"]) and is_case(tok_2, ["が"]) and is_case(tok_3, ["の", "から"]):
                    # D068p_PB37_00050-50
                    tok_3.dep_label = "obl"
            elif len(ctok_pos_lst) == 2:
                # 一つの語に nsubj の子が2つあって、1つめが「は」、2つめが「が」の場合：1つめを dislocated に
                tok_1 = sent.get_word_from_tokpos(ctok_pos_lst[0]-1)
                tok_2 = sent.get_word_from_tokpos(ctok_pos_lst[1]-1)
                if is_case(tok_1, ["は"]) and is_case(tok_2, ["が"]):
                    tok_1.dep_label = "dislocated"
            elif len(ctok_pos_lst) == 4:
                tok_1 = sent.get_word_from_tokpos(ctok_pos_lst[0]-1)
                tok_2 = sent.get_word_from_tokpos(ctok_pos_lst[1]-1)
                tok_3 = sent.get_word_from_tokpos(ctok_pos_lst[2]-1)
                tok_4 = sent.get_word_from_tokpos(ctok_pos_lst[3]-1)
                if is_case(tok_1, ["は"]) and is_case(tok_2, ["が"]) and is_case(tok_3, ["は"]) and is_case(tok_4, ["が"]):
                    tok_1.dep_label = "dislocated"
                    tok_3.dep_label = "dislocated"
                elif is_case(tok_1, ["は"]) and is_case(tok_2, ["は"]) and is_case(tok_4, ["が"]):
                    tok_1.dep_label = "dislocated"
                    tok_2.dep_label = "dislocated"

