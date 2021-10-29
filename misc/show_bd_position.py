# -*- coding: utf-8 -*-

"""
cut cabocha file
"""

import sys
import configargparse
from typing import cast

from cabocha2ud.lib.yaml_dict import YamlDict
from cabocha2ud.bd import BunsetsuDependencies
from cabocha2ud.bd.word import Word


def _get_argparser() -> configargparse.ArgumentParser:
    parser = configargparse.ArgumentParser(default_config_files=['./configargparse.yaml'])
    parser.add_argument("-c", "--configarg-file", is_config_file=True, help="configargparse file")
    parser.add_argument("base_file", type=str)
    parser.add_argument("-p", "--pipeline", default=[], type=str)
    parser.add_argument("-b", "--bunsetu-func", default="none", choices=["none", "type1", "type2"])
    parser.add_argument("-s", "--skip-space", default=False, action="store_true")
    parser.add_argument("-m", "--space-marker",
                        choices=["zenkaku", "hankaku"], default="zenkaku", help="スペースに何を使うか")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("-w", "--writer", type=configargparse.FileType("w"), default="-")
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
        "space_marker": args.space_marker, "bunsetu_func": args.bunsetu_func,
        "debug": args.debug, "is_skip_space": args.skip_space
    })
    bobj = BunsetsuDependencies(file_name=args.base_file, options=options)
    for doc in bobj.documents():
        doc.detect_ud_dependencies()
        sss = 0
        for sent_pos, sent in enumerate(doc.sentences()):
            tok_pos = 0
            for bun_pos, bun in enumerate(sent):
                print(bun.get_header())
                for wpos, wrd in enumerate(bun):
                    wrd_size = len(wrd.get_surface())
                    print("{}:{}:{}-{}".format(
                        sent_pos, tok_pos, sss, sss+wrd_size
                    ) + "\t" + str(wrd))
                    sss += wrd_size
                    tok_pos += 1
            print("EOS")


if __name__ == '__main__':
    main()
