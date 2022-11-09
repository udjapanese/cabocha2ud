# -*- coding: utf-8 -*-

"""
長単位が文節をまたいでいるものを修正する
"""

import argparse

from cabocha2ud.bd import BunsetsuDependencies
from cabocha2ud.bd.sentence import Sentence
from cabocha2ud.bd.word import Word


def create_new_dependencies_positon(sent: Sentence) -> tuple[dict[int, int], dict[int, int], set[int]]:
    """ 長単位を超えた文節を結合するための情報を獲得

    Args:
        sent (Sentence): 対象の文

    Returns:
        tuple[dict[int, int], dict[int, int], set[int]]: (target_luw_pos, new_deppos_map, skip_poss)
            dict[int, int]: target_luw_pos: 結合する文節の番号（値は対象番号から手前にある結合する文節の数）
            dict[int, int]: new_deppos_map: 新しいかかり先番号
            set[int]: skip_poss: スキップする文節番号
    """
    new_deppos_map: dict[int, int] = {}
    skip_poss: set[int] = set([])
    target_luw_pos: dict[int, int] = {}
    checked: set[int] = set([])
    npos_diff = 0
    for bpos, bun in enumerate(sent.bunsetues()):
        if bpos in checked:
            continue
        if bun.get_luw_list()[0][0].luw_label == "B":
            new_deppos_map[bpos] = bpos - npos_diff
            continue
        diff = 0
        while bpos+diff < len(sent) and sent[bpos+diff].get_luw_list()[0][0].luw_label != "B":
            checked.add(bpos+diff)
            diff += 1
        last_bpos = bpos+diff-1
        target_luw_pos[last_bpos] = diff
        assert sent[last_bpos].dep_pos not in list(range(bpos-1, last_bpos+1))
        for n in range(bpos-1, last_bpos+1):
            new_deppos_map[n] = bpos - 1 - npos_diff
            if n != last_bpos:
                skip_poss.add(n)
        npos_diff += len(range(bpos-1, last_bpos+1)) - 1
    return target_luw_pos, new_deppos_map, skip_poss


def merge_overluw_for_sentence(sent: Sentence, target_luw_pos: dict[int, int], new_deppos_map: dict[int, int], skip_poss: set[int]) -> None:
    """ 長単位を超えた文節を結合する

    Args:
        sent (Sentence): 対象の文
        target_luw_pos (dict[int, int]) 結合する文節の番号（値は対象番号から手前にある結合する文節の数）
            dict[int, int]: new_deppos_map: 新しいかかり先番号
            set[int]: skip_poss: スキップする文節番号
    """
    # 一度文節番号を無視して新しく文節を構築
    new_bun_count = 0
    for bpos, bun in enumerate(sent.bunsetues()):
        if bpos in skip_poss:
            # 結合する長単位を含む最後の文節まで飛ばす
            continue
        if bpos in target_luw_pos:
            # 最後の文節まできたらLUWをくっつけ、入れ替える
            diff = target_luw_pos[bpos]
            wlist: list[Word] = []
            for p in range(bpos-diff, bpos+1):
                wlist.extend(sent[p].words())
            bun.update_word_list(wlist)
            sent.update_bunsetu(new_bun_count, bun)
        else:
            # それ以外の文節はそのまま挿入
            sent.update_bunsetu(new_bun_count, bun)
        new_bun_count += 1
    for _ in range(len(sent.bunsetues()) - new_bun_count):
        # あまった文節を取り除く
        sent.pop(-1)
    # 番号を再度Update付与
    for bpos in range(len(sent.bunsetues())):
        sent[bpos].bunsetu_pos = bpos
        prev_dep = sent[bpos].dep_pos
        assert isinstance(prev_dep, int)
        sent[bpos].dep_pos = new_deppos_map[prev_dep] if prev_dep != -1 else -1


def _main() -> None:
    """
        main function
    """
    parser = argparse.ArgumentParser("")
    parser.add_argument("base_file", type=str)
    parser.add_argument("-w", "--writer", type=str, default="-")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    b_obj = BunsetsuDependencies(file_name=args.base_file)
    for sent in b_obj.sentences():
        """
            1. 結合する文節を算出する（create_new_dependencies_positon）
            2. 算出結果から長単位を結合する（merge_overluw_for_sentence）
        """
        target_luw_pos, new_deppos_map, skip_poss = create_new_dependencies_positon(sent)
        if len(target_luw_pos) == 0:
            continue
        merge_overluw_for_sentence(sent, target_luw_pos, new_deppos_map, skip_poss)
    b_obj.write_cabocha_file(args.writer)


if __name__ == '__main__':
    _main()
