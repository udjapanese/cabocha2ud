# encoding: utf8

"""

Merge number pipeline

"""

import argparse
from typing import Any, Optional

from cabocha2ud.bd import BunsetsuDependencies
from cabocha2ud.bd.bunsetu import Bunsetu
from cabocha2ud.bd.util import SUWFeaField
from cabocha2ud.bd.word import Word
from cabocha2ud.lib import flatten
from cabocha2ud.lib.logger import Logger
from cabocha2ud.lib.yaml_dict import YamlDict
from cabocha2ud.pipeline.component import BDPipeLine

USAGE = '''
Token aggregator for arabic numbers.
This command relies on the field order of input `cabocha.dumped` format.
The 3rd field of Bunsetu header line (Shuji/Kinougo index like 1/2) will not modified even the numerical tokens merged.
Usage:
    pipenv run cabocha2ud/pipeline/merge_number.py dev.cabocha -w dev.merged.cabocha
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
TARGET_XPOS = "名詞-数詞"


def merge_word_unit(num_stack: list[Word], bunsetu: Bunsetu, pwrd: Word) -> Word:
    """ return Merge Word Unit for target Bunsetsu """
    token_size: int = len(num_stack[0].get_tokens())
    token_ = [
        "".join([r.get_token(ORTH_FIELD) for r in num_stack]),
        ",".join([
            "".join([
                r.get_token(SUW_FORM_FILD).split(",")[idx] for r in num_stack
            ]) if idx in GATHER_TARGET_FIELDS
            else '' if idx in RM_ID_FIELDS and len(num_stack) > 1
            else field
            for idx, field in enumerate(num_stack[0].get_token(SUW_FORM_FILD).split(","))
        ]),
        num_stack[0].get_token(LUW_FORM_FILD) if token_size > 2 else "",
        num_stack[0].get_token(LUW_FES_FILD) if token_size > 2 else "",
        num_stack[0].get_token(BUNSETU_BI_FIELD) if token_size > 2 else ""
    ]
    _ddd: dict[str, Any] = {
        "doc": num_stack[0].doc, "token": token_,
        "word_unit_mode": num_stack[0].word_unit_mode,
        "bunsetu": bunsetu, "logger": bunsetu.logger
    }
    if not (token_size <= 2 or num_stack[0].get_token(LUW_FORM_FILD) != ""):
        _ddd["luw_info"] = pwrd
    return Word(**_ddd)


def check_bunsetu_merge_number(bunsetu: Bunsetu) -> None:
    """ check bunsetu for exists merge number """
    new_luw_unit_list: list[list[Word]] = []

    for luw_unit in bunsetu.get_luw_list():
        new_luw_unit: list[Word] = []
        num_stack: Optional[list[Word]] = None

        for lwrd in luw_unit:
            suw_pos = lwrd.get_features()
            is_num = suw_pos[SUWFeaField.orth] in NUMBER_ORTH
            if num_stack and (is_num and "-".join(suw_pos[0:2]) == TARGET_XPOS):
                num_stack.append(lwrd)
            elif num_stack and not (is_num and "-".join(suw_pos[0:2]) == TARGET_XPOS):
                new_luw_unit.append(merge_word_unit(num_stack, bunsetu, luw_unit[0]))
                num_stack = None
                new_luw_unit.append(lwrd)
            elif num_stack is None and (is_num and "-".join(suw_pos[0:2]) == TARGET_XPOS):
                num_stack = [lwrd]
            else:
                new_luw_unit.append(lwrd)

        if num_stack:
            new_luw_unit.append(merge_word_unit(num_stack, bunsetu, luw_unit[0]))
        new_luw_unit_list.append(new_luw_unit)

    bunsetu.update_word_list(flatten(new_luw_unit_list))

class MergeNumberComponent(BDPipeLine):
    """ Merge Number SUW

    Args:
        PipeLineComponent (_type_): _description_
    """
    name = "merge_number"

    def __init__(self, target: BunsetsuDependencies, opts: YamlDict) -> None:
        super().__init__(target, opts)

    def __call__(self) -> None:
        assert isinstance(self.target, BunsetsuDependencies)
        self.logger.debug(f"do {self.name}")
        for doc in self.target.documents():
            for sent in doc.sentences():
                for bunsetu in sent.bunsetues():
                    check_bunsetu_merge_number(bunsetu)

    def prepare(self) -> None:
        pass

COMPONENT = MergeNumberComponent


def _main() -> None:
    parser = argparse.ArgumentParser(description=USAGE)
    parser.add_argument("cabocha_file")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("-w", "--writer", default="-", type=str)
    args = parser.parse_args()
    options = YamlDict(init={"logger": Logger(debug=args.debug)})
    bobj = BunsetsuDependencies(file_name=args.cabocha_file, options=options)
    COMPONENT(bobj, opts=options)()
    bobj.write_cabocha_file(args.writer)


if __name__ == '__main__':
    _main()
