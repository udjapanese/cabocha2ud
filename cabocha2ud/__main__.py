# -*- coding: utf-8 -*-

"""
BCCWJ DepParaPAS to universal dependencies
"""

import configargparse

from typing import Optional

from cabocha2ud.lib.yaml_dict import YamlDict
from cabocha2ud.pipeline import Pipeline, PIPE_FUNCS
from cabocha2ud.lib.logger import Logger
from cabocha2ud.bd import BunsetsuDependencies
from cabocha2ud.ud import UniversalDependencies


def parse_pipe(pipe_str: Optional[str]) -> list[str]:
    if pipe_str is None:
        return []
    pipes = pipe_str.split(",")
    for pipe in pipes:
        if pipe not in PIPE_FUNCS:
            raise KeyError("please set from {}".format(",".join(PIPE_FUNCS)))
    return pipes


def _get_argparser() -> configargparse.ArgumentParser:
    parser = configargparse.ArgumentParser(default_config_files=['./configargparse.yaml'])
    parser.add_argument("-c", "--configarg-file", is_config_file=True, help="configargparse file")
    parser.add_argument("base_file", type=str)
    parser.add_argument("-p", "--pipeline", default=[], type=parse_pipe)
    parser.add_argument("-b", "--bunsetu-func", default="none", choices=["none", "type1", "type2"])
    parser.add_argument("-s", "--skip-space", default=False, action="store_true")
    parser.add_argument("--remove-luw-space", default=False, action="store_true")
    parser.add_argument("-m", "--space-marker",
                        choices=["zenkaku", "hankaku"], default="zenkaku", help="スペースに何を使うか")
    parser.add_argument("--rep-multi-root-mode", default="convert", choices=["remove", "convert"], help="for replace_multi_root")
    parser.add_argument("--patch-file", default=None, help="for patch_fix")
    parser.add_argument("--sp-file", default=None, help="for merge_sp_to_conll")
    parser.add_argument("--pos-rule-file", default="conf/bccwj_pos_suw_rule.yaml", help="for fit")
    parser.add_argument("--dep-rule-file", default="conf/bccwj_dep_suw_rule.yaml", help="for fit")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("-w", "--writer", type=str, default="-")
    return parser


def main() -> None:
    """
        main function
    """
    args = _get_argparser().parse_args()
    logger = Logger(debug=args.debug)
    logger.debug(str(args) + "\n")
    args.space_marker = {"zenkaku": "　", "hankaku": " "}[args.space_marker]
    options = YamlDict(init={
        "space_marker": args.space_marker, "bunsetu_func": args.bunsetu_func,
        "debug": args.debug, "is_skip_space": args.skip_space,
        "logger": logger, "rep_multi_root_mode": args.rep_multi_root_mode,
        "patch_file": args.patch_file, "sp_file": args.sp_file,
        "pos_rule_file": args.pos_rule_file, "dep_rule_file": args.dep_rule_file,
        "remove_luw_space": args.remove_luw_space
    })
    bobj = BunsetsuDependencies(file_name=args.base_file, options=options)
    uobj = UniversalDependencies(options=options)
    pipeline = Pipeline(bd=bobj, ud=uobj, pipe=args.pipeline, logger=logger, options=options)
    pipeline.do()
    pipeline.get_ud().write_ud_file(args.writer)


if __name__ == '__main__':
    main()
