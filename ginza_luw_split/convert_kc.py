# -*- coding: utf-8 -*-

"""
convert to KC format for cabocha files
"""

import sys
import argparse
from typing import List

from cabocha2ud.lib.iterate_function import iterate_document, iterate_sentence


def filter_excabocha_information(lines: List[str]) -> List[str]:
    return [line for line in lines if not line.startswith("#! ")]


def to_kc(tokens: List[str]) -> List[str]:
    result: List[str] = []
    spos = tokens[1].split(",")
    detail_spos = "-".join([s for s in spos[0:4] if s != "*"])
    lpos = tokens[3].split(",")
    detail_lpos = "-".join([s for s in lpos[0:4] if s != "*"])
    result.extend([
        tokens[0], spos[6] if spos[6] != "" else "*", spos[7] if spos[7] != "" else "*",
        detail_spos, spos[4] if spos[4] != "" else "*", spos[5] if spos[5] != "" else "*",
        spos[20] if spos[20] != "" else spos[23] if spos[23] != "" else "*",
        spos[6] if spos[6] != "" else "*", spos[7] if spos[7] != "" else "*", spos[8] if spos[8] != "" else "*",
        "*", "*", spos[12]
    ])
    if tokens[2] != "":
        # this is LUW-B information
        result.append(detail_lpos)
        result.append(lpos[4] if lpos[4] != "" else "*")
        result.append(lpos[5] if lpos[5] != "" else "*")
        result.append(lpos[6] if lpos[6] != "" else "*")
        result.append(lpos[7] if lpos[7] != "" else "*")
        result.append(tokens[2])
    else:
        # this is LUW-I information
        result.extend(["*", "*", "*", "*", "*", "*"])
    assert len(result) == 19
    return result


def convert_sent_kc(senttext: List[str]) -> List[str]:
    result: List[str] = []
    for sent in senttext:
        if sent.startswith("* "):
            result.append("*B")
        else:
            tokens = sent.split("\t")
            result.append(" ".join(to_kc(tokens)))
    result.append("EOS")
    return result


def convert_kc(lines: List[str]) -> List[str]:
    result_output: List[str] = []
    for _, doctext, _ in iterate_document(lines, separate_info=False):
        for senttext, _ in iterate_sentence(filter_excabocha_information(doctext), separate_info=False):
            result_output.extend(convert_sent_kc(senttext))
    return result_output


def main() -> None:
    """
        main function
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("cabocha_file", type=str)
    parser.add_argument("writer", type=str)
    args = parser.parse_args()
    cabocha_file = args.cabocha_file
    writer = args.writer
    lines: List[str] = []
    if cabocha_file == "-":
        lines = [line.rstrip("\n") for line in sys.stdin]
    else:
        with open(cabocha_file, "r") as rdr:
            lines = [line.rstrip("\n") for line in rdr]
    result_output = convert_kc(lines)
    if writer == "-":
        for line in result_output:
            sys.stdout.write(line + "\n")
        return
    with open(writer, "w") as wrt:
        for line in result_output:
            wrt.write(line + "\n")


if __name__ == '__main__':
    main()

