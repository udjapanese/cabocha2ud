# -*- coding: utf-8 -*-

"""
BCCWJ DepParaPAS rule function: for bunsetu
"""

import re


REGEX_TYPE = type(re.compile(''))
NUM_RE = re.compile(r"\* (\d+) (-?\d+)([A-Z][A-Z]?) (\d+)/(\d+) .*$")
BUNSETU_FUNC_MATCH_RE = re.compile(
    r"(?:助詞|助動詞|接尾辞,形容詞的|接尾辞,形状詞的|接尾辞,動詞的|動詞,非自立)"
)
BUNSETU_SUBJ_MATCH_RE = re.compile(
    r"(?!助詞|助動詞|接尾辞,形容詞的|接尾辞,形状詞的|接尾辞,動詞的|空白|補助記号|動詞,非自立|形状詞,助動詞語幹)"
)  # remove `記号` because maybe 記号 is noun already when i checked
BUNSETU_NOHEAD_MATCH_RE = re.compile(
    r"(?!空白|補助記号|URL)"
)
BUNSETU_NO_SUBJ_MATCH_RE = re.compile(
    r"(?:補助記号,括弧|接頭辞)"
)
SPECIAL_MATCH_RE = re.compile(
    r"(?:接尾辞,名詞的)"
)


def detect_bunsetu_pos_each(bunsetu, func_type="type2"):
    """
        detect bunsetu pos function
    """
    if func_type == "type2":
        return detect_bunsetu_pos(bunsetu)
    raise TypeError("do not this")


def _get_features(features):
    """
        素性をすべて,区切りに（フォーマット統一のため）
    """
    nfes = []
    for f in features:
        nfes.extend(f.split("-"))
    return ",".join(nfes)


def detect_bunsetu_pos(bunsetu):
    """
        detect subject and function position
        最新版
    """
    bunsetu.subj_pos, bunsetu.func_pos, flag, no_head_flag = 0, 0, True, True
    for word in bunsetu.words():
        fes = _get_features(word.features)
        if BUNSETU_FUNC_MATCH_RE.match(fes):
            bunsetu.func_pos = word.word_pos
            flag = False
        if flag and BUNSETU_SUBJ_MATCH_RE.match(fes):
            bunsetu.subj_pos = word.word_pos
        elif not flag and BUNSETU_SUBJ_MATCH_RE.match(fes):
            bunsetu.func_pos = word.word_pos
    if bunsetu.subj_pos > bunsetu.func_pos:
        bunsetu.func_pos = bunsetu.subj_pos
    subj_fes = _get_features(bunsetu.words()[bunsetu.subj_pos].features)
    if BUNSETU_NO_SUBJ_MATCH_RE.match(subj_fes):
        while BUNSETU_NO_SUBJ_MATCH_RE.match(subj_fes) and bunsetu.subj_pos < bunsetu.func_pos:
            bunsetu.subj_pos += 1
            subj_fes = ",".join(bunsetu.words()[bunsetu.subj_pos].features)
    bunsetu.subj_pos = check_special_subject_pos(bunsetu, subj_fes, bunsetu.subj_pos)
    if bunsetu.subj_pos is None or bunsetu.func_pos is None:
        raise TypeError


def check_special_subject_pos(bunsetu, subj_fes, subj_pos):
    """
        「XX」＋さ は「XX」がheadに
    """
    if not SPECIAL_MATCH_RE.match(subj_fes):
        return subj_pos
    if bunsetu.words()[subj_pos].get_origin() != "さ":
        return subj_pos
    subj_pos -= 1
    while subj_pos > 0:
        subj_fes = ",".join(bunsetu.words()[subj_pos].features)
        if BUNSETU_SUBJ_MATCH_RE.match(subj_fes):
            return subj_pos
        subj_pos -= 1
    return subj_pos


def _detect_dep_inbunsetu(bunsetu, parent_pos):
    for word in bunsetu:
        if word.is_subj() is None or word.is_func() is None:
            # HEADなし, parent_pos はそのまま親
            word.ud_misc["BunsetuPositionType"] = "NO_HEAD"
            word.dep_num = parent_pos
        elif bunsetu.is_loop and word.is_subj():
            # 主辞はあるがその主辞に掛かり先がない場合 その主辞の掛かり先はroot
            word.ud_misc["BunsetuPositionType"] = "NO_HEAD"
            word.dep_num = 0
        elif word.is_subj():
            if parent_pos == 0:
                word.ud_misc["BunsetuPositionType"] = "ROOT"
            else:
                word.ud_misc["BunsetuPositionType"] = "SEM_HEAD"
            # 1. 主辞の場合掛かり先の主辞にかける
            word.dep_num = parent_pos
        elif word.is_func():
            # 2. 機能語確定(SYN_HEAD)、機能語は主辞にかける
            word.dep_num = bunsetu[bunsetu.subj_pos].token_pos
            word.ud_misc["BunsetuPositionType"] = "SYN_HEAD"
        elif (
                word.features[0].startswith("助") or word.features[1] == "非自立可能"
        ) and not word.is_func():
            # 3. 助詞、助動詞、非自立可能はその他機能語(FUNC), 掛かり先は主辞にかける
            word.dep_num = bunsetu[bunsetu.subj_pos].token_pos
            word.ud_misc["BunsetuPositionType"] = "FUNC"
        else:
            # 4. のこりは主辞にかける
            word.dep_num = bunsetu[bunsetu.subj_pos].token_pos
            word.ud_misc["BunsetuPositionType"] = "CONT"


def detect_dep_inbunsetu(sentence):
    """
        detect bunsetu type
        同時にUDの係り受り先も決める

        特殊な掛かり先の変更(is_the_special_bunsetu_word)
    """
    is_the_special_bunsetu_word(sentence)
    for bunsetu in sentence.bunsetues():
        dep_pos, parent_pos = sentence.bunsetu_dep[bunsetu.bunsetu_pos], None
        if dep_pos == -1:  # root にする
            parent_pos = 0
        else:
            try:
                parent = sentence.bunsetues()[dep_pos]
            except:
                print(str(sentence))
                print(sentence.sent_pos, bunsetu.bunsetu_pos, dep_pos, len(sentence.bunsetues()))
                raise ValueError("cannot bunsetu of dependency bunsetu")
            parent_pos = parent[parent.subj_pos].token_pos
        for word in bunsetu:
            # 文節内係り関係
            _detect_dep_inbunsetu(bunsetu, parent_pos)
        for word in bunsetu:
            if word.dep_num == word.token_pos:
                word.ud_misc["BunsetuPositionType"] = "NO_HEAD"
                word.dep_num = 0
        # 文節内係り間の変更
        change_dependency_inbunsetu(bunsetu)


def change_dependency_inbunsetu(bunsetu):
    target_positions = []
    for word in bunsetu:
        if word.luw_label == "B" and word.luw_pos == "助詞-格助詞":
            target_positions.append(word.word_pos)
    if len(target_positions) == 0:
        return
    for target_position in target_positions:
        last_pos = target_position + 1
        while last_pos < len(bunsetu) and bunsetu[last_pos].luw_label == "I":
            last_pos += 1
        last_pos = last_pos - 1
        if last_pos >= len(bunsetu) or last_pos == target_position:
            continue
        assert [bunsetu[w].luw_pos == "助詞-格助詞" for w in range(target_position, last_pos+1)]
        for wrd in range(target_position, last_pos+1):
            if wrd == target_position:
                continue
            bunsetu[wrd].dep_num = bunsetu[target_position].token_pos


def is_the_special_bunsetu_word(sent):
    """
        特殊な文節だ
    """
    for bunsetu in sent:
        if _is_the_special_bunsetu_word(bunsetu):
            # 入れ替える、実装的に、文節内には一回しかないと仮定
            bunsetu.subj_pos = bunsetu.subj_pos - 1
            for word in bunsetu.words():
                word.set_bunsetsu_info(
                    bunsetu.subj_pos == word.word_pos,
                    bunsetu.func_pos == word.word_pos
                )


def _is_the_special_bunsetu_word(bunsetu):
    """
        主辞と機能語を入れ替える対象であるか
            - 名詞-普通名詞-サ変可能/動詞-非自立可能
    """
    txpos = bunsetu[bunsetu.subj_pos].get_xpos()
    if bunsetu.subj_pos > 0 and re.match("動詞-非自立可能", txpos):
        pxpos = bunsetu[bunsetu.subj_pos-1].get_xpos()
        return re.match("名詞-普通名詞-サ変可能", pxpos)
    return False
