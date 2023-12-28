# -*- encoding: utf-8 -*-

"""

Change Bunsetu multi root

"""

import argparse

from cabocha2ud.bd import BunsetsuDependencies
from cabocha2ud.lib.logger import Logger
from cabocha2ud.lib.yaml_dict import YamlDict
from cabocha2ud.pipeline.component import BDPipeLine

USAGE = '''

Usage:
    pipenv run python cabocha2ud/pipeline/change_bunsetu_multi_root.py dev.cabocha -w dev.merged.cabocha
'''


class ChangeBunsetuMultiRootComponent(BDPipeLine):
    """ Change Bunsetu multi root
    Args:
        PipeLineComponent (_type_): _description_
    """
    name = "change_bunsetu_root"


    def __init__(self, target: BunsetsuDependencies, opts: YamlDict) -> None:
        super().__init__(target, opts)

    def __call__(self) -> None:
        assert isinstance(self.target, BunsetsuDependencies)
        self.logger.debug(f"do {self.name}")

        for doc in self.target.documents():
            doc.detect_ud_dependencies()
            for sent in doc.sentences():
                bunsetues = sent.bunsetues()
                if not len([b for b in bunsetues if b.dep_pos == -1]) > 1:
                    continue
                last_pos: int = -100
                for bun in bunsetues:
                    if bun.dep_pos == -1 and bun.dep_type == "D":
                        assert bun.bunsetu_pos is not None
                        last_pos = bun.bunsetu_pos
                    elif bun.bunsetu_pos == len(bunsetues) - 1 and last_pos == -100:
                        assert bun.bunsetu_pos is not None
                        last_pos = bun.bunsetu_pos
                assert last_pos != -100
                for bun in bunsetues:
                    if bun.bunsetu_pos != last_pos and bun.dep_pos == -1:
                        bun.dep_pos = last_pos
                sent.validate_bunsetu_dependencies()

    def prepare(self) -> None:
        pass

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


if __name__ == '__main__':
    _main()
