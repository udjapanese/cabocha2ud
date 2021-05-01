# -*- coding: utf-8 -*-

"""

filter by sent ID
"""

import argparse
import sys


def _iterate_sentence(file_obj):
    sent_lst = []
    for line in file_obj:
        line = line.rstrip("\n")
        if line == "":
            yield sent_lst
            sent_lst = []
        else:
            sent_lst.append(line)


def main():
    """
        main function
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("conll_file", type=argparse.FileType("r"))
    parser.add_argument("filtered_file", type=argparse.FileType("r"))
    parser.add_argument("error_sent_file", type=argparse.FileType("w"))
    parser.add_argument("-w", "--writer", type=argparse.FileType("w"), default="-")
    args = parser.parse_args()
    filtered_ids = set([l.rstrip("\n") for l in args.filtered_file])
    for sent in _iterate_sentence(args.conll_file):
        sent_id = sent[0].split(" ")[-1]
        if sent_id in filtered_ids:
            sys.stderr.write("\n".join(sent) + "\n\n")
        else:
            args.writer.write("\n".join(sent) + "\n\n")


if __name__ == '__main__':
    main()
