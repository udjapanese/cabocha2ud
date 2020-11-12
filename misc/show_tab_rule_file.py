# -*- coding: utf-8 -*-

"""
    ルールファイルをテーブルに変換
"""

import json
import argparse

import ruamel.yaml


def show_word_table(data, writer):
    """
        UD POSラベル変換のルール表の出力
    """
    keys = data["default"]
    writer.write("\t".join([k for k in keys] + ["UPOS"]) + "\n")
    for rule in data["rule"]:
        rule, result = rule
        res_line = [
            rule[k] if k in rule else "" for k in keys
        ] + [
            ",".join(result)
        ]
        writer.write("\t".join(res_line) + "\n")


def show_dep_table(data, writer):
    """
        係り関係ラベル変換のルール表の出力
    """
    keys = data["column_order"]
    writer.write(
        "\t".join([data["column_mapping"][k] for k in keys] + ["UD rel"]) + "\n"
    )
    for rule in data["order_rule"]:
        rrr = {}
        for rrule in rule["rule"]:
            kkk = rrule[0] + ":" + rrule[1][0]
            if len(rrule[1]) < 2 or rrule[1][1] == "parent_word":
                rrr[kkk] = "YES"
            elif isinstance(rrule[1][1], str) or isinstance(rrule[1][1], int):
                rrr[kkk] = str(rrule[1][1])
            elif isinstance(rrule[1][1], list):
                rrr[kkk] = ",".join(rrule[1][1])
            else:
                raise TypeError
        res_line = [
            rrr[key] if key in rrr else "" for key in keys
        ] + [rule["res"]]
        writer.write("\t".join(res_line) + "\n")


def _main():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('base_file', type=argparse.FileType('r'))
    parser.add_argument('-f', '--file-type', choices=["pos", "dep"], default="pos")
    parser.add_argument('-w', '--writer', type=argparse.FileType('w'), default="-")
    args = parser.parse_args()
    yaml = ruamel.yaml.YAML()
    data = yaml.load(args.base_file)
    if args.file_type == "pos":
        show_word_table(data, args.writer)
    elif args.file_type == "dep":
        show_dep_table(data, args.writer)


if __name__ == '__main__':
    _main()
