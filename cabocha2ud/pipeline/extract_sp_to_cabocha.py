"""Merge to sp information to GSD cabocha."""

import argparse
from typing import TYPE_CHECKING

from cabocha2ud.bd import BunsetsuDependencies
from cabocha2ud.lib.logger import Logger
from cabocha2ud.lib.yaml_dict import YamlDict
from cabocha2ud.pipeline.component import BDPipeLine

if TYPE_CHECKING:
    from cabocha2ud.bd.sentence import Sentence
    from cabocha2ud.bd.word import Word


class ExtractSPtoCabochaComponent(BDPipeLine):
    """Extract Sp information to adapt Cabocha.

    Args:
        PipeLineComponent: BaseComponent

    """

    name = "extract_sp_to_cabocha"

    def __init__(self, target: BunsetsuDependencies, opts: YamlDict) -> None:
        """Init."""
        super().__init__(target, opts)

    def prepare(self) -> None:
        """Prepare func."""

    def remove_blank_word(self, sent: "Sentence") -> tuple[bool, bool, list[tuple[int, int]]]:
        """[summary].

        Args:
            sent (Sentence): check Sentence.

        Returns:
            bool1: 先頭が空白だった
            bool2: 自分自身が削除されるかどうか

        """
        wlist: list[tuple[int, int]] = []
        sp_lst: list[tuple[int, int, str]] = []
        remove_blank_wrd_size: int = 0
        rm_bun_pos: list[int] = []
        prefix_space = False
        wind = 0
        for bpos, bun in enumerate(sent.bunsetues()):
            nwrd: list[Word] = []
            for _, wrd in enumerate(bun.words()):
                if wrd.get_xpos().startswith("空白"):
                    remove_blank_wrd_size += 1
                    if len(wlist) == 0:
                        # 前の単語がないというときは、文頭の空白なので飛ばす
                        prefix_space = True
                        continue
                    if len(nwrd) == 0:
                        # 文節の先頭のとき
                        pbun = sent.bunsetues()[bpos-1]
                        sp_lst.append(
                            (wlist[-1][0], wlist[-1][1], pbun.words()[-1].get_surface())
                        )
                    else:
                        sp_lst.append((wlist[-1][0], wlist[-1][1], nwrd[-1].get_surface()))
                    continue
                if wrd.dep_num is not None and wrd.dep_num > 0:
                    wrd.dep_num = wrd.dep_num - remove_blank_wrd_size
                nwrd.append(wrd)
                wlist.append((wind, wind + len(wrd.get_surface())))
                wind += len(wrd.get_surface())
            if len(nwrd) > 0:
                bun.update_word_list(nwrd)
            else:
                rm_bun_pos.append(bpos)
        if len(rm_bun_pos) > 0:
            sent.remove_bunsetu_pos(rm_bun_pos)
        self.insert_sp_info(sent, sp_lst)
        return prefix_space, len(sent.words()) == 0, wlist

    def insert_sp_info(self, sent: "Sentence", sp_lst: list[tuple[int, int, str]]) -> None:
        """Insert Sp Info."""
        assert sent.annotation_list is not None
        for s, e, w in sp_lst:
            sent.annotation_list.append_segment([
                s.split(" ") for s in [
                    f'#! SEGMENT_S space-after:seg {s} {e} "{w}"',
                    '#! ATTR space-after:value "YES"'
                ]
            ])

    def __call__(self) -> None:
        """Call Main function."""
        assert isinstance(self.target, BunsetsuDependencies)
        self.logger.debug("do %s", self.name)
        for doc in self.target:
            rm_sent_pos: list[int] = []
            wlst_stack: list[tuple[int, list[tuple[int, int]]]] = []
            doc.detect_ud_dependencies()
            for sent in doc.sentences():
                if not any(w.get_xpos().startswith("空白") for w in sent.words()):
                    # 空白のないものは処理をしないが文字位置情報だけ保存
                    wlst_stack.append((sent.sent_pos, sent.abs_pos_list))
                    continue
                prefix_space, is_removed, wlst = self.remove_blank_word(sent)
                if is_removed:
                    rm_sent_pos.append(sent.sent_pos)
                if prefix_space and sent.sent_pos > 0:
                    if len(wlst_stack) == 0:
                        # 空白を除く見える単語がない状態なら処理をしない。
                        continue
                    tspos, pwlst = wlst_stack[-1]
                    pwrd = list(doc[tspos].words())[-1]
                    assert len(pwrd.get_surface()) == pwlst[-1][1] - pwlst[-1][0]
                    self.insert_sp_info(
                        doc[tspos], [(pwlst[-1][0], pwlst[-1][1], pwrd.get_surface())]
                    )
                if len(wlst) > 0:
                    wlst_stack.append((sent.sent_pos, wlst))
            doc.remove_sentence_pos(rm_sent_pos)
            doc.detect_ud_dependencies()


COMPONENT = ExtractSPtoCabochaComponent

def main() -> None:
    """Call Main function."""
    parser = argparse.ArgumentParser()
    parser.add_argument("cabocha_file")
    parser.add_argument("-w", "--writer", default="-", type=str)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    options = YamlDict(init={"logger": Logger(debug=args.debug)})
    bobj = BunsetsuDependencies(file_name=args.cabocha_file, options=options)
    COMPONENT(bobj, opts=options)()
    bobj.write_cabocha_file(args.writer)


if __name__ == "__main__":
    main()
