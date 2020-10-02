# -*- coding: utf-8 -*-

"""
python replace_gsd_id_base_idmap.py

"""

import sys
import argparse
import os
import codecs
import json

import tqdm

def load_id_map(align_file):
    align_data, ldata = [], []
    with codecs.open(align_file, encoding='utf-8') as rdr:
        for line in rdr:
            ldata.append(line)
    rdr = iter(ldata)
    header = next(rdr).rstrip("\r\n").split("\t")
    align_data = [
        dict(zip(header, line.rstrip("\r\n").split("\t")))
        for line in rdr
    ]
    align_map_data = {
        int(align["cabocha_pos"]): align for align in align_data
        if align["cabocha_pos"] != "_"
    }
    return align_map_data


def load_conllu_file(conllu_file):
    conllu_data = []
    with codecs.open(conllu_file, encoding='utf-8') as rdr:
        sent = []
        for line in rdr:
            line = line.rstrip("\n")
            if line == "":
                conllu_data.append(sent)
                sent = []
                continue
            sent.append(line)
        assert len(sent) == 0, "conllu must be new line in last"
    return conllu_data


def write_conllu_file(conllu_data, writer):
    for conll in conllu_data:
        for col in conll:
            writer.write(col + "\n")
        writer.write("\n")


def replace_conllu_id(conllu_data, align_map_data, target_col):
    nconll_data = []
    for sent_pos, sent in enumerate(conllu_data):
        assert sent_pos in align_map_data
        nsent = []
        line_pos = 0
        while sent[line_pos].startswith("#! sent_id ="):
            nsent.append(sent[line_pos])
            line_pos += 1
        new_id = align_map_data[sent_pos][target_col]
        nsent.append(new_id)
        for sss in sent[line_pos+1:]:
            nsent.append(sss)
        assert len(nsent) == len(sent)
        nconll_data.append(nsent)
    return nconll_data


def main():
    """
    main function
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("id_map_file")
    parser.add_argument("conllu_file")
    parser.add_argument("target_column", help="maybe must be sent_id|sent_id(v2.5)")
    parser.add_argument("-w", "--writer", type=argparse.FileType("w"))
    args = parser.parse_args()
    align_map_data = load_id_map(args.id_map_file)
    conllu_data = load_conllu_file(args.conllu_file)
    assert len(align_map_data) == len(conllu_data)
    conllu_data = replace_conllu_id(conllu_data, align_map_data, args.target_column)
    write_conllu_file(conllu_data, args.writer)


if __name__ == '__main__':
    main()
