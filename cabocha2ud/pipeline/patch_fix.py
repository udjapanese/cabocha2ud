# -*- coding: utf-8 -*-

"""
fix based patch file
"""

from typing import Union, cast, TypedDict, Optional
import argparse
import ruamel

from cabocha2ud.lib.logger import Logger
from cabocha2ud.ud import UniversalDependencies
from cabocha2ud.ud.util import Field


class Rule(TypedDict):
    ids: list[int]
    target: str
    value: Union[str, int]


def load_path_file(patch_file_name: Optional[str]) -> dict[str, list[Rule]]:
    if patch_file_name is None:
        return {}
    yaml = ruamel.yaml.YAML()
    rule_list: list[dict[str, Union[str, list[Rule]]]] = yaml.load(open(patch_file_name).read().replace('\t', '    '))
    rule_set = dict([(cast(str, rule["sent_id"]), cast(list[Rule], rule["rules"])) for rule in rule_list])
    return rule_set


def do(ud: UniversalDependencies, rule_list: dict[str, list[Rule]], logger: Optional[Logger]=None):
    if logger is None:
        logger = Logger()
    logger.debug("do patch fix")
    if len(rule_list) == 0:
        return
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
                if id_ > 0:
                    word = sent.word(id_)
                    word[Field[rule["target"]]].set_content(str(rule["value"]))
                else:
                    # idが-1のときheaderをみる, rule["target"] はheaderのheaderになる
                    assert id_ == -1
                    sent_header = sent.get_header(rule["target"])
                    assert sent_header is not None
                    sent_header.set_value(str(rule["value"]))

def main() -> None:
    """
        main function
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("conll_file")
    parser.add_argument("patch_file")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("-w", "--writer", default="-", type=str)
    args = parser.parse_args()
    logger = Logger(debug=args.debug)
    rule_list = load_path_file(args.patch_file)
    ud = UniversalDependencies(file_name=args.conll_file)
    do(ud, rule_list, logger=logger)
    ud.write_ud_file(args.writer)


if __name__ == '__main__':
    main()
