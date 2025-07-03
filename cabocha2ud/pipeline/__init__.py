"""Pipeline base function."""

import argparse
import importlib
import pathlib
import re
import tempfile
from typing import Type

from cabocha2ud.bd import BunsetsuDependencies
from cabocha2ud.lib.logger import Logger
from cabocha2ud.lib.yaml_dict import YamlDict
from cabocha2ud.pipeline.component import PipeLineComponent
from cabocha2ud.rule import dep, pos
from cabocha2ud.ud import UniversalDependencies, fit

MODULE_FILES = importlib.import_module("cabocha2ud.pipeline").__file__
assert MODULE_FILES is not None
PIPE_FUNCS: list[Type[PipeLineComponent]] = [
    p.COMPONENT for p in [
        importlib.import_module(f'cabocha2ud.pipeline.{p.name.replace(".py", "")}')
        for p in pathlib.Path(MODULE_FILES).parent.glob("*.py") if re.match("^[^_].*.py$", p.name)
    ] if "COMPONENT" in p.__dict__
]
PIPE_FUNCS_NAMES = [f.name for f in PIPE_FUNCS]
PIPE_FUNC_MAPS: dict[str, Type[PipeLineComponent]] = dict(zip(PIPE_FUNCS_NAMES, PIPE_FUNCS))


class RunnerPipeline:
    """Pipeline class."""

    def __init__(
        self, _bd: BunsetsuDependencies, _ud: UniversalDependencies,
        pipe: list[str]|None=None, options: YamlDict|None=None
    ) -> None:
        """Init and prepare."""
        if options is None:
            options = YamlDict()
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

    def prepare(self, pipe_funcs: list[str]) -> None:
        """Prepare pipeline functions.

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

    def get_bd(self) -> BunsetsuDependencies:
        """Get Bunsetu Dependencies Object."""
        return self._bd

    def get_ud(self) -> UniversalDependencies:
        """Get Universal Dependencies Object."""
        return self._ud

    def do_pipeline(self) -> None:
        """パイプラインを実行する."""
        if self.opts.get("temporary_file"):
            temp_dir = tempfile.mkdtemp()
            self.logger.info("saved %s", temp_dir)
        step_count = 0
        for pre in self.components["pre"]:
            pre()
            step_count = step_count + 1
            if self.opts.get("temporary_file"):
                self.save_temporary_file(step_count, pre, temp_dir)
        fit(self._ud, self._bd, self.pos_rule, self.dep_rule)
        step_count = step_count + 1
        if self.opts.get("temporary_file"):
            self.save_temporary_file(step_count, None, temp_dir)
        for post in self.components["post"]:
            post()
            step_count = step_count + 1
            if self.opts.get("temporary_file"):
                self.save_temporary_file(step_count, post, temp_dir)

    def save_temporary_file(
        self, step: int, comp: PipeLineComponent|None,
        save_dir: str
    ) -> None:
        """一時ファイルを保存する."""
        assert self.opts.get("temporary_file")
        save_dir_p = pathlib.Path(save_dir)
        if comp is None:
            save_file = f"{step:02}_cab2ud.conllu"
            wrt = str(save_dir_p / pathlib.Path(save_file))
            self.get_ud().write_ud_file(wrt)
            self.logger.info("saved %s", wrt)
        elif comp.mode == "bd":
            save_file = f"{step:02}_{comp.name}_bd.cabocha"
            wrt = str(save_dir_p / pathlib.Path(save_file))
            self.get_bd().write_cabocha_file(wrt)
            self.logger.info("saved %s", wrt)
        elif comp.mode == "ud":
            save_file = f"{step:02}_{comp.name}_ud.conllu"
            wrt = str(save_dir_p / pathlib.Path(save_file))
            self.get_ud().write_ud_file(wrt)
            self.logger.info("saved %s", wrt)


def _main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    _ = parser.parse_args()
    for pfunc in PIPE_FUNC_MAPS:
        print(pfunc,
              str(PIPE_FUNC_MAPS[pfunc]).replace("<class 'cabocha2ud.", ""),
              PIPE_FUNC_MAPS[pfunc].mode, sep="\t")



if __name__ == "__main__":
    _main()
