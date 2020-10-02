# -*- coding: utf-8 -*-

"""

merge LUW information

"""

import sys
import argparse
import difflib
import json

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

BCCWJ_FES = [
    "pos1",
    "pos2",
    "pos3",
    "pos4",
    "cType",
    "cForm",
    "lForm",
    "lemma",
    "orth",
    "pron",
    "orthBase",
    "pronBase",
    "goshu",
    "iType",
    "iForm",
    "fType",
    "fForm"
]

MISSING_BCCWJ_MATCH = json.load(open("conf/missing_bccwj_match.json"))
NUMBER_ORTH = {
    # number expression merged
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
    '０', '１', '２', '３', '４', '５', '６', '７', '８', '９',
    "〇", "７千", "ろく", "一", "億", "九", "九十", "五", "五十", "五千",
    "五百", "三", "三十", "三百", "四", "四十", "四百", "七", "十", "兆",
    "二", "二十", "二千", "八", "八十", "八千", "八百", "万", "六", "六十", "六百"
}

def parse_luw_file(luw_file):
    """
        parse luw file
    """
    sent_data = []
    header = next(luw_file).rstrip("\r\n").split("\t")
    prev_item = None
    for line in luw_file:
        item = dict(list(zip(header, line.rstrip("\r\n").split("\t"))))
        if item["luw(L)"] == "B" or item["luw(L)"] == "Update":
            prev_item = item
        else:
            assert item["luw(L)"] == "" and prev_item is not None
            for flabel in ["l_readingNew(L)", "l_lemmaNew(L)", "l_pos(L)", "l_cForm(L)"]:
                item[flabel] = prev_item[flabel]
        if item["file(S)"] == "BWJ_OY13_01853_c" and item["start(S)"] == "5410" and item["end(S)"] == "5450":
            # ここだけおかしい（？）ので直す
            item["pos(S)"] = "名詞-数詞"
            item["l_pos(L)"] = "名詞-数詞"
        pos2 = item["pos(S)"].split("-")[1] if len(item["pos(S)"].split("-")) > 1 else None
        nitem = {"fes": {"pos2": pos2}, "org": item}
        sent_data.append(nitem)
    return sent_data


def parse_cabocha_file(cab_file):
    """
        parse cabocha files
    """
    cab_data = [l.rstrip("\r\n") for l in cab_file]
    top, sents, bottom = [], [], []
    pos = 0
    while cab_data[pos].startswith("#! "):
        top.append(cab_data[pos])
        pos += 1
    cab_data = cab_data[pos:]
    pos = -1
    while not cab_data[pos].startswith("EOS"):
        bottom.insert(0, cab_data[pos])
        pos -= 1
    cab_data, sent = cab_data[:pos] + ["EOS"], []
    for line in cab_data:
        line = line.rstrip("\r\n")
        if line.startswith("EOS"):
            sents.append(sent)
            sent = []
        else:
            sent.append(_parse_cab_line(line))
    assert len(sent) == 0
    return top, sents, bottom


def _parse_cab_line(line):
    if line.startswith("#! ") or line.startswith("* "):
        return {"base_line": line, "output_line": line, "fes": None}
    nitem = {"base_line": line, "output_line": None, "fes": None}
    nitem["fes"] = dict(zip(BCCWJ_FES, line.split("\t")[1].split(",")))
    return nitem


def _parse_num_zone(num_stack):
    nnum_stack = []
    assert all([num_stack[0].split("\t")[3:7] == s.split("\t")[3:7] for s in num_stack])
    ofes = "\t".join(num_stack[0].split("\t")[3:7])
    luw_b = num_stack[0].split("\t")[2]
    orth = "".join([s.split("\t")[0] for s in num_stack])
    fes_s = None
    for line in num_stack:
        # 6,7
        fes = line.split("\t")[1].split(",")
        if fes_s is None:
            fes_s = fes[:]
            continue
        assert fes_s[0] == fes[0] and fes_s[1] == fes[1]
        fes_s[6] = fes_s[6] + fes[6]
        fes_s[7] = fes_s[7] + fes[7]
    return "{orth}\t{fes}\t{luw_b}\t{ofes}".format(
        orth=orth, fes=",".join(fes_s), luw_b=luw_b, ofes=ofes
    )


def merge_num_zone(output_lines):
    noutput_lines = []
    flag = False
    num_stack = []
    for line in output_lines:
        items = line.split("\t")
        if len(items) < 2:
            noutput_lines.append(line)
            continue
        if not flag and (items[-1] == "NUM_ZONE" and items[0] in NUMBER_ORTH):
            if noutput_lines[-1].split("\t")[-1] == "NUM_ZONE" and noutput_lines[-1].split("\t")[0] not in NUMBER_ORTH:
                rml = "\t".join(noutput_lines[-1].split("\t")[:-1])
                noutput_lines = noutput_lines[:-1]
                noutput_lines.append(rml)
                noutput_lines.append(line)
                continue
            flag = True
            num_stack.append(noutput_lines[-1])
            num_stack.append("\t".join(items[:-1]))
            noutput_lines = noutput_lines[:-1]
        elif flag and (items[-1] == "NUM_ZONE" and items[0] in NUMBER_ORTH):
            num_stack.append("\t".join(items[:-1]))
        elif flag and not (items[-1] == "NUM_ZONE" and items[0] in NUMBER_ORTH):
            flag = False
            num_stack = _parse_num_zone(num_stack)
            noutput_lines.append(num_stack)
            noutput_lines.append(line)
            num_stack = []
        else:
            noutput_lines.append(line)
    if len(num_stack) > 0:
        num_stack = _parse_num_zone(num_stack)
        noutput_lines.append(num_stack)
        noutput_lines.append(line)
    return noutput_lines


def insert_luw_info_to_cabocha(
        cab_sent, token_list, cab_match_tokens_pos,
        luw_data, match_token_pos
):
    """
        write to cabocha file
    """
    output_lines = []
    prev_line = None
    for sent_pos, sent in enumerate(cab_sent):
        for token_pos, token in enumerate(sent):
            if (sent_pos, token_pos) not in token_list:
                output_lines.append(token["output_line"])
            else:
                # 対応する長単位情報の獲得
                tok_pos = cab_match_tokens_pos[(sent_pos, token_pos)]
                if tok_pos in match_token_pos:
                    luw_info = luw_data[match_token_pos[tok_pos]]
                    token["output_line"] = _insert_cab_info(token, luw_info["org"])
                    output_lines.append(token["output_line"])
                    prev_line = token["output_line"]
                else:
                    luw_info = prev_line.split("\t")[2:]
                    luw_info[0] = "I"
                    output_lines.append(
                        token["base_line"] + "\t" + "\t".join(luw_info) + "\tNUM_ZONE"
                    )
        output_lines.append("EOS")
    return output_lines


def _insert_cab_info(token, luw_info):
    token["fes"][7] = luw_info["orthBase(S)"]
    orth = token["base_line"].split("\t")[0]
    return "{orth}\t{fes}\t{l_bound}\t{l_lemma}\t{l_yomi}\t{l_pos}\t{l_ctype}".format(
        orth=orth, fes=",".join([token["fes"][f] for f in BCCWJ_FES]),
        l_bound="B" if luw_info["luw(L)"] == "B" else "I",
        l_lemma=luw_info["l_lemmaNew(L)"],
        l_yomi=luw_info["l_readingNew(L)"],
        l_pos=luw_info["l_pos(L)"],
        l_ctype=luw_info["l_cForm(L)"] if luw_info["l_cForm(L)"] != "" else "_"
    )


def merge_and_detect_num_zone(org_tokens):
    """
      連続するNUM_ZONEを統合して、かつNUM_ZONEの場所を記録する
          # NUM_ZONEが連続の部分はくっつけ、ひとつのNUM_ZONEにする
        [a, b, NUM_ZONE, NUM_ZONE, c, d, ....] -> [a, b, NUM_ZONE, c, d, ....]
    """
    ntokens, num_zone_pos, flag, bun_cnt, prev_bun_cnt = [], [], False, 0, None
    for cpos, ctok in enumerate(org_tokens):
        bun, ctok = ctok.split("/")
        if bun == "B":
            bun_cnt += 1
        if not flag and ctok == "NUM_ZONE":
            flag = True
            num_zone_pos.append([])
            num_zone_pos[-1].append(cpos)
            ntokens.append(ctok)
        elif flag and ctok not in ["NUM_ZONE", "、", "，"]:
            flag = False
            ntokens.append(ctok)
        elif flag and ctok in ["、", "，"]:
            if len(org_tokens[cpos+1].split("/")) > 1 and org_tokens[cpos+1].split("/")[1] == "NUM_ZONE":
                assert cpos+1 < len(org_tokens)
                # 前が数字のものはまとめるので飛ばす
                num_zone_pos[-1].append(cpos)
            else:
                flag = False
                ntokens.append(ctok)
        elif flag and prev_bun_cnt != bun_cnt:
            # 文節が違う場合分ける必要がある
            ntokens.append(ctok)
            num_zone_pos.append([])
            num_zone_pos[-1].append(cpos)
        elif not flag:
            ntokens.append(ctok)
        else:
            assert flag and prev_bun_cnt == bun_cnt
            num_zone_pos[-1].append(cpos)
        prev_bun_cnt = bun_cnt
    ncount, dtokens = 0, []
    for tok in ntokens:
        if tok == "NUM_ZONE":
            dtokens += [org_tokens[pos].split("/")[1] for pos in num_zone_pos[ncount]]
            ncount += 1
        else:
            dtokens.append(tok)
    assert dtokens == [o.split("/")[1] for o in org_tokens]
    return ntokens, num_zone_pos


def create_token_lines(cab_sent, luw_data):
    """
        create base tokens list
        (対応付けをするためのデータづくり)
        token_list: Cabochaファイルのトークンのみの位置リスト
                        要素はcab_sentの(sent_pos, token_pos)
        cab_tokens: Cabochaファイルのトークンのみリスト
        luw_tokens: Dynagonファイルのトークンのみリスト
            cab_tokensとluw_tokensで対応付をする
        cab_match_tokens_pos: token_listとcab_sentの対応付け
                キーはtoken_listの位置
    """
    token_list, bunsetu_flag = [], False
    for sent_pos, sent in enumerate(cab_sent):
        for token_pos, token in enumerate(sent):
            if token["output_line"] is None:
                if bunsetu_flag:
                    token_list.append(("B", sent_pos, token_pos))
                else:
                    token_list.append(("", sent_pos, token_pos))
                bunsetu_flag = False
            elif token["output_line"].split(" ")[0] == "*":
                bunsetu_flag = True
    cab_tokens = [
        b + "/" + cab_sent[s][t]["base_line"].split("\t")[0]
        if cab_sent[s][t]["fes"]["pos2"] != "数詞" else b + "/NUM_ZONE"
        for b, s, t in token_list
    ]
    luw_tokens = [
        luw["org"]["bunsetsu1(L)"] + "/" + luw["org"]["orthToken(S)"]
        if luw["org"]["pos(S)"] != "名詞-数詞" else luw["org"]["bunsetsu1(L)"] + "/NUM_ZONE"
        for luw in luw_data
    ]
    ncab_tokens, ncab_num_pos = merge_and_detect_num_zone(cab_tokens)
    nluw_tokens, nluw_num_pos = merge_and_detect_num_zone(luw_tokens)
    # 文節情報不要になったので外す
    token_list = [(s, t) for _, s, t in token_list]
    cab_tokens_pos = {ppp: p for p, ppp in enumerate(token_list)}
    return token_list, ncab_tokens, ncab_num_pos, nluw_tokens, nluw_num_pos, cab_tokens_pos


def match_cab_and_luw(cab_tokens, cab_num_pos, luw_tokens, luw_num_pos):
    merge_sm = difflib.SequenceMatcher(None, a=cab_tokens, b=luw_tokens)
    match_token_pos = {}
    counter, num_counter, num_c_diff, num_l_diff = 0, 0, 0, 0
    sousa_lst = merge_sm.get_opcodes()
    for tag, cab_i1, cab_i2, luw_j1, luw_j2 in sousa_lst:
        if tag == "equal":
            assert cab_i2 - cab_i1 == luw_j2 - luw_j1
            for cab_pos, luw_pos in zip(range(cab_i1, cab_i2), range(luw_j1, luw_j2)):
                if cab_tokens[cab_pos] == "NUM_ZONE":
                    nluw_pos = luw_num_pos[num_counter][0]
                    match_token_pos[cab_pos+num_c_diff] = nluw_pos
                    num_c_diff += len(cab_num_pos[num_counter]) - 1
                    num_l_diff += len(luw_num_pos[num_counter]) - 1
                    num_counter += 1
                else:
                    match_token_pos[cab_pos+num_c_diff] = luw_pos + num_l_diff
        else:
            assert len(cab_tokens[cab_i1:cab_i2]) <= 1
            # MISSING_BCCWJ_MATCHから対応するluw_posをとりだす
            if len(cab_tokens[cab_i1:cab_i2]) == 0:
                # cabocha側の対応付けは不要なので飛ばす
                continue
            assert "NUM_ZONE" not in cab_tokens[cab_i1:cab_i2]
            assert cab_tokens[cab_i1:cab_i2][0] in MISSING_BCCWJ_MATCH
            luw_rel_pos = MISSING_BCCWJ_MATCH[cab_tokens[cab_i1:cab_i2][0]]["pos"]
            if luw_rel_pos >= 0:
                match_token_pos[cab_i1+num_c_diff] = range(luw_j1, luw_j2)[luw_rel_pos] + num_l_diff
            else:
                assert luw_j1 == luw_j2
                match_token_pos[cab_i1+num_c_diff] = luw_j1 + num_l_diff + luw_rel_pos
        counter += 1
    return match_token_pos


def main():
    """
    main function
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("base_file")
    parser.add_argument("-m", "--merge-number", action="store_true")
    parser.add_argument("-w", "--writer", type=argparse.FileType("w"), default="-")
    args = parser.parse_args()
    luw_data, cab_doc, cab_sent, cab_doc_info = None, None, None, None
    with open(args.base_file + ".luw", "r") as inp:
        luw_data = parse_luw_file(inp)
    with open(args.base_file + ".cabocha", "r") as inp:
        cab_doc, cab_sent, cab_doc_info = parse_cabocha_file(inp)
    token_list, cab_tokens, cab_num_pos, luw_tokens, luw_num_pos, cab_tokens_pos = create_token_lines(
        cab_sent, luw_data
    )
    match_token_pos = match_cab_and_luw(cab_tokens, cab_num_pos, luw_tokens, luw_num_pos)
    output_lines = insert_luw_info_to_cabocha(
        cab_sent, token_list, cab_tokens_pos, luw_data, match_token_pos
    )
    if args.merge_number:
        output_lines = merge_num_zone(output_lines)
    for line in cab_doc + output_lines + cab_doc_info:
        args.writer.write(line + "\n")


if __name__ == '__main__':
    main()
