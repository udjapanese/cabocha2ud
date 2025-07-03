"""Pipeline Component base function."""

from typing import ClassVar, cast

from cabocha2ud.bd import BunsetsuDependencies
from cabocha2ud.lib.logger import Logger
from cabocha2ud.lib.yaml_dict import YamlDict
from cabocha2ud.ud import UniversalDependencies


class PipeLineComponent:
    """Pipeline Component class."""

    name: str
    mode: str
    need_opt: ClassVar[list[str]] = []

    def __init__(
        self, target: BunsetsuDependencies|UniversalDependencies, opts: YamlDict
    ) -> None:
        """Init method."""
        self.target = target
        self.opts: YamlDict = opts
        self.logger: Logger
        if opts.get("logger", None) is not None:
            self.logger = cast(Logger, opts.get("logger"))
        self.prepare()

    def __call__(self) -> None:
        """Call function."""
        raise NotImplementedError

    def prepare(self) -> None:
        """Prepare function."""
        raise NotImplementedError


class BDPipeLine(PipeLineComponent):
    """Bunsetu Dependencies Input Component."""

    mode = "bd"

    def __init__(
        self, target: BunsetsuDependencies, opts: YamlDict
    ) -> None:
        """Init method."""
        super().__init__(target, opts)

    def __call__(self) -> None:
        """Call function."""
        assert isinstance(self.target, BunsetsuDependencies)

    def prepare(self) -> None:
        """Prepare function."""
        raise NotImplementedError


class UDPipeLine(PipeLineComponent):
    """Universal Dependencies Input Component."""

    mode = "ud"

    def __init__(self, target: UniversalDependencies, opts: YamlDict) -> None:
        """Init method."""
        super().__init__(target, opts)

    def __call__(self) -> None:
        """Call function."""
        assert isinstance(self.target, UniversalDependencies)

    def prepare(self) -> None:
        """Prepare function."""
        raise NotImplementedError
