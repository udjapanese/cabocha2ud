# -*- coding: utf-8 -*-

"""
merge to sp information to GSD conll file
"""

import argparse
import codecs
from typing import TextIO

from difflib import SequenceMatcher


def load_db_file(db_file: TextIO) -> list[list[dict[str, str]]]:
    """
        load dainagon data
    """
    full_data: list[dict[str, str]] = []
    header = next(db_file).rstrip("\r\n").split("\t")
    for line in db_file:
        item: dict[str, str] = dict(list(zip(header, line.rstrip("\r\n").split("\t"))))
        if item["orthToken(S)"] == '","':
            item["orthToken(S)"] = ','
        full_data.append(item)
    return _split_db_file(full_data, "boundary(S)")


def _split_db_file(full_data: list[dict[str, str]], target_column: str) -> list[list[dict[str, str]]]:
    nfull: list[list[dict[str, str]]] = []
    stack: list[dict[str, str]] = []
    flag: bool = False
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


def load_conll_file(conll_file: TextIO) -> list[list[list[str]]]:
    """
        load conll data
    """
    full_data: list[list[list[str]]] = []
    sent: list[list[str]] = []
    for line in conll_file:
        line = line.rstrip("\r\n")
        if line == "":
            full_data.append(sent)
            sent = []
        else:
            if line.startswith("# "):
                sent.append(line.split(" "))
            else:
                sent.append(line.split("\t"))
    return full_data


def similarity(alst, blst) -> float:
    if len(alst) < len(blst):
        alst, blst = blst, alst
    return SequenceMatcher(None, alst, blst).ratio()


def get_conll_header_pos(conll: list[list[str]]) -> int:
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
    """ SPデータと統合する
     conllデータとSPデータをマッチングする
    Args:
        conll_data ([type]): [description]
        sp_data ([type]): [description]

    Returns:
        [type]: [description]
    """
    assert len(conll_data) <= len(sp_data)
    print(len(conll_data), len(sp_data))
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


def adapt_spafter_to_conll(conll: list[list[str]], spd: list[dict[str, str]]):
    """ adapt spafter to CoNLL line

    Args:
        conll (list[list[str]]): SpaceAfter=を書き換えるCoNLL文
        spd (list[dict[str, str]]): SpaceAfterデータ

    Returns:
        [type]: [description]
    """
    hpos = get_conll_header_pos(conll)
    if all([s["SpaceAfter"] != "YES" for s in spd]):
        return hpos, conll
    nconll = conll[0:hpos]
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


def write_header_including_sp(header: list[str], content: list[str], writer: TextIO) -> None:
    """
        refrected sp information to text line
        SpaceAfter=を元に書き換え
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


def main() -> None:
    """
        main function
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("conll_file")
    parser.add_argument("sp_file")
    parser.add_argument("-w", "--writer", default="output.conllu")
    args = parser.parse_args()
    conll_data: list[list[list[str]]] = []
    sp_data: list[list[dict[str, str]]] = []
    with codecs.open(args.conll_file, encoding="utf-8") as conll_file:
        conll_data = load_conll_file(conll_file)
    with codecs.open(args.sp_file, encoding="utf-8") as sp_file:
        sp_data = load_db_file(sp_file)
    pos_list = get_merged_poslist(conll_data, sp_data)
    with codecs.open(args.writer, "w", encoding="utf-8") as writer:
        for cpos, spos in pos_list:
            hpos, result = adapt_spafter_to_conll(conll_data[cpos], sp_data[spos])
            write_header_including_sp(result[:hpos], result[hpos:], writer)
            for line in result[hpos:]:
                writer.write("\t".join(line) + "\n")
            writer.write("\n")


if __name__ == '__main__':
    main()
