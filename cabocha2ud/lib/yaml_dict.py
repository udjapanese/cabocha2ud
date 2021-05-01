# -*- coding: utf-8 -*-

"""
utility File object
"""


from pathlib import Path
from typing import Union, Optional, Dict, Any
from io import StringIO

import ruamel.yaml


class YamlDict(Dict[Any, Any]):
    """ YamlDict class

    Utility Dict object class, which can convert YAML format

    Attributes:
        init (dict, optional): initialized object
        file_name (str, optional): `file_name` default "-" is `sys.std*`
        auto_load (bool, default: False): do automatic load data
    """

    def __init__(self, init: Optional[dict]=None, file_name: Union[str, Path, None]="-", auto_load: bool=False) -> None:
        super().__init__()
        self.file_path: Path = Path()
        self.file_name: str = "-"
        self.set_filename(file_name)
        if auto_load and file_name is not None:
            self.load()
        if init is not None:
            self.update(init)

    def set_filename(self, file_name: Union[str, Path, None]):
        if file_name == "-" or file_name is None:
            self.file_path = Path()
            self.file_name = "-"
        elif isinstance(file_name, str):
            self.file_path = Path(file_name)
            self.file_name = str(self.file_path)
        elif isinstance(file_name, Path):
            self.file_path = file_name
            self.file_name = str(self.file_path)

    def load(self, file_name: str=None) -> None:
        target_filename: str = ""
        if file_name is not None:
            target_filename = file_name
        elif self.file_name is not None:
            target_filename = self.file_name
        else:
            raise ValueError("please set file_name or use .loads")
        with open(target_filename) as reader:
            self.loads(reader.read())

    def loads(self, content: str) -> None:
        yaml = ruamel.yaml.YAML()
        dic_cont = yaml.load(content)
        if len(self.keys()) != 0:
            self.clear()
        self.update(dic_cont)

    def dump(self, file_name: Union[str, Path]) -> None:
        if isinstance(file_name, str):
            with open(file_name, "w") as wrt:
                dumped_data = self.dumps()
                wrt.write(dumped_data + "\n")
        elif isinstance(file_name, Path):
            with file_name.open("w") as wrt:
                dumped_data = self.dumps()
                wrt.write(dumped_data + "\n")
        else:
            assert ValueError("please set `file_name`")

    def dumps(self) -> str:
        yaml = ruamel.yaml.YAML()
        str_io = StringIO()
        yaml.dump(dict(self), str_io)
        return str_io.getvalue()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("file_name", type=str)

