# -*- coding: utf-8 -*-

"""
BCCWJ DepParaPAS to universal dependencies
"""

from typing import Optional

from configargparse import ArgumentParser, Namespace

from cabocha2ud.bd import BunsetsuDependencies
from cabocha2ud.lib.logger import Logger
from cabocha2ud.lib.yaml_dict import YamlDict
from cabocha2ud.pipeline import RunnerPipeline, PIPE_FUNCS_NAMES
from cabocha2ud.ud import UniversalDependencies


def parse_pipe(pipe_str: Optional[str]) -> list[str]:
    """ Parse Pipe function """
    if pipe_str is None:
        return []
    pipes = pipe_str.split(",")
    for pipe in pipes:
        if pipe not in PIPE_FUNCS_NAMES:
            raise KeyError(f"{pipe}: please set from {PIPE_FUNCS_NAMES}")
    return pipes


def parse_sp(spm: Optional[str]) -> str:
    """ Parse Space mark """
    sp_replase_dict = {"zenkaku": "　", "hankaku": " "}
    if spm not in sp_replase_dict:
        raise KeyError("please set from {}".format(",".join(sp_replase_dict)))
    return {"zenkaku": "　", "hankaku": " "}[spm]


def _get_argparser() -> ArgumentParser:
    parser = ArgumentParser(default_config_files=["./configargparse.yaml"])
    parser.add_argument("base_file", type=str)
    parser.add_argument("-c", "--configarg-file", is_config_file=True, help="configargparse file")
    parser.add_argument("-p", "--pipeline", default=[], type=parse_pipe)
    parser.add_argument("-s", "--skip-space", default=False, action="store_true")
    parser.add_argument("-m", "--space-marker", type=parse_sp, default="zenkaku", help="スペースに何を使うか")
    parser.add_argument("--rep-multi-root-mode", default="convert",
                        choices=["remove", "convert"], help="for replace_multi_root")
    parser.add_argument("--patch-file", default=None, help="file for patch_fix")
    parser.add_argument("--sp-file", default=None, help="file for merge_sp_to_conll")
    parser.add_argument("--pos-rule-file", default="conf/bccwj_pos_suw_rule.yaml",
                        help="file for fit rule")
    parser.add_argument("--dep-rule-file", default="conf/bccwj_dep_suw_rule.yaml",
                        help="file for fit rule")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("-w", "--writer", type=str, default="-")
    return parser


def get_args_and_options(arg_str: Optional[list[str]]=None) -> tuple[Namespace, YamlDict]:
    """ Get Args and Options """
    args: Namespace = _get_argparser().parse_args(arg_str)
    logger = Logger(debug=args.debug)
    logger.debug(str(args) + "\n")
    options = YamlDict(init={
        "space_marker": args.space_marker,
        "debug": args.debug, "skip_space": args.skip_space,
        "logger": logger, "rep_multi_root_mode": args.rep_multi_root_mode,
        "patch_file": args.patch_file, "sp_file": args.sp_file,
        "pos_rule_file": args.pos_rule_file, "dep_rule_file": args.dep_rule_file
    })
    return args, options


def main() -> None:
    """
        main function
    """
    args, options = get_args_and_options()
    bobj = BunsetsuDependencies(file_name=args.base_file, options=options)
    uobj = UniversalDependencies(options=options)
    runner = RunnerPipeline(_bd=bobj, _ud=uobj, pipe=args.pipeline, options=options)
    runner.do_pipeline()
    runner.get_ud().write_ud_file(args.writer)


if __name__ == '__main__':
    main()
