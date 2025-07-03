"""Build LUW Bunsetu Dependencies."""


import argparse
import re
from typing import TYPE_CHECKING

from cabocha2ud.bd import BunsetsuDependencies
from cabocha2ud.bd.sentence import Sentence
from cabocha2ud.lib.logger import Logger
from cabocha2ud.lib.yaml_dict import YamlDict
from cabocha2ud.pipeline.component import BDPipeLine

if TYPE_CHECKING:
    from cabocha2ud.bd.annotation import Segment

SP_TOKEN = re.compile(r"[ 　]+")

def reconstract_space_after(sent: Sentence) -> None:
    """Change space after for luw unit.

    Args:
        sent (Sentence): sentence object of `luw_unit`

    """
    assert sent.annotation_list is not None
    seg_lst = [
        (spos, seg) for spos, seg in enumerate(sent.annotation_list.get_segments())
        if seg.get_name() == "space-after:seg" and not sent.include_segment_pos(seg)
        # 単語の範囲が変更になったもののみ対象
    ]
    if len(seg_lst) == 0:
        return
    rm_seg: list[Segment] = []
    for _, seg in seg_lst:
        luw_pos_cand_s = [
            (s, e) for s, e in sent.abs_pos_list
            if s == seg.start_pos or s < seg.start_pos < e
        ]
        luw_pos_cand_e = [(s, e) for s, e in sent.abs_pos_list if e == seg.end_pos]
        assert len(luw_pos_cand_s) > 0 or len(luw_pos_cand_e) > 0
        if len(luw_pos_cand_s) > 0 and len(luw_pos_cand_e) > 0:
            # 文節の手前にあるスペースの場合（？）
            nseg = seg.copy()
            wrd = sent.words()[sent.abs_pos_dict[luw_pos_cand_e[0]]]
            s_pos, e_pos = sent.get_pos_from_word(wrd)
            nseg.set_pos(s_pos, e_pos)
            nseg.comment = wrd.get_surface()
            sent.annotation_list.update_segment(seg, nseg)
        elif len(luw_pos_cand_s) > 0:
            assert len(luw_pos_cand_s) == 1, "SpaceAfterの位置は重複はしないはずです."
            rm_seg.append(seg)
        elif len(luw_pos_cand_e) > 0:
            assert len(luw_pos_cand_e) == 1, "SpaceAfterの位置は重複はしないはずです."
            nseg = seg.copy()
            wrd = sent.words()[sent.abs_pos_dict[luw_pos_cand_e[0]]]
            s_pos, e_pos = sent.get_pos_from_word(wrd)
            nseg.set_pos(s_pos, e_pos)
            nseg.comment = wrd.get_surface()
            sent.annotation_list.update_segment(seg, nseg)
    for seg in rm_seg:
        sent.annotation_list.remove_segment(seg)


def build_luw_unit(sent: Sentence) -> None:
    """Build LUW Unit."""
    assert sent.word_unit_mode == "luw", "differ mode: " + sent.word_unit_mode
    for _, bunsetu in enumerate(sent):
        assert len(bunsetu) > 0
        bunsetu.word_unit_mode = "luw"
        bunsetu.build_luw_unit()
    sent.update_word_pos()
    reconstract_space_after(sent)


class BuildLUWComponent(BDPipeLine):
    """Build LUW for BD.

    Args:
        PipeLineComponent (_type_): _description_

    """

    name = "build_luw"

    def prepare(self) -> None:
        """Prepare method."""

    def __call__(self) -> None:
        """Call base func."""
        assert isinstance(self.target, BunsetsuDependencies)
        self.logger.debug("do %s", self.name)
        self.target.word_unit_mode = "luw"
        for _, doc in enumerate(self.target):
            doc.word_unit_mode = "luw"
            for _, sent in enumerate(doc):
                sent.word_unit_mode = "luw"
                build_luw_unit(sent)
            doc.detect_ud_dependencies()


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


if __name__ == "__main__":
    _main()
