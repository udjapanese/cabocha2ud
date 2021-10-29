# -*- coding: utf-8 -*-

import argparse
import re
from typing import Optional

from cabocha2ud.lib.yaml_dict import YamlDict
from cabocha2ud.lib.logger import Logger
from cabocha2ud.bd import BunsetsuDependencies
from cabocha2ud.bd.sentence import Sentence
from cabocha2ud.bd.word import Word
from cabocha2ud.bd.annotation import AnnotationList, Segment


def reconstract_space_after(luw_unit: list[Word], sent: Sentence):
    """ change space after for luw unit

    Args:
        luw_unit (list[Word]): luw_unit
        sent (Sentence): sentence object of `luw_unit`
    """
    assert len(luw_unit) > 0
    first_wrd, last_wrd = luw_unit[0], luw_unit[-1]
    space_after_flag = False
    if last_wrd.has_space_after():
        space_after_flag = True
    for _, wrd in enumerate(luw_unit):
        if wrd.has_space_after():
            wrd_pos = sent.get_pos_from_word(wrd)
            assert isinstance(sent.annotation_list, AnnotationList)
            res = sent.annotation_list.get_segment(wrd_pos)
            assert isinstance(res, Segment)
            sent.annotation_list.remove_segment(res)
    first_pos, last_pos = -1, -1
    if space_after_flag:
        first_pos, _ = sent.get_pos_from_word(first_wrd)
        _, last_pos = sent.get_pos_from_word(last_wrd)
    if space_after_flag:
        luw_surface = "".join([w.get_surface() for w in luw_unit])
        assert len(range(first_pos, last_pos)) == len(luw_surface)
        assert isinstance(sent.annotation_list, AnnotationList)
        sent.annotation_list.append_segment([
            '#! SEGMENT_S space-after:seg {} {} "{}"'.format(first_pos, last_pos, luw_surface).split(" "),
            '#! ATTR space-after:value "YES"'.split(" ")
        ])


def update_luw_unit_to_bunsetu(sent: Sentence):
    """
        文節をまたぐ長単位を移動させる
            e.g 「事もあり」
    """
    remove_top_lst: list[tuple[int, int]] = []
    for bun_pos, bun in enumerate(sent):
        for pos, luw_unit in enumerate(bun.get_luw_list()):
            # 文節またぐ長単位の情報を引きづぎ
            if pos >= 1:
                break
            assert pos == 0
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


def check_dep(sent: Sentence, bun_pos: int):
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
                #print("luw----", luw_unit[0].luw_pos)
                #print("\n".join([str(lll) for lll in luw_unit]))
                #print("luw----")
                return False, bun_pos, len(luw_unit)
    return True, -1, -1


def move_luw_unit(sent: Sentence):
    result, bun_pos, luw_unit_size = check_luw_unit(sent)
    #print(sent.sent_id, result, bun_pos, luw_unit_size)
    while not result:
        #print("while --->", sent.sent_id, result, bun_pos, luw_unit_size)
        bunsetu = sent[bun_pos]
        #print("---- bun")
        #print(str(bunsetu))
        #print("------")
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


def build_luw_unit(sent: Sentence):
    assert sent.word_unit_mode == "luw", "differ mode: " + sent.word_unit_mode
    for bun in sent:
        for luw_unit in bun.get_luw_list():
            reconstract_space_after(luw_unit, sent)
    update_luw_unit_to_bunsetu(sent)
    move_luw_unit(sent)
    for _, bunsetu in enumerate(sent):
        assert len(bunsetu) > 0
        bunsetu.word_unit_mode = "luw"
        bunsetu.build_luw_unit()
    sent.bunsetu_dep = [bun.dep_pos for bun in sent.bunsetues()]
    sent.update_word_pos()


def do(bobj: BunsetsuDependencies, logger: Optional[Logger]=None) -> None:
    if logger is None:
        logger = Logger()
    logger.debug("do build luw")
    bobj.word_unit_mode = "luw"
    for _, doc in enumerate(bobj):
        doc.word_unit_mode = "luw"
        for _, sent in enumerate(doc):
            sent.word_unit_mode = "luw"
            build_luw_unit(sent)



def _main() -> None:
    parser = argparse.ArgumentParser(description="BUILD LUW format")
    parser.add_argument("cabocha_file")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("-w", "--writer", default="-", type=str)
    args = parser.parse_args()
    logger = Logger(debug=args.debug)
    bobj = BunsetsuDependencies(file_name=args.cabocha_file, options=YamlDict())
    do(bobj, logger=logger)
    bobj.write_cabocha_file(args.writer)


if __name__ == '__main__':
    _main()
