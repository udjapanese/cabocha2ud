# -*- coding: utf-8 -*-

"""
BCCWJ DepParaPAS swaping rule

主にcc周り

"""


def _check_bunsetu_cc_and_punct(word):
    """
    子の中に文節外の子があれば除く
    """
    cc_and_punct_flag, save_tpos = True, 0
    for tpos, twrd in enumerate(word.bunsetu):
        save_tpos = twrd.token_pos
        # print(tpos, len(word.bunsetu), twrd.dep_label)
        if tpos == len(word.bunsetu) - 1:
            if twrd.dep_label != 'punct':
                cc_and_punct_flag = False
                break
        elif twrd.dep_label != "cc":
            cc_and_punct_flag = False
            break
    return cc_and_punct_flag, save_tpos


def filter_cand_children(sent, word, chrd):
    """
    子の中に文節外の子があれば除く
    """
    return [
        c_pos for c_pos in chrd
        if word.bunsetu_pos == sent.get_word_from_tokpos(c_pos-1).bunsetu_pos
    ]


def _detect_new_parent(sent, word, chrd):
    chrd = filter_cand_children(sent, word, chrd)
    for c_pos in reversed(chrd):
        ctok = sent.get_word_from_tokpos(c_pos-1)
        if ctok.dep_label not in ['punct', 'aux', 'cc', 'case', "mark"]:
            return c_pos
    return -1


UDEP_LABEL_WITHOUT_CHILD = ["cc", "aux", "punct", "mark", 'case']

def swap_dep_without_child_from_sent(sent):
    """
        swap position
            cc <- X を cc -> Xに変更
            （主に子をもっていけないもの対策）
    """
    # print(sent.sent_id)
    for word in sent.words():
        if word.dep_label in UDEP_LABEL_WITHOUT_CHILD:
            chrd = [
                cwrd for cwrd in sent.get_ud_children(word, is_reconst=True)
            ]
            if len(chrd) == 0:
                continue
            org_dep_num = word.dep_num
            chrd = sorted(chrd)
            last_chrd_pos = _detect_new_parent(sent, word, chrd)
            if last_chrd_pos == -1:
                # すべて子を持てないdep_labelの子しかかかってなかった場合
                # しょうがないので、swapではなくccの親に全部かける
                for cwrd_pos in chrd:
                    sent.get_word_from_tokpos(cwrd_pos-1).dep_num = org_dep_num
                # 文節内すべてccとpunctだったらpunctは最後のccにかける
                cc_and_punct_flag, save_tpos = _check_bunsetu_cc_and_punct(word)
                if cc_and_punct_flag:
                    sent.get_word_from_tokpos(save_tpos-1).dep_num = save_tpos-1
            else:
                # 子をもてるのがあった場合
                last_chrd = sent.get_word_from_tokpos(last_chrd_pos-1)
                for cwrd_pos in [c for c in chrd if c != last_chrd]:  #chrd[:-1]:
                    sent.get_word_from_tokpos(cwrd_pos-1).dep_num = last_chrd.token_pos
                word.dep_num = last_chrd.token_pos
                last_chrd.dep_num = org_dep_num
