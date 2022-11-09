# -*- coding: utf-8 -*-

from functools import partial
from typing import Any, Callable, Optional, TypedDict, Union

import typing_extensions as tx

from ..bd import BunsetsuDependencies
from ..lib.logger import Logger
from ..lib.yaml_dict import YamlDict
from ..rule import dep, pos
from ..ud import UniversalDependencies
from . import (build_luw, convert_paren, fixed_newdoc, merge_number,
               merge_sp_to_cabocha, merge_sp_to_conll, patch_fix,
               replace_multi_root)


class PrePost(tx.Protocol):
    def __call__(self, x: Union[BunsetsuDependencies, UniversalDependencies], logger: Optional[Logger]=None) -> int:
        pass


PIPE_FUNCS: dict[str, Callable] = {
    "merge_number": merge_number.do,
    "build_luw": build_luw.do,
    "convert_paren": convert_paren.do,
    "fixed_newdoc": fixed_newdoc.do,
    "merge_sp_to_cabocha": merge_sp_to_cabocha.do,
    "merge_sp_to_conll": merge_sp_to_conll.do,
    "patch_fix": patch_fix.do,
    "replace_multi_root": replace_multi_root.do
}
PRE_FUNC = ["merge_sp_to_cabocha", "merge_number", "build_luw"]
POST_FUNC = ["convert_paren", "fixed_newdoc", "merge_sp_to_conll", "patch_fix", "replace_multi_root"]

class Predata(TypedDict):
    sp_data: list[list[dict[str, str]]]
    rule_list: dict[str, list[patch_fix.Rule]]
    replace_multi_mode: str
    pos_rule: list
    dep_rule: list[tuple[list[dep.SubRule], str]]


class Pipeline:

    def __init__(self, bd: BunsetsuDependencies, ud: UniversalDependencies, pipe: list[str]=[], logger=Logger, options: YamlDict=YamlDict()):
        self.logger = logger
        self.bd = bd
        self.ud = ud
        self.components: dict[str, list[PrePost]] = {
            "pre":[], "post": []
        }
        self.options: YamlDict = options
        self.pipe: list[str] = pipe
        self.predata: Predata = {
            "sp_data": [], "rule_list": {}, "replace_multi_mode": "",
            "pos_rule": [], "dep_rule": []
        }
        self.prepare(pipe)

    def prepare(self, pipe_funcs: list[str]):
        assert all([pf in PIPE_FUNCS for pf in pipe_funcs])
        self.logger.debug("loading sub-data.... ({})".format(self.pipe))
        self.logger.debug("loading pos_rule")
        assert self.options.get("pos_rule_file", None) is not None
        self.predata["pos_rule"] = pos.load_pos_rule(self.options.get("pos_rule_file", None))
        self.logger.debug("loading dep_rule")
        assert self.options.get("dep_rule_file", None) is not None
        self.predata["dep_rule"] = dep.load_dep_rule(self.options.get("dep_rule_file", None))
        if "merge_sp_to_cabocha" in pipe_funcs:
            self.logger.debug("loading sp_data")
            self.predata["sp_data"] = merge_sp_to_conll.load_db_file(self.options.get("sp_file", None))
            self.logger.debug(self.predata["sp_data"])
            PIPE_FUNCS["merge_sp_to_cabocha"] = partial(
                PIPE_FUNCS["merge_sp_to_cabocha"], sp_data=self.predata["sp_data"]
            )
        if "merge_sp_to_conll" in pipe_funcs:
            self.logger.debug("loading sp_data")
            self.predata["sp_data"] = merge_sp_to_conll.load_db_file(self.options.get("sp_file", None))
            self.logger.debug(self.predata["sp_data"])
            PIPE_FUNCS["merge_sp_to_conll"] = partial(
                PIPE_FUNCS["merge_sp_to_conll"], sp_data=self.predata["sp_data"]
            )
        if "patch_fix" in pipe_funcs:
            self.logger.debug("loading patch file")
            self.predata["rule_list"] = patch_fix.load_path_file(self.options.get("patch_file", None))
            PIPE_FUNCS["patch_fix"] = partial(
                PIPE_FUNCS["patch_fix"], rule_list=self.predata["rule_list"]
            )
        if "replace_multi_root" in pipe_funcs:
            self.logger.debug("loading replace_multi_root")
            self.predata["replace_multi_mode"] = self.options.get("rep_multi_root_mode", "convert")
            PIPE_FUNCS["replace_multi_root"] = partial(
                PIPE_FUNCS["replace_multi_root"], mode=self.predata["replace_multi_mode"]
            )
        for pipe_func in pipe_funcs:
            PIPE_FUNCS[pipe_func] = partial(PIPE_FUNCS[pipe_func], logger=self.logger)
            if pipe_func in PRE_FUNC:
                self.components["pre"].append(
                    partial(PIPE_FUNCS[pipe_func], logger=self.logger)
                )
            elif pipe_func in POST_FUNC:
                self.components["post"].append(
                    partial(PIPE_FUNCS[pipe_func], logger=self.logger)
                )
            else:
                raise NotImplementedError("cannot detect: " + pipe_func)

    def get_bd(self) -> BunsetsuDependencies:
        return self.bd

    def get_ud(self) -> UniversalDependencies:
        return self.ud

    def do(self) -> None:
        for pre in self.components["pre"]:
            pre(self.bd, logger=self.logger)
        self.ud.fit(self.bd, self.predata["pos_rule"], self.predata["dep_rule"])
        for post in self.components["post"]:
            post(self.ud, logger=self.logger)
