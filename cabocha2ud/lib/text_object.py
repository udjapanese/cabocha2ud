"""Utility File object."""

import argparse
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Iterator, TextIO, Union


class TextObject:
    """TextObject class.

    Utility File object class

    Attributes:
        file_name (str, optional): `file_name` default "-" is `sys.std*`
        mode (str, optional): `r`: read mode, `w`: write mode

    """

    def __init__(self, file_name: Union[str, Path]="-", mode: str="r") -> None:
        """Init."""
        self.file_path: Path = Path()
        self.file_name: str = "-"
        self.mode: str = mode
        self.encoding = "utf-8"
        if file_name != "-":
            if isinstance(file_name, str):
                self.file_path = Path(file_name)
                self.file_name = str(self.file_path)
            else:
                self.file_path = file_name
                self.file_name = str(self.file_path)
        if self.mode not in ["r", "w"]:
            msg = "Please choice [r: read mode | w: write mode]"
            raise ValueError(msg)
        if self.mode == "r" and not (self.file_name == "-" or self.file_path.exists()):
            raise FileNotFoundError("File not found: " + self.file_name)

    def set_filename(self, file_name: Union[str, Path]) -> None:
        """Set filename."""
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
    def open_data(self) -> Iterator[TextIO]:
        """Open data.

        Yields:
            file stream: sys.stdin or OpenFile

        """
        if self.file_name == "-":
            if self.mode == "r":
                yield sys.stdin
            else:
                yield sys.stdout
        elif self.mode == "r":
            with self.file_path.open("r", encoding=self.encoding) as rdr:
                yield rdr
        elif self.mode == "w":
            with self.file_path.open("w", encoding=self.encoding) as wrd:
                yield wrd
        else:
            msg = "Please choice [r: read mode | w: write mode]"
            raise ValueError(msg)

    def read(self) -> Iterator[str]:
        """Read method.

        Yields:
            file stream: str lists

        Raises:
            ValueError: only read mode

        """
        if self.mode == "w":
            msg = "Value error: mode `w` not used `read` method"
            raise ValueError(msg)
        with self.open_data() as reader:
            for line in reader:
                yield line.rstrip("\n")

    def write(self, content: Iterable[str]) -> None:
        """Write method.

        Yields:
            file stream: str lists

        Raises:
            ValueError: only write mode

        """
        if self.mode == "r":
            msg = "Value error: mode `r` not used `write` method"
            raise ValueError(msg)
        with self.open_data() as writer:
            for line in content:
                writer.write(line + "\n")


    def write_list(self, content: Iterable[list[str]], sep: str="\t") -> None:
        """Write method.

        Yields:
            file stream: str lists

        Raises:
            ValueError: only write mode

        """
        if self.mode == "r":
            msg = "Value error: mode `r` not used `write` method"
            raise ValueError(msg)
        with self.open_data() as writer:
            for lst in content:
                writer.write(sep.join(lst) + "\n")


def _main() -> None:
    """Check the main component function."""
    parser = argparse.ArgumentParser()
    parser.add_argument("file_name", type=str)
    args = parser.parse_args()
    fobj = TextObject(args.file_name)
    for line in fobj.read():
        print(line)


if __name__ == "__main__":
    _main()
