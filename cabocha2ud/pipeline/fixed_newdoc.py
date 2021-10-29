# -*- coding: utf-8 -*-

"""
fix SpaceAfter information for newdoc
"""

import argparse
from typing import cast, Optional

from cabocha2ud.lib.logger import Logger
from cabocha2ud.ud import UniversalDependencies
from cabocha2ud.ud.word import Misc
from cabocha2ud.ud.util import Field

def do(ud: UniversalDependencies, logger: Optional[Logger]=None) -> None:
    if logger is None:
        logger = Logger()
    logger.debug("do fixed newdoc")
    spos_lst: list[int] = []
    for spos, sent in enumerate(ud.sentences()):
        header_keys = sent.get_header_keys()
        if spos == len(ud.sentences()) - 1:
            spos_lst.append(spos)
        if "newdoc id" not in header_keys:
            continue
        if spos > 0:
            spos_lst.append(spos - 1)
    for spos in spos_lst:
        sent = ud.sentences()[spos]
        misc = cast(Misc, sent.words()[-1][Field.MISC])
        misc.update("SpaceAfter", "Yes")


def main() -> None:
    """
        main function
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("conll_file")
    parser.add_argument("-w", "--writer", default="-", type=str)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    logger = Logger(debug=args.debug)
    ud = UniversalDependencies(file_name=args.conll_file)
    do(ud, logger=logger)
    ud.write_ud_file(args.writer)


if __name__ == '__main__':
    main()
