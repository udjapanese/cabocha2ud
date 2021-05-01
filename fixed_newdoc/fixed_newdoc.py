# -*- coding: utf-8 -*-

"""
fix SpaceAfter information for newdoc
"""

import argparse
from typing import cast

from cabocha2ud.ud import UniversalDependencies
from cabocha2ud.ud.word import Misc
from cabocha2ud.ud.util import Field


def main() -> None:
    """
        main function
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("conll_file")
    parser.add_argument("-w", "--writer", default="-", type=argparse.FileType("w"))
    args = parser.parse_args()
    ud = UniversalDependencies(file_name=args.conll_file)
    spos_lst: list[int] = []
    for spos, sent in enumerate(ud.sentences()):
        header_keys = sent.get_header_keys()
        if "newdoc id" not in header_keys:
            continue
        spos_lst.append(spos - 1)
    for spos in spos_lst[1:]:
        sent = ud.sentences()[spos]
        misc = cast(Misc, sent.words()[-1][Field.MISC])
        misc.update("SpaceAfter", "Yes")
    args.writer.write(str(ud) + "\n")


if __name__ == '__main__':
    main()
