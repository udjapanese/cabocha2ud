# -*- coding: utf-8 -*-

"""
merge oneline for Ginza
"""

import argparse


def main():
    """
    main function
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("base_file", type=argparse.FileType("r"))
    parser.add_argument("writer", type=argparse.FileType("w"))
    args = parser.parse_args()
    sent = []
    for line in args.base_file:
        line = line.rstrip()
        if line == "EOS":
            for token in sent:
                _surface = token[0]
                _pos = token[1]
                _dictionary_form = _pos.split(",")[23]
                _reading_form = _pos.split(",")[11]
                args.writer.write("\t".join([_surface, _pos, _dictionary_form, _reading_form]) + "\t")
            args.writer.write("\n")
            sent = []
        elif line.startswith("#!") or line.startswith("* "):
            continue
        else:
            tokens = line.split("\t")
            sent.append(tokens)


if __name__ == '__main__':
    main()

