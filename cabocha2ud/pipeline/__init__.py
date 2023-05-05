# -*- coding: utf-8 -*-

"""
Pipeline base function
"""

from typing import Optional, Type

from cabocha2ud.bd import BunsetsuDependencies as BD
from cabocha2ud.lib.logger import Logger
from cabocha2ud.lib.yaml_dict import YamlDict
from cabocha2ud.pipeline import (build_luw, convert_paren,
                                 merge_number, merge_sp_to_cabocha, patch_fix,
                                 replace_multi_root)
from cabocha2ud.pipeline.component import PipeLineComponent
from cabocha2ud.rule import dep, pos
from cabocha2ud.ud import UniversalDependencies as UD

PIPE_FUNCS: list[Type[PipeLineComponent]] = [
    merge_number.COMPONENT, merge_sp_to_cabocha.COMPONENT, build_luw.COMPONENT,
    replace_multi_root.COMPONENT, convert_paren.COMPONENT,
    patch_fix.COMPONENT
]
PIPE_FUNCS_NAMES = [f.name for f in PIPE_FUNCS]
PIPE_FUNC_MAPS: dict[str, Type[PipeLineComponent]] = dict(zip(PIPE_FUNCS_NAMES, PIPE_FUNCS))


class RunnerPipeline:
    """
        Pipeline class
    """

    def __init__(
        self, _bd: BD, _ud: UD, pipe: Optional[list[str]]=None, options: YamlDict=YamlDict()
    ):
        self.logger: Logger = options.get("logger") or Logger()
        self._bd = _bd
        self._ud = _ud
        self.components: dict[str, list[PipeLineComponent]] = {
            "pre":[], "post": []
        }
        self.pos_rule: list[tuple]
        self.dep_rule: list[tuple[list[dep.SubRule], str]]
        self.opts: YamlDict = options
        self.pipe: list[str] = []
        if pipe is not None:
            self.pipe = pipe
        self.prepare(self.pipe)

    def prepare(self, pipe_funcs: list[str]):
        """ prepare pipeline functions

        Args:
            pipe_funcs (list[str]): list of pipeline

        """
        assert all(pf in PIPE_FUNCS_NAMES for pf in pipe_funcs)
        self.logger.debug("loading pos_rule")
        assert self.opts.get("pos_rule_file", None) is not None
        self.pos_rule = pos.load_pos_rule(self.opts.get("pos_rule_file", None))
        self.logger.debug("loading dep_rule")
        assert self.opts.get("dep_rule_file", None) is not None
        self.dep_rule = dep.load_dep_rule(self.opts.get("dep_rule_file", None))
        for cfunc in pipe_funcs:
            comp = PIPE_FUNC_MAPS[cfunc]
            if comp.mode == "bd":
                self.components["pre"].append(comp(self._bd, self.opts))
            elif comp.mode == "ud":
                self.components["post"].append(comp(self._ud, self.opts))
            else:
                raise KeyError

    def get_bd(self) -> BD:
        """ Get Bunsetu Dependencies Object """
        return self._bd

    def get_ud(self) -> UD:
        """ Get Universal Dependencies Object """
        return self._ud

    def do_pipeline(self) -> None:
        """ パイプラインを実行する """
        for pre in self.components["pre"]:
            pre()
        self._ud.fit(self._bd, self.pos_rule, self.dep_rule)
        for post in self.components["post"]:
            post()
