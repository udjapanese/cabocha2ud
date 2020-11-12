# -*- coding: utf-8 -*-

"""
マルチルートを係り先を変更してシングルにする
プログラム
"""

import argparse
import sys

COLCOUNT = 10
ID, FORM, LEMMA, UPOS, XPOS, FEATS, HEAD, DEPREL, DEPS, MISC = range(COLCOUNT)


def collect_ancestors(id, tree, ancestors):
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


def get_caused_nonprojectivities(iid, tree):
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


def build_tree(sentence):
    tree = {'nodes': [['0', '_', '_', '_', '_', '_', '_', '_', '_', '_']]}
    for line in sentence:
        tree['nodes'].append(line)
    return tree


def fix_projectivity_rule_to_punct(data, tree):
    """
        punctの非交差を直す
    """
    nonproj_list = {}
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
                conf_pos = nonproj_list[fix_target]
                assert len(conf_pos) == 1
                conf_pos = conf_pos[0]
                new_fix_pos = fix_target - 1
                while conf_pos < new_fix_pos and int(data[new_fix_pos-1][HEAD]) != save_head:
                    new_fix_pos = new_fix_pos - 1
                if conf_pos < new_fix_pos:
                    data[conf_pos-1][HEAD] = str(new_fix_pos)
                    data[fix_target-1][HEAD] = str(new_fix_pos)
    return data


def fix_leafpunct_rule_to_punct(data):
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


def separate_document(conll_file):
    """
        文書ごとに区切る
    """
    bstack, tid, prev_tid = [], None, None
    line = next(conll_file).rstrip("\r\n")
    try:
        while True:
            assert line.startswith("# sent_id =")
            tid = line.split(" ")[3].split("-")[0]
            if prev_tid is not None and tid != prev_tid:
                yield bstack
                bstack = []
            while line != "":
                bstack.append(line)
                line = next(conll_file).rstrip("\r\n")
            bstack.append(line)
            prev_tid = tid
            line = next(conll_file).rstrip("\r\n")
    except StopIteration:
        yield bstack


def separate_sentence(conll_file):
    """
        文分割する
    """
    cstack = []
    for line in conll_file:
        if line == "":
            yield cstack
            cstack = []
            continue
        cstack.append(line)


def __restore_rel(line):
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


def __remove_root(sent_id_line, data, sent_text_line):
    """
        複数あるルートを決定する
    """
    nsent_st = []
    lst = ["ROOT"] + [int(line[HEAD]) for line in data]
    tree = {}
    for pos, dnum in enumerate(lst):
        if dnum == "ROOT":
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


def remove_multi_root(sent_st, mode, debug=False):
    """
        いくつかの方法でmulti rootを除く
    """
    nsent_st = []
    sent_id_line = sent_st[0]
    sent_text_line = sent_st[1]
    data = [line.rstrip("\n").split("\t") for line in sent_st[2:]]
    cnum = sum([int(int(d[6]) == 0) for d in data])
    if cnum == 1:
        return sent_st
    elif cnum == 0:
        assert ValueError("`root` must be rather one in sentence, but {}".format(cnum))
    else:
        if debug:
            sys.stderr.write("{} is {}\n".format(sent_id_line.strip("#"), mode))
        if mode == "convert":
            nsent_st = __remove_root(sent_id_line, data, sent_text_line)
        elif mode == "remove":
            return []
        else:
            raise KeyError("cannot use `{}`, `mode` must be `convert` or `remove`".format(mode))
    return nsent_st


def remove_root_from_sentence(conll_file, mode, writer, debug=False):
    """
        fill word by bccwj file
    """
    if debug:
        sys.stderr.write("mode: {}\n".format(mode))
    for cnl in separate_document(conll_file):
        assert cnl[0].startswith("# sent_id =")
        for sent_st in separate_sentence(cnl):
            # ひとまずrootを決める
            sent = remove_multi_root(sent_st, mode, debug=debug)
            header = sent[0:2]
            data = [line.rstrip("\n").split("\t") for line in sent[2:]]
            tree = build_tree(data)
            # ここに非交差修正ルール
            data = fix_projectivity_rule_to_punct(data, tree)
            # ここにpunct修正ルール
            data = fix_leafpunct_rule_to_punct(data)
            sent = header + ["\t".join(ll) for ll in data]
            if len(sent) > 0:
                for sss in sent:
                    writer.write(sss + "\n")
                writer.write("\n")


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument("conll_file", type=argparse.FileType("r"))
    parser.add_argument(
        "mode", choices=["convert", "remove"], help="""
            convert: シングルルートに変換する
            remove: マルチルートを削除する
        """
    )
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("-w", "--writer", type=argparse.FileType("w"), default="-")
    args = parser.parse_args()
    remove_root_from_sentence(args.conll_file, args.mode, args.writer, debug=args.debug)


if __name__ == '__main__':
    _main()
