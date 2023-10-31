# -*- coding: utf-8 -*-

"""

Convert CONLL file to blank data.

"""

import argparse
import pickle as pkl
from typing import Iterable, Optional, TextIO, TypedDict

from lib import (FORM, ID, LEMMA, MISC, XPOS, is_spaceafter_yes,
                 load_bccwj_core_file, separate_document)


class MiscMapData(TypedDict):
    """ Misc Map Data """
    cont_bl_to_org: dict[str, dict]
    cont_org_to_bl: dict[str, dict]
    label_bl_to_org: dict[str, str]
    label_org_to_bl: dict[str, str]


def _convert_misc(conll: list[str], misc_data: MiscMapData) -> list[str]:
    """
        convert MISC Filed
    """
    nfes: list[str] = []
    for item in conll[MISC].split("|"):
        key, value = item.split("=")
        if key == "SpacesAfter" and value == "Yes":
            continue
        if key in ["BunsetuPositionType", "LUWPOS", "UnidicInfo"]:
            value = misc_data["cont_org_to_bl"][key][value]
        if key in ["BunsetuPositionType", "LUWPOS", "BunsetuBILabel",
                    "LUWBILabel", "UnidicInfo", "PrevUDLemma"]:
            key = misc_data["label_org_to_bl"][key]
        nfes.append(key + "=" + str(value))
    return nfes


def _extract_num_info(bpos: int, bcc: list[dict[str, str]], cll: list[str]) -> list:
    bccwj_info: list = [bpos, False, [0]]
    if [b["品詞"] for b in bcc][0] == "名詞-数詞" and len(bcc) > 1:
        bccwj_info[1] = True
        bccwj_info[2] = []
        for ccc in cll[FORM]:
            for ppp, bbb in enumerate(bcc):
                if ccc == bbb["原文文字列"]:
                    bccwj_info[2].append(ppp)
                    break
            # assert len(bccwj_info[2]) == len(cll[FORM]) or cll[FORM] == "目　次"
    return bccwj_info


def merge_conll_and_bccwj(
    bccwj_flat: list[list[dict[str, str]]], conll_flat: list[str], debug=False
) -> Iterable[tuple[tuple[int, str], Optional[tuple[int, list[dict[str, str]]]]]]:
    """
        merge bccwj and conll
    """
    bccwj_iter = iter(enumerate(bccwj_flat))
    conll_iter = iter(enumerate(conll_flat))
    while True:
        try:
            bctm, citem = next(bccwj_iter), next(conll_iter)
            if debug:
                print("ccccc", bctm, citem)
            while citem[1] == "" or citem[1].startswith("# "):
                # skip merge sent_id and text
                yield (citem, None)
                citem = next(conll_iter)
            cll = citem[1].split("\t")
            bwrd = "".join([b["原文文字列"] for b in bctm[1]]).strip("　")
            if cll[FORM] == "目　次":
                # A025n_OY01_00148-4
                yield (citem, bctm)
                continue
            if cll[FORM] == bwrd:
                yield (citem, bctm)
            else:
                if debug:
                    print("c", citem[1].split("\t")[FORM], "".join([b["原文文字列"] for b in bctm[1]]))
                assert citem[1].split("\t")[FORM] in "".join([b["原文文字列"] for b in bctm[1]])
                yield (citem, bctm)
                cnt = len([b["原文文字列"] for b in bctm[1]]) - len(citem[1].split("\t")[FORM])
                while cnt > 0:
                    citem = next(conll_iter)
                    if debug:
                        print(
                            "d", citem[1].split("\t")[FORM],
                            "".join([b["原文文字列"] for b in bctm[1]]), cnt
                        )
                    yield (citem, bctm)
                    cnt -= len(citem[1].split("\t")[FORM])
        except StopIteration:
            break


def _write_sentence(
    sent: list[tuple[ tuple[int, str], Optional[tuple[int, list[dict[str, str]]]] ]],
    misc_data: MiscMapData, tid: str, bcc_conll_map: dict[str, dict],
    errors: dict[tuple[str, ...], list[str]],
    filtered_ids: set[str], writer: TextIO, debug=False
):
    output_sent_lines: list[str] = []
    sent_id = sent[0][0][1].replace("# sent_id =", "")
    output_sent_lines.append(sent[0][0][1])
    output_sent_lines.append(
        "# text = {}".format("".join([
            "_　" if is_spaceafter_yes(conll[1].split("\t")) else "_" for conll, _ in sent[2:]
        ]).strip("　"))
    )
    for citem, bctm in sent[2:]:
        assert bctm is not None
        cpos, ccll = citem
        bpos, bcc = bctm
        cll = ccll.split("\t")
        if debug:
            print("CL:{} BCC:{}".format(cll[FORM], "".join([b["原文文字列"] for b in bcc])))
        assert cll[FORM] in "".join([b["原文文字列"] for b in bcc]) or cll[FORM] == "目　次"
        misc_info = _convert_misc(cll, misc_data)
        # bccwj_info saved: [bpos, num_flag, num_pos]
        bccwj_info = _extract_num_info(bpos, bcc, cll)
        cll[FORM], cll[LEMMA], cll[XPOS] = "_", "_", "_"
        output_sent_lines.append("\t".join(cll[ID:MISC] + ["|".join(misc_info)]))
        bcc_conll_map[tid][cpos] = bccwj_info
    if sent_id not in filtered_ids:
        writer.write("\n".join(output_sent_lines) + "\n")
        writer.write("\n")
    else:
        sid: tuple[str, ...] = tuple(output_sent_lines[0].split(" ")[-1].split("-"))
        errors[sid] = output_sent_lines


def replace_blank_files(
    conll_file: TextIO, base_data: dict[str, list[list[dict[str, str]]]], misc_data: MiscMapData,
    filtered_ids: set[str], writer: TextIO, debug: bool=False
):
    """
        replace blank file
    """
    bcc_conll_map: dict[str, dict] = {}
    errors: dict[tuple[str, ...], list[str]] = {}
    orders: dict[str, int] = {}
    order_count: int = 0
    for tid, cnl in separate_document(conll_file):
        assert cnl[0].startswith("# sent_id =")
        assert tid is not None and tid in base_data, tid
        if debug:
            print("aaa ->", cnl[0], tid)
        orders[tid] = order_count
        order_count += 1
        bcc_conll_map[tid] = {}
        # merge mapping conll and bccwj
        map_lst = merge_conll_and_bccwj(base_data[tid], cnl, debug=debug)
        sent_lists: list[
            list[tuple[tuple[int, str], Optional[tuple[int, list[dict[str, str]]]]]]
        ] = []
        sent: list[tuple[ tuple[int, str], Optional[tuple[int, list[dict[str, str]]]] ]] = []
        # divide each sentence
        for citem, bctm in map_lst:
            if citem[1] == "":
                sent_lists.append(sent)
                sent = []
            else:
                sent.append((citem, bctm))
        if len(sent) > 0:
            sent_lists.append(sent)
        for sent in sent_lists:
            assert sent[0][1] is None and sent[1][1] is None
            _write_sentence(
                sent, misc_data, tid, bcc_conll_map, errors,
                filtered_ids, writer, debug=debug
            )
    return bcc_conll_map, errors, orders


def main():
    """
        main function
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("conll_file", type=argparse.FileType("r"))
    parser.add_argument("misc_file", type=argparse.FileType("rb"))
    parser.add_argument("filtered_file", type=argparse.FileType("r"))
    parser.add_argument("bccwj_file_name")
    parser.add_argument("bccwj_conll_map_data", type=argparse.FileType("wb"))
    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("-w", "--writer", type=argparse.FileType("w"), default="-")
    args = parser.parse_args()
    filtered_ids: set[str] = set(l.rstrip("\n") for l in args.filtered_file)
    misc_data: MiscMapData = pkl.load(args.misc_file)
    bccwj_data = load_bccwj_core_file(args.bccwj_file_name, load_pkl=True)
    bcc_conll_map, errors, orders = replace_blank_files(
        args.conll_file, bccwj_data, misc_data, filtered_ids, args.writer, debug=args.debug
    )
    pkl.dump((bcc_conll_map, errors, orders), args.bccwj_conll_map_data, protocol=4)


if __name__ == '__main__':
    main()
