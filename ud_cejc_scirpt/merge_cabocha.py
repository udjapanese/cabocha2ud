# -*- coding: utf-8 -*-

"""
merge CEJC cabocha to LUW

```shell
python merge_cejc/merge_cabocha.py ~/CEJC_data/20220914-CEJC-DEP\
            ~/CEJC_data/morphSUW ~/CEJC_data/morphLUW
```

"""

import argparse
import glob
import os
import re
import shutil
import sys
from typing import TypedDict, cast

import pandas as pd
import tqdm

CORE_FILE_SIZE = 52  # refer size from https://www2.ninjal.ac.jp/conversation/cejc/design.html
CAB_DEP = 2
CAB_MORPH = 1
SUW_SIZE = 29
LUW_SIZE = 8


class CEJCFiles(TypedDict):
    """ CEJC file object """
    suw_db: pd.DataFrame
    luw_db: pd.DataFrame
    parsons: dict[str, str]


def collect_cabocha_files(base_cabocha_dir: str) -> dict[str, dict[str, str]]:
    """ Cabochaファイルを話者ごとにまとめます。

    Args:
        base_cabocha_dir (str): Cabochaファイルのあるディレクトリ

    Returns:
        dict[str, dict[str, str]]: files_path[dialog_id][parson_id] 値はファイルPath
    """
    files_path: dict[str, dict[str, str]] = {}
    for cab_file_name in glob.glob(os.path.join(base_cabocha_dir, "*.cabocha")):
        base_name = os.path.basename(cab_file_name)
        if file_re := re.match(r"(.*)-(.*).cabocha", base_name):
            dialog_id, parson_id = cast(tuple[str, str], file_re.groups())
            if dialog_id not in files_path:
                files_path[dialog_id] = {}
            files_path[dialog_id][parson_id] = cab_file_name
        else:
            raise ValueError("cabocha pathname format is in-valid")
    return files_path


def collect_morph_dir(
    files_path: dict[str, dict[str, str]], suw_dir: str, luw_dir: str
) -> dict[str, CEJCFiles]:
    """ Cabochaファイルを元に必要な形態素ファイルを算出

    Args:
        files_path (dict[str, dict[str, str]]): dict[dialog_id][parson_id]
        suw_dir (str): morphSUW ディレクトリのパス
        luw_dir (str): morphLUW ディレクトリのパス

    Raises:
        ValueError: 該当ファイル名がないか、ファイル名がおかしいと発生

    Returns:
        dict[str, CECJ_FILES]: keyがdialog_id
    """
    morph_files_path: dict[str, dict[str, str]] = {}
    for unit_name, dir_path in [("SUW", suw_dir), ("LUW", luw_dir)]:
        for u_file in glob.glob(os.path.join(dir_path, "*.csv")):
            base_name = os.path.basename(u_file)
            if file_re := re.match(r"(.*)-morph{}.csv".format(unit_name), base_name):
                dialog_id, = cast(tuple[str, ], file_re.groups())
                if dialog_id not in files_path:
                    continue
                if dialog_id not in morph_files_path:
                    morph_files_path[dialog_id] = {}
                morph_files_path[dialog_id][unit_name] = u_file
            else:
                raise ValueError("morph pathname format is in-valid")
    assert len(morph_files_path) == CORE_FILE_SIZE
    return {
        dialog_id: {
            "suw_path": pd.read_csv(
                morph_files_path[dialog_id]["SUW"], header=0, encoding="shift-jis"
            ),
            "luw_path": pd.read_csv(
                morph_files_path[dialog_id]["LUW"], header=0, encoding="shift-jis"
            ),
            "parsons": p_data
        } for dialog_id, p_data in files_path.items()
    }


def parse_cabocha_file(cabocha_file: str) -> list[list[tuple[int, str]]]:
    """
        Parse Cabocha File
    """
    cab_list: list[list[tuple[int, str]]] = [[]]
    with open(cabocha_file, "r", encoding="utf-8") as rdr:
        for line in rdr:
            line = line.rstrip("\r\n")
            if line.startswith("#! "):
                continue
            if line.startswith("EOS"):
                cab_list.append([])
            elif line.startswith("* "):
                cab_list[-1].append((CAB_DEP, line))
            else:
                cab_list[-1].append((CAB_MORPH, line))
    assert not cab_list[-1]
    cab_list.pop(-1)
    return cab_list


def parse_morph_file(pdb: pd.DataFrame) -> list[list[dict[str, str]]]:
    """ Morphファイルの解析

    Args:
        pdb (pd.DataFrame): morphファイル

    Returns:
        list[list[dict[str, str]]]: 解析結果
    """
    headers = pdb.columns.values.tolist()
    sents: list[list[dict[str, str]]] = []
    for pos, row in enumerate(zip(*[pdb[s] for s in headers])):
        items: dict[str, str] = dict(zip(headers, row))
        if pos == 0 or items["文頭フラグ"] == "B":
            sents.append([])
        sents[-1].append(items)
    return sents


def extract_morph_line(
    smorph: dict[str, str], lmorph: dict[str, str], luw_first: bool=False
) -> list[str]:
    """
        短単位情報smorph、長単位情報lmorphを抽出した行を返す
    """
    mlist: list[str] = []
    mlist.append(smorph["書字形"])
    def nan_s(xxx: str) -> str:
        return xxx if not pd.isna(xxx) else ""
    mlist.append(
        ",".join([
            nan_s(s) for s in smorph["品詞"].split("-") + (["*"] * (4 - len(smorph["品詞"].split("-"))))
            + [smorph["活用型"], smorph["活用形"], smorph["語彙素読み"], smorph["語彙素"]]
            + [smorph["書字形"], smorph["発音形出現形"], smorph["タグ付き書字形"], "*", smorph["語種"]]
                + (["*"]*10) + [smorph["語形"]] + (["*"]*5)
        ])
    )
    if luw_first:
        mlist.append(lmorph["書字形"])
        mlist.append(
            ",".join([
                nan_s(l)
                for l in lmorph["品詞"].split("-") + (["*"] * (4 - len(lmorph["品詞"].split("-"))))
                + [lmorph["活用型"], lmorph["活用形"], lmorph["発音形出現形"], lmorph["語彙素"]]
            ])
        )
    else:
        mlist.extend(["", "*,*,*,,,,,"])
    assert len(mlist[1].split(",")) == SUW_SIZE and len(mlist[3].split(",")) == LUW_SIZE
    assert len(mlist) == 4
    return mlist


def expand_morph_information(
    suw_sent: list[dict[str, str]], luw_sent: list[dict[str, str]]
) -> list[list[str]]:
    """

    拡張Cabochaの形態素情報4列まで抽出をする。（5列目：文節境界情報は後で付与）

    Args:
        suw_sent (list[list[dict[str, str]]]): 短単位の文の形態素リスト
        luw_sent (list[list[dict[str, str]]]): 長単位の文の形態素リスト
    """
    assert "".join([stk["書字形"] for stk in suw_sent]) == "".join([ltk["書字形"] for ltk in luw_sent])
    ppos, wsize = 0, 1
    suw_position: list[tuple[int, int]] = []
    for ltok in luw_sent:
        while ltok["書字形"] != "".join([stok["書字形"] for stok in suw_sent[ppos:ppos+wsize]]):
            wsize += 1
        suw_position.append((ppos, ppos + wsize))
        ppos = ppos + wsize
        wsize = 1
    assert len(suw_position) == len(luw_sent), "{}".format(suw_position)
    nmorph_data: list[list[str]] = []
    for lpos, (spos, epos) in enumerate(suw_position):
        for suw_pos, smorph in enumerate(suw_sent[spos:epos]):
            nmorph_data.append(extract_morph_line(smorph, luw_sent[lpos], suw_pos == 0))
    return nmorph_data


def create_header(dialog_id: str, cab_files: list[tuple[str, str]]) -> str:
    """ ヘッダーを生成する

    # dialog_id := <DialogID>.*</DialogID>
    # files_list :=<FileInfo><File><Speaker>{}</Speaker><FilePath>{}</FilePath></File>...</FileInfo>

    Args:
        dialog_id (str): 会話ID
        cab_files (list[tuple[str, str]]): Cabochaデータ

    Returns:
        str: ヘッダー文字列
    """
    dialog_id_f = "<DialogID>{_id}</DialogID>".format(_id=dialog_id)
    file_list = "<FileInfo>{}</FileInfo>".format(
        "".join([
            "<File><Speaker>{}</Speaker><FilePath>{}</FilePath></File>".format(sid, fname)
            for sid, fname in cab_files
        ])
    )
    return "<DocInfo>{dialog_id}{files_list}</DocInfo>".format(
        dialog_id=dialog_id_f, files_list=file_list
    )


def create_utterance_footter(
    dialog_id: str, speaker_id: str, speaker_count: dict[str, int], dialog_sent_pos: int,
    end_spos: int, suw_range: list[str], luw_range: list[str]
) -> list[str]:
    """ generate uttrance footer for ex-cabocha format """
    speaker_id_s = speaker_id.split("_")[0]  # 話者名を外す
    sent_id = "{dialog_id}-{dialog_utterance_position}_{speaker_id}_{speaker_utterance_pos}".format(
        dialog_id=dialog_id, dialog_utterance_position=dialog_sent_pos,
        speaker_id=speaker_id_s, speaker_utterance_pos=speaker_count[speaker_id]
    )
    footer: list[str] = [
        '#! SEGMENT_S cejc-dep:utterance 0 {} "{}"'.format(end_spos, sent_id),
        '#! ATTR cejc-dep:sent-id "{}"'.format(sent_id),
        '#! ATTR cejc-dep:dialog-utterance-position "{dialog_utterance_position}"'.format(
            dialog_utterance_position=dialog_sent_pos+1
        ),
        '#! ATTR cejc-dep:speaker-id "{speaker_id}"'.format(speaker_id=speaker_id_s),
        '#! ATTR cejc-dep:speaker-utterance-position "{}"'.format(speaker_count[speaker_id]),
        '#! ATTR cejc-dep:suw-sequence-number "{}-{}"'.format(*suw_range),
        '#! ATTR cejc-dep:luw-sequence-number "{}-{}"'.format(*luw_range),
    ]
    return footer


def expand_cabocha_info(
    morphs: list[list[str]], cab_sent: list[tuple[int, str]]
) -> tuple[int, list[str]]:
    """ Cabochaの形態素行を展開します

    Args:
        morphs (list[list[str]]): _description_
        cab_sent (list[tuple[int, str]]): _description_
    Raises:
        KeyError: cab_sent自体に問題があると発生

    Returns:
            int: end_pos  list[str]: 出力行

    """
    morph_it = iter(morphs)
    prev_bunsetu = False
    out_content: list[str] = []
    end_range: int = 0
    for line_info, tok_line in cab_sent:
        if line_info == CAB_DEP:
            out_content.append(tok_line)
            prev_bunsetu = True
        elif line_info == CAB_MORPH:
            nmorph_line: list[str] = []
            tok, _, _ = tok_line.split("\t")
            nmorph = next(morph_it)
            if tok != nmorph[0] and nmorph[1].split(",")[0] == "形態論情報付与対象外":
                # Morph情報とCabochaではCabochaサイドに形態論情報付与対象外の抜けが " あったり、なかったり " する
                while nmorph[1].split(",")[0] == "形態論情報付与対象外" and tok != nmorph[0]:
                    nmorph = next(morph_it)
            assert tok == nmorph[0], "MUST BE same orth each {} <-> {}".format(tok, nmorph[0])
            end_range += len(tok)
            nmorph_line.extend([tok, nmorph[1], nmorph[2], nmorph[3]])
            if prev_bunsetu:
                nmorph_line.append("B")
                prev_bunsetu = False
            else:
                nmorph_line.append("")
            assert len(nmorph_line) == 5
            out_content.append("\t".join(nmorph_line))
        else:
            raise KeyError("cab_sent's line_info MUST be CAB_DEP or CAB_MORPH")
    return end_range, out_content


def extract_morph_sent(cejc_data: CEJCFiles):
    """ 形態素ファイルを抽出する

    Args:
        cejc_data (CECJ_FILES): _description_

    Returns:
        _type_: _description_
    """
    suw_db = cejc_data["suw_path"]
    luw_db = cejc_data["luw_path"]
    assert set(suw_db["会話ID"].to_list()) == set(luw_db["会話ID"].to_list()), "会話IDが短単位・長単位ともに揃っていません"
    assert suw_db["短単位連番"].to_list() == list(range(1, suw_db.shape[0]+1))
    assert luw_db["長単位連番"].to_list() == list(range(1, luw_db.shape[0]+1)), "短単位長単位連番になっていなくてはいけません"
    assert set(suw_db["話者ラベル"].to_list()) == set(luw_db["話者ラベル"].to_list()), "短単位・長単位で話者ラベルが一致してません"
    speaker_labels: list[str] = sorted(set(suw_db["話者ラベル"].to_list()))
    speaker_ids: dict[str, str] = dict((k.split("_")[0], k) for k in speaker_labels)
    cab_info: list[tuple[str, str]] = []
    cab_content: dict[str, list[list[tuple[int, str]]]] = {}
    for speaker_id in cejc_data["parsons"]:
        cab_filename = cejc_data["parsons"][speaker_id]
        expand_speaker_id = speaker_ids[speaker_id]
        cab_info.append((expand_speaker_id, os.path.basename(cab_filename)))
        cab_content[expand_speaker_id] = parse_cabocha_file(cab_filename)
    return parse_morph_file(suw_db), parse_morph_file(luw_db), cab_info, cab_content, speaker_labels


def generate_output(
    dialog_id: str, suw_sents, luw_sents, cab_content, speaker_labels
) -> list[str]:
    """ generate output for dialog_id """
    out_content: list[str] = []
    speaker_count: dict[str, int] = {sid: 0 for sid in speaker_labels}
    for dialog_sent_pos, (suw_sent, luw_sent) in enumerate(zip(suw_sents, luw_sents)):
        # 文ごとの処理
        speaker_id = suw_sent[0]["話者ラベル"]
        speaker_count[speaker_id] += 1

        # 1文の処理: 対象のCabochaファイルを取り出して、短単位情報と長単位情報を展開する
        cab_sent: list[tuple[int, str]] = cab_content[suw_sent[0]["話者ラベル"]].pop(0)
        end_range, ncont = expand_cabocha_info(
            expand_morph_information(suw_sent, luw_sent), cab_sent
        )
        out_content.extend(ncont)

        # フッター情報の付与（詳しくはREADME.md）
        out_content.extend(
            create_utterance_footter(
                dialog_id, speaker_id, speaker_count, dialog_sent_pos+1, end_range,
                [suw_sent[0]["短単位連番"], suw_sent[-1]["短単位連番"]],
                [luw_sent[0]["長単位連番"], luw_sent[-1]["長単位連番"]]
            )
        )
        out_content.append("EOS")
    assert sum(len(k) for _, k in cab_content.items()) == 0, "全部の文から展開されてないようです"
    return out_content


def _main() -> None:
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('base_cabocha_dir', type=str)
    parser.add_argument('base_suw_dir', type=str)
    parser.add_argument('base_luw_dir', type=str)
    parser.add_argument('-o', '--output-dir', type=str, default="../CEJC_data/output_cabocha")
    args = parser.parse_args()

    # Cabochaファイルを会話IDごとにまとめる
    files_path: dict[str, dict[str, str]] = collect_cabocha_files(args.base_cabocha_dir)
    assert len(files_path) == CORE_FILE_SIZE, len(files_path)

    # SUWファイルとLUWファイルをCabochaファイルとまとめる
    cejc_files = collect_morph_dir(files_path, args.base_suw_dir, args.base_luw_dir)

    if os.path.exists(args.output_dir):
        shutil.rmtree(args.output_dir)
    os.mkdir(args.output_dir)

    for dialog_id, cejc_data in tqdm.tqdm(cejc_files.items()):
        suw_sents, luw_sents, cab_info, cab_content, speaker_labels = extract_morph_sent(cejc_data)
        assert len(suw_sents) == len(luw_sents)
        out_content: list[str] = [
            "#! DOC\t1", "#! DOCID\t1\t" + dialog_id,
            "#! DOCATTR\t" + create_header(dialog_id, cab_info)
        ]
        out_content += generate_output(
            dialog_id, suw_sents, luw_sents, cab_content, speaker_labels
        )
        output_filename = os.path.join(args.output_dir, "{}-dialog.cabocha".format(dialog_id))
        with open(output_filename, "w", encoding="utf-8") as wrt:
            wrt.write("\n".join(out_content) + "\n")
        sys.stderr.write("Merged and save {}.\n".format("{}-dialog.cabocha".format(dialog_id)))


if __name__ == '__main__':
    _main()
