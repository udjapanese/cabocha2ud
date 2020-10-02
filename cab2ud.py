# -*- coding: utf-8 -*-

"""
BCCWJ DepParaPAS to universal dependencies
"""

import sys
import configargparse

import base.document
from lib.iterate_function import iterate_document


def main():
    """
    main function
    """
    parser = configargparse.ArgumentParser(default_config_files=['./configargparse.yaml'])
    parser.add_argument("-c", "--configarg-file", is_config_file=True, help="configargparse file")
    parser.add_argument("base_file")
    parser.add_argument("-d", "--data-type", required=True, choices=["chj", "bccwj", "gsd"])
    parser.add_argument(
        "-u", "--word-unit",  required=True, choices=["suw", "luw"]
    )
    parser.add_argument("-b", "--bunsetu-func", default="none", choices=["none", "type1", "type2"])
    parser.add_argument("-s", "--skip-space", default=False, action="store_true")
    parser.add_argument("-m", "--space-marker", default=" ", help="スペースに何を使うか")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("-w", "--writer", type=configargparse.FileType("w"), default="-")
    args = parser.parse_args()
    if args.debug:
        sys.stderr.write(str(args) + "\n")
    with open(args.base_file) as doc_texts:
        prev_newdoc = None
        for text in iterate_document(doc_texts):
            doc = base.document.Document(
                args.data_type, text=text, base_file_name=args.base_file,
                bunsetu_func=args.bunsetu_func, word_unit=args.word_unit,
                space_marker=args.space_marker
            )
            if doc.doc_attrib_xml is not None and doc.doc_attrib_xml.find('newdoc_id') is not None:
                if prev_newdoc != doc.doc_attrib_xml.find('newdoc_id').text:
                    args.writer.write(doc.doc_attrib_xml.find('newdoc_id').text + "\n")
                prev_newdoc = doc.doc_attrib_xml.find('newdoc_id').text
            args.writer.write(doc.convert(is_skip_space=args.skip_space) + "\n")
    if args.debug:
        sys.stderr.write("Cabocha file {} -> .conll finished\n".format(args.base_file))


if __name__ == '__main__':
    main()
