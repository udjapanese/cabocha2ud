# -*- coding: utf-8 -*-

"""
Utility Yaml object
"""


from io import StringIO
from pathlib import Path
from typing import Any, Callable, Optional, Union, cast

import ruamel.yaml

from cabocha2ud.lib.text_object import TextObject


class YamlObj:
    """ YamlObj class

    Utility Yaml object class, which can convert YAML format

    Attributes:
        init (dict, optional): initialized object
        file_name (str, optional): `file_name` default "-" is `sys.std*`
        auto_load (bool, default: False): do automatic load data
    """

    def __init__(
        self, file_name: Union[str, Path, None]="-",
        auto_load: bool=False
    ) -> None:
        self.file_obj: Optional[TextObject] = None
        self._str: str = ""
        self._cont: object = object()
        self._conv_func: Callable = lambda x: x
        if file_name is not None:
            self.file_obj = TextObject(file_name)
        if auto_load and file_name is not None:
            self.load()

    def get_content(self):
        """ get yaml original content """
        return self._cont

    def load(self, file_name: Optional[str]=None) -> None:
        """ load from file object """
        if file_name is not None:
            self.file_obj = TextObject(file_name)
        if self.file_obj is None:
            raise ValueError("please set file_name or use .loads")
        with self.file_obj.open_data() as reader:
            self.loads(reader.read())

    def loads(self, content: str) -> None:
        """ load from string """
        yaml = ruamel.yaml.YAML()
        self._str = content.replace('\t', '    ')
        self._cont = self._conv_func(yaml.load(StringIO(self._str)))

    def dump(self, file_name: Union[str, Path]) -> None:
        """ dump to file """
        if isinstance(file_name, str):
            with open(file_name, "w", encoding="utf-8") as wrt:
                dumped_data = self.dumps()
                wrt.write(dumped_data + "\n")
        elif isinstance(file_name, Path):
            with file_name.open("w", encoding="utf-8") as wrt:
                dumped_data = self.dumps()
                wrt.write(dumped_data + "\n")
        else:
            assert ValueError("please set `file_name`")

    def dumps(self) -> str:
        """ dump to string """
        yaml = ruamel.yaml.YAML()
        str_io = StringIO()
        yaml.dump(self._conv_func(self), str_io)
        self._cont = str_io.getvalue()
        return self._cont


class YamlDict(YamlObj, dict[Any, Any]):
    """ YamlDict class

    Utility Dict object class, which can convert YAML format

    Attributes:
        init (dict, optional): initialized object
        file_name (str, optional): `file_name` default "-" is `sys.std*`
        auto_load (bool, default: False): do automatic load data
    """

    def __init__(
        self, init: Optional[dict]=None, file_name: Union[str, Path, None]="-",
        auto_load: bool=False
    ) -> None:
        super().__init__(file_name=file_name, auto_load=auto_load)
        self._conv_func = dict
        if init is not None:
            self.update(init)
            self._cont = self.copy()

    def load(self, file_name: Optional[str]=None) -> None:
        super().load(file_name)
        if len(self.keys()) != 0:
            self.clear()
        self.update(dict(cast(dict, self._cont)))

    def loads(self, content: str) -> None:
        """ load from string """
        super().loads(content)
        if len(self.keys()) != 0:
            self.clear()
        self.update(dict(cast(dict, self._cont)))


class YamlList(YamlObj, list[Any]):
    """ YamlList class

    Utility List object class, which can convert YAML format

    Attributes:
        init (dict, optional): initialized object
        file_name (str, optional): `file_name` default "-" is `sys.std*`
        auto_load (bool, default: False): do automatic load data
    """

    def __init__(
        self, init: Optional[list]=None, file_name: Union[str, Path, None]="-",
        auto_load: bool=False
    ) -> None:
        super().__init__(file_name=file_name, auto_load=auto_load)
        self._conv_func = list
        if init is not None:
            self.extend(init)
            self._cont = self.copy()

    def load(self, file_name: Optional[str]=None) -> None:
        super().load(file_name)
        self.clear()
        self.extend(cast(list, self._cont))

    def loads(self, content: str) -> None:
        """ load from string """
        super().loads(content)
        self.clear()
        self.extend(cast(list, self._cont))
