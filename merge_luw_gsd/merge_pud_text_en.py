# -*- coding: utf-8 -*-

"""
python conv_gsd/merge_pud_text_en.py
"""

import argparse
import os
import codecs
import json

import tqdm


def load_conll_file(base_file):
    full_data, sent = [], []
    for line in base_file:
        line = line.rstrip("\n")
        if line == "":
            full_data.append(sent)
            sent = []
            continue
        sent.append(line)
    assert line == ""
    return full_data


def _write_conll(base, writer):
    for line in base:
        writer.write(line + "\n")
    writer.write("\n")


def _featch_info(base):
    eheader, epos = [], 0
    while base[epos].startswith("# "):
        eheader.append(base[epos])
        epos += 1
    nheader = {}
    for eee in eheader:
        eee = eee.replace("# ", "").split(" = ")
        nheader[eee[0]] = eee[1]
    return nheader

def _remove_info(base):
    eheader, epos = [], 0
    while base[epos].startswith("# "):
        epos += 1
    return base[epos:]

def main():
    """
    main function
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("base_file")
    parser.add_argument("en_file")
    parser.add_argument("-w", "--writer", default="-", type=argparse.FileType("w"))
    args = parser.parse_args()
    with codecs.open(args.base_file, encoding="utf-8") as base_file:
        base_data = load_conll_file(base_file)
    with codecs.open(args.en_file, encoding="utf-8") as en_file:
        en_data = load_conll_file(en_file)
    assert len(base_data) == len(en_data)
    for base, een in zip(base_data, en_data):
        eheader = _featch_info(een)
        bheader = _featch_info(base)
        assert "text_en" in eheader
        horder = ['newdoc id', 'sent_id', 'text', 'text_en']
        nbaseh = []
        for hhh in horder:
            if hhh == "text":
                # textはbaseにあわせる
                nbaseh.append("# {} = {}".format(hhh, bheader[hhh]))
            elif hhh in eheader:
                nbaseh.append("# {} = {}".format(hhh, eheader[hhh]))
        _write_conll(nbaseh + _remove_info(base), args.writer)


if __name__ == '__main__':
    main()
