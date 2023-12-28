# -*- coding: utf-8 -*-

"""
Filter UD for CEJC
"""

import argparse
from pathlib import Path

CORE_FILE_SIZE = 52


def extract_id_from_filename(file_name: Path, col_suffix: str) -> str:
    """ extract id from file name """
    return file_name.name.replace(col_suffix, "")


def load_info_data(info_file: str) -> dict[str, str]:
    """ load info csv file """
    info_dict: dict[str, str] = {}
    with open(info_file, "r", encoding="utf-8") as rdr:
        header = next(rdr).rstrip("\n").split("\t")
        info = [dict(zip(header, line.rstrip("\n").split("\t"))) for line in rdr]
        info_dict = {d["会話ID"]: d["データ種類"] for d in info}
    assert len(info_dict) == CORE_FILE_SIZE
    return info_dict


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument("base_dir", type=str)
    parser.add_argument("-i", "--info-file", type=str, default="ud_cejc_scirpt/core_sp_info.tsv")
    parser.add_argument("-c", "--col-suffix", default="-dialog.conllu")
    parser.add_argument("-o", "--output-dir", default=None)
    args = parser.parse_args()

    info_dict = load_info_data(args.info_file)
    if not Path(args.base_dir, "SUW").exists() and Path(args.base_dir, "LUW").exists():
        raise FileNotFoundError(f"base_dir must include SUW and LUW directory: {args.base_dir}")
    if args.output_dir is None:
        args.output_dir = args.base_dir
    for unit_type in ["suw", "luw"]:
        cab_dir = Path(args.base_dir, unit_type.upper())
        ud_files = [
            uname for uname in sorted(cab_dir.iterdir()) if str(uname).endswith(args.col_suffix)
        ]
        assert len(ud_files) == CORE_FILE_SIZE, f"Err: size {len(ud_files)} != {CORE_FILE_SIZE}"
        udfiles_map = {
            extract_id_from_filename(filename, args.col_suffix): filename
            for filename in ud_files
        }
        for data_type in ["train", "dev", "test"]:
            fchk = {c: False for c in sorted(info_dict) if info_dict[c] == data_type}
            wrt_ud_filename = Path(args.output_dir, f"ud_cejc_{unit_type}_{data_type}.conllu")
            with open(wrt_ud_filename, "w", encoding="utf-8") as wrt:
                for id_ in fchk:
                    assert id_ in udfiles_map, "not found ID {}".format(id_)
                    with open(udfiles_map[id_], "r", encoding="utf-8") as rdr:
                        wrt.write(rdr.read())
                    fchk[id_] = True
            assert all(fchk[c] for c in fchk), f"not found:{[fchk[c] for c in fchk if not fchk[c]]}"
            print("write " + str(wrt_ud_filename) + ".")


if __name__ == '__main__':
    _main()
