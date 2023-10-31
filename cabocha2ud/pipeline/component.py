# -*- coding: utf-8 -*-

"""
Pipeline Component base function
"""

from typing import Union, cast

from cabocha2ud.bd import BunsetsuDependencies as BD
from cabocha2ud.lib.logger import Logger
from cabocha2ud.lib.yaml_dict import YamlDict
from cabocha2ud.ud import UniversalDependencies as UD


class PipeLineComponent:
    """
        Pipeline Component class
    """
    name: str
    mode: str
    need_opt: list[str] = []

    def __init__(
        self, target: Union[BD, UD], opts: YamlDict
    ) -> None:
        self.target = target
        self.opts: YamlDict = opts
        self.logger: Logger
        if opts.get("logger", None) is not None:
            self.logger = cast(Logger, opts.get("logger"))
        self.prepare()

    def __call__(self) -> None:
        raise NotImplementedError

    def prepare(self) -> None:
        """ prepare function """
        raise NotImplementedError


class BDPipeLine(PipeLineComponent):
    """ Bunsetu Dependencies Input Component

    """
    mode = "bd"

    def __init__(
        self, target: BD, opts: YamlDict
    ) -> None:
        super().__init__(target, opts)

    def __call__(self) -> None:
        assert isinstance(self.target, BD)

    def prepare(self) -> None:
        """ prepare function """
        raise NotImplementedError


class UDPipeLine(PipeLineComponent):
    """ Universal Dependencies Input Component

    """
    mode = "ud"

    def __init__(self, target: UD, opts: YamlDict) -> None:
        super().__init__(target, opts)

    def __call__(self) -> None:
        assert isinstance(self.target, UD)

    def prepare(self) -> None:
        """ prepare function """
        raise NotImplementedError
