# -*- coding: utf-8 -*-

"""
    extract MISC Information from conllu file
"""

import argparse
import pickle as pkl
from collections import Counter

from lib import MISC


def main():
    """
        main function
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("conllu_file", type=argparse.FileType("r"))
    parser.add_argument("-w", "--writer", type=argparse.FileType("wb"), default="misc_mapping.pkl")
    args = parser.parse_args()
    misc_cnt = {"BunsetuPositionType": Counter(), "LUWPOS": Counter()}
    misc_map_data = {
        "cont_bl_to_org": {"BunsetuPositionType": None, "LUWPOS": None},
        "cont_org_to_bl": {"BunsetuPositionType": None, "LUWPOS": None},
        "label_bl_to_org": None, "label_org_to_bl": None
    }
    for line in args.conllu_file:
        line = line.rstrip("\n")
        if line.startswith("#") or line == "":
            continue
        misc = line.rstrip("\n").split("\t")[MISC]
        item = dict([l.split("=") for l in misc.rstrip("\n").split("|")])
        misc_cnt["BunsetuPositionType"][item["BunsetuPositionType"]] += 1
        misc_cnt["LUWPOS"][item["LUWPOS"]] += 1
    for label in ["BunsetuPositionType", "LUWPOS"]:
        misc_map_data["cont_org_to_bl"][label] = {
            value[0]: pos for pos, value
            in enumerate(sorted(misc_cnt[label].items(), key=lambda x: (x[1], x[0]), reverse=True))
        }
        misc_map_data["cont_bl_to_org"][label] = {
            v: k for k, v in misc_map_data["cont_org_to_bl"][label].items()
        }
    misc_map_data["label_org_to_bl"] = {
        "BunsetuPositionType": "BPT", "LUWPOS": "LPOS",
        "BunsetuBILabel": "BBIL", "LUWBILabel": "LBIL"
    }
    misc_map_data["label_bl_to_org"] = {v: k for k, v in misc_map_data["label_org_to_bl"].items()}
    print(misc_map_data)
    pkl.dump(misc_map_data, args.writer, protocol=4)


if __name__ == '__main__':
    main()