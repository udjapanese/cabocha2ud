# -*- coding: utf-8 -*-

"""
fix based patch file
"""

from typing import Union, cast, TypedDict
import argparse
import ruamel

from cabocha2ud.ud import UniversalDependencies
from cabocha2ud.ud.util import Field


class Rule(TypedDict):
    ids: list[int]
    target: str
    value: Union[str, int]


def load_path_file(patch_file_name: str) -> dict[str, list[Rule]]:
    yaml = ruamel.yaml.YAML()
    rule_list: list[dict[str, Union[str, list[Rule]]]] = yaml.load(open(patch_file_name).read().replace('\t', '    '))
    rule_set = dict([(cast(str, rule["sent_id"]), cast(list[Rule], rule["rules"])) for rule in rule_list])
    return rule_set


def main() -> None:
    """
        main function
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("conll_file")
    parser.add_argument("patch_file")
    parser.add_argument("-w", "--writer", default="-", type=argparse.FileType("w"))
    args = parser.parse_args()
    rule_list = load_path_file(args.patch_file)
    ud = UniversalDependencies(file_name=args.conll_file)
    if len(rule_list) == 0:
        args.writer.write(str(ud) + "\n")
    for sent in ud.sentences():
        header_keys = sent.get_header_keys()
        if "sent_id" not in header_keys:
            continue
        sent_id_header = sent.get_header("sent_id")
        if sent_id_header is None:
            continue
        sent_id = sent_id_header.get_value()
        if sent_id not in rule_list:
            continue
        for rule in rule_list[sent_id]:
            # 埋めていく
            ids = rule["ids"]
            for id_ in ids:
                word = sent.word(id_)
                word[Field[rule["target"]]].set_content(str(rule["value"]))
    args.writer.write(str(ud) + "\n")


if __name__ == '__main__':
    main()
