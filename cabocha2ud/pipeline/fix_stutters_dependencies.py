
"""Fix dependencies for stutters."""

import argparse

from cabocha2ud.lib.logger import Logger
from cabocha2ud.lib.yaml_dict import YamlDict
from cabocha2ud.pipeline.component import UDPipeLine
from cabocha2ud.ud import UniversalDependencies
from cabocha2ud.ud.util import Field


class FixStuttersComponent(UDPipeLine):
    """Fix Stutters Dependencies."""

    name = "fix_stutters"

    def prepare(self: "FixStuttersComponent") -> None:
        """Prepare func."""

    def __call__(self: "FixStuttersComponent") -> None:
        """Call func."""
        assert isinstance(self.target, UniversalDependencies)
        self.logger.debug("do " + self.name)
        for sent in self.target.sentences():
            hlst: list[int] = [-1] + [
                int(wrd.get(Field.HEAD).get_content()) for wrd in sent.words()]
            mlst: list[str] = ["dummy"] +  [
                wrd.get(Field.DEPREL).get_content() for wrd in sent.words()
            ]
            res = [
                (p, int(c), mlst[p], mlst[int(c)]) for p, c in enumerate(hlst)
                if p > 0 and mlst[p] != "fixed" and mlst[p] != "punct" and\
                    mlst[int(c)] in ["case", "mark", "aux", "cc"]
            ]
            if len(res) == 0:
                continue
            self.logger.debug(res)
            for cpos, ppos, clabel, plabel in res:
                self.logger.debug(cpos, ppos, clabel, plabel)
                cwrd = sent[cpos-1]
                pwrd = sent[ppos-1]
                if plabel in ["case", "aux"]:
                    cwrd.set(Field.HEAD, pwrd.get(Field.HEAD).get_content())
                    pwrd.set(Field.HEAD, str(cwrd.get(Field.ID)))
                elif plabel in ["mark", "cc"]:
                    cwrd.set(Field.HEAD, pwrd.get(Field.HEAD).get_content())


COMPONENT = FixStuttersComponent


def _main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("conll_file")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("-w", "--writer", default="-", type=str)
    args = parser.parse_args()
    options = YamlDict(
        init={"logger": Logger(debug=args.debug)}
    )
    _ud = UniversalDependencies(file_name=args.conll_file, options=options)
    COMPONENT(_ud,  opts=options)()
    _ud.write_ud_file(args.writer)


if __name__ == "__main__":
    _main()
