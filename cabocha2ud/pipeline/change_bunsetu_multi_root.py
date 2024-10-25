"""Change Bunsetu multi root.

Pipeline
"""

import argparse

from cabocha2ud.bd import BunsetsuDependencies
from cabocha2ud.bd.bunsetu import Bunsetu
from cabocha2ud.lib.logger import Logger
from cabocha2ud.lib.yaml_dict import YamlDict
from cabocha2ud.pipeline.component import BDPipeLine

USAGE = """
Usage:
    pipenv run python cabocha2ud/pipeline/change_bunsetu_multi_root.py\
        dev.cabocha -w dev.merged.cabocha
"""

MIN_NUM: int = -10000

class ChangeBunsetuMultiRootComponent(BDPipeLine):
    """Change Bunsetu of multi root and Fix the bunsetu (複数の係り先がある文節の修正をする).

    Args:
        BDPipeLine PipeLineComponent: base object.

    """

    name = "change_bunsetu_root"


    def __init__(self, target: BunsetsuDependencies, opts: YamlDict) -> None:
        """Init Method."""
        super().__init__(target, opts)

    def check_target(self, bun: Bunsetu, last_pos: int,  bunsetues: list[Bunsetu]) -> bool:
        """Check target Bunsetu.

        Args:
            bun (Bunsetu): 文節
            last_pos (int): 現状の候補
            bunsetues (list[Bunsetu]): 文節のリスト

        Returns:
            bool: result.

        """
        return (
            (bun.dep_pos == -1 and bun.dep_type == "D") or
            (bun.bunsetu_pos == len(bunsetues) - 1 and last_pos == MIN_NUM)
        )

    def __call__(self) -> None:
        """Call Method."""
        assert isinstance(self.target, BunsetsuDependencies)
        self.logger.debug("do %s", self.name)

        for doc in self.target.documents():
            doc.detect_ud_dependencies()
            for sent in doc.sentences():
                bunsetues = sent.bunsetues()
                if not len([b for b in bunsetues if b.dep_pos == -1]) > 1:
                    continue
                last_pos: int = MIN_NUM
                for bun in bunsetues:
                    if self.check_target(bun, last_pos, bunsetues):
                        assert bun.bunsetu_pos is not None
                        last_pos = bun.bunsetu_pos
                assert last_pos != MIN_NUM
                for bun in bunsetues:
                    if bun.bunsetu_pos != last_pos and bun.dep_pos == -1:
                        bun.dep_pos = last_pos
                sent.validate_bunsetu_dependencies()

    def prepare(self) -> None:
        """Prepare method."""


COMPONENT = ChangeBunsetuMultiRootComponent


def _main() -> None:
    parser = argparse.ArgumentParser(description=USAGE)
    parser.add_argument("cabocha_file")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("-w", "--writer", default="-", type=str)
    args = parser.parse_args()
    options = YamlDict(init={"logger": Logger(debug=args.debug)})
    bobj = BunsetsuDependencies(file_name=args.cabocha_file, options=options)
    COMPONENT(bobj, opts=options)()
    bobj.write_cabocha_file(args.writer)


if __name__ == "__main__":
    _main()
