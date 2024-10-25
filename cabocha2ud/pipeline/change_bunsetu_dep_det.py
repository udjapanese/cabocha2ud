"""Change Bunsetu multi root.

Pipeline
"""

import argparse
import re

from cabocha2ud.bd import BunsetsuDependencies
from cabocha2ud.bd.sentence import Sentence
from cabocha2ud.bd.word import Word
from cabocha2ud.lib.logger import Logger
from cabocha2ud.lib.yaml_dict import YamlDict
from cabocha2ud.pipeline.component import BDPipeLine

USAGE = """
Usage:
    pipenv run python cabocha2ud/pipeline/change_bunsetu_dep_det.py\
        dev.cabocha -w dev.merged.cabocha
"""

MIN_NUM: int = -10000
DET_TERM: list[str] = ["^[こそあど此其彼何]の", "^或る", "^とある", "^我が", "^あらゆる"]
DET_REPHRASE: list[re.Pattern] = [re.compile(r) for r in DET_TERM]


class ChangeBunsetuDepDetComponent(BDPipeLine):
    """Change Bunsetu of `det` Bunsetu and Fix the bunsetu (detの文節の係りを修正する).

    Args:
        BDPipeLine PipeLineComponent: base object.

    """

    name = "change_dep_det"


    def __init__(self, target: BunsetsuDependencies, opts: YamlDict) -> None:
        """Init Method."""
        super().__init__(target, opts)

    def check_the_word_det(self, wrd: Word) -> bool:
        """Check the word is UPOS `DET`."""
        return wrd.get_xpos() == "連体詞" and any(r.match(wrd.get_origin()) for r in DET_REPHRASE)

    def prepare_check_target(self, sentence: Sentence) -> tuple:
        """Check target Sentence.

        Args:
            sentence: Sentence: 文

        Returns:
            bool: result.

        """
        target_bunpos = [
            bpos for bpos, bun in enumerate(sentence.bunsetues())
            if any(self.check_the_word_det(w) for w in bun.words())
        ]
        if len(target_bunpos) == 0:
            return [], [], []
        dep_pos = [bun.dep_pos for bun in sentence.bunsetues()]
        return target_bunpos, dep_pos, [
            chp for chp, bpos in enumerate(dep_pos) if bpos in target_bunpos
        ]

    def __call__(self) -> None:
        """Call Method."""
        assert isinstance(self.target, BunsetsuDependencies)
        self.logger.debug("do %s", self.name)

        for doc in self.target.documents():
            doc.detect_ud_dependencies()
            scnt = 0
            for sent in doc.sentences():
                scnt += 1
                bunlst = sent.bunsetues()
                target_bunpos, dep_pos, chbun = self.prepare_check_target(sent)
                if len(target_bunpos) == 0 or len(chbun) == 0:
                    continue
                for target_pos in chbun:
                    parent = dep_pos[target_pos]
                    assert len(bunlst[parent]) >= 1, "Maybe det bunsetu size is 1?"
                    sent[target_pos].dep_pos = bunlst[parent].dep_pos
                sent.validate_bunsetu_dependencies()

    def prepare(self) -> None:
        """Prepare method."""


COMPONENT = ChangeBunsetuDepDetComponent


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
