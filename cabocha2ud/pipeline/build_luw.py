# -*- coding: utf-8 -*-

"""

Build LUW Bunsetu Dependencies

"""


import argparse

from cabocha2ud.bd import BunsetsuDependencies
from cabocha2ud.bd.sentence import Sentence
from cabocha2ud.lib.logger import Logger
from cabocha2ud.lib.yaml_dict import YamlDict
from cabocha2ud.pipeline.component import BDPipeLine


def reconstract_space_after(sent: Sentence):
    """ Change space after for luw unit

    Args:
        sent (Sentence): sentence object of `luw_unit`
    """
    assert sent.annotation_list is not None
    seg_lst = [
        seg for seg in sent.annotation_list.get_segments()
        if seg.get_name() == "space-after:seg"
    ]
    if len(seg_lst) == 0:
        return
    assert len(sent.words()) == len(sent.abs_pos_list)
    sp_after_word_pos = []
    for (luw_spos, luw_end_pos), (wpos, wrd) in zip(sent.abs_pos_list, enumerate(sent.words())):
        insert_sp_pos_list: list = []
        for seg in seg_lst:
            if luw_spos <= seg.start_pos and seg.end_pos <= luw_end_pos:
                if luw_spos <= seg.start_pos and seg.end_pos < luw_end_pos:
                    # 中にある場合
                    insert_sp_pos_list.append(seg.end_pos - luw_spos)
                elif seg.end_pos == luw_end_pos:
                    # 末尾にある場合, SpaceAfterセグメント追加
                    sp_after_word_pos.append(wpos)
                else:
                    raise ValueError
        wrd.luw_form = "".join([
            w + " " if p + 1 in insert_sp_pos_list else w
            for p, w in enumerate(wrd.luw_form)
        ])
        wrd.set_token(0, wrd.luw_form)
        wrd.set_token(2, wrd.luw_form)
    for seg in seg_lst:
        sent.annotation_list.remove_segment(seg)
    sent.update_word_pos()
    for wpos in sp_after_word_pos:
        # SpaceAfterのがあれば追加する
        wrd = sent.words()[wpos]
        luw_surface = wrd.get_surface()
        s_pos, e_pos = sent.get_pos_from_word(wrd)
        sent.annotation_list.append_segment([
            f'#! SEGMENT_S space-after:seg {s_pos} { e_pos} "{luw_surface}"'.split(" "),
            str('#! ATTR space-after:value "YES"').split(" ")
        ])


def build_luw_unit(sent: Sentence):
    """ build LUW Unit """
    assert sent.word_unit_mode == "luw", "differ mode: " + sent.word_unit_mode
    for _, bunsetu in enumerate(sent):
        assert len(bunsetu) > 0
        bunsetu.word_unit_mode = "luw"
        bunsetu.build_luw_unit()
    sent.update_word_pos()
    reconstract_space_after(sent)


class BuildLUWComponent(BDPipeLine):
    """ Build LUW

    Args:
        PipeLineComponent (_type_): _description_
    """
    name = "build_luw"

    def __call__(self) -> None:
        assert isinstance(self.target, BunsetsuDependencies)
        self.logger.debug(f"do {self.name}")
        self.target.word_unit_mode = "luw"
        for _, doc in enumerate(self.target):
            doc.word_unit_mode = "luw"
            for _, sent in enumerate(doc):
                sent.word_unit_mode = "luw"
                build_luw_unit(sent)

    def prepare(self) -> None:
        pass


COMPONENT = BuildLUWComponent


def _main() -> None:
    parser = argparse.ArgumentParser(description="BUILD LUW format")
    parser.add_argument("cabocha_file")
    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("-w", "--writer", default="-", type=str)
    args = parser.parse_args()
    options = YamlDict(
        init={"logger": Logger(debug=args.debug)}
    )
    bobj = BunsetsuDependencies(file_name=args.cabocha_file, options=options)
    COMPONENT(bobj, opts=options)()
    bobj.write_cabocha_file(args.writer)


if __name__ == '__main__':
    _main()
