# -*- coding: utf-8 -*-

"""
BCCWJ DepParaPAS remove multi subj
"""


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
                tok_3 = sent.get_word_from_tokpos(ctok_pos_lst[2]-1)
                if len(tok_1.case_set) == 1 and "は" in tok_1.case_set and len(tok_3.case_set) == 1 and "が" in tok_3.case_set:
                    # 1つめが「は」、3つめが「が」の場合：1つめを dislocated に
                    tok_1.dep_label = "dislocated"
            elif len(ctok_pos_lst) == 2:
                # 一つの語に nsubj の子が2つあって、1つめが「は」、2つめが「が」の場合：1つめを dislocated に
                tok_1 = sent.get_word_from_tokpos(ctok_pos_lst[0]-1)
                tok_2 = sent.get_word_from_tokpos(ctok_pos_lst[1]-1)
                if len(tok_1.case_set) == 1 and "は" in tok_1.case_set and len(tok_2.case_set) == 1 and "が" in tok_2.case_set:
                    # 1つめが「は」、2つめが「が」の場合：1つめを dislocated に
                    tok_1.dep_label = "dislocated"
