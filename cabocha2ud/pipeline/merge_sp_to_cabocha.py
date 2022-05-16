# -*- coding: utf-8 -*-

"""
merge to sp information to GSD cabocha
"""

import argparse
import re
from typing import Optional, Union, cast

from difflib import SequenceMatcher

from cabocha2ud.lib.logger import Logger
from cabocha2ud.bd import BunsetsuDependencies
from cabocha2ud.bd.sentence import Sentence



def load_db_file(db_file: Optional[str]) -> list[list[dict[str, str]]]:
    """
        load dainagon data
    """
    if db_file is None:
        return []
    full_data: list[dict[str, str]] = []
    target_column: str = "boundary(S)"
    nfull: list[list[dict[str, str]]] = []
    stack: list[dict[str, str]] = []
    with open(db_file) as db_data:
        header = next(db_data).rstrip("\r\n").split("\t")
        for line in db_data:
            item: dict[str, str] = dict(list(zip(header, line.rstrip("\r\n").split("\t"))))
            if item["orthToken(S)"] == '","':
                item["orthToken(S)"] = ','
            full_data.append(item)
        for item in full_data[1:]:
            if item[target_column] == "B":
                nfull.append(stack)
                stack = []
            stack.append(item)
        assert stack[0][target_column] == "B"
        if len(stack) > 0:
            nfull.append(stack)
    return nfull


def similarity(alst: str, blst: str) -> float:
    if len(alst) < len(blst):
        alst, blst = blst, alst
    return SequenceMatcher(None, alst, blst).ratio()


def get_merged_poslist(bd: BunsetsuDependencies, sp_data: list[list[dict[str, str]]]) -> list[tuple[int, int]]:
    """ SPデータと統合する
     conllデータとSPデータをマッチングする
    Args:
        conll_data ([type]): [description]
        sp_data ([type]): [description]

    Returns:
        [type]: [description]
    """
    if len(bd.sentences()) == len(sp_data):
        return [(p, p) for p in range(len(bd.sentences()))]
    sp_it = iter(enumerate(sp_data))
    pos_list: list[tuple[int, int]] = []
    for cpos, sentence in enumerate(bd.sentences()):
        spos, cand_sp = next(sp_it)
        stext = "".join([c["orthToken(S)"] for c in cand_sp])
        ctext = sentence.get_text()
        while similarity(stext, ctext) < 0.8:
            spos, cand_sp = next(sp_it)
            stext = "".join([c["orthToken(S)"] for c in cand_sp])
        pos_list.append((cpos, spos))
    assert len(pos_list) == len(bd.sentences())
    return pos_list


def matching_from_seqmath(sentence: Sentence, spd: list[dict[str, str]]) -> list[tuple[Union[int, tuple[int, int]], tuple[int,...]]]:
    """
        diff using by SequenceMatcher
         return [(conll_wrd_pos, spd_wrd_pos_tuple), ....]
    """
    assert len(sentence.words()) <= len(spd)
    cwrds = [w.get_surface() for w in sentence.words()]
    swrds = [c["orthToken(S)"] for c in spd]
    if len(cwrds) == len(swrds):
        return [(p, (p, )) for p in range(len(cwrds))]
    sentence.logger.debug("cwrds: ", cwrds, "swrds: ", swrds)
    smcr = SequenceMatcher(None, cwrds, swrds)
    # pos_lst: list[tuple[int, tuple[int,...]]] = []
    pos_lst: list[ tuple[Union[int, tuple[int, int]], tuple[int,...]] ] = []
    for opt, ii1, ii2, jj1, jj2 in smcr.get_opcodes():
        sentence.logger.debug(opt, cwrds[ii1:ii2], swrds[jj1:jj2])
        if opt == 'equal':
            assert cwrds[ii1:ii2] == swrds[jj1:jj2]
            for iii, jjj in zip(range(ii1, ii2), range(jj1, jj2)):
                pos_lst.append((iii, (jjj, )))
        elif opt == 'replace':
            assert ii2 - ii1 <= jj2 - jj1 and ii2 - ii1 == 1
            pos_lst.append(
                (ii1, tuple([j for j in range(jj1, jj2)]))
            )
        else:
            assert KeyError("not found: ", opt)
    return pos_lst


def adapt_spafter_to_cabocha(sentence: Sentence, spd: list[dict[str, str]]) -> None:
    """ adapt spafter to Cabocha Data

    """
    if all([s["SpaceAfter"] != "YES" for s in spd]):
        return
    assert len(sentence.words()) <= len(spd)
    result_pos = matching_from_seqmath(sentence, spd)
    # assert [p for p, _ in result_pos] == list(range(len(conll[hpos:])))
    for cpos, sp_pos in result_pos:
        assert isinstance(sp_pos, tuple)
        if len(sp_pos) == 1:  # 1対1
            if spd[sp_pos[0]]["SpaceAfter"] == "YES":
                wrd = sentence.words()[cpos]
                pos = sentence.get_pos_from_word(wrd)
                assert sentence.annotation_list is not None
                sentence.annotation_list.append_segment([
                    '#! SEGMENT_S space-after:seg {} {} "{}"'.format(pos[0], pos[1], wrd.get_surface()).split(" "),
                    '#! ATTR space-after:value "YES"'.split(" ")
                ])
        elif len(sp_pos) > 1:
            assert all([spd[spos]["SpaceAfter"] != "YES" for spos in sp_pos])


def do(bd: BunsetsuDependencies, sp_data: list[list[dict[str, str]]], logger: Optional[Logger]=None) -> None:
    if logger is None:
        logger = Logger()
    logger.debug("do merge sp to cabocha")
    pos_list = get_merged_poslist(bd, sp_data)
    for cpos, spos in pos_list:
        sentence = bd.get_sentence(cpos)
        adapt_spafter_to_cabocha(sentence, sp_data[spos])


def main() -> None:
    """
        main function
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("cabocha_file")
    parser.add_argument("sp_file")
    parser.add_argument("-w", "--writer", default="-", type=str)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    logger = Logger(debug=args.debug)
    bd = BunsetsuDependencies(file_name=args.cabocha_file)
    sp_data: list[list[dict[str, str]]] = load_db_file(args.sp_file)
    do(bd, sp_data, logger=logger)
    bd.write_cabocha_file(args.writer)


if __name__ == '__main__':
    main()
