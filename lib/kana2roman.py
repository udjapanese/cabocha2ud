# -*- coding: utf-8 -*-

"""
Roman kana
"""
import argparse
from pykakasi import kakasi

KAKASI = kakasi()
KAKASI.setMode("H", "a")
KAKASI.setMode("J", "a")
KAKASI.setMode("K", "a")
KAKASI.setMode("J", "a")
KAKASI.setMode("r", "Hepburn")
KAKASI.setMode("E", "a")
KAKASI.setMode("C", True)
KCONV = KAKASI.getConverter()


def kana2roman(target_string):
    """
        kana to roman
    """
    return KCONV.do(target_string)


def main():
    """
        test function
    """
    parser = argparse.ArgumentParser(description='romankana')
    parser.add_argument('text', type=argparse.FileType('r'))
    args = parser.parse_args()
    for line in args.text:
        print(kana2roman(line.rstrip().decode("utf-8")).encode("utf-8"))


if __name__ == '__main__':
    main()
