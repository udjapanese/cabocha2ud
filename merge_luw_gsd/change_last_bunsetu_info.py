# -*- coding: utf-8 -*-

"""
python conv_gsd/
"""

import argparse
import itertools
import re


# Cabocha Unidicのコピペ
HEAD_POS_RE = re.compile(r"(?!助詞|助動詞|動詞-非自立可能|接尾辞-形容詞的|接尾辞-形状詞的|接尾辞,動詞的|空白|補助記号|記号)")
FUNC_POS_RE = re.compile(r"(?:助詞|助動詞|接尾辞-形容詞的|接尾辞-形状詞的|接尾辞-動詞的)")


def __detect_pos(last_bunsetu):
    chunk_size = len(last_bunsetu)
    head_pos, func_pos = 0, 0
    for pos in range(chunk_size):
        if FUNC_POS_RE.match(last_bunsetu[pos].split("\t")[3]):
            func_pos = pos
        if HEAD_POS_RE.match(last_bunsetu[pos].split("\t")[3]):
            head_pos = pos
    if head_pos > func_pos:
        func_pos = head_pos
    return head_pos, func_pos

def __check_include_kuten(bunsetu):
    # nbunsetu_info = bunsetu[0].rstrip("\r\n").split(" ")
    nbunsetu = bunsetu[1:]
    chunk_size = len(nbunsetu)
    for pos in range(chunk_size):
        if nbunsetu[pos].split("\t")[3] in ["補助記号-読点", "補助記号-句点"]:
            return pos
    return None


def __check_sentnece(sents):
    nsents = []
    for line in sents:
        if line.startswith("* "):
            nsents.append([line])
            continue
        nsents[-1].append(line)
    for bunsetu_pos, bunsetu in enumerate(nsents):
        # print bunsetu[-1].encode("utf-8")
        kuten_bunsetu_pos = __check_include_kuten(bunsetu)
        if kuten_bunsetu_pos is None:
            continue
        nbunsetu_info = bunsetu[0].rstrip("\r\n").split(" ")
        nbunsetu = bunsetu[1:]
        assert nbunsetu[kuten_bunsetu_pos].split("\t")[3] in ["補助記号-読点", "補助記号-句点"]
        head_pos, func_pos = [int(n) for n in nbunsetu_info[3].split("/")]
        chunk_size = len(nbunsetu)
        head_pos, func_pos = 0, 0
        for pos in range(chunk_size):
            if FUNC_POS_RE.match(nbunsetu[pos].split("\t")[3]):
                func_pos = pos
            if HEAD_POS_RE.match(nbunsetu[pos].split("\t")[3]):
                head_pos = pos
        if head_pos > func_pos:
            func_pos = head_pos
            # print head_pos, func_pos
        nsents[bunsetu_pos][0] = "* {pos} {dep} {head_pos}/{func_pos} {score}".format(
            pos=nbunsetu_info[1], dep=nbunsetu_info[2],
            head_pos=head_pos, func_pos=func_pos, score=nbunsetu_info[4]
        )
    return itertools.chain.from_iterable(nsents)


def main():
    """
    main function
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("cabocha_file", type=argparse.FileType("r"))
    parser.add_argument("-w", "--writer", type=argparse.FileType("w"), default="-")
    args = parser.parse_args()
    line = next(args.cabocha_file)
    while line.startswith("#! "):
        args.writer.write(line)
        line = next(args.cabocha_file)
    sents = [line.rstrip()]
    for line in args.cabocha_file:
        line = line.rstrip()
        if line.startswith("EOS"):
            sents = __check_sentnece(sents)
            args.writer.write("\n".join(sents) + "\n")
            args.writer.write("EOS\n")
            sents = []
            continue
        sents.append(line)


if __name__ == '__main__':
    main()
