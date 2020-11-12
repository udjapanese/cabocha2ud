# -*- coding: utf-8 -*-

"""
merge to sp information to GSD conll file
"""

import argparse
import codecs

from difflib import SequenceMatcher


def load_db_file(db_file):
    """
        load dainagon data
    """
    full_data = []
    header = next(db_file).rstrip("\r\n").split("\t")
    for line in db_file:
        line = line.rstrip("\r\n").split("\t")
        item = dict(list(zip(header, line)))
        if item["orthToken(S)"] == '","':
            item["orthToken(S)"] = ','
        full_data.append(item)
    return _split_db_file(full_data, "boundary(S)")


def _split_db_file(full_data, target_column):
    nfull, stack = [], []
    flag = False
    for item in full_data:
        if flag and item[target_column] == "B":
            nfull.append(stack)
            stack = []
        flag = True
        stack.append(item)
    assert stack[0][target_column] == "B"
    if len(stack) > 0:
        nfull.append(stack)
    return nfull

def load_conll_file(conll_file):
    """
        load conll data
    """
    full_data, sent = [], []
    for line in conll_file:
        line = line.rstrip("\r\n")
        if line == "":
            full_data.append(sent)
            sent =[]
        else:
            if line.startswith("# "):
                sent.append(line.split(" "))
            else:
                sent.append(line.split("\t"))
    return full_data


def similarity(alst, blst):
    if len(alst) < len(blst):
        alst, blst = blst, alst
    return SequenceMatcher(None, alst, blst).ratio()


def get_conll_header_pos(conll):
    """
        detect conll header size
    """
    cnt = 0
    for line in conll:
        if line[0] != "#":
            break
        cnt += 1
    return cnt


def get_merged_poslist(conll_data, sp_data):
    assert len(conll_data) <= len(sp_data)
    if len(conll_data) == len(sp_data):
        return [(p, p) for p in range(len(conll_data))]
    sp_it = iter(enumerate(sp_data))
    pos_list = []
    for cpos in range(len(conll_data)):
        spos, cand_sp = next(sp_it)
        hpos = get_conll_header_pos(conll_data[cpos])
        stext = "".join([c["orthToken(S)"] for c in cand_sp])
        ctext = "".join([c[1] for c in conll_data[cpos][hpos:]])
        while similarity(stext, ctext) < 0.8:
            spos, cand_sp = next(sp_it)
            stext = "".join([c["orthToken(S)"] for c in cand_sp])
        pos_list.append((cpos, spos))
    assert len(pos_list) == len(conll_data)
    return pos_list


def matching_from_seqmath(conll, spd):
    """
        diff using by SequenceMatcher
         return [(conll_wrd_pos, spd_wrd_pos_tuple), ....]
    """
    assert len(conll) <= len(spd)
    cwrds = [c[1] for c in conll]
    swrds = [c["orthToken(S)"] for c in spd]
    if len(cwrds) == len(swrds):
        return [(p, (p, )) for p in range(len(cwrds))]
    smcr = SequenceMatcher(None, cwrds, swrds)
    pos_lst = []
    for opt, ii1, ii2, jj1, jj2 in smcr.get_opcodes():
        #print(opt, ii1, ii2, jj1, jj2)
        if opt == 'equal':
            assert cwrds[ii1:ii2] == swrds[jj1:jj2]
            for iii, jjj in zip(range(ii1, ii2), range(jj1, jj2)):
                pos_lst.append((iii, (jjj, )))
        elif opt == 'replace':
            assert ii2 - ii1 <= jj2 - jj1 and ii2 - ii1 == 1
            pos_lst.append(
                (ii1, tuple([j for j in range(jj1, jj2)]))
            )
        else:
            assert KeyError("not found: ", opt)
    return pos_lst


def adapt_spafter_to_conll(conll, spd):
    """
    TODO:
    mergeした数字対応対策をする
    textも書き換えること
    """
    hpos = get_conll_header_pos(conll)
    if not any([s["SpaceAfter"] == "YES" for s in spd]):
        return hpos, conll
    nconll = conll[0:hpos]
    # テキスト書き換え用
    word_lst = []
    assert len(conll[hpos:]) <= len(spd)
    result_pos = matching_from_seqmath(conll[hpos:], spd)
    assert [p for p, _ in result_pos] == list(range(len(conll[hpos:])))
    for cpos, sp_pos in result_pos:
        assert isinstance(sp_pos, tuple)
        if len(sp_pos) == 1:  # 1対1
            if spd[sp_pos[0]]["SpaceAfter"] == "YES":
                nccc = [
                    "SpaceAfter=Yes" if ddd.startswith("SpaceAfter") else ddd
                    for ddd in conll[hpos:][cpos][-1].split("|")
                ]
                nconll.append(conll[hpos:][cpos][:-1] + ["|".join(nccc)])
            else:
                nconll.append(conll[hpos:][cpos])
        elif len(sp_pos) > 1:
            assert all([spd[spos]["SpaceAfter"] != "YES" for spos in sp_pos])
            nconll.append(conll[hpos:][cpos])
    assert len(conll) == len(nconll)
    return hpos, nconll


def output_header_including_sp(header, content, writer):
    """
        refrected sp information to text line
    """
    for hhh in header:
        assert hhh[0] == "#"
        if hhh[1] == "text":
            assert hhh[3] == "".join([c[1] for c in content])
            writer.write("# text = ")
            wrds = []
            for cont in content:
                wrd, inf = cont[1], cont[-1]
                wrds.append(wrd)
                if any([iii == "SpaceAfter=Yes" for iii in inf.split("|")]):
                    wrds.append(" ")
            writer.write("".join(wrds) + "\n")
        else:
            writer.write(" ".join(hhh) + "\n")


def main():
    """
        main function
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("conll_file")
    parser.add_argument("sp_file")
    parser.add_argument("-w", "--writer", default="output.conllu")
    args = parser.parse_args()
    conll_data, sp_data = None, None
    with codecs.open(args.conll_file, encoding="utf-8") as conll_file:
        conll_data = load_conll_file(conll_file)
    with codecs.open(args.sp_file, encoding="utf-8") as sp_file:
        sp_data = load_db_file(sp_file)
    pos_list = get_merged_poslist(conll_data, sp_data)
    with codecs.open(args.writer, "w", encoding="utf-8") as writer:
        for cpos, spos in pos_list:
            hpos, result = adapt_spafter_to_conll(conll_data[cpos], sp_data[spos])
            output_header_including_sp(result[:hpos], result[hpos:], writer)
            for line in result[hpos:]:
                writer.write("\t".join(line) + "\n")
            writer.write("\n")


if __name__ == '__main__':
    main()
