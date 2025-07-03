"""マルチルートを係り先を変更してシングルにするプログラム."""

import argparse
from typing import ClassVar, cast

from cabocha2ud.lib.dependency import get_caused_nonprojectivities
from cabocha2ud.lib.logger import Logger
from cabocha2ud.lib.yaml_dict import YamlDict
from cabocha2ud.pipeline.component import UDPipeLine
from cabocha2ud.ud import UniversalDependencies
from cabocha2ud.ud.sentence import Sentence
from cabocha2ud.ud.util import DEPREL, HEAD, ID, UPOS, XPOS, Field


def fix_projectivity_rule_to_punct(data: list[list[str]]) -> list[list[str]]:
    """punctの非交差を直す."""
    nonproj_list: dict[int, list[int]] = {}
    for line in data:
        # 再び非交差を確認する
        if line[DEPREL] == "punct":
            num = int(line[ID])
            tree = [-1] + [int(line[HEAD]) for line in data]
            nonprojnodes = get_caused_nonprojectivities(num, tree)
            if len(nonprojnodes) > 0:
                nonproj_list[num] = nonprojnodes
    if len(nonproj_list) > 0:
        for fix_target in nonproj_list:
            kakko_pos = data[fix_target-1][XPOS]
            if kakko_pos == "補助記号-括弧開":
                # 外にあるのが問題なので括弧開直後の単語にかける
                data[fix_target-1][HEAD] = str(int(data[fix_target-1][ID]) + 1)
            else:
                # 下括弧と上の方の掛かり先を、下括弧がかけていた最下の単語へと入れ替える
                #  対象文: A240n_OY14_03106-10, OC09_04679-5
                save_head = int(data[fix_target-1][HEAD])
                conf_pos_l = nonproj_list[fix_target]
                assert len(conf_pos_l) == 1
                conf_pos = conf_pos_l[0]
                new_fix_pos = fix_target - 1
                while conf_pos < new_fix_pos and int(data[new_fix_pos-1][HEAD]) != save_head:
                    new_fix_pos = new_fix_pos - 1
                if conf_pos < new_fix_pos:
                    data[conf_pos-1][HEAD] = str(new_fix_pos)
                    data[fix_target-1][HEAD] = str(new_fix_pos)
    return data


def fix_leafpunct_rule_to_punct(data: list[list[str]]) -> list[list[str]]:
    """Fix left punct."""
    errors = []
    for line in data:
        num, parent_num = int(line[ID]), int(line[HEAD])
        if line[DEPREL] != "punct" and data[parent_num-1][XPOS] == "補助記号-括弧開":
            errors.append([num, parent_num])
    if len(errors) == 0:
        return data
    if len({parent_num for _, parent_num in errors}) != 1:
        # おなじ親がふさわしい
        return data
    parent_num = next(parent_num for _, parent_num in errors)
    cand_parent = int(parent_num) + 1
    if cand_parent > len(data) or data[cand_parent-1][DEPREL] == "punct":
        return data
    assert int(data[cand_parent-1][HEAD]) == parent_num
    data[cand_parent-1][HEAD] = data[parent_num-1][HEAD]
    data[parent_num-1][HEAD] = str(cand_parent)
    if data[cand_parent-1][HEAD] == "0":
        data[cand_parent-1][DEPREL] = "root"
        data[parent_num-1][DEPREL] = "punct"
    for enum, _ in errors:
        if enum == cand_parent:
            continue
        data[int(enum)-1][HEAD] = str(cand_parent)
    for line in data:
        num, aparent_num = int(line[ID]), int(line[HEAD])
        if line[DEPREL] == "punct" and aparent_num == parent_num:
            line[HEAD] = str(cand_parent)
    return data


def __restore_rel(line: list[str]) -> None:
    if line[UPOS] == "PUNCT":
        line[DEPREL] = "punct"
    if line[UPOS] == "CCONJ":
        line[DEPREL] = "cc"
    # FOR CEJC
    if line[XPOS] == "言いよどみ":
        line[DEPREL] = "reparandum"
    if line[XPOS] == "感動詞-フィラー":
        line[DEPREL] = "discourse"


def detect_true_root(data: list[list[str]], numlst: list[int]) -> tuple[list[int], int]:
    """ひとまずひとつの root を決める関数."""
    target_pos = 1
    true_root = numlst[len(numlst)-1]
    num_line = {int(line[0]): line for line in data}
    true_root_pos = num_line[true_root][UPOS]
    while len(numlst)-target_pos >= 0 and true_root_pos == "PUNCT":
        target_pos += 1
        true_root = numlst[len(numlst)-target_pos]
        true_root_pos = num_line[true_root][UPOS]
    if len(numlst)-target_pos == -1:
        # どれもpunctの場合は最後のを選び直す
        true_root = numlst[-1]
    frmpos = [n for n in numlst if n != true_root]
    return frmpos, true_root


def convert_to_single_root(data: list[list[str]]) -> list[list[str]]:
    """複数あるルートの中で基本のルートを決める."""
    nsent_st: list[list[str]] = []
    tree: dict[int, set[int]] = {}
    for pos, dnum in [(int(line[ID]), int(line[HEAD])) for line in data]:
        if dnum not in tree:
            tree[dnum] = set()
        tree[dnum].add(pos)
    numlst = sorted(tree[0])
    frmpos, true_root = detect_true_root(data, numlst)
    for line in data:
        num, dnum = int(line[ID]), int(line[HEAD])
        if num not in frmpos:
            nsent_st.append(line)
            continue
        assert dnum == 0
        dnum = true_root
        line[DEPREL] = "dep"
        __restore_rel(line)
        nsent_st.append([str(num)] + line[1:6] + [str(dnum)] + line[7:])
    return nsent_st


class ReplaceMultiRootComponent(UDPipeLine):
    """Replace multi root component.

    Args:
        PipeLineComponent (_type_): _description_

    """

    name = "replace_multi_root"
    need_opt: ClassVar[list[str]] = ["rep_multi_root_mode"]

    def __init__(self, target: UniversalDependencies, opts: YamlDict) -> None:
        """Init."""
        self.rep_multi_root_mode: str = ""
        self.space_marker: str = " "
        super().__init__(target, opts)

    def prepare(self) -> None:
        """Prepare func."""
        if self.opts.get("rep_multi_root_mode") is not None:
            self.rep_multi_root_mode = cast(str, self.opts.get("rep_multi_root_mode"))
        if self.opts.get("space_marker") is not None:
            self.space_marker = cast(str, self.opts.get("space_marker"))
        assert self.rep_multi_root_mode in ["convert", "remove"]

    def __call__(self) -> None:
        """Call Main function."""
        assert isinstance(self.target, UniversalDependencies)
        self.logger.debug(self.name)
        if self.rep_multi_root_mode == "convert":
            for pos, ud_sent in enumerate(self.target.sentences()):
                heads_size = sum(c.get_content() == "0" for c in ud_sent.get_colmuns(Field.HEAD))
                assert heads_size > 0, "`root` must be rather one in sentence, but Zero root"
                if heads_size == 1:
                    continue
                header = ud_sent.get_str_list(mode="header")
                data = [
                    line.rstrip("\n").split("\t")
                    for line in ud_sent.get_str_list(mode="full")[len(header):]
                ]
                data = convert_to_single_root(data)
                # ここに非交差修正ルール
                data = fix_projectivity_rule_to_punct(data)
                # ここにpunct修正ルール
                data = fix_leafpunct_rule_to_punct(data)
                sent = header + ["\t".join(ll) for ll in data]
                nsent = Sentence.load_from_list(sent, spt=self.space_marker)
                self.target.update_sentence_of_index(pos, nsent)
        elif self.rep_multi_root_mode == "remove":
            rm_sent_lst: list[int] = []
            for pos, ud_sent in enumerate(self.target.sentences()):
                heads_size = sum(c.get_content() == "0" for c in ud_sent.get_colmuns(Field.HEAD))
                assert heads_size > 0, "`root` must be rather one in sentence, but Zero root"
                if heads_size == 1:
                    continue
                rm_sent_lst.append(pos)
            self.target.remove_sentence_from_index(rm_sent_lst)
        else:
            msg = "mode must be `remove` or `convert`"
            raise ValueError(msg)


COMPONENT = ReplaceMultiRootComponent

def _main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("conll_file")
    parser.add_argument(
        "mode", choices=["convert", "remove"], help="""
            convert: シングルルートに変換する
            remove: マルチルートを削除する
        """
    )
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("-w", "--writer", default="-", type=str)
    args = parser.parse_args()
    options = YamlDict(
        init={"logger": Logger(debug=args.debug), "rep_multi_root_mode": args.mode}
    )
    _ud = UniversalDependencies(file_name=args.conll_file, options=options)
    if options.get("space_marker") is None:
        options["space_marker"] = _ud.get_sp()
    COMPONENT(_ud,  opts=options)()
    _ud.write_ud_file(args.writer)


if __name__ == "__main__":
    _main()
