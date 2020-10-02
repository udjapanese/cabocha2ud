# -*- coding: utf-8 -*-

"""
マルチルートを係り先を変更してシングルにする
プログラム
"""

import argparse
import sys


FIX_POS_FILE_NAME = "conf/fix_projection_lst_2.4.tsv"
def __load_fix_data():
    fix_data = {}
    for line in open(FIX_POS_FILE_NAME):
        sent_id, ddd, fff = line.rstrip("\n").split("\t")
        if sent_id not in fix_data:
            fix_data[sent_id] = {}
        fix_data[sent_id][int(ddd)] = int(fff)
    return fix_data
# FIX_POS_DATA = __load_fix_data()



def fix_projectivity_rule_from_text(sent_st):
    """
        非交差を直す
            1. punctをみる
            2. punctの親と自分の間のノードを確認する
                if 自分のノードを超えるかかり先を発見 -> 非交差
                    その場合自分のノードを超えるかかり先に変更
    """
    data = [line.rstrip("\n").split("\t") for line in sent_st[2:]]
    for line in data:
        if line[7] == 'punct':
            num = int(line[0])
            dep_num = int(line[6])
            if num == len(data):
                # punctが末尾ならrootにかける
                assert num != dep_num
                root = [int(d[0]) for d in data if d[7] == 'root']
                assert len(root) == 1
                root_num = root[0]
                data[int(num)-1][6] = str(root_num)
            elif num > dep_num:
                for nnn in range(dep_num, num):
                    tdep = int(data[int(nnn)][6])
                    if tdep > num:
                        # 交差している
                        data[int(num)-1][6] = str(data[int(dep_num)-1][6])
                        break
    data = ["\t".join(ll) for ll in data]
    return sent_st[0:2] + data


def fix_projectivity_rule_from_hand(sent_st):
    """
        非交差を直す
    """
    sent_id = sent_st[0].split(" ")[-1]
    if sent_id not in FIX_POS_DATA:
        return sent_st
    data = [line.rstrip("\n").split("\t") for line in sent_st[2:]]
    for fix_pos in FIX_POS_DATA[sent_id]:
        data[fix_pos-1][6] = str(FIX_POS_DATA[sent_id][fix_pos])
    data = ["\t".join(ll) for ll in data]
    return sent_st[0:2] + data


def __detect_swap_parent(data, chrd):
    for c_pos in reversed(chrd):
        cdep_label = data[c_pos-1][7]
        if cdep_label not in ['punct', 'aux', 'cc', 'case']:
            return c_pos
    return -1


def swap_dep_rule_from_text(sent_st):
    """
        ccの修正をする....
    """
    target_cc_toks = []
    data = [line.rstrip("\n").split("\t") for line in sent_st[2:]]
    parent_dict = {}
    for line in data:
        # 依存関係の抽出
        num = int(line[0])
        dep_num = int(line[6])
        if dep_num not in parent_dict:
            parent_dict[dep_num] = set([])
        parent_dict[dep_num].add(num)
        if line[7] in ["cc", "punct"]:
            target_cc_toks.append(num)
    if len(target_cc_toks) == 0:  # ccがなかった
        return sent_st
    for cc_tok_num in target_cc_toks:
        if cc_tok_num not in parent_dict:
            continue
        chrd = sorted(parent_dict[cc_tok_num])
        nparent_pos = __detect_swap_parent(data, chrd)
        if nparent_pos == -1:
            ndep = int(data[cc_tok_num-1][6])
            for dcc in parent_dict[cc_tok_num]:
                data[dcc-1][6] = str(ndep)
        else:
            ndep = int(data[cc_tok_num-1][6])
            for dcc in parent_dict[cc_tok_num]:
                if dcc != nparent_pos:
                    data[dcc-1][6] = str(nparent_pos)
            data[cc_tok_num-1][6] = str(nparent_pos)
            data[nparent_pos-1][6] = str(ndep)
    data = ["\t".join(ll) for ll in data]
    return sent_st[0:2] + data


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


def _create_replaced_line_num(data, rm_lst):
    """
        restore below information to json file
            old_pos
               修正後のpos: 修正前のpos
            inserted_token
               修正前のpos: line
    """
    nmap, counter = {0: 0}, 1
    for line in data:
        num = int(line[0])
        if num in rm_lst:
            continue
        nmap[num] = counter
        counter += 1
    return nmap


def __restore_rel(line):
    if line[3] == "PUNCT":
        line[7] = "punct"
    if line[3] == "CCONJ":
        line[7] = "cc"


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
    lst = ["ROOT"] + [int(line[6]) for line in data]
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


def _remove_root(sent_st, mode, debug=False):
    nsent_st = []
    sent_id_line = sent_st[0]
    sent_text_line = sent_st[1]
    data = [line.rstrip("\n").split("\t") for line in sent_st[2:]]
    cnum = sum([int(int(d[6]) == 0) for d in data])
    if cnum == 1:
        return sent_st
    elif cnum == 0:
        assert ValueError("{} must be rather one.".format(cnum))
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
            sent = _remove_root(sent_st, mode, debug=debug)
            # ここにswapルール
            #sent = swap_dep_rule_from_text(sent)
            # ここに非交差修正ルール
            #sent = fix_projectivity_rule_from_text(sent)
            #sent = fix_projectivity_rule_from_hand(sent)
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
