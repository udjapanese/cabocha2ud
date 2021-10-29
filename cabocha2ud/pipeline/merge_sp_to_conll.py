# -*- coding: utf-8 -*-

"""
merge to sp information to GSD conll file
"""

import argparse
import re
from typing import Optional, Union, cast

from difflib import SequenceMatcher

from cabocha2ud.lib.logger import Logger
from cabocha2ud.ud import UniversalDependencies
from cabocha2ud.ud.sentence import Sentence
from cabocha2ud.ud.word import Word, Misc
from cabocha2ud.ud.util import FORM, MISC


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


def get_merged_poslist(ud: UniversalDependencies, sp_data: list[list[dict[str, str]]]) -> list[tuple[int, int]]:
    """ SPデータと統合する
     conllデータとSPデータをマッチングする
    Args:
        conll_data ([type]): [description]
        sp_data ([type]): [description]

    Returns:
        [type]: [description]
    """
    if len(ud.sentences()) == len(sp_data):
        return [(p, p) for p in range(len(ud.sentences()))]
    sp_it = iter(enumerate(sp_data))
    pos_list: list[tuple[int, int]] = []
    for cpos in range(len(ud.sentences())):
        spos, cand_sp = next(sp_it)
        stext = "".join([c["orthToken(S)"] for c in cand_sp])
        txt = ud.get_sentence(cpos).get_header("text")
        assert txt is not None
        ctext = txt.get_value()
        while similarity(stext, ctext) < 0.8:
            spos, cand_sp = next(sp_it)
            stext = "".join([c["orthToken(S)"] for c in cand_sp])
        pos_list.append((cpos, spos))
    assert len(pos_list) == len(ud.sentences())
    return pos_list


def matching_from_seqmath(sentence: Sentence, spd: list[dict[str, str]]) -> list[ tuple[Union[int, tuple[int, int]], tuple[int,...]] ]:
    """
        diff using by SequenceMatcher
         return [(conll_wrd_pos, spd_wrd_pos_tuple), ....]
    """
    assert len(sentence.words()) <= len(spd)
    cwrds = [cast(str, c[FORM].get_content()) for c in sentence.words()]
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
            if ii2 - ii1 <= jj2 - jj1 and ii2 - ii1 == 1:
                pos_lst.append(
                    (ii1, tuple([j for j in range(jj1, jj2)]))
                )
            else:
                pos_lst.append(
                    ((ii1, ii2), tuple([j for j in range(jj1, jj2)]))
                )
        else:
            assert KeyError("not found: ", opt)
    return pos_lst


def accent(text: str) -> str:
    text = re.sub(r'à|â', "_", text)
    text = re.sub(r'ï|î|í', "_", text)
    text = re.sub(r'û|ù|ü', "_", text)
    text = re.sub(r'è|é|ê|ë', "_", text)
    return text


def adapt_spafter_to_conll(sentence: Sentence, spd: list[dict[str, str]]) -> None:
    """ adapt spafter to CoNLL line

    Args:
        conll (list[list[str]]): SpaceAfter=を書き換えるCoNLL文
        spd (list[dict[str, str]]): SpaceAfterデータ
    Return
        なし、ただしsentenceはアップデートされている
    """
    if all([s["SpaceAfter"] != "YES" for s in spd]):
        return
    assert len(sentence.words()) <= len(spd)
    result_pos = matching_from_seqmath(sentence, spd)
    # assert [p for p, _ in result_pos] == list(range(len(conll[hpos:])))
    for cpos, sp_pos in result_pos:
        assert isinstance(sp_pos, tuple)
        # sp_posをみて、SpaceAfterがいるか確認する
        if len(sp_pos) == 1:  # 1対1
            if isinstance(cpos, int):
                if spd[sp_pos[0]]["SpaceAfter"] == "YES":
                    misc = sentence[cpos][MISC]
                    assert isinstance(misc, Misc)
                    misc.update("SpaceAfter", "Yes")
        elif len(sp_pos) > 1:
            if all([spd[spos]["SpaceAfter"] != "YES" for spos in sp_pos]):
                continue
            if isinstance(cpos, int):
                form = sentence[cpos][FORM].get_content()
                assert isinstance(form, str)
                ccc = accent(form)  # conll[hpos:][cpos][1])
                sss = "".join([
                    spd[spos]["orthToken(S)"] for spos in sp_pos
                ])
                assert ccc == sss, "{} != {}".format(ccc, sss)
            else:
                assert isinstance(cpos, tuple) and len(cpos) == 2
                cwrds = [sentence[ccc][FORM].get_content() for ccc in range(cpos[0], cpos[1])]
                assert all([isinstance(ccc, str) for ccc in cwrds])
        else:
            raise ValueError


def do(ud: UniversalDependencies, sp_data: list[list[dict[str, str]]], logger: Optional[Logger]=None) -> None:
    if logger is None:
        logger = Logger()
    logger.debug("do merge sp to conll")
    pos_list = get_merged_poslist(ud, sp_data)
    for cpos, spos in pos_list:
        sentence = ud.get_sentence(cpos)
        adapt_spafter_to_conll(sentence, sp_data[spos])
        new_text: str = ""
        for word in sentence:
            form = word[FORM].get_content()
            assert isinstance(form, str)
            new_text += form
            misc = word[MISC]
            assert isinstance(misc, Misc)
            sp = misc.get_from_key("SpaceAfter")
            if sp == "Yes":
                new_text += " "
        txt = ud.get_sentence(cpos).get_header("text")
        assert txt is not None
        txt.set_value(new_text)


def main() -> None:
    """
        main function
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("conll_file")
    parser.add_argument("sp_file")
    parser.add_argument("-w", "--writer", default="-", type=str)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    logger = Logger(debug=args.debug)
    ud = UniversalDependencies(file_name=args.conll_file)
    sp_data: list[list[dict[str, str]]] = []
    sp_data = load_db_file(args.sp_file)
    do(ud, sp_data, logger=logger)
    ud.write_ud_file(args.writer)


if __name__ == '__main__':
    main()
