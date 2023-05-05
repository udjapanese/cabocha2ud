# -*- coding: utf-8 -*-

"""
Filter UD for CEJC
"""

import argparse
import os

CORE_FILE_SIZE = 52


def extract_id_from_filename(file_name: str, col_suffix: str) -> str:
    return file_name.replace(col_suffix, "")


def load_info_data(info_file: str) -> dict[str, str]:
    info_dict: dict[str, str] = {}
    with open(info_file, "r") as rdr:
        header = next(rdr).rstrip("\n").split("\t")
        info = [dict(zip(header, l.rstrip("\n").split("\t"))) for l in rdr]
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
    if not os.path.exists(os.path.join(args.base_dir, "SUW")) and os.path.exists(os.path.join(args.base_dir, "LUW")):
        raise FileNotFoundError("base_dir must include SUW and LUW directory: {}".format(args.base_dir))
    if args.output_dir is None:
        args.output_dir = args.base_dir
    for unit_type in ["suw", "luw"]:
        cab_dir = os.path.join(args.base_dir, unit_type.upper())
        ud_files = [
            ufilename for ufilename in sorted(os.listdir(cab_dir)) if ufilename.endswith(args.col_suffix)
        ]
        assert len(ud_files) == CORE_FILE_SIZE, "FileNotFoundError: ud_files size != CORE_FILE_SIZE {} {}".format(len(ud_files), CORE_FILE_SIZE)
        udfiles_map = {
            extract_id_from_filename(filename, args.col_suffix): os.path.join(cab_dir, filename)
            for filename in ud_files
        }
        for data_type in ["train", "dev", "test"]:
            file_check = {c: False for c in sorted(info_dict) if info_dict[c] == data_type}
            wrt_ud_filename = os.path.join(args.output_dir, "ud_cejc_{}_{}.conllu".format(unit_type, data_type))
            with open(wrt_ud_filename, "w") as wrt:
                for id_ in file_check:
                    assert id_ in udfiles_map, "not found ID {}".format(id_)
                    with open(udfiles_map[id_], "r") as rdr:
                        wrt.write(rdr.read())
                    file_check[id_] = True
            assert all([file_check[c] for c in file_check]), "not found some file: {}".format([file_check[c] for c in file_check if not file_check[c]])
            print("write " + wrt_ud_filename + ".")


if __name__ == '__main__':
    _main()
