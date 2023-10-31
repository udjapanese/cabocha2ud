# -*- coding: utf-8 -*-

"""
    extract MISC Information from conllu file
"""

import argparse
import pickle as pkl
import sys
from typing import TypedDict

from lib import MISC


class MiscCount(TypedDict):
    """ Misc Count """
    BunsetuPositionType: dict[str, int]
    LUWPOS: dict[str, int]
    UnidicInfo: dict[str, int]


class MiscMapData(TypedDict):
    """ Misc Map Data """
    cont_bl_to_org: dict[str, dict]
    cont_org_to_bl: dict[str, dict]
    label_bl_to_org: dict[str, str]
    label_org_to_bl: dict[str, str]


def _main():
    """
        main function
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("conllu_file")
    parser.add_argument("-w", "--writer", type=argparse.FileType("wb"), default="misc_mapping.pkl")
    args = parser.parse_args()
    misc_cnt: MiscCount = {"BunsetuPositionType": {}, "LUWPOS": {}, "UnidicInfo": {}}
    misc_map_data: MiscMapData = {
        "cont_bl_to_org": {"BunsetuPositionType": {}, "LUWPOS": {}},
        "cont_org_to_bl": {"BunsetuPositionType": {}, "LUWPOS": {}},
        "label_bl_to_org": {}, "label_org_to_bl": {}
    }
    fileo = None
    if args.conllu_file == "-":
        fileo = sys.stdin
    else:
        fileo = open(args.conllu_file, "r", encoding="utf-8")
    with fileo as rdr:
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
            in enumerate(
                sorted(misc_cnt[label].items(), # type: ignore[literal-required]
                       key=lambda x: (x[1], x[0]), reverse=True
            ))
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
    pkl.dump(misc_map_data, args.writer, protocol=4)


if __name__ == '__main__':
    _main()
