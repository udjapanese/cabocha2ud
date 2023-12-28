"""merge CEJC cabocha to LUW.

```shell
python merge_cejc/merge_cabocha.py ~/CEJC_data/20220914-CEJC-DEP\
            ~/CEJC_data/morphSUW ~/CEJC_data/morphLUW
```

"""

import argparse
import csv
import glob
import os
import re
import shutil
import sys
from dataclasses import dataclass
from typing import Callable, TypeVar, cast

CORE_FILE_SIZE = 52  # refer size from https://www2.ninjal.ac.jp/conversation/cejc/design.html
CAB_DEP = 2
CAB_MORPH = 1
SUW_SIZE = 29
LUW_SIZE = 8
T = TypeVar("T")


@dataclass
class MorphDB:
    """ Morph DB object """
    header: list[str]
    items: list[dict[str, str]]

    def __post_init__(self):
        self.sents: list[list[dict[str, str]]] = []
        for pos, item in enumerate(self.items):
            if pos == 0 or item["文頭フラグ"] == "B":
                self.sents.append([])
            self.sents[-1].append(item)

    def __len__(self):
        return len(self.items)

    def to_list(self, _key: str, cnv: Callable[[str], T]) -> list[T]:
        """ get list for _key """
        return [cnv(item[_key]) for item in self.items]


@dataclass
class CabData:
    """ Cabocha Information Object """
    speaker_id: str
    cab_file_name: str

    def __post_init__(self) -> None:
        self.base_name = os.path.basename(self.cab_file_name)
        self.sent_list: list[list[tuple[int, str]]] = [[]]
        with open(self.cab_file_name, "r", encoding="utf-8") as rdr:
            for line in rdr:
                line = line.rstrip("\r\n")
                if line.startswith("#! "):  # 改めて作り直すため不要
                    continue
                if line.startswith("EOS"):
                    self.sent_list.append([])
                elif line.startswith("* "):
                    self.sent_list[-1].append((CAB_DEP, line))
                else:
                    self.sent_list[-1].append((CAB_MORPH, line))
        assert not self.sent_list[-1]
        self.sent_list.pop(-1)

    def generate_filelist(self, speaker_ids: dict[str, str]) -> str:
        """ generate file list """
        full_id = speaker_ids[self.speaker_id]
        return f"<File><Speaker>{full_id}</Speaker><FilePath>{self.base_name}</FilePath></File>"


@dataclass
class CEJCFiles:
    """ CEJC file object それぞれ対応している """
    dialog_id: str
    suw_db: MorphDB
    luw_db: MorphDB
    cabocha_files: dict[str, str]

    def __post_init__(self) -> None:
        suw_db, luw_db = self.suw_db, self.luw_db
        assert set(suw_db.to_list("会話ID", str)) == set(luw_db.to_list("会話ID", str)), "会話IDが揃っていません"
        assert set(suw_db.to_list("話者ラベル", str)) == set(luw_db.to_list("話者ラベル", str)), "話者ラベル不一致"
        self.speaker_labels: list[str] = sorted(set(suw_db.to_list("話者ラベル", str)))
        self.speaker_ids: dict[str, str] = dict((k.split("_")[0], k) for k in self.speaker_labels)
        self.cab_cont: dict[str, CabData] = {}
        for speaker_id in self.cabocha_files:
            exspeaker_id = self.speaker_ids[speaker_id]
            self.cab_cont[exspeaker_id] = CabData(speaker_id, self.cabocha_files[speaker_id])
        assert set(list(self.cab_cont.keys())) == set(list(self.speaker_ids.values())), "話者ラベルの不一致"

    def generate_cabocha_filename(self, output_dir) -> str:
        """ generate Cabocha filename """
        return os.path.join(output_dir, f"{self.dialog_id}-dialog.cabocha")

    def create_dialog_header(self) -> list[str]:
        """ ヘッダーを生成する

        dialog_id := <DialogID>.*</DialogID>
        files_list
            :=<FileInfo><File><Speaker>{}</Speaker><FilePath>{}</FilePath></File>...</FileInfo>

        Args:
            dialog_id (str): 会話ID
            cab_files (list[tuple[str, str]]): Cabochaデータ

        Returns:
            str: ヘッダー文字列
        """
        file_list = "<FileInfo>{}</FileInfo>".format(
            "".join([c.generate_filelist(self.speaker_ids) for _, c in self.cab_cont.items()])
        )
        return [
            f"#! DOCID\t1\t{self.dialog_id}",
            "#! DOC\t1",
            f"#! DOCATTR\t<DocInfo><DialogID>{self.dialog_id}</DialogID>{file_list}</DocInfo>"
        ]


def read_morph_csv(file_name: str, encoding="shift-jis") -> MorphDB:
    """ CSVファイルの読み込み（CEJCの形態素ファイル）

    Args:
        file_name (str): ファイル名
        encoding (str, optional): ファイルのエンコード. Defaults to "shift-jis".

    Returns:
        MorphDB: MorphファイルのObject
    """
    items: list[dict[str, str]] = []
    header: list[str] = []
    with open(file_name, "r", encoding=encoding) as rdr:
        header = cast(list, csv.DictReader(rdr).fieldnames)
        rdr.seek(0, os.SEEK_SET)
        items = list(csv.DictReader(rdr))
    return MorphDB(header, items)


def collect_cabocha_files(base_cabocha_dir: str) -> dict[str, dict[str, str]]:
    """ Cabochaファイルを話者ごとにまとめる。

    Args:
        base_cabocha_dir (str): Cabochaファイルのあるディレクトリ

    Returns:
        dict[str, dict[str, str]]: files_path[dialog_id][parson_id] 値はファイルのPath
    """
    cab_file_paths: dict[str, dict[str, str]] = {}
    for cab_file_name in glob.glob(os.path.join(base_cabocha_dir, "*.cabocha")):
        base_name = os.path.basename(cab_file_name)
        if file_re := re.match(r"(.*)-(.*).cabocha", base_name):
            dialog_id, parson_id = cast(tuple[str, str], file_re.groups())
            if dialog_id not in cab_file_paths:
                cab_file_paths[dialog_id] = {}
            cab_file_paths[dialog_id][parson_id] = cab_file_name
        else:
            raise ValueError("cabocha path name format is in-valid")
    return cab_file_paths


def collect_morph_dir(base_cabocha_dir: str, suw_dir: str, luw_dir: str) -> list[CEJCFiles]:
    """ Cabochaファイルを元に必要な形態素ファイルを算出しまとめる

    Args:
        base_cabocha_dir: Cabochaのディレクトリ
        suw_dir (str): morphSUW ディレクトリのパス
        luw_dir (str): morphLUW ディレクトリのパス

    Raises:
        ValueError: 該当ファイル名がないか、ファイル名がおかしいと発生

    Returns:
        list[CEJCFiles]: CEJCFilesのリスト
    """

    # Cabochaファイルを会話IDごとにまとめる
    cab_file_paths: dict[str, dict[str, str]] = collect_cabocha_files(base_cabocha_dir)
    assert len(cab_file_paths) == CORE_FILE_SIZE, len(cab_file_paths)

    morph_files_path: dict[str, dict[str, str]] = {}
    for unit_name, dir_path in [("SUW", suw_dir), ("LUW", luw_dir)]:
        for u_file in glob.glob(os.path.join(dir_path, "*.csv")):
            base_name = os.path.basename(u_file)
            if file_re := re.match(r"(.*)-morph{}.csv".format(unit_name), base_name):
                dialog_id, = cast(tuple[str, ], file_re.groups())
                if dialog_id not in cab_file_paths:  # コアデータ以外
                    continue
                if dialog_id not in morph_files_path:
                    morph_files_path[dialog_id] = {}
                morph_files_path[dialog_id][unit_name] = u_file
            else:
                raise ValueError("morph pathname format is in-valid")
    assert len(morph_files_path) == CORE_FILE_SIZE
    return [
        CEJCFiles(
            dialog_id=dialog_id, cabocha_files=p_data,
            suw_db=read_morph_csv(morph_files_path[dialog_id]["SUW"]),
            luw_db=read_morph_csv(morph_files_path[dialog_id]["LUW"]),
        ) for dialog_id, p_data in cab_file_paths.items()
    ]


def generate_morph_line(
    smorph: dict[str, str], lmorph: dict[str, str], luw_first: bool=False
) -> list[str]:
    """
        短単位情報smorph、長単位情報lmorphを抽出した行を返す
    """
    mlist: list[str] = []
    mlist.append(smorph["書字形"])
    mlist.append(
        ",".join(
            s for s in smorph["品詞"].split("-") + (["*"] * (4 - len(smorph["品詞"].split("-"))))
            + [smorph["活用型"], smorph["活用形"], smorph["語彙素読み"], smorph["語彙素"]]
            + [smorph["書字形"], smorph["発音形出現形"], smorph["タグ付き書字形"], "*", smorph["語種"]]
                + (["*"] * 10) + [smorph["語形"]] + (["*"] * 5)
        )
    )
    if luw_first:
        mlist.append(lmorph["書字形"])
        mlist.append(
            ",".join(
                ltem for ltem in
                    lmorph["品詞"].split("-") + (["*"] * (4 - len(lmorph["品詞"].split("-"))))
                + [lmorph["活用型"], lmorph["活用形"], lmorph["発音形出現形"], lmorph["語彙素"]]
            )
        )
    else:
        mlist.extend(["", "*,*,*,,,,,"])
    assert len(mlist[1].split(",")) == SUW_SIZE and len(mlist[3].split(",")) == LUW_SIZE
    assert len(mlist) == 4
    return mlist


def create_utterance_footter(
    dialog_id: str, speaker_id: str, speaker_count: dict[str, int], dialog_sent_pos: int,
    end_spos: int, tok_range: list[str]
) -> list[str]:
    """ generate uttrance footer for ex-cabocha format """
    speaker_id_s = speaker_id.split("_")[0]  # 話者名を外す
    sent_id = f"{dialog_id}-{dialog_sent_pos}_{speaker_id}_{speaker_count[speaker_id_s]}"
    return [
        f'#! SEGMENT_S cejc-dep:utterance 0 {end_spos} "{sent_id}"',
        f'#! ATTR cejc-dep:sent-id "{sent_id}"',
        f'#! ATTR cejc-dep:dialog-utterance-position "{dialog_sent_pos}"',
        f'#! ATTR cejc-dep:speaker-id "{speaker_id}"',
        f'#! ATTR cejc-dep:speaker-utterance-position "{speaker_count[speaker_id]}"',
        f'#! ATTR cejc-dep:suw-sequence-number "{tok_range[0]}-{tok_range[1]}"',
        f'#! ATTR cejc-dep:luw-sequence-number "{tok_range[2]}-{tok_range[3]}"'
    ]


def expand_sentence(morphs: list[list[str]], cab: list[tuple[int, str]]) -> tuple[int, list[str]]:
    """ Cabochaの形態素行を展開

    Args:
        morphs (list[list[str]]): morphSUWとmorphLUWからの情報列
        cab_sent (list[tuple[int, str]]): Cabochaファイルのデータ
    Raises:
        KeyError: cab_sent自体に問題があると発生

    Returns:
            int: end_pos,  list[str]: 出力行

    """
    morph_it = iter(morphs)
    prev_bunsetu = False
    out_content: list[str] = []
    end_range: int = 0
    for line_info, tok_line in cab:
        assert line_info in [CAB_DEP, CAB_MORPH], "line_info MUST be CAB_DEP or CAB_MORPH"
        if line_info == CAB_DEP:
            out_content.append(tok_line)
            prev_bunsetu = True
        elif line_info == CAB_MORPH:
            nmorph_line: list[str] = []
            tok, _, _ = tok_line.split("\t")
            end_range += len(tok)
            nmorph = next(morph_it)
            while tok != nmorph[0] and nmorph[1].split(",")[0] == "形態論情報付与対象外":
                nmorph = next(morph_it)
            assert tok == nmorph[0], f"MUST BE same orth each {tok} <-> {nmorph[0]}"
            nmorph_line.extend([nmorph[0], nmorph[1], nmorph[2], nmorph[3]])
            if prev_bunsetu:
                nmorph_line.append("B")
                prev_bunsetu = False
            else:
                nmorph_line.append("")
            assert len(nmorph_line) == 5
            out_content.append("\t".join(nmorph_line))
    return end_range, out_content


def expand_morph_information(
    suw_sent: list[dict[str, str]], luw_sent: list[dict[str, str]]
) -> list[list[str]]:
    """
    拡張Cabochaの形態素情報4列まで抽出をする。（5列目：文節境界情報は`expand_cabocha_info`で付与）

    Args:
        suw_sent (list[dict[str, str]]): 短単位の文の形態素リスト
        luw_sent (list[dict[str, str]]): 長単位の文の形態素リスト
    """
    assert "".join([stk["書字形"] for stk in suw_sent]) == "".join([ltk["書字形"] for ltk in luw_sent])
    ppos = 0
    suw_position: list[tuple[int, int]] = []
    for ltok in luw_sent:
        wsize = 1
        while ltok["書字形"] != "".join([stok["書字形"] for stok in suw_sent[ppos:ppos + wsize]]):
            wsize += 1
        suw_position.append((ppos, ppos + wsize))
        ppos += wsize
    assert len(suw_position) == len(luw_sent), "{}".format(suw_position)
    return [
        generate_morph_line(smorph, luw_sent[lpos], suw_pos == 0)
        for lpos, (spos, epos) in enumerate(suw_position)
        for suw_pos, smorph in enumerate(suw_sent[spos:epos])
    ]


def generate_excabocha_output(cejc_data: CEJCFiles) -> list[str]:
    """ Generate output for dialog_id """
    suw_sents = cejc_data.suw_db.sents
    luw_sents = cejc_data.luw_db.sents
    assert len(suw_sents) == len(luw_sents)
    out_content: list[str] = cejc_data.create_dialog_header()
    speaker_count: dict[str, int] = {sid.split("_")[0]: 0 for sid in cejc_data.speaker_labels}
    for sent_pos, (suw_sent, luw_sent) in enumerate(zip(suw_sents, luw_sents)):
        # 文ごとの処理
        speaker_id = suw_sent[0]["話者ラベル"]
        speaker_count[speaker_id.split("_")[0]] += 1

        target_cab = cejc_data.cab_cont[speaker_id].sent_list.pop(0)
        assert speaker_id.startswith(cejc_data.cab_cont[speaker_id].speaker_id)

        # 1文の処理: 対象のCabochaファイルを取り出して、短単位情報と長単位情報を展開する
        end_range, ncont = expand_sentence(
            expand_morph_information(suw_sent, luw_sent), target_cab
        )
        out_content.extend(ncont)

        out_content.extend(  # フッター情報の付与（詳しくはREADME.md）
            create_utterance_footter(
                cejc_data.dialog_id, cejc_data.cab_cont[speaker_id].speaker_id,
                speaker_count, sent_pos + 1, end_range,
                [suw_sent[0]["短単位連番"], suw_sent[-1]["短単位連番"],
                 luw_sent[0]["長単位連番"], luw_sent[-1]["長単位連番"]]
            )
        )

        out_content.append("EOS")
    assert sum(len(cont.sent_list) for _, cont in cejc_data.cab_cont.items()) == 0, "未展開の文あり"
    return out_content


@dataclass
class Args:
    """ ArgParse typing object for argparse """
    base_cabocha_dir: str
    base_suw_dir: str
    base_luw_dir: str
    output_dir: str


def _main() -> None:
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('base_cabocha_dir', type=str)
    parser.add_argument('base_suw_dir', type=str)
    parser.add_argument('base_luw_dir', type=str)
    parser.add_argument('-o', '--output-dir', type=str, default="../CEJC_data/output_cabocha")
    args = Args(**parser.parse_args().__dict__)

    # SUWファイルとLUWファイルとCabochaファイルとをまとめる
    cejc_files = collect_morph_dir(args.base_cabocha_dir, args.base_suw_dir, args.base_luw_dir)
    assert len(cejc_files) == CORE_FILE_SIZE, "ファイルサイズが合いません"

    if os.path.exists(args.output_dir):
        shutil.rmtree(args.output_dir)
    os.mkdir(args.output_dir)

    cejc_dialog_size = len(cejc_files)
    for dialog_cnt, cejc_data in enumerate(cejc_files):
        output_filename = cejc_data.generate_cabocha_filename(args.output_dir)
        with open(output_filename, "w", encoding="utf-8") as wrt:
            wrt.write("\n".join(generate_excabocha_output(cejc_data)) + "\n")
        sys.stderr.write(f"Merged and save {output_filename}. {dialog_cnt+1}/{cejc_dialog_size}\n")


if __name__ == '__main__':
    _main()
