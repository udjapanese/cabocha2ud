# -*- coding: utf-8 -*-

"""
show luw parse result from cabocha files
"""

import sys
import argparse
from typing import TextIO, List, Optional


def _strip_sp(ressent: List[List[str]]) -> List[List[str]]:
    nnressent: List[List[str]] = []
    # 先頭処理
    flag = False
    for res in ressent:
        _surface, luw_pos = res
        if _surface == "　":
            continue
        nnressent.append([_surface, luw_pos])
    return nnressent


def _extract_mecabpos(pos: List[str]) -> str:
    fes_l: List[str] = []
    for item in pos[0:4]:
        if item == "*":
            break
        fes_l.append(item)
    return "-".join(fes_l)


def parse_gold_cabocha(gold_file: Optional[TextIO], strip_sp: bool=True) -> List[List[List[str]]]:
    if gold_file is None:
        return []
    sent: List[List[str]] = []
    result: List[List[List[str]]] = []
    prev_pos: str = ""
    for line in gold_file:
        line = line.rstrip("\n")
        if line == "EOS":
            ressent: List[list] = []
            for token in sent:
                _surface: str = token[0]
                _pos = token[3].split(",")
                _luw = token[2]
                luw_pos: str = ""
                if _luw != "":
                    _lpos = _extract_mecabpos(_pos)
                    luw_pos = "B" + "-" + _lpos
                    prev_pos = _lpos
                else:
                    luw_pos = "I" + "-" + prev_pos
                ressent.append([_surface, luw_pos])
            if strip_sp:
                ressent = _strip_sp(ressent)
            result.append(ressent)
            sent = []
        elif line.startswith("#!") or line.startswith("* "):
            continue
        else:
            tokens = line.split("\t")
            sent.append(tokens)
    return result


def _parse_kc_output(base_file: TextIO, strip_sp: bool=True) -> List[List[List[str]]]:
    result: List[List[List[str]]] = []
    sent: List[List[str]] = []
    text: str = ""
    for line in base_file:
        line = line.rstrip("\n")
        if line == "EOS":
            ressent: List[List[str]] = []
            prev_pos = "_"
            for token in sent:
                bio = token[0]
                _surface = token[1]
                luw_pos = "_"
                if bio.replace("a", "") == "B":
                    luw_pos = bio.replace("a", "") + "-" + token[14]
                    prev_pos = token[14]
                else:
                    assert bio.replace("a", "") == "I"
                    luw_pos = "I" + "-" + prev_pos
                ressent.append([_surface, luw_pos])
            if strip_sp:
                ressent = _strip_sp(ressent)
            result.append(ressent)
            sent = []
        else:
            tokens: List[str] = line.split(" ")
            sent.append(tokens)
    return result


def _parse_ginza_output(base_file: TextIO, strip_sp: bool=True) -> List[List[List[str]]]:
    result: List[List[List[str]]] = []
    sent: List[List[str]] = []
    text: str = ""
    for line in base_file:
        line = line.rstrip("\n")
        if line == "":
            ttext: str = ""
            ressent: List[List[str]] = []
            for token in sent:
                _surface = token[1]
                ttext += _surface
                _inf = token[9]
                inf = dict([(k.split("=")[0], "".join(k.split("=")[1:])) for k in _inf.split("|")])
                luw_pos = "_"
                if "ENE" in inf:
                    luw_pos = inf["ENE"]
                ressent.append([_surface, luw_pos])
            if strip_sp:
                ressent = _strip_sp(ressent)
            result.append(ressent)
            assert text == ttext
            sent = []
        elif line.startswith("# text"):
            text = line.replace("# text = ", "")
        else:
            tokens: List[str] = line.split("\t")
            sent.append(tokens)
    return result


def parse_output(mode: str, base_file: Optional[TextIO], strip_sp: bool=True) -> List[List[List[str]]]:
    if base_file is None:
        return []
    if mode == "ginza":
        return _parse_ginza_output(base_file)
    elif mode == "kc":
        return _parse_kc_output(base_file)
    else:
        raise KeyError


def main(mode: str, base_file: str, gold_file: str, writer: str="-") -> None:
    """
        main function
    """
    gold, result = [], []
    with open(gold_file, "r") as rdr:
        gold = parse_gold_cabocha(rdr)
    with open(base_file, "r") as rdr:
        result = parse_output(mode, rdr)
    output: List[str] = []
    assert len(gold) == len(result)
    print(len(gold), len(result))
    full_count: int = 0
    corr_count: int = 0
    scorr_count: int = 0
    for gold_sent, res_sent in zip(gold, result):
        assert len(gold_sent) == len(res_sent)
        for gtoken, rtoken in zip(gold_sent, res_sent):
            assert gtoken[0] == rtoken[0]
            ans = "x"
            if gtoken[1] == rtoken[1]:
                corr_count += 1
                scorr_count += 1
                ans = "o"
            elif gtoken[1].split("-")[0] == rtoken[1].split("-")[0]:
                scorr_count += 1
                ans = "△"
            output.append("{}\t{}\t{}\t{}\n".format(gtoken[0], gtoken[1], rtoken[1], ans))
            full_count += 1
    if writer == "-":
        for line in output:
            sys.stdout.write(line)
        sys.stdout.write("result count（品詞つき）: {}/{} ({})\n".format(corr_count, full_count, corr_count / float(full_count)))
        sys.stdout.write("result count（品詞抜き）: {}/{} ({})\n".format(scorr_count, full_count, scorr_count / float(full_count)))
    else:
        with open(writer, "w") as writer_obj:
            for line in output:
                writer_obj.write(line)
            writer_obj.write("result count（品詞つき）: {}/{} ({})\n".format(corr_count, full_count, corr_count / float(full_count)))
            writer_obj.write("result count（品詞抜き）: {}/{} ({})\n".format(scorr_count, full_count, scorr_count / float(full_count)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["ginza", "kc"])
    parser.add_argument("base_file", type=str)
    parser.add_argument("gold_file", type=str)
    parser.add_argument("writer", type=str)
    args = parser.parse_args()
    main(args.mode, args.base_file, args.gold_file, args.writer)


