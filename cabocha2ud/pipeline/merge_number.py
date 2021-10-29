# encoding: utf8

import argparse
import itertools
from typing import Optional, cast

from cabocha2ud.lib.yaml_dict import YamlDict
from cabocha2ud.lib.logger import Logger
from cabocha2ud.bd import BunsetsuDependencies
from cabocha2ud.bd.word import Word
from cabocha2ud.bd.bunsetu import Bunsetu


USAGE = '''
Token aggregator for arabic numbers.
This command relies on the field order of input `cabocha.dumped` format.
The 3rd field of Bunsetu header line (Shuji/Kinougo index like 1/2) will not modified even the numerical tokens merged.
Usage:
    python merge_number/merge_number.py dev.cabocha.dumped -w dev.cabocha.dumped.n
'''

GATHER_TARGET_FIELDS = {7, 8, 9, 10, 20, 21, 22, 23}
RM_ID_FIELDS = {27, 28}
ORTH_FIELD = 0
POS_FIELD = 3
LUW_BI_FIELD = 2  # 11
BUNSETU_BI_FIELD = 4  # 10
SUW_FORM_FILD = 1
LUW_FORM_FILD = 2
LUW_FES_FILD = 3
NUMBER_ORTH = {
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
    '０', '１', '２', '３', '４', '５', '６', '７', '８', '９',
}


def merge_word_unit(num_stack: list[Word], bunsetu: Bunsetu, pwrd: Word) -> Word:
    token_size: int = len(num_stack[0]._token)
    token_txt = "{form}\t{suw_fes}{luw_form}{luw_fes}{bunsetu_pos}".format(
        form="".join([cast(str, r._token[0]) for r in num_stack]),
        suw_fes=','.join([
            ''.join([
                r._token[SUW_FORM_FILD].split(",")[idx] for r in num_stack
            ]) if idx in GATHER_TARGET_FIELDS
            else '' if idx in RM_ID_FIELDS and len(num_stack) > 1
            else field
            for idx, field in enumerate(num_stack[0]._token[SUW_FORM_FILD].split(","))
        ]),
        luw_form="\t" + num_stack[0]._token[LUW_FORM_FILD] if token_size > 2 else "",
        luw_fes="\t" + num_stack[0]._token[LUW_FES_FILD] if token_size > 2 else "",
        bunsetu_pos="\t" + num_stack[0]._token[BUNSETU_BI_FIELD]  if token_size > 2 else ""
    )
    if token_size <= 2 or num_stack[0]._token[LUW_FORM_FILD] != "":
        return Word(
            token=token_txt, doc=num_stack[0].doc, bunsetu=bunsetu,
            word_unit_mode=num_stack[0].word_unit_mode
        )
    else:
        return Word(
            token=token_txt, doc=num_stack[0].doc, bunsetu=bunsetu,
            luw_info=pwrd, word_unit_mode=num_stack[0].word_unit_mode
        )

def do(bobj: BunsetsuDependencies, logger: Optional[Logger]=None) -> None:
    if logger is None:
        logger = Logger()
    logger.debug("do merge number")
    for doc in bobj.documents():
        for sent in doc.sentences():
            for bunsetu in sent.bunsetues():
                new_luw_unit_list: list[list[Word]] = []
                for luw_unit in bunsetu.get_luw_list():
                    new_luw_unit: list[Word] = []
                    num_stack: Optional[list[Word]] = None
                    for lwrd in luw_unit:
                        suw_pos = lwrd.get_features()
                        if num_stack and (suw_pos[8] in NUMBER_ORTH and "-".join(suw_pos[0:2]) == "名詞-数詞"):
                            num_stack.append(lwrd)
                        elif num_stack and not (suw_pos[8] in NUMBER_ORTH and "-".join(suw_pos[0:2]) == "名詞-数詞"):
                            logger.debug("--->>>", merge_word_unit(num_stack, bunsetu, luw_unit[0]))
                            new_luw_unit.append(merge_word_unit(num_stack, bunsetu, luw_unit[0]))
                            num_stack = None
                            new_luw_unit.append(lwrd)
                        elif num_stack is None and (suw_pos[8] in NUMBER_ORTH and "-".join(suw_pos[0:2]) == "名詞-数詞"):
                            num_stack = [lwrd]
                        else:
                            new_luw_unit.append(lwrd)
                    if num_stack:
                        new_luw_unit.append(merge_word_unit(num_stack, bunsetu, luw_unit[0]))
                    new_luw_unit_list.append(new_luw_unit)
                bunsetu.update_word_list(list(itertools.chain.from_iterable(new_luw_unit_list)))


def _main() -> None:
    parser = argparse.ArgumentParser(description=USAGE)
    parser.add_argument("cabocha_file")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("-w", "--writer", default="-", type=str)
    args = parser.parse_args()
    logger = Logger(debug=args.debug)
    bobj = BunsetsuDependencies(file_name=args.cabocha_file, options=YamlDict())
    do(bobj, logger=logger)
    bobj.write_cabocha_file(args.writer)


if __name__ == '__main__':
    _main()
