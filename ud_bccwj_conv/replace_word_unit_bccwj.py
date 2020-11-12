# -*- coding: utf-8 -*-

"""

Convert CONLL file to blank data.

"""

import argparse
import pickle as pkl
import itertools
from lib import (
    separate_document, load_bccwj_core_file,
    is_spaceafter_yes, iterate_conll_and_bccwj,
    ID, FORM, LEMMA, UPOS, XPOS, FEATS, HEAD, DEPREL, DEPS, MISC
)



def _convert_misc(conll, misc_data):
    """
        convert MISC Filed
    """
    nfes = []
    for item in conll[MISC].split("|"):
        key, value = item.split("=")
        if key in ["BunsetuPositionType", "LUWPOS"]:
            value = misc_data["cont_org_to_bl"][key][value]
        if key in ["BunsetuPositionType", "LUWPOS", "BunsetuBILabel", "LUWBILabel"]:
            key = misc_data["label_org_to_bl"][key]
        nfes.append(key + "=" + str(value))
    return nfes


def _extract_num_info(bpos, bcc, cll):
    bccwj_info = [bpos, False, [0]]
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


def _write_sentence(sent, misc_data, tid, bcc_conll_map, writer, debug=False):
    writer.write(sent[0][0][1] + "\n")
    writer.write(
        "# text = {}".format("".join([
            "_　" if is_spaceafter_yes(conll[1].split("\t")) else "_" for conll, _ in sent[2:]
        ]).strip("　")) + "\n"
    )
    for citem, bctm in sent[2:]:
        assert bctm is not None
        cpos, cll = citem
        bpos, bcc = bctm
        cll = cll.split("\t")
        if debug:
            print("CL:{} BCC:{}".format(cll[FORM], "".join([b["原文文字列"] for b in bcc])))
        assert cll[FORM] in "".join([b["原文文字列"] for b in bcc]) or cll[FORM] == "目　次"
        misc_info = _convert_misc(cll, misc_data)
        # bccwj_info saved: [bpos, num_flag, num_pos]
        bccwj_info = _extract_num_info(bpos, bcc, cll)
        cll[FORM], cll[LEMMA], cll[XPOS] = "_", "_", "_"
        writer.write("\t".join(cll[ID:MISC] + ["|".join(misc_info)]) + "\n")
        bcc_conll_map[tid][cpos] = bccwj_info
    writer.write("\n")


def merge_conll_and_bccwj(bccwj_flat, conll_flat, debug=False):
    """
        merge bccwj and conll
    """
    bccwj_iter = iter(enumerate(bccwj_flat))
    conll_iter = iter(enumerate(conll_flat))
    while True:
        try:
            bctm, citem = next(bccwj_iter), next(conll_iter)
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
                    print(citem[1].split("\t")[FORM], "".join([b["原文文字列"] for b in bctm[1]]))
                assert citem[1].split("\t")[FORM] in "".join([b["原文文字列"] for b in bctm[1]])
                yield (citem, bctm)
                cnt = len([b["原文文字列"] for b in bctm[1]]) - len(citem[1].split("\t")[FORM])
                while cnt > 0:
                    citem = next(conll_iter)
                    if debug:
                        print(citem[1].split("\t")[FORM], "".join([b["原文文字列"] for b in bctm[1]]), cnt)
                    yield (citem, bctm)
                    cnt -= len(citem[1].split("\t")[FORM])
        except StopIteration:
            break



def replace_blank_files(conll_file, base_data, misc_data, writer, debug=False):
    """
        replace blank file
    """
    bcc_conll_map = {}
    for tid, cnl in separate_document(conll_file):
        assert cnl[0].startswith("# sent_id =")
        assert tid in base_data, tid
        bcc_conll_map[tid] = {}
        # merge mapping conll and bccwj
        map_lst = merge_conll_and_bccwj(base_data[tid], cnl, debug=debug)
        sent_lists, sent = [], []
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
            _write_sentence(sent, misc_data, tid, bcc_conll_map, writer, debug=False)
    return bcc_conll_map


def main():
    """
        main function
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("conll_file", type=argparse.FileType("r"))
    parser.add_argument("misc_file", type=argparse.FileType("rb"))
    parser.add_argument("bccwj_file_name")
    parser.add_argument("bccwj_conll_mapping", type=argparse.FileType("wb"))
    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("-w", "--writer", type=argparse.FileType("w"), default="-")
    args = parser.parse_args()
    misc_data = pkl.load(args.misc_file)
    bccwj_data = load_bccwj_core_file(args.bccwj_file_name, load_pkl=True)
    bcc_conll_map = {}
    bcc_conll_map = replace_blank_files(args.conll_file, bccwj_data, misc_data, args.writer, debug=args.debug)
    pkl.dump(bcc_conll_map, args.bccwj_conll_mapping, protocol=4)


if __name__ == '__main__':
    main()
