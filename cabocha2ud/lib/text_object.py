# -*- coding: utf-8 -*-

"""
utility File object
"""

import os
import sys
from pathlib import Path
from typing import Iterator, Iterable, Union, Optional, List
from contextlib import contextmanager



class TextObject:
    """TextObject class

    Utility File object class

    Attributes:
        file_name (str, optional): `file_name` default "-" is `sys.std*`
        mode (str, optional): `r`: read mode, `w`: write mode

    """

    def __init__(self, file_name: Union[str, Path]="-", mode: str="r") -> None:
        self.file_path: Path = Path()
        self.file_name: str = "-"
        self.mode: str = mode
        if file_name != "-":
            if isinstance(file_name, str):
                self.file_path = Path(file_name)
                self.file_name = str(self.file_path)
            else:
                self.file_path = file_name
                self.file_name = str(self.file_path)
        if self.mode not in ["r", "w"]:
            raise ValueError("Please choice [r: read mode | w: write mode]")
        if self.mode == "r" and not (self.file_name == "-" or self.file_path.exists()):
            raise FileNotFoundError("File not found: " + self.file_name)

    def set_filename(self, file_name: Union[str, Path]):
        if file_name == "-":
            self.file_path = Path()
            self.file_name = "-"
        elif isinstance(file_name, str):
            self.file_path = Path(file_name)
            self.file_name = str(self.file_path)
        elif isinstance(file_name, Path):
            self.file_path = file_name
            self.file_name = str(self.file_path)

    @contextmanager
    def open_data(self) -> Iterator:
        """open_data

        Yields:
            file stream: sys.stdin or OpenFile

        """
        if self.file_name == "-":
            if self.mode == "r":
                yield sys.stdin
            else:
                yield sys.stdout
        else:
            if self.mode == "r":
                fobj = self.file_path.open("r")
            else:
                fobj = self.file_path.open("w")
            yield fobj
            fobj.close()

    def read(self) -> Iterator[str]:
        """read method

        Yields:
            file stream: str lists

        Raises:
            ValueError: only read mode

        """
        if self.mode == "w":
            raise ValueError("Value error: mode `w` not used `read` method")
        with self.open_data() as reader:
            for line in reader:
                yield line.rstrip("\n")

    def write(self, content: Iterable[str]) -> None:
        """write method

        Yields:
            file stream: str lists

        Raises:
            ValueError: only write mode

        """
        if self.mode == "r":
            raise ValueError("Value error: mode `r` not used `write` method")
        with self.open_data() as writer:
            for line in content:
                writer.write(line + "\n")


    def write_list(self, content: Iterable[List[str]], sep: str="\t") -> None:
        """write method

        Yields:
            file stream: str lists

        Raises:
            ValueError: only write mode

        """
        if self.mode == "r":
            raise ValueError("Value error: mode `r` not used `write` method")
        with self.open_data() as writer:
            for lst in content:
                writer.write(sep.join(lst) + "\n")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("file_name", type=str)
    args = parser.parse_args()
    fobj = TextObject(args.file_name)
    for line in fobj.read():
        print(line)

