# -*- coding: utf-8 -*-

"""
BCCWJ LUW file
"""

import argparse
import os
import glob

LUW_HEADER = [
    "corpusName(S)",
    "file(S)",
    "start(S)",
    "end(S)",
    "boundary(S)",
    "orthToken(S)",
    "pronToken(S)",
    "reading(S)",
    "lemma(S)",
    "originalText(S)",
    "pos(S)",
    "sysCType(S)",
    "cForm(S)",
    "apply(S)",
    "additionalInfo(S)",
    "lid(S)",
    "meaning(S)",
    "UpdUser(S)",
    "UpdDate(S)",
    "order(S)",
    "note(S)",
    "open(S)",
    "close(S)",
    "wType(S)",
    "fix(S)",
    "variable(S)",
    "formBase(S)",
    "lemmaID(S)",
    "usage(S)",
    "sentenceId(S)",
    "s_memo(S)",
    "origChar(S)",
    "pSampleID(S)",
    "pStart(S)",
    "orthBase(S)",
    "file(L)",
    "l_orthToken(L)",
    "l_pos(L)",
    "l_cType(L)",
    "l_cForm(L)",
    "l_reading(L)",
    "l_lemma(L)",
    "luw(L)",
    "memo(L)",
    "UpdUser(L)",
    "UpdDate(L)",
    "l_start(L)",
    "l_end(L)",
    "bunsetsu1(L)",
    "bunsetsu2(L)",
    "corpusName(L)",
    "diffSuw(L)",
    "l_lemmaNew(L)",
    "l_readingNew(L)",
    "l_orthBase(L)",
    "l_formBase(L)",
    "l_pronToken(L)",
    "l_wType(L)",
    "l_originalText(L)",
    "complex(L)",
    "l_meaning(L)",
    "l_kanaToken(L)",
    "l_formOrthBase(L)",
    "l_origChar(L)",
    "note(L)",
    "pSampleID(L)",
    "pStart(L)", ""
]


def iterate_db_file(db_filename):
    """
        iterate db file by pSampleID
    """
    with open(db_filename, encoding="utf-16") as db_file:
        tmp_lst, prev_item = [], None
        for line in db_file:
            items = line.rstrip("\r\n").split("\t")
            ditems = dict(zip(LUW_HEADER, items))
            if ditems["pSampleID(S)"] == "":
                ditems["pSampleID(S)"] = prev_item
            if prev_item is not None and ditems["pSampleID(S)"] != prev_item:
                yield prev_item, tmp_lst
                tmp_lst = []
            tmp_lst.append("\t".join(items))
            prev_item = ditems["pSampleID(S)"]
        if len(tmp_lst) > 0:
            yield prev_item, tmp_lst


def _conv_filename(filename):
    return "_".join(
        os.path.basename(filename).split("_")[2:4]
    ).replace(".cabocha", "")


def main():
    """
    main function
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("db_file")
    parser.add_argument("base_dir")
    args = parser.parse_args()
    cab_files = {
        _conv_filename(filename): filename
        for filename in glob.glob(os.path.join(args.base_dir, "*.cabocha"))
    }
    file_list = set(cab_files.keys())
    header = LUW_HEADER
    for file_id, items in iterate_db_file(args.db_file):
        print(file_id, file_id in file_list)
        if file_id in file_list:
            txt = "\n".join(items)
            filename = cab_files[file_id].replace(".cabocha", ".luw")
            with open(filename, "w") as wrt:
                wrt.write("\t".join(header) + "\n")
                wrt.write(txt + "\n")


if __name__ == '__main__':
    main()
