# -*- coding: utf-8 -*-

"""
fix based patch file
"""

import argparse
from typing import Optional, TypedDict, Union, cast

from cabocha2ud.lib.logger import Logger
from cabocha2ud.lib.yaml_dict import YamlDict, YamlList
from cabocha2ud.pipeline.component import UDPipeLine
from cabocha2ud.ud import UniversalDependencies as UD
from cabocha2ud.ud.util import Field


class Rule(TypedDict):
    """ Rule Object """
    ids: list[int]
    target: str
    value: Union[str, int]


def load_path_file(patch_file_name: Optional[str]) -> dict[str, list[Rule]]:
    """ load path file """
    if patch_file_name is None:
        return {}
    rule_list: list[dict[str, Union[str, list[Rule]]]] = cast(
        list[dict[str, Union[str, list[Rule]]]],
        list(YamlList(file_name=patch_file_name, auto_load=True))
    )
    rule_set = dict(
        (cast(str, rule["sent_id"]), cast(list[Rule], rule["rules"])) for rule in rule_list
    )
    return rule_set


class PatchFixComponent(UDPipeLine):
    """ patch fix

    Args:
        PipeLineComponent (_type_): _description_
    """
    name = "patch_fix"
    need_opt = ["patch_file"]

    def __init__(self, target: UD, opts: YamlDict) -> None:
        self.rule_list: dict[str, list[Rule]] = {}
        super().__init__(target, opts)

    def prepare(self) -> None:
        assert "patch_file" in self.opts, "please set path_file"
        self.rule_list = load_path_file(self.opts["patch_file"])

    def __call__(self) -> None:
        assert isinstance(self.target, UD)
        self.logger.debug(f"do {self.name}")
        if len(self.rule_list) == 0:
            return
        for sent in self.target.sentences():
            header_keys = sent.get_header_keys()
            if "sent_id" not in header_keys:
                continue
            sent_id_header = sent.get_header("sent_id")
            if sent_id_header is None:
                continue
            sent_id = sent_id_header.get_value()
            if sent_id not in self.rule_list:
                continue
            for rule in self.rule_list[sent_id]:
                # ルールに従い埋めていく
                for id_ in rule["ids"]:
                    if id_ > 0:
                        word = sent.word(id_)
                        word[Field[rule["target"]]].set_content(str(rule["value"]))
                    else:
                        # idが-1のときheaderをみる, rule["target"] はheaderのheaderになる
                        assert id_ == -1
                        sent_header = sent.get_header(rule["target"])
                        assert sent_header is not None
                        sent_header.set_value(str(rule["value"]))


COMPONENT = PatchFixComponent


def _main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("conll_file")
    parser.add_argument("patch_file")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("-w", "--writer", default="-", type=str)
    args = parser.parse_args()
    options = YamlDict(
        init={"logger": Logger(debug=args.debug), "patch_file": args.path_file}
    )
    _ud = UD(file_name=args.conll_file, options=options)
    COMPONENT(_ud,  opts=options)()
    _ud.write_ud_file(args.writer)


if __name__ == '__main__':
    _main()
