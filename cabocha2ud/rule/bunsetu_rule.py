# -*- coding: utf-8 -*-

"""
BCCWJ DepParaPAS rule function: for bunsetu
"""

import re
from typing import TYPE_CHECKING, Optional, cast

if TYPE_CHECKING:
    from ..bd.bunsetu import Bunsetu
    from ..bd.sentence import Sentence

REGEX_TYPE = type(re.compile(''))
BUNSETU_FUNC_MATCH_RE = re.compile(
    r"(?:助詞|助動詞|接尾辞,形容詞的|接尾辞,形状詞的|接尾辞,動詞的)"
)
BUNSETU_SUBJ_MATCH_RE = re.compile(
    r"(?!助詞|助動詞|接尾辞,形容詞的|接尾辞,形状詞的|接尾辞,動詞的|空白|補助記号|形状詞,助動詞語幹|名詞,助動詞語幹|接頭辞|接続詞)"
)  # remove `記号` because maybe 記号 is noun already when i checked
BUNSETU_NOHEAD_MATCH_RE = re.compile(
    r"(?!空白|補助記号|URL)"
)
BUNSETU_NO_SUBJ_MATCH_RE = re.compile(
    r"(?:補助記号,括弧|接頭辞)"
)

BUNSETU_NO_POS_SUBJ_MATCH_RE = re.compile(
    r"(?:名詞,普通名詞,副詞可能)"
)


def _get_features(features: list[str]) -> str:
    """
        素性をすべて,区切りに（フォーマット統一のため）
    """
    nfes = []
    for fff in features:
        nfes.extend(fff.split("-"))
    return ",".join(nfes)


def detect_bunsetu_pos(bunsetu: "Bunsetu") -> None:
    """
        detect subject and function position in bunsetu
    """
    # 初期位置はどちらも 最初の単語
    bunsetu.subj_pos, bunsetu.func_pos = 0, 0
    tmp_subj_pos: list[int] = []
    tmp_func_pos: list[int] = []
    bunsetsu_features: list[str] = []
    # 機能語がきたかどうかのflag
    kino_flag: bool = True
    kino_end_flag: Optional[bool] = None
    for word in bunsetu.words():
        fes = _get_features(word.get_features())
        bunsetsu_features.append(fes)
        if BUNSETU_FUNC_MATCH_RE.match(fes):
            bunsetu.func_pos = word.word_pos
            kino_flag = False
            if kino_end_flag is None:
                kino_end_flag = True
            if kino_end_flag:
                tmp_func_pos.append(word.word_pos)
        elif kino_flag and BUNSETU_SUBJ_MATCH_RE.match(fes):
            tmp_subj_pos.append(word.word_pos)
            if BUNSETU_NO_POS_SUBJ_MATCH_RE.match(fes) and word.get_luw_pos() in ["助詞-接続助詞"]:
                continue
            bunsetu.subj_pos = word.word_pos
        elif not kino_flag and BUNSETU_SUBJ_MATCH_RE.match(fes):
            # 「という」など
            tmp_subj_pos.append(word.word_pos)
            bunsetu.func_pos = word.word_pos
            if kino_end_flag is not None:
                kino_end_flag = False
        bunsetu.logger.debug("------")
        bunsetu.logger.debug(word.word_pos, str(
            word), "\n", fes, bunsetu.subj_pos, bunsetu.func_pos)
    if kino_end_flag and len(tmp_func_pos) > 0:
        # 機能語がつづいていたら一番上
        fpos = 0
        bunsetu.func_pos = tmp_func_pos[fpos]
        while fpos + 1 < len(tmp_func_pos) and\
            bunsetu[bunsetu.func_pos].get_luw_pos().split("-")[0] in ["動詞", "形容詞", "形容動詞"]:
            # 「やって」などは非自立になるが...長単位だとそうでないときもある
            fpos += 1
            bunsetu.func_pos = tmp_func_pos[fpos]
    bunsetu.logger.debug(bunsetu.subj_pos, bunsetu.func_pos)
    if bunsetu.subj_pos > bunsetu.func_pos:
        # 主辞が機能語より右だったら、主辞と機能語を同じ位置にする
        bunsetu.func_pos = bunsetu.subj_pos
    assert len(bunsetsu_features) == len(bunsetu.words())
    # 補助記号,括弧|接頭辞などは主辞ではない
    bunsetu.subj_pos = check_special_nosubj(
        bunsetsu_features, bunsetu.subj_pos, bunsetu.func_pos)
    # 「XX」＋さ は「XX」がheadになるように変更
    bunsetu.subj_pos = check_special_subject_pos(
        bunsetu, bunsetsu_features[bunsetu.subj_pos], bunsetu.subj_pos)
    # 括弧内部がheadになっていたら別のものをheadに変更
    bunsetu.subj_pos = check_special_blacket_head(
        bunsetsu_features, bunsetu.subj_pos)
    # 主辞にならないものを変更
    bunsetu.subj_pos, bunsetu.func_pos = check_other_subj(
        bunsetsu_features, tmp_subj_pos, tmp_func_pos, bunsetu)
    # そうして
    bunsetu.subj_pos = check_sousite_subj(bunsetu)
    assert bunsetu.subj_pos <= bunsetu.func_pos
    bunsetu.logger.debug("result->>>", bunsetu.subj_pos, bunsetu.func_pos)


def check_other_subj(
    bun_fes: list[str], tmp_s_pos: list[int], tmp_f_pos: list[int], bun: "Bunsetu"
) -> tuple[int, int]:
    """[summary]
    お/願い/申し上げ/ます -> 「願い」主辞を「申し上げ」に
    見た/目、揚げ/アイス なども対象
    長単位/助詞or接続助詞or助動詞or補助記号除く

    Args:
        bun_fes (list[str]): [description]
        tmp_s_pos (list[int]): [description]
        tmp_f_pos (list[int]): [description]
        bun (Bunsetu): 対象のBunsetu

    Returns:
        tuple[int, int]: subject_pos, function_pos 新しい主辞番号、機能語番号
    """
    if not (bun_fes[bun.subj_pos].startswith("動詞,非自立可能")) \
            and not (bun[bun.subj_pos].get_origin() in ["もの", "物"]\
                and bun[bun.subj_pos].get_luw_pos() == "助詞-接続助詞")\
            and not (bun[bun.subj_pos].get_origin() in ["こと", "事"]\
                and bun[bun.subj_pos].get_luw_pos().startswith("助動詞")):
        return bun.subj_pos, bun.func_pos
    tmp_subj_pos = [
        t for t in tmp_s_pos
        if bun[t].get_luw_pos().split("-")[0] not in ["助詞", "接続助詞", "助動詞", "補助記号", "接尾辞"]
        # and bun[t].get_origin() not in ["する", "できる", "くださる", "いただく", "なさる"]
        and bun[t].get_origin() not in ["為る", "出来る", "下さる", "頂く", "為さる"]
        and not bun.is_inner_brank_word(t)  # かっこ内部ではない
    ]
    bun.logger.debug("dd->>>", bun.subj_pos, bun.func_pos, tmp_subj_pos)
    bun.logger.debug("aaa->", bun.subj_pos, bun.func_pos,
                     [t < bun.subj_pos for t in tmp_subj_pos])
    old_subj, old_func = bun.subj_pos, bun.func_pos
    new_subj, new_func = bun.subj_pos, bun.func_pos
    for tpos in tmp_subj_pos:
        bun.logger.debug("ccc", tpos, new_subj, tpos < old_subj)
        if tpos < old_subj:
            new_subj = tpos
    if new_subj > new_func:
        flag = False
        for tsp in tmp_f_pos:
            if bun.subj_pos <= tsp:
                new_func = tsp
                flag = True
                break
        if not flag:
            # おそらくむりなんで戻す
            bun.logger.debug(3333)
            return old_subj, old_func
    bun.logger.debug("dd->>>", new_subj, new_func, old_subj, old_func)
    return new_subj, new_func


def check_sousite_subj(bunsetu: "Bunsetu") -> int:
    """[summary]
        そう/し/てのとき fixed的に左主辞じゃないといけない
    Args:
        bunsetu (Bunsetu): [description]
    """
    if not (bunsetu[bunsetu.subj_pos].get_luw_pos().split("-")[0] == "接続詞"
            and bunsetu[0].get_luw_pos().split("-")[0] == "接続詞"):
        return bunsetu.subj_pos
    bunsetu.logger.debug("eaea->", bunsetu.subj_pos, bunsetu.func_pos)
    tpos = bunsetu.subj_pos
    while tpos > 0 and bunsetu[tpos].get_luw_pos().split("-")[0] == "接続詞":
        tpos = tpos - 1
    bunsetu.logger.debug("eaea->", bunsetu.subj_pos, bunsetu.func_pos, tpos)
    return tpos


def check_special_nosubj(bunsetsu_features: list[str], subj_pos: int, func_pos: int) -> int:
    """
    補助記号,括弧|接頭辞など 弾かれないものを弾く
    """
    subj_fes = bunsetsu_features[subj_pos]
    if not BUNSETU_NO_SUBJ_MATCH_RE.match(subj_fes):
        return subj_pos
    while BUNSETU_NO_SUBJ_MATCH_RE.match(subj_fes) and subj_pos < func_pos:
        subj_pos += 1
        subj_fes = bunsetsu_features[subj_pos]
    return subj_pos


RE_OPEN_EXP = re.compile("^補助記号,括弧開.*")
RE_KUHAKU_EXP = re.compile("^空白,.*$")
RE_KIGO_EXP = re.compile("^補助記号.*")


def check_special_blacket_head(bunsetsu_features: list[str], subj_pos: int) -> int:
    """
        括弧内部がheadになっていたら別のものをheadに
        ここでは単純に最初のかっこより右側を括弧内部と仮定する
         1  2  3  4  5  6
        X1 X2 （ X3  X4  ）
         このばあい  X3をX2にかえる
         （かなり単純化しているため精密に文構造をみるならば細かく作業が必要）
    """
    if all(RE_OPEN_EXP.match(fes) is None for fes in bunsetsu_features):
        return subj_pos
    kakko_pos = [
        (fpos, fes) for fpos, fes in enumerate(bunsetsu_features) if RE_OPEN_EXP.match(fes)
    ]
    assert len(kakko_pos) > 0
    most_left_blacket = kakko_pos[0]
    bpos = 0
    while bpos <= most_left_blacket[0] and RE_KUHAKU_EXP.match(bunsetsu_features[bpos]):
        # 空白を飛ばす
        bpos += 1
    if subj_pos < most_left_blacket[0] or most_left_blacket[0] == bpos:
        # 括弧開きより左にあるあるいは括弧開きが最も左ならsubj_posを返す
        return subj_pos
    assert most_left_blacket[0] > 0
    target_pos = most_left_blacket[0] - 1
    while target_pos >= 0 and RE_KIGO_EXP.match(bunsetsu_features[target_pos]):
        target_pos -= 1
    if target_pos < 0:
        return subj_pos
    return target_pos


SPECIAL_MATCH_RE = re.compile(r"(?:接尾辞,名詞的)")


def check_special_subject_pos(bunsetu: "Bunsetu", subj_fes: str, subj_pos: int) -> int:
    """
        「XX」＋さ は「XX」がheadに
    """
    if not (SPECIAL_MATCH_RE.match(subj_fes) and bunsetu.words()[subj_pos].get_origin() == "さ"):
        return subj_pos
    subj_pos -= 1
    while subj_pos > 0:
        subj_fes = ",".join(bunsetu.words()[subj_pos].get_features())
        if BUNSETU_SUBJ_MATCH_RE.match(subj_fes):
            return subj_pos
        subj_pos -= 1
    return subj_pos


def _detect_dep_inbunsetu(bunsetu: "Bunsetu", parent_pos: Optional[int]) -> None:
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
                word.get_features()[0].startswith(
                    "助") or word.get_features()[1] == "非自立可能"
        ) and not word.is_func():
            # 3. 助詞、助動詞、非自立可能はその他機能語(FUNC), 掛かり先は主辞にかける
            word.dep_num = bunsetu[bunsetu.subj_pos].token_pos
            word.ud_misc["BunsetuPositionType"] = "FUNC"
        else:
            # 4. のこりは主辞にかける
            word.dep_num = bunsetu[bunsetu.subj_pos].token_pos
            word.ud_misc["BunsetuPositionType"] = "CONT"


def detect_dep_bunsetu(sentence: "Sentence") -> None:
    """
        detect bunsetu type
        同時にUDの係り受り先も決める

        特殊な掛かり先の変更は`is_the_special_bunsetu_word`に
    """
    is_the_special_bunsetu_word(sentence)
    for bunsetu in sentence.bunsetues():
        assert bunsetu.bunsetu_pos is not None
        dep_pos, parent_pos = bunsetu.dep_pos, None
        if dep_pos == -1:  # root にする
            parent_pos = 0
        else:
            try:
                assert dep_pos is not None
                parent = sentence.bunsetues()[dep_pos]
            except Exception as exc:
                raise ValueError(
                    "cannot bunsetu of dependency bunsetu: {} {} {}".format(
                        sentence.sent_id, bunsetu.bunsetu_pos, dep_pos
                    )
                ) from exc
            parent_pos = parent[parent.subj_pos].token_pos
        for word in bunsetu:
            # 基本的な文節内係り関係の設定
            _detect_dep_inbunsetu(bunsetu, parent_pos)
        for word in bunsetu:
            # NO_HEADにどうしてもなってしまうものはNO_HEAD（ほとんどない）
            if word.dep_num == word.token_pos:
                word.ud_misc["BunsetuPositionType"] = "NO_HEAD"
                word.dep_num = 0
        # 文節内係り間の変更
        change_dependency_inbunsetu_luw_post_particle(bunsetu)
        change_dependency_inbunsetu_innner_luw_teki(bunsetu)
        change_dependency_outbunsetu_blanck_replace(bunsetu)
    # 文節間係り間の変更
    change_dependency_outbunsetu(sentence)


RE_VERB_MATH = re.compile("^動詞.*")
RE_JOSI_MATCH = re.compile("^助詞")
TARGET_AUX = ["だ", "わけにはいかない", "こともある", "こととなる",
     "ことになる", "ことがある", "こともない", "ことができない", "ではない"]

def change_dependency_outbunsetu(sentence: "Sentence") -> None:
    """ change dependencies for out bunsetu """
    for bunsetu_pos, bunsetu in enumerate(sentence.bunsetues()):
        subj_tok = bunsetu[bunsetu.subj_pos]
        if subj_tok.dep_num == 0:
            continue
        assert subj_tok.dep_num is not None
        parent = sentence.get_word_from_tokpos(subj_tok.dep_num-1)
        bunsetu.logger.debug(bunsetu_pos, bunsetu, parent)
        if parent is None:
            raise KeyError
        if subj_tok.get_xpos() == "補助記号-括弧開" and subj_tok.dep_num != subj_tok.token_pos + 1:
            # 交差していないか確認して、してる場合は諦めて隣にかけるようにする
            nonpro_flag = False
            for ctok in range(1, subj_tok.token_pos):
                wrd = sentence.get_word_from_tokpos(ctok-1)
                assert wrd is not None and wrd.dep_num is not None
                if subj_tok.token_pos <= wrd.dep_num <= parent.token_pos:
                    nonpro_flag = True
                    break
            if nonpro_flag:
                bunsetu[bunsetu.subj_pos].dep_num = subj_tok.token_pos + 1
        elif parent.get_xpos().split("-")[0] == "助動詞" and parent.get_origin() in TARGET_AUX:
            # AUXが親になってしまうものを 入れ替える、AUXにかかるもの自体は変えないため下は未適応
            new_pos = parent.dep_num
            parent.dep_num = subj_tok.token_pos
            subj_tok.dep_num = new_pos
            if subj_tok.dep_num == 0:
                subj_tok.ud_misc["BunsetuPositionType"] = "ROOT"
                parent.ud_misc["BunsetuPositionType"] = "SYN_HEAD"
        elif parent.get_xpos() == "補助記号-括弧開":
            # 括弧開きが掛かり先になっている場合、次の文節の方にかける
            if parent.bunsetu_pos + 1 >= len(sentence):
                # できないので
                continue
            new_target = sentence[parent.bunsetu_pos + 1]
            nsubj_tok = new_target[new_target.subj_pos]
            subj_tok.dep_num = nsubj_tok.token_pos
        elif parent.get_xpos().split("-")[0] == "助動詞" and parent.get_origin() in ["つう"]:
            # AUXが掛かり先の場合、AUXがかかっている先にかける
            if parent.dep_num == 0:
                # できないので
                continue
            nparent = sentence.get_word_from_tokpos(
                cast(int, parent.dep_num)-1
            )
            if nparent is None:
                raise KeyError
            subj_tok.dep_num = nparent.token_pos
        elif parent.get_xpos() == "助詞-格助詞" and parent.get_origin() in ["の"]:
            # PB39_00017-125
            if parent.dep_num == 0:
                # できないので
                continue
            nparent = sentence.get_word_from_tokpos(
                cast(int, parent.dep_num)-1)
            if nparent is None:
                raise KeyError
            subj_tok.dep_num = nparent.token_pos
        elif parent.get_xpos() == "動詞-非自立可能" and parent.get_origin() in ["来る"]:
            if not RE_VERB_MATH.match(subj_tok.get_luw_pos()) or\
                parent.ud_misc["BunsetuPositionType"] == "ROOT":
                # AUXでないパターンがある その場合dep_numをみて入れ替えるのをやめる
                if parent.ud_misc["BunsetuPositionType"] == "SYN_HEAD":
                    parent.ud_misc["BunsetuPositionType"] = "SEM_HEAD"
                continue
            # 入れ替える
            new_pos = parent.dep_num
            parent.dep_num = subj_tok.token_pos
            subj_tok.dep_num = new_pos
            if subj_tok.dep_num == 0:
                subj_tok.ud_misc["BunsetuPositionType"] = "ROOT"
                parent.ud_misc["BunsetuPositionType"] = "SYN_HEAD"
            for _, nbunsetu in enumerate(sentence.bunsetues()):
                # 入れ替えたあと子の確認
                nsubj_tok = nbunsetu[nbunsetu.subj_pos]
                if nsubj_tok.dep_num == parent.token_pos:
                    nsubj_tok.dep_num = subj_tok.token_pos
        elif RE_JOSI_MATCH.match(parent.get_luw_pos()) and parent.get_origin() in ["上", "所"]:
            if parent.word_pos != 0:
                continue
            new_pos = parent.dep_num
            parent.dep_num = subj_tok.token_pos
            subj_tok.dep_num = new_pos
            if subj_tok.dep_num == 0:
                subj_tok.ud_misc["BunsetuPositionType"] = "ROOT"
                parent.ud_misc["BunsetuPositionType"] = "SYN_HEAD"
            for _, nbunsetu in enumerate(sentence.bunsetues()):
                # 入れ替えたあと子の確認
                nsubj_tok = nbunsetu[nbunsetu.subj_pos]
                if nsubj_tok.dep_num == parent.token_pos:
                    nsubj_tok.dep_num = subj_tok.token_pos


RE_JODOUSI_MATCH = re.compile("^(助動詞|助詞)")


def change_dependency_inbunsetu_luw_post_particle(bunsetu: "Bunsetu") -> None:
    """ 「について」みたいな「長単位」は一番上のにかかるように変更する

    Args:
        bunsetu (Bunsetu): 対象文節
    """
    target_positions = []
    for word in bunsetu:
        if word.luw_label == "B" and RE_JODOUSI_MATCH.match(word.get_luw_pos()):
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
        assert len(list(set([bunsetu[w].get_luw_pos()
                             for w in range(target_position, last_pos+1)]))) == 1
        for wrd in range(target_position, last_pos+1):
            if wrd == target_position:
                continue
            bunsetu[wrd].dep_num = bunsetu[target_position].token_pos


def change_dependency_outbunsetu_blanck_replace(bunsetu: "Bunsetu") -> None:
    """ 
    括弧『「』が逆になっているものがあれば、内部にさすようにする
    Args:
        bunsetu (Bunsetu): 対象文節
    """
    if not (bunsetu[bunsetu.subj_pos].get_xpos() == "補助記号-括弧開"
            and bunsetu[bunsetu.subj_pos].ud_misc["BunsetuPositionType"] == "SEM_HEAD"
            and bunsetu.subj_pos+1 < len(bunsetu)
            and bunsetu[bunsetu.subj_pos+1].dep_num == bunsetu[bunsetu.subj_pos].token_pos):
        return
    if bunsetu.subj_pos+1 >= len(bunsetu):
        # できないので
        return
    old_subj_pos = bunsetu.subj_pos
    old_subj_dep = bunsetu[old_subj_pos].dep_num
    bunsetu.subj_pos = old_subj_pos+1
    bunsetu[old_subj_pos].dep_num = bunsetu[old_subj_pos+1].token_pos
    bunsetu[old_subj_pos].ud_misc["BunsetuPositionType"] = "CONT"
    bunsetu[old_subj_pos+1].dep_num = old_subj_dep
    bunsetu[old_subj_pos+1].ud_misc["BunsetuPositionType"] = "SEM_HEAD"
    for cbpos in range(len(bunsetu)-1, old_subj_pos+1, -1):
        if bunsetu[cbpos].dep_num == bunsetu[old_subj_pos].token_pos:
            bunsetu[cbpos].dep_num = bunsetu[old_subj_pos+1].token_pos
    for word in bunsetu.words():
        word.set_bunsetsu_info(
            bunsetu.subj_pos == word.word_pos, bunsetu.func_pos == word.word_pos)


def change_dependency_inbunsetu_innner_luw_teki(bunsetu: "Bunsetu") -> None:
    """ 「地形/的/理由」などを「地形」がHEADではなく「理由」をHEADにする

    Args:
        bunsetu (Bunsetu): 対象文節
    """
    if not (bunsetu.subj_pos+1 < len(bunsetu) and bunsetu[bunsetu.subj_pos+1].get_origin() == "的"
            and bunsetu[bunsetu.subj_pos+1].get_xpos() == "接尾辞-形状詞的"):
        return
    if len([w for w in bunsetu if w.get_xpos() == "接尾辞-形状詞的"]) > 1:
        # 恣意的だが....
        return
    assert len([w for w in bunsetu if w.get_xpos() == "接尾辞-形状詞的"]) == 1
    done_flag = False
    old_subj_pos: Optional[int] = None
    new_subj_pos: Optional[int] = None
    for luw_unit in bunsetu.get_luw_list():
        if done_flag:
            break
        for lpos, lwrd in enumerate(luw_unit):
            if lwrd.word_pos < bunsetu[bunsetu.subj_pos+1].word_pos:
                continue
            assert lwrd.word_pos == bunsetu[bunsetu.subj_pos+1].word_pos
            assert lwrd.get_xpos() == "接尾辞-形状詞的", "{} {} {}".format(
                cast("Sentence", bunsetu.parent_sent).sent_id,
                bunsetu[bunsetu.subj_pos+1].get_xpos(), lwrd.get_xpos())
            if lpos == len(luw_unit) - 1 or bunsetu[lwrd.word_pos+1].get_xpos() != "名詞-普通名詞-一般":
                done_flag = True
                break
            cnt = 1
            while lwrd.word_pos+cnt <= luw_unit[len(luw_unit) - 1].word_pos and\
                bunsetu[lwrd.word_pos+cnt].get_xpos() == "名詞-普通名詞-一般":
                cnt += 1
            # bunsetu[lwrd.word_pos+cnt-1]があらたなsubj_posになる
            assert bunsetu.parent_sent is not None
            old_subj_pos = bunsetu.subj_pos
            new_subj_pos = lwrd.word_pos+cnt-1
            ndep_num = bunsetu[bunsetu.subj_pos].dep_num
            bunsetu[old_subj_pos+1].dep_num = bunsetu[old_subj_pos].token_pos
            bunsetu[old_subj_pos+1].ud_misc["BunsetuPositionType"] = "CONT"
            bunsetu[old_subj_pos].dep_num = bunsetu[new_subj_pos].token_pos
            bunsetu[old_subj_pos].ud_misc["BunsetuPositionType"] = "CONT"
            for nnn in range(cnt-2):
                bunsetu[lwrd.word_pos+nnn +
                        1].dep_num = bunsetu[new_subj_pos].token_pos
                bunsetu[lwrd.word_pos+nnn +
                        1].ud_misc["BunsetuPositionType"] = "CONT"
            bunsetu.subj_pos = new_subj_pos
            bunsetu[new_subj_pos].dep_num = ndep_num
            bunsetu[new_subj_pos].ud_misc["BunsetuPositionType"] = "SEM_HEAD"
            if bunsetu[new_subj_pos].dep_num == 0:
                bunsetu[new_subj_pos].ud_misc["BunsetuPositionType"] = "ROOT"
            done_flag = True
            break
    if old_subj_pos is not None and new_subj_pos is not None:
        for word in bunsetu.words():
            if (word.token_pos > bunsetu[old_subj_pos].token_pos + 1
                and word.dep_num == bunsetu[old_subj_pos].token_pos):
                word.dep_num = bunsetu[new_subj_pos].token_pos
            word.set_bunsetsu_info(
                bunsetu.subj_pos == word.word_pos, bunsetu.func_pos == word.word_pos
            )


def is_the_special_bunsetu_word(sent: "Sentence") -> None:
    """
        特殊な文節だ
    """
    for bunsetu in sent:
        if _is_the_special_bunsetu_word(bunsetu):
            # 入れ替える、実装的に、文節内には一回しかないと仮定
            bunsetu.subj_pos = bunsetu.subj_pos - 1
            for word in bunsetu.words():
                word.set_bunsetsu_info(
                    bunsetu.subj_pos == word.word_pos, bunsetu.func_pos == word.word_pos)


def _is_the_special_bunsetu_word(bunsetu: "Bunsetu") -> bool:
    """
        主辞と機能語を入れ替える対象であるか
            - 名詞-普通名詞-サ変可能/動詞-非自立可能
    """
    txpos = bunsetu[bunsetu.subj_pos].get_xpos()
    if bunsetu.subj_pos > 0 and re.match("動詞-非自立可能", txpos):
        pxpos = bunsetu[bunsetu.subj_pos-1].get_xpos()
        return re.match("名詞-普通名詞-サ変可能", pxpos) is not None
    return False


def detect_bunsetu_jp_type(bunsetu: "Bunsetu") -> Optional[str]:
    """
    コピュラ：名詞+だ
    用言：動詞、形容詞、形容動詞、など
    体言：名詞、代名詞、形式名詞など
    その他（接続詞など）
    長単位でみたほうがよさげ？
    """
    subj_pos, func_pos = bunsetu.subj_pos, bunsetu.func_pos
    subj_luw_pos = bunsetu[subj_pos].get_luw_pos().split("-")[0]
    func_luw_pos = bunsetu[func_pos].get_luw_pos().split("-")[0]
    if func_luw_pos == "助動詞" and any([
        wrd.get_origin() == "だ"
        for wrd in bunsetu if wrd.get_bunsetu_position_type() in ["FUNC", "SYN_HEAD"]
    ]):
        # 体言っぽいもの + 助動詞「だ」
        if subj_luw_pos in ["名詞", "代名詞", "形式名詞", "形状詞"]:
            return "コピュラ"
    if subj_luw_pos in ["動詞", "形容詞", "形容動詞"]:
        # 主辞(長単位レベル)が"動詞", "形容詞", "形容動詞"だ
        return "用言"
    elif subj_luw_pos in ["記号", "名詞", "代名詞", "形式名詞", "形状詞"]:
        # 主辞(長単位レベル)が"名詞", "代名詞", "形式名詞", "形状詞"
        return "体言"
    return "その他"
