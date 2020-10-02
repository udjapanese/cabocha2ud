# -*- coding: utf-8 -*-

import sys
import argparse
import os
import codecs
import json

import tqdm

LUW_HEADER = [
    "corpusName(S)",
    "file(S)",
    "start(S)",
    "end(S)",
    "boundary(S)",
    "orthToken(S)",
    "pronToken(S)",
    "reading(S)",
    "lemma(S)",
    "originalText(S)",
    "pos(S)",
    "sysCType(S)",
    "cForm(S)",
    "apply(S)",
    "additionalInfo(S)",
    "lid(S)",
    "meaning(S)",
    "UpdUser(S)",
    "UpdDate(S)",
    "order(S)",
    "note(S)",
    "open(S)",
    "close(S)",
    "wType(S)",
    "fix(S)",
    "variable(S)",
    "formBase(S)",
    "lemmaID(S)",
    "usage(S)",
    "sentenceId(S)",
    "s_memo(S)",
    "origChar(S)",
    "pSampleID(S)",
    "pStart(S)",
    "orthBase(S)",
    "file(L)",
    "l_orthToken(L)",
    "l_pos(L)",
    "l_cType(L)",
    "l_cForm(L)",
    "l_reading(L)",
    "l_lemma(L)",
    "luw(L)",
    "memo(L)",
    "UpdUser(L)",
    "UpdDate(L)",
    "l_start(L)",
    "l_end(L)",
    "bunsetsu1(L)",
    "bunsetsu2(L)",
    "corpusName(L)",
    "diffSuw(L)",
    "l_lemmaNew(L)",
    "l_readingNew(L)",
    "l_orthBase(L)",
    "l_formBase(L)",
    "l_pronToken(L)",
    "l_wType(L)",
    "l_originalText(L)",
    "complex(L)",
    "l_meaning(L)",
    "l_kanaToken(L)",
    "l_formOrthBase(L)",
    "l_origChar(L)",
    "note(L)",
    "pSampleID(L)",
    "pStart(L)", "rn"
]


def load_db_file(db_file, add_header=False):
    """
        load dainagon data
    """
    full_data = []
    if add_header:
        header = LUW_HEADER
    else:
        header = next(db_file).rstrip("\r\n").split("\t")
    for line in tqdm.tqdm(db_file):
        line = line.rstrip("\r\n").split("\t")
        item = dict(list(zip(header, line)))
        if item["orthToken(S)"] == '","':
            item["orthToken(S)"] = ','
        full_data.append(item)
    return _split_db_file(full_data, "boundary(S)")


def _split_db_file(full_data, target_column):
    nfull, stack = [], []
    flag = False
    for item in full_data:
        if flag and item[target_column] == "B":
            nfull.append(stack)
            stack = []
        flag = True
        stack.append(item)
    assert stack[0][target_column] == "B"
    if len(stack) > 0:
        nfull.append(stack)
    return nfull


def _pre_parse_sent_cab(cabocha_data):
    pos = 0
    while cabocha_data[pos].startswith("#!"):
        pos += 1
    stack = []
    for line in cabocha_data[pos:]:
        line = line.rstrip("\r\n")
        if line.startswith("EOS"):
            yield stack
            stack = []
            continue
        stack.append(line)


def _pre_parse_cab(cabocha_list):
    cab_list_full = []
    cabocha_list = list(cabocha_list)
    for cabocha_data in cabocha_list:
        cab_list = []
        for line in cabocha_data:
            line = line.rstrip("\r\n")
            if line.startswith("* "):
                cab_list.append({
                    "type": "other", "org_line": line, "info": None,
                    "output_line": line, "detail": "bunsetu"
                })
            elif line.startswith("#! "):
                cab_list.append({
                    "type": "other", "org_line": line, "info": None,
                    "output_line": line, "detail": "doc_info"
                })
            else:
                items = line.split("\t")
                assert items[0] == items[2] or items[2] == ""
                info = {}
                info["orth"] = items[0]
                info["lemma"] = items[2]
                info["pos"] = items[3]
                info["ctype"] = items[4]
                info["cform"] = items[5]
                cab_list.append({
                    "type": "token", "org_line": line, "info": info,
                    "detail": "word"
                })
        cab_list_full.append(cab_list)
    return cab_list_full


def __fill_info(cab_info, morph, spa):
    ncab_info = {k: v for k, v in cab_info.items()}
    ncab_info["morph_full"] = morph
    ncab_info["orth"] = morph["orthToken(S)"]
    ncab_info["sp"] = "Yes" if spa["SpaceAfter"] == "YES" else "No"
    ncab_info["lemma"] = morph["lemma(S)"]
    ncab_info["pos"] = morph["pos(S)"]
    ncab_info["ctype"] = morph["sysCType(S)"] if morph["sysCType(S)"] != "" else "_"
    ncab_info["cform"] = morph["cForm(S)"] if morph["cForm(S)"] != "" else "_"
    ncab_info["yomi"] = morph["reading(S)"] if morph["reading(S)"] != "" else "_"
    ncab_info["usage"] = morph["usage(S)"] if morph["usage(S)"] != "" else "_"
    ncab_info["orth_base"] = morph["orthBase(S)"] if morph["orthBase(S)"] != "" else "_"
    ncab_info["l_yomi"] = morph["l_readingNew(L)"]
    ncab_info["l_lemma"] = morph["l_lemmaNew(L)"]
    ncab_info["l_bound"] = "B" if morph["luw(L)"] == "B" else "I"
    ncab_info["l_pos"] = morph["l_pos(L)"]
    ncab_info["l_cform"] = morph["l_cForm(L)"] if morph["l_cForm(L)"] != "" else "_"
    ncab_info["b_bound"] = "B" if morph["bunsetsu1(L)"] == "B" else "I"
    return ncab_info


LINE_FORMAT = "{orth}\t\t{lemma}\t{pos}\t{ctype}\t{cform}"\
    "\t{yomi}\t{usage}\t{sp}\t{orth_base}\t{b_bound}\t{l_bound}\t{l_lemma}\t{l_yomi}\t{l_pos}\t{l_cform}"
def __fill_output(cab_info):
    return LINE_FORMAT.format(
        orth=cab_info["orth"], orth_base=cab_info["orth_base"], lemma=cab_info["lemma"],
        pos=cab_info["pos"], ctype=cab_info["ctype"], cform=cab_info["cform"],
        sp=cab_info["sp"], yomi=cab_info["yomi"], usage=cab_info["usage"],
        l_bound=cab_info["l_bound"], l_lemma=cab_info["l_lemma"], l_yomi=cab_info["l_yomi"],
        l_pos=cab_info["l_pos"], l_cform=cab_info["l_cform"],
        b_bound=cab_info["b_bound"]
    )


def __fill_luw_info(merged_lines):
    prev_luw = None
    for pos, _ in enumerate(merged_lines):
        if "output_line" not in merged_lines[pos]:
            raise KeyError
        olines = merged_lines[pos]["output_line"].split("\t")
        if len(olines) < 4:
            continue
        if olines[11] == "I":
            olines[11] = "I"
            olines[12] = prev_luw[12]  # l_lemma
            olines[13] = prev_luw[13]  # l_yomi
            olines[14] = prev_luw[14]  # l_pos
            olines[15] = prev_luw[15]  # l_cform
        else:
            assert olines[11] == "B"
        prev_luw = olines[:]
        merged_lines[pos]["output_line"] = "\t".join(olines)


def _check_data(mdata, sdata, cdata):
    mmm = [m["orthToken(S)"] for m in mdata]
    sss = [s["orthToken(S)"] for s in sdata]
    ccc = [c["info"]["orth"] for c in cdata if c["detail"] == "word"]
    return mmm == sss == ccc


def filter_removed_nonconform_data(morph_data, sp_data, cab_list, pos_lst):
    """
        大納言データと対応しない（できない？）データを捨てる
    """
    mndata, sndata, cndata, pndata = [], [], [], []
    for pos, fdata in enumerate(zip(morph_data, sp_data, cab_list, pos_lst)):
        mdata, sdata, cdata, pdata = fdata
        if not _check_data(mdata, sdata, cdata):
            continue
        mndata.append(mdata)
        sndata.append(sdata)
        cndata.append(cdata)
        pndata.append(pdata)
    assert len(mndata) == len(sndata) == len(cndata) == len(pndata)
    return mndata, sndata, cndata, pndata


def mapping_data(cab_list, morph_data, spa_data):
    """
        map cabocha file and db files
    """
    merged_lines = []
    assert len(morph_data) == len(spa_data) == len(cab_list)
    for mdata, sdata, cdata in zip(morph_data, spa_data, cab_list):
        assert len(mdata) == len(sdata) and len(mdata) <= len(cdata)
        mit = iter(mdata)
        sit = iter(sdata)
        for target_cab in cdata:
            if target_cab["type"] == "other":
                merged_lines.append(target_cab)
                continue
            morph = next(mit)
            spinfo = next(sit)
            target_cab["info"] = __fill_info(target_cab["info"], morph, spinfo)
            target_cab["output_line"] = __fill_output(target_cab["info"])
            merged_lines.append(target_cab)
        merged_lines.append({"output_line": "EOS"})
    # 長単位情報を埋める
    __fill_luw_info(merged_lines)
    return merged_lines


def detect_cabocha_corpus_type(filename):
    if "pud" in filename.lower():
        return "CCD_UD-PUD"
    if "test" in filename.lower():
        return "CCD_UD-TEST"
    if "dev" in filename.lower():
        return "CCD_UD-DEV"
    if "train" in filename.lower():
        return "CCD_UD-TRAIN"
    raise KeyError


def load_align_file(align_file):
    align_data, ldata = [], []
    with codecs.open(align_file, encoding='utf-8', errors='ignore') as rdr:
        for line in rdr:
            if line.startswith("NULL"):
                break
            ldata.append(line)
    rdr = iter(ldata)
    header = next(rdr).rstrip("\r\n").split("\t")
    align_data = [
        dict(zip(header, line.rstrip("\r\n").split("\t")))
        for line in rdr
    ]
    return align_data, header


def filter_duplicated_removed_data(morph_data, sp_data, cab_list, align_data):
    assert len(morph_data) == len(sp_data) == len(cab_list) == len(align_data)
    cnt = 0
    mndata, sndata, cndata, plst, count = [], [], [], [], 0
    for pos, fdata in enumerate(zip(morph_data, sp_data, cab_list, align_data)):
        mdata, sdata, cdata, adata = fdata
        assert pos == int(adata["ID"])
        if adata["is_delete"] == "TRUE":
            continue
        cnt += 1
        plst.append(pos)
        mndata.append(mdata)
        sndata.append(sdata)
        cndata.append(cdata)
    assert len(mndata) == len(sndata) == len(cndata) == len(plst)
    return mndata, sndata, cndata, plst


def _write_cabocha(cab_data, merged_lines, writer):
    pos = 0
    while cab_data[pos].startswith("#!"):
        writer.write(cab_data[pos] + "\n")
        pos += 1
    for item in merged_lines:
        writer.write(item["output_line"] + "\n")

def main():
    """
    main function
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("morph_file")
    parser.add_argument("sp_file")
    parser.add_argument("cabocha_file")
    parser.add_argument("-a", "--add-header", default=False, action="store_true")
    parser.add_argument("-s", "--output-suffix", default=".dumped")
    parser.add_argument("-m", "--skip-sharp-mark", default=False, action="store_true")
    parser.add_argument("-d", "--delete-files", default=None)
    parser.add_argument("-i", "--id-map-files", default="id_map.tsv", type=argparse.FileType("w"))
    parser.add_argument("-r", "--not-remove-files", default=True, action="store_false")
    args = parser.parse_args()
    morph_data, sp_data, cab_data, align_data, aheder = [], [], [], None, None
    with codecs.open(args.morph_file, encoding="utf-16") as morph_file:
        morph_data = load_db_file(morph_file, add_header=args.add_header)
    with codecs.open(args.sp_file, encoding="utf-8") as sp_file:
        sp_data = load_db_file(sp_file)
    with codecs.open(args.cabocha_file, encoding="utf-8") as cab_file:
        cab_data = [c.rstrip("\r\n") for c in cab_file]
    cab_list = list(_pre_parse_cab(_pre_parse_sent_cab(cab_data)))
    if args.delete_files is not None:
        align_data, aheader = load_align_file(args.delete_files)
        morph_data, sp_data, cab_list, plst = filter_duplicated_removed_data(
            morph_data, sp_data, cab_list, align_data
        )
    else:
        plst = [p for p, _ in enumerate(cab_list)]
    if args.not_remove_files:
        morph_data, sp_data, cab_list, plst = filter_removed_nonconform_data(
            morph_data, sp_data, cab_list, plst
        )
    corpus_name = detect_cabocha_corpus_type(args.morph_file).split("-")[1].lower()
    assert len(morph_data) == len(sp_data) == len(cab_list) == len(plst)
    merged_lines = mapping_data(cab_list, morph_data, sp_data)
    with open(args.cabocha_file + args.output_suffix, "w") as writer:
        _write_cabocha(cab_data, merged_lines, writer)
    if args.delete_files is not None:
        cab_pos = {c: p for p, c in enumerate(plst)}
        assert align_data is not None
        if args.id_map_files is None:
            args.id_map_files = sys.stdout
        args.id_map_files.write("\t".join(aheader + ["cabocha_pos"]) + "\n")
        for pos, data in enumerate(align_data):
            assert str(pos) == data["ID"]
            line = [data[item] for item in aheader]
            if pos in cab_pos:
                args.id_map_files.write("\t".join(line + [str(cab_pos[pos])]) + "\n")
            else:
                args.id_map_files.write("\t".join(line + ["_"]) + "\n")


if __name__ == '__main__':
    main()
