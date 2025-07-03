"""Merge to sp information to GSD cabocha."""

import argparse
from difflib import SequenceMatcher
from pathlib import Path
from typing import ClassVar, Optional

from cabocha2ud.bd import BunsetsuDependencies
from cabocha2ud.bd.sentence import Sentence
from cabocha2ud.lib.logger import Logger
from cabocha2ud.lib.yaml_dict import YamlDict
from cabocha2ud.pipeline.component import BDPipeLine


def load_db_file(db_file: Optional[str]) -> list[list[dict[str, str]]]:
    """Load SP data."""
    if db_file is None:
        return []
    full_data: list[dict[str, str]] = []
    target_column: str = "boundary(S)"
    nfull: list[list[dict[str, str]]] = []
    stack: list[dict[str, str]] = []
    with Path(db_file).open("r", encoding="utf-8") as db_data:
        header = next(db_data).rstrip("\r\n").split("\t")
        for line in db_data:
            item: dict[str, str] = dict(list(zip(header, line.rstrip("\r\n").split("\t"))))
            if item["orthToken(S)"] == '","':
                item["orthToken(S)"] = ","
            full_data.append(item)
        for item in full_data[1:]:
            if item[target_column] == "B":
                nfull.append(stack)
                stack = []
            stack.append(item)
        assert stack[0][target_column] == "B"
        if len(stack) > 0:
            nfull.append(stack)
    return nfull


def similarity(alst: str, blst: str) -> float:
    """Caluclate similarity."""
    if len(alst) < len(blst):
        alst, blst = blst, alst
    return SequenceMatcher(None, alst, blst).ratio()


def matching_from_spd(snt: Sentence, spd: list[dict[str, str]]) -> list[tuple[int, tuple[int,...]]]:
    """Diff using by SequenceMatcher.

    return [(conll_wrd_pos, spd_wrd_pos_tuple), ....]

    """
    assert len(snt.words()) <= len(spd)
    cwrds = [w.get_surface() for w in snt.words()]
    swrds = [c["orthToken(S)"] for c in spd]
    if len(cwrds) == len(swrds):
        return [(p, (p, )) for p in range(len(cwrds))]
    snt.logger.debug("cwrds: %s swrds: %s", cwrds, swrds)
    smcr = SequenceMatcher(None, cwrds, swrds)
    pos_lst: list[tuple[int, tuple[int, ...]]] = []
    for opt, ii1, ii2, jj1, jj2 in smcr.get_opcodes():
        snt.logger.debug(opt, cwrds[ii1:ii2], swrds[jj1:jj2])
        if opt == "equal":
            assert cwrds[ii1:ii2] == swrds[jj1:jj2]
            for iii, jjj in zip(range(ii1, ii2), range(jj1, jj2)):
                pos_lst.append((iii, (jjj, )))
        elif opt == "replace":
            assert ii2 - ii1 <= jj2 - jj1
            assert ii2 - ii1 == 1
            pos_lst.append((ii1, tuple(range(jj1, jj2))))
        else:
            assert KeyError("not found: ", opt)
    return pos_lst


def adapt_spafter_to_cabocha(sentence: Sentence, spd: list[dict[str, str]]) -> None:
    """Adapt spafter to Cabocha Data."""
    if all(s["SpaceAfter"] != "YES" for s in spd):
        return
    assert len(sentence.words()) <= len(spd)
    result_pos = matching_from_spd(sentence, spd)
    for bpos, sp_pos in result_pos:
        assert isinstance(sp_pos, tuple)
        if len(sp_pos) == 1:  # 1対1
            if spd[sp_pos[0]]["SpaceAfter"] == "YES":
                wrd = sentence.words()[bpos]
                pos = sentence.get_pos_from_word(wrd)
                assert sentence.annotation_list is not None
                seg_s = [
                    f'#! SEGMENT_S space-after:seg {pos[0]} {pos[1]} "{wrd.get_surface()}"',
                    '#! ATTR space-after:value "YES"'
                ]
                sentence.annotation_list.append_segment([s.split(" ") for s in seg_s])
        elif len(sp_pos) > 1:
            assert all(spd[spos]["SpaceAfter"] != "YES" for spos in sp_pos)


def get_merged_poslist(
    _bd: BunsetsuDependencies, sp_data: list[list[dict[str, str]]]
) -> list[tuple[int, int]]:
    """SPデータと統合する.

    cabochaデータとSPデータをマッチングする

    Args:
        _bd (BunsetsuDependencies): Bunsetsu Dependencies
        sp_data (list[list[dict[str, str]]]): [description]

    Returns:
        list[tuple[int, int]]: [description]

    """
    if len(_bd.sentences()) == len(sp_data):
        return [(p, p) for p in range(len(_bd.sentences()))]
    sp_it = iter(enumerate(sp_data))
    pos_list: list[tuple[int, int]] = []
    sim_threshold = 0.8
    for bpos, sentence in enumerate(_bd.sentences()):
        spos, cand_sp = next(sp_it)
        stext = "".join([c["orthToken(S)"] for c in cand_sp])
        ctext = sentence.get_text()
        while similarity(stext, ctext) < sim_threshold:
            spos, cand_sp = next(sp_it)
            stext = "".join([c["orthToken(S)"] for c in cand_sp])
        pos_list.append((bpos, spos))
    assert len(pos_list) == len(_bd.sentences())
    return pos_list


class MergeSPtoCabochaComponent(BDPipeLine):
    """Build Sp Cabocha.

    Args:
        PipeLineComponent (_type_): Component

    """

    name = "merge_sp_to_cabocha"
    need_opt: ClassVar[list[str]] = ["sp_file"]

    def __init__(self, target: BunsetsuDependencies, opts: YamlDict) -> None:
        """Init."""
        self.sp_data: list[list[dict[str, str]]]
        super().__init__(target, opts)

    def prepare(self) -> None:
        """Prepare func."""
        assert "sp_file" in self.opts, "please set sp_file"
        self.sp_data = load_db_file(self.opts["sp_file"])

    def __call__(self) -> None:
        """Call Main function."""
        assert isinstance(self.target, BunsetsuDependencies)
        self.logger.debug("do %s", self.name)
        for doc in self.target.documents():
            doc.detect_ud_dependencies()
        pos_list = get_merged_poslist(self.target, self.sp_data)
        for bpos, spos in pos_list:
            adapt_spafter_to_cabocha(self.target.get_sentence(bpos), self.sp_data[spos])


COMPONENT = MergeSPtoCabochaComponent

def main() -> None:
    """Call Main function."""
    parser = argparse.ArgumentParser()
    parser.add_argument("cabocha_file")
    parser.add_argument("sp_file")
    parser.add_argument("-w", "--writer", default="-", type=str)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    options = YamlDict(init={"logger": Logger(debug=args.debug), "sp_file": args.sp_file})
    bobj = BunsetsuDependencies(file_name=args.cabocha_file, options=options)
    COMPONENT(bobj, opts=options)()
    bobj.write_cabocha_file(args.writer)


if __name__ == "__main__":
    main()
