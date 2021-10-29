# -*- coding: utf-8 -*-

"""
BCCWJ DepParaPAS remove space function
"""

import re


def _skip_jsp_token_from_sentence(bunsetu):
    """
        飛ばすワードがあればTrue
    """
    skip_lst, tmp_lst = [], []
    for word_pos in range(0, len(bunsetu)):
        word = bunsetu[word_pos]
        if re.match("空白", word.get_xpos()):
            skip_lst.append(word_pos)
        else:
            word.surface = re.sub(r"　　+", "　", word.get_surface())
            word.origin = re.sub(r"　　+", "　", word.origin)
            if word.get_surface().endswith("　"):
                # 末尾に　 -> 削って MISTにSpaceAfter=Yesを足す
                word.surface = word.surface.rstrip("　")
                word.origin = word.origin.rstrip("　")
                word.ud_misc["SpaceAfter"] = "Yes"
            if word.get_surface().startswith("　"):
                # 末尾に　 -> 削って MISTにSpaceAfter=Yesを足す
                word.surface = word.surface.lstrip("　")
                word.origin = word.origin.lstrip("　")
                if word_pos > 1:
                    bunsetu[word_pos-1].ud_misc["SpaceAfter"] = "Yes"
        tmp_lst.append((word_pos, word))
    if len(skip_lst) == 0:
        return False
    del bunsetu[:]
    nword_pos = 0
    for word_pos, word in tmp_lst:
        if word_pos not in skip_lst:
            if word.word_pos + 1 in skip_lst:
                word.ud_misc["SpaceAfter"] = "Yes"
            word.word_pos = nword_pos
            bunsetu.append(word)
            nword_pos += 1
    return True


def skip_jsp_token_from_sentence(doc):
    """
        スペースを除く
        TODO: 実装
    """
    for sent in doc.sentences():
        skip_lst, tmp_lst, remove_flag, update_flag = [], [], False, False
        for bunsetu_pos, bunsetu in enumerate(sent):
            assert bunsetu_pos == bunsetu.bunsetu_pos
            p_is_update = _skip_jsp_token_from_sentence(bunsetu)
            if p_is_update:
                update_flag = True
            if len(bunsetu) == 0:
                remove_flag = True
                skip_lst.append(bunsetu_pos)
            tmp_lst.append((bunsetu_pos, bunsetu))
        if remove_flag:
            del sent[:]
            nbunsetu_pos = 0
            for bunsetu_pos, bunsetu in tmp_lst:
                if bunsetu_pos not in skip_lst:
                    bunsetu.bunsetu_pos = nbunsetu_pos
                    sent.append(bunsetu)
                    nbunsetu_pos += 1
        if update_flag:
            update_sentence_token_pos(sent)
    remove_sentence_zero_token(doc)


def update_sentence_token_pos(sent):
    """
        トークンの位置を修正する
    """
    tok_map, sss = {}, set()
    for tok_pos, word in enumerate(sent.flatten()):
        tok_map[word.token_pos] = tok_pos + 1
        sss.add(word.token_pos)
    if len(sent) == 0:
        return
    ex_sp_lst = set([])
    for bbb in list(range(1, max(sss))):
        if bbb not in sss:
            ex_sp_lst.add(bbb)
    for tok_pos, word in enumerate(sent.flatten()):
        word.token_pos = tok_map[word.token_pos]
        if word.dep_num != 0:
            if word.dep_num not in tok_map:
                assert word.dep_num in ex_sp_lst or word.dep_num > max(sss)
                word.dep_num = 0
                word.dep_label = 'root'
            else:
                word.dep_num = tok_map[word.dep_num]


def remove_sentence_zero_token(doc):
    """
        トークンがゼロの文を飛ばす
        TODO: 実装
    """
    skip_lst, tmp_lst = [], []
    doc_size = len(doc.sentences())
    for sent_pos in range(0, doc_size):
        sent = doc[sent_pos]
        if len(sent.flatten()) == 0:
            skip_lst.append(sent.sent_pos)
        tmp_lst.append((sent_pos, sent))
    del doc[:]
    new_sent_pos = 0
    for sent_pos, sent in tmp_lst:
        if sent_pos not in skip_lst:
            doc.append(sent)
            sent.set_sent_pos(new_sent_pos)
            new_sent_pos += 1
