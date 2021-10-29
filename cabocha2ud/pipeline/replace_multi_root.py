# -*- coding: utf-8 -*-

"""
マルチルートを係り先を変更してシングルにする
プログラム
"""

import argparse
from typing import Optional

from cabocha2ud.ud import UniversalDependencies
from cabocha2ud.ud.sentence import Sentence
from cabocha2ud.lib.logger import Logger
from cabocha2ud.ud.util import ID, FORM, LEMMA, UPOS, XPOS, FEATS, HEAD, DEPREL, DEPS, MISC
COLCOUNT = len([ID, FORM, LEMMA, UPOS, XPOS, FEATS, HEAD, DEPREL, DEPS, MISC])


def collect_ancestors(id: int, tree: dict, ancestors: list[int]) -> list[int]:
    """
    Usage: ancestors = collect_ancestors(nodeid, nodes, [])
    """
    pid = int(tree['nodes'][int(id)][HEAD])
    if pid == 0:
        ancestors.append(0)
        return ancestors
    if pid in ancestors:
        # Cycle has been reported on level 2. But we must jump out of it now.
        return ancestors
    ancestors.append(pid)
    return collect_ancestors(pid, tree, ancestors)


def get_caused_nonprojectivities(iid: int, tree: dict) -> list[int]:
    """
    Checks whether a node is in a gap of a nonprojective edge. Report true only
    if the node's parent is not in the same gap. (We use this function to check
    that a punctuation node does not cause nonprojectivity. But if it has been
    dragged to the gap with a larger subtree, then we do not blame it.)
    tree ... dictionary:
      nodes ... array of word lines, i.e., lists of columns; mwt and empty nodes are skipped, indices equal to ids (nodes[0] is empty)
      children ... array of sets of children indices (numbers, not strings); indices to this array equal to ids (children[0] are the children of the root)
      linenos ... array of line numbers in the file, corresponding to nodes (needed in error messages)
    """
    ancestors = collect_ancestors(iid, tree, [])
    maxid = len(tree['nodes']) - 1
    pid = int(tree['nodes'][iid][HEAD])
    if pid < iid:
        left = range(pid + 1, iid)
        right = range(iid + 1, maxid + 1)
    else:
        left = range(1, iid)
        right = range(iid + 1, pid)
    sancestors = set(ancestors)
    leftna = [x for x in left if int(tree['nodes'][x][HEAD]) not in sancestors]
    rightna = [x for x in right if int(tree['nodes'][x][HEAD]) not in sancestors]
    leftcross = [x for x in leftna if int(tree['nodes'][x][HEAD]) > iid]
    rightcross = [x for x in rightna if int(tree['nodes'][x][HEAD]) < iid]
    if pid < iid:
        rightcross = [x for x in rightcross if int(tree['nodes'][x][HEAD]) > pid]
    else:
        leftcross = [x for x in leftcross if int(tree['nodes'][x][HEAD]) < pid]
    return sorted(leftcross + rightcross)


def build_tree(sentence: list[list[str]]) -> dict[str, list[list[str]]]:
    tree = {'nodes': [['0', '_', '_', '_', '_', '_', '_', '_', '_', '_']]}
    for line in sentence:
        tree['nodes'].append(line)
    return tree


def fix_projectivity_rule_to_punct(data: list[list[str]], tree: dict) -> list[list[str]]:
    """
        punctの非交差を直す
    """
    nonproj_list: dict[int, list[int]] = {}
    for line in data:
        # 再び非交差を確認する
        if line[DEPREL] == 'punct':
            num, dep_num = int(line[ID]), int(line[HEAD])
            nonprojnodes = get_caused_nonprojectivities(num, tree)
            if nonprojnodes:
                nonproj_list[num] = nonprojnodes
    if len(nonproj_list) > 0:
        for fix_target in nonproj_list:
            kakko_pos = data[fix_target-1][XPOS]
            assert kakko_pos in ["補助記号-括弧開", "補助記号-括弧閉"]
            if kakko_pos == "補助記号-括弧開":
                # 外にあるのが問題なので括弧開直後の単語にかける
                data[fix_target-1][HEAD] = str(int(data[fix_target-1][ID]) + 1)
            else:
                # 下括弧と上の方の掛かり先を、下括弧がかけていた最下の単語へと入れ替える
                #  対象文: A240n_OY14_03106-10, OC09_04679-5
                save_head = int(data[fix_target-1][HEAD])
                conf_pos_l = nonproj_list[fix_target]
                assert len(conf_pos_l) == 1
                conf_pos = conf_pos_l[0]
                new_fix_pos = fix_target - 1
                while conf_pos < new_fix_pos and int(data[new_fix_pos-1][HEAD]) != save_head:
                    new_fix_pos = new_fix_pos - 1
                if conf_pos < new_fix_pos:
                    data[conf_pos-1][HEAD] = str(new_fix_pos)
                    data[fix_target-1][HEAD] = str(new_fix_pos)
    return data


def fix_leafpunct_rule_to_punct(data: list[list[str]]) -> list[list[str]]:
    errors = []
    for line in data:
        num, parent_num = int(line[ID]), int(line[HEAD])
        if line[DEPREL] != 'punct' and data[parent_num-1][XPOS] == '補助記号-括弧開':
            errors.append([num, parent_num])
    if len(errors) == 0:
        return data
    if len(set([parent_num for num, parent_num in errors])) != 1:
        # おなじ親がふさわしい
        return data
    parent_num = [parent_num for num, parent_num in errors][0]
    cand_parent = int(parent_num) + 1
    if cand_parent > len(data) or data[cand_parent-1][DEPREL] == 'punct':
        return data
    assert int(data[cand_parent-1][HEAD]) == parent_num
    data[cand_parent-1][HEAD] = data[parent_num-1][HEAD]
    data[parent_num-1][HEAD] = str(cand_parent)
    if data[cand_parent-1][HEAD] == "0":
        data[cand_parent-1][DEPREL] = "root"
        data[parent_num-1][DEPREL] = "punct"
    for enum, _ in errors:
        if enum == cand_parent:
            continue
        data[int(enum)-1][HEAD] = str(cand_parent)
    for line in data:
        num, aparent_num = int(line[ID]), int(line[HEAD])
        if line[DEPREL] == 'punct' and aparent_num == parent_num:
            line[HEAD] = str(cand_parent)
    return data


def __restore_rel(line: list[str]) -> None:
    if line[UPOS] == "PUNCT":
        line[DEPREL] = "punct"
    if line[UPOS] == "CCONJ":
        line[DEPREL] = "cc"


def __detect_true_root(data, numlst):
    target_pos = 1
    true_root = numlst[len(numlst)-target_pos]
    num_line = {int(line[0]): line for line in data}
    true_root_pos = num_line[true_root][3]
    while len(numlst)-target_pos >= 0 and true_root_pos == "PUNCT":
        target_pos += 1
        true_root = numlst[len(numlst)-target_pos]
        true_root_pos = num_line[true_root][3]
    if len(numlst)-target_pos == -1:
        # どれもpunctの場合は最後のを選び直す
        true_root = numlst[-1]
    frmpos = [n for n in numlst if n != true_root]
    return frmpos, true_root


def __remove_root(sent_id_line: str, data: list[list[str]], sent_text_line: str) -> list[str]:
    """
        複数あるルートを決定する
    """
    nsent_st = []
    lst: list[int] = [-1] + [int(line[HEAD]) for line in data]
    tree: dict[int, set] = {}
    for pos, dnum in enumerate(lst):
        if dnum == -1:
            continue
        if dnum not in tree:
            tree[dnum] = set()
        tree[dnum].add(pos)
    numlst = sorted(tree[0])
    frmpos, true_root = __detect_true_root(data, numlst)
    nsent_st.append(sent_id_line)
    nsent_st.append(sent_text_line)
    for line in data:
        num, dnum = int(line[0]), int(line[6])
        if num in frmpos:
            assert dnum == 0
            dnum = true_root
            line[7] = "dep"
            __restore_rel(line)
        nsent_st.append("\t".join([str(num)] + line[1:6] + [str(dnum)] + line[7:]))
    return nsent_st


def remove_multi_root(sent_st: list[str], mode: str, logger: Logger) -> list[str]:
    """
        いくつかの方法でmulti rootを除く
    """
    sent_id_line: str = sent_st[0]
    sent_text_line: str = sent_st[1]
    data = [line.rstrip("\n").split("\t") for line in sent_st[2:]]
    cnum = sum([int(int(d[6]) == 0) for d in data])
    if cnum == 1:
        return sent_st
    elif cnum == 0:
        assert ValueError("`root` must be rather one in sentence, but {}".format(cnum))
    logger.debug("{} is {}".format(sent_id_line.strip("#"), mode))
    if mode == "convert":
        return __remove_root(sent_id_line, data, sent_text_line)
    elif mode == "remove":
        return []
    else:
        raise KeyError("cannot use `{}`, `mode` must be `convert` or `remove`".format(mode))


def do(ud: UniversalDependencies, mode: str, logger: Optional[Logger]=None) -> None:
    if logger is None:
        logger = Logger()
    logger.debug("do replace multi root")
    rm_sent_lst: list[int] = []
    for pos, ud_sent in enumerate(ud.sentences()):
        sent_st = ud_sent.get_str_list(mode="full")
        sent = remove_multi_root(sent_st, mode, logger=logger)
        header = ud_sent.get_str_list(mode="header")
        data = [line.rstrip("\n").split("\t") for line in sent[len(header):]]
        tree = build_tree(data)
        # ここに非交差修正ルール
        data = fix_projectivity_rule_to_punct(data, tree)
        # ここにpunct修正ルール
        data = fix_leafpunct_rule_to_punct(data)
        sent = header + ["\t".join(ll) for ll in data]
        if len(data) > 0:
            nsent = Sentence.load_from_list(sent)
            ud.update_sentence_of_index(pos, nsent)
        elif mode == "remove":
            rm_sent_lst.append(pos)
    ud.remove_sentence_from_index(rm_sent_lst)


def _main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("conll_file")
    parser.add_argument(
        "mode", choices=["convert", "remove"], help="""
            convert: シングルルートに変換する
            remove: マルチルートを削除する
        """
    )
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("-w", "--writer", default="-", type=str)
    args = parser.parse_args()
    logger = Logger(debug=args.debug)
    logger.debug("mode: {}".format(args.mode))
    ud = UniversalDependencies(file_name=args.conll_file)
    do(ud, args.mode, logger=logger)
    ud.write_ud_file(args.writer)


if __name__ == '__main__':
    _main()
