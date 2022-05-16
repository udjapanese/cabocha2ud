# -*- coding: utf-8 -*-

"""
    extract MISC Information from conllu file
"""

import argparse
import pickle as pkl
import sys
from typing import TypedDict

from lib import MISC

class Misc_count(TypedDict):
    BunsetuPositionType: dict[str, int]
    LUWPOS: dict[str, int]
    UnidicInfo: dict[str, int]

class Misc_map_data(TypedDict):
    cont_bl_to_org: dict[str, dict]
    cont_org_to_bl: dict[str, dict]
    label_bl_to_org: dict[str, str]
    label_org_to_bl: dict[str, str]


def main():
    """
        main function
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("conllu_file")
    parser.add_argument("-w", "--writer", type=argparse.FileType("wb"), default="misc_mapping.pkl")
    args = parser.parse_args()
    misc_cnt: Misc_count = {"BunsetuPositionType": {}, "LUWPOS": {}, "UnidicInfo": {}}
    misc_map_data: Misc_map_data = {
        "cont_bl_to_org": {"BunsetuPositionType": {}, "LUWPOS": {}},
        "cont_org_to_bl": {"BunsetuPositionType": {}, "LUWPOS": {}},
        "label_bl_to_org": {}, "label_org_to_bl": {}
    }
    f = None
    if args.conllu_file == "-":
        f = sys.stdin
    else:
        f = open(args.conllu_file, "r")
    with f as rdr:
        for line in rdr:
            line = line.rstrip("\n")
            if line.startswith("#") or line == "":
                continue
            misc = line.rstrip("\n").split("\t")[MISC]
            def split_data(content: str):
                data = content.split("=")
                return data[0], "=".join(data[1:])
            item = dict([split_data(l) for l in misc.rstrip("\n").split("|")])
            if item["BunsetuPositionType"] not in misc_cnt["BunsetuPositionType"]:
                misc_cnt["BunsetuPositionType"][item["BunsetuPositionType"]] = 0
            misc_cnt["BunsetuPositionType"][item["BunsetuPositionType"]] += 1
            if "LUWPOS" in item:
                if item["LUWPOS"] not in misc_cnt["LUWPOS"]:
                    misc_cnt["LUWPOS"][item["LUWPOS"]] = 0
                misc_cnt["LUWPOS"][item["LUWPOS"]] += 1
            if "UnidicInfo" in item:
                if item["UnidicInfo"] not in misc_cnt["UnidicInfo"]:
                    misc_cnt["UnidicInfo"][item["UnidicInfo"]] = 0
                misc_cnt["UnidicInfo"][item["UnidicInfo"]] += 1
    for label in ["BunsetuPositionType", "LUWPOS", "UnidicInfo"]:
        misc_map_data["cont_org_to_bl"][label] = {
            value[0]: pos for pos, value
            in enumerate(sorted(misc_cnt[label].items(), key=lambda x: (x[1], x[0]), reverse=True))
        }
        misc_map_data["cont_bl_to_org"][label] = {
            v: k for k, v in misc_map_data["cont_org_to_bl"][label].items()
        }
    misc_map_data["label_org_to_bl"] = {
        "BunsetuPositionType": "BPT", "LUWPOS": "LPOS",
        "BunsetuBILabel": "BBIL", "LUWBILabel": "LBIL", "UnidicInfo": "UI",
        "PrevUDLemma": "PUDL"
    }
    misc_map_data["label_bl_to_org"] = {v: k for k, v in misc_map_data["label_org_to_bl"].items()}
    print(misc_map_data)
    pkl.dump(misc_map_data, args.writer, protocol=4)


if __name__ == '__main__':
    main()