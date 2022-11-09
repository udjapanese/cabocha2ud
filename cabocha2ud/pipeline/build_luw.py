# -*- coding: utf-8 -*-

import argparse
import re
from typing import Optional

from cabocha2ud.bd import BunsetsuDependencies
from cabocha2ud.bd.sentence import Sentence
from cabocha2ud.lib.logger import Logger
from cabocha2ud.lib.yaml_dict import YamlDict


def reconstract_space_after(sent: Sentence, remove_luw_space: bool=False):
    """ change space after for luw unit

    Args:
        luw_unit (list[Word]): luw_unit
        sent (Sentence): sentence object of `luw_unit`
    """
    assert sent.annotation_list is not None
    if len([seg for seg in sent.annotation_list.get_segments() if seg.get_name() == "space-after:seg"]) == 0:
        return
    assert len(sent.flatten()) == len(sent.abs_pos_list)
    seg_lst = [seg for seg in sent.annotation_list.get_segments() if seg.get_name() == "space-after:seg"]
    sp_after_word_pos = []
    for (luw_start_pos, luw_end_pos), (wpos, wrd) in zip(sent.abs_pos_list, enumerate(sent.flatten())):
        insert_sp_pos_list: list = []
        for seg in seg_lst:
            if luw_start_pos <= seg.start_pos and seg.end_pos <= luw_end_pos:
                if luw_start_pos <= seg.start_pos and seg.end_pos < luw_end_pos:
                    # 中にある場合
                    insert_sp_pos_list.append(seg.end_pos - luw_start_pos)
                elif seg.end_pos == luw_end_pos:
                    # 末尾にある場合, SpaceAfterセグメント追加
                    sp_after_word_pos.append(wpos)
                else:
                    raise ValueError
        wrd.luw_form = "".join([w + " " if p + 1 in insert_sp_pos_list else w for p, w in enumerate(wrd.luw_form)])
        wrd._token[0] = wrd.luw_form
        wrd._token[2] = wrd.luw_form
    for seg in seg_lst:
        sent.annotation_list.remove_segment(seg)
    sent.update_word_pos()
    for wpos in sp_after_word_pos:
        # SpaceAfterのがあれば追加する
        wrd = sent.flatten()[wpos]
        luw_surface = wrd.get_surface()
        start_pos, end_pos = sent.get_pos_from_word(wrd)
        sent.annotation_list.append_segment([
            '#! SEGMENT_S space-after:seg {} {} "{}"'.format(start_pos, end_pos, luw_surface).split(" "),
            '#! ATTR space-after:value "YES"'.split(" ")
        ])
    return


def update_luw_unit_to_bunsetu(sent: Sentence):
    """
        文節をまたぐ長単位を移動させる
            e.g 「〜事も|あり/ますが」
    """
    remove_top_lst: list[tuple[int, int]] = []
    for bun_pos, bun in enumerate(sent):
        luw_unit = bun.get_luw_list()[0]
        if luw_unit[0].luw_label == "I":
            """
                対象のBをみつけ、情報を更新
            """
            assert bun.prev_bunsetu is not None
            prev_bun = bun.prev_bunsetu  # .get_luw_list()[-1]
            for lunit in luw_unit:
                prev_bun.append(lunit)
            remove_top_lst.append((bun_pos, len(luw_unit)))
    rmed_cnt = 0
    for bun_pos, luw_unit_size in remove_top_lst:
        for _ in range(luw_unit_size):
            sent[bun_pos-rmed_cnt].pop(0)
        if len(sent[bun_pos-rmed_cnt]) > 0:
            continue
        # もし0になってしまった場合文節を更新しないといけない
        for bpos, bbun in enumerate(sent[bun_pos-rmed_cnt+1:]):
            assert bbun.bunsetu_pos is not None and bbun.dep_pos is not None
            bbun.bunsetu_pos = bbun.bunsetu_pos - 1
            if bbun.dep_pos >= 0:
                bbun.dep_pos = bbun.dep_pos - 1
            else:
                assert bbun.dep_pos == -1
            sent.update_bunsetu(bun_pos-rmed_cnt+bpos, bbun)
        for bpos, bbun in enumerate(sent[:bun_pos-rmed_cnt-1]):
            assert bbun.dep_pos is not None
            if bbun.dep_pos >= bun_pos:
                bbun.dep_pos = bbun.dep_pos - 1
        sent.pop()
        rmed_cnt += 1
    for bun in sent:
        for new_wpos, wrd in enumerate(bun):
            wrd.word_pos = new_wpos
            wrd.bunsetu = bun
    assert all([len(bun) > 0 for bun in sent])


def check_dep(sent: Sentence, bun_pos: int) -> bool:
    for prev_bun in sent[:bun_pos]:
        if prev_bun.dep_pos == bun_pos:
            return True
    return False


CHECK_LUW_POS = re.compile(r"^(助動詞|助詞|補助記号-句点|補助記号-読点|補助記号-括弧|接続詞)")
def check_luw_unit(sent: Sentence) -> tuple[bool, int, int]:
    for bun_pos, bun in enumerate(sent):
        if bun_pos == 0:
            # 対象でないため
            continue
        for pos, luw_unit in enumerate(bun.get_luw_list()):
            if pos >= 1:
                break
            assert pos == 0
            if CHECK_LUW_POS.match(luw_unit[0].luw_pos) and check_dep(sent, bun_pos):
                return False, bun_pos, len(luw_unit)
    return True, -1, -1


def move_luw_unit(sent: Sentence):
    result, bun_pos, luw_unit_size = check_luw_unit(sent)
    while not result:
        bunsetu = sent[bun_pos]
        assert bun_pos > 0
        prev_bun = sent[bun_pos-1]
        luw_unit = bunsetu.get_luw_list()[0]
        for lunit in luw_unit:
            prev_bun.append(lunit)
        for _ in range(luw_unit_size):
            sent[bun_pos].pop(0)
        if len(sent[bun_pos]) > 0:
            for bun in sent:
                for new_wpos, wrd in enumerate(bun):
                    wrd.word_pos = new_wpos
                    wrd.bunsetu = bun
            result, bun_pos, luw_unit_size = check_luw_unit(sent)
            continue
        # もし0になってしまった場合文節を更新しないといけない
        for bpos, bbun in enumerate(sent[bun_pos+1:]):
            assert bbun.bunsetu_pos is not None and bbun.dep_pos is not None
            bbun.bunsetu_pos = bbun.bunsetu_pos - 1
            if bbun.dep_pos >= 0:
                bbun.dep_pos = bbun.dep_pos - 1
            else:
                assert bbun.dep_pos == -1
            sent.update_bunsetu(bun_pos+bpos, bbun)
        for bpos, bbun in enumerate(sent[:bun_pos-1]):
            assert bbun.dep_pos is not None
            if bbun.dep_pos >= bun_pos:
                bbun.dep_pos = bbun.dep_pos - 1
        sent.pop()
        for bun in sent:
            for new_wpos, wrd in enumerate(bun):
                wrd.word_pos = new_wpos
                wrd.bunsetu = bun
        assert all([len(bun) > 0 for bun in sent])
        result, bun_pos, luw_unit_size = check_luw_unit(sent)
    assert bun_pos == -1 and luw_unit_size == -1
    for bun_pos, bun in enumerate(sent):
        for new_wpos, wrd in enumerate(bun):
            wrd.word_pos = new_wpos
            wrd.bunsetu = bun
        if bun_pos == len(sent) - 1 and isinstance(bun.dep_pos, int) and bun.dep_pos > 0:
            bun.dep_pos = -1


def build_luw_unit(sent: Sentence, remove_luw_space: bool=False):
    assert sent.word_unit_mode == "luw", "differ mode: " + sent.word_unit_mode
    for _, bunsetu in enumerate(sent):
        assert len(bunsetu) > 0
        bunsetu.word_unit_mode = "luw"
        bunsetu.build_luw_unit()
    sent.update_word_pos()
    reconstract_space_after(sent, remove_luw_space=remove_luw_space)


def do(bobj: BunsetsuDependencies, logger: Optional[Logger]=None) -> None:
    if logger is None:
        logger = Logger()
    logger.debug("do build luw")
    bobj.word_unit_mode = "luw"
    for _, doc in enumerate(bobj):
        doc.word_unit_mode = "luw"
        for _, sent in enumerate(doc):
            sent.word_unit_mode = "luw"
            build_luw_unit(sent, bobj.options.get("remove_luw_space", False))


def _main() -> None:
    parser = argparse.ArgumentParser(description="BUILD LUW format")
    parser.add_argument("cabocha_file")
    parser.add_argument("--remove-luw-space", default=False, action="store_true")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("-w", "--writer", default="-", type=str)
    args = parser.parse_args()
    logger = Logger(debug=args.debug)
    options = YamlDict(init={"remove_luw_space": args.remove_luw_space})
    bobj = BunsetsuDependencies(file_name=args.cabocha_file, logger=logger, options=options)
    do(bobj, logger=logger)
    bobj.write_cabocha_file(args.writer)


if __name__ == '__main__':
    _main()
