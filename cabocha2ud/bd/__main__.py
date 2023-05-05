# -*- coding: utf-8 -*-

"""
BCCWJ DepParaPAS to universal dependencies
"""

import sys

import configargparse

from cabocha2ud.bd import BunsetsuDependencies
from cabocha2ud.lib.yaml_dict import YamlDict


def _get_argparser() -> configargparse.ArgumentParser:
    parser = configargparse.ArgumentParser(default_config_files=['./configargparse.yaml'])
    parser.add_argument("-c", "--configarg-file", is_config_file=True, help="configargparse file")
    parser.add_argument("base_file", type=str)
    parser.add_argument("-s", "--skip-space", default=False, action="store_true")
    parser.add_argument("-m", "--space-marker",
                        choices=["zenkaku", "hankaku"], default="zenkaku", help="スペースに何を使うか")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("-w", "--writer", type=str, default="-")
    return parser


def main() -> None:
    """
        main function
    """
    args = _get_argparser().parse_args()
    if args.debug:
        sys.stderr.write(str(args) + "\n")
    args.space_marker = {"zenkaku": "　", "hankaku": " "}[args.space_marker]
    options = YamlDict(init={
        "space_marker": args.space_marker,
        "debug": args.debug, "skip_space": args.skip_space
    })
    bobj = BunsetsuDependencies(file_name=args.base_file, options=options)
    bobj.write_cabocha_file(args.writer)


if __name__ == '__main__':
    main()
