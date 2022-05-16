# -*- coding: utf-8 -*-

import argparse

from merged_ud import MatchedSentence, get_matched_sentence, MISC


"""
Append LUWUPOS to SUW conllu from SUW and LUW conllu
"""


def _main():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('suw_file', type=str)
    parser.add_argument('luw_file', type=str)
    parser.add_argument('-w', '--writer', type=argparse.FileType("w"), default="-")
    args = parser.parse_args()
    matched_sent_data: list[MatchedSentence] = get_matched_sentence(args.suw_file, args.luw_file)
    for matched in matched_sent_data:
        # print("{}, {}".format(matched.sent1.get_sentid(), matched.sent1.get_text()))
        for tok1_lst, tok2_lst in matched.iter_merged_token():
            assert len(tok2_lst) == 1
            luw_pos = tok2_lst[0].UPOS
            for tok in tok1_lst:
                misc = tok.get_misc()
                misc["LUWUPOS"] = luw_pos
                new_keys = sorted([k for k in misc.keys()])
                tok[MISC] = "|".join([
                    "{}={}".format(key, misc[key]) for key in new_keys
                ])
        args.writer.write(
            matched.sent1.to_conllu() + "\n"
        )


if __name__ == '__main__':
    _main()