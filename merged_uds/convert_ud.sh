#!/bin/sh -x

set -e

usage () {
  cat <<EOS
Usage: $(basename "$0") [OPTION]...
  -h            Display help
  -b BASE_DIR   base directory including cabocha files (default: ${BASE_DIR})
  -o OUTPUT_DIR   base directory including cabocha files (default: ${OUTPUT_DIR})
EOS

  exit 2
}

GSD_DIR=../cabocha_files/GSD
BCCWJ_DIR=../cabocha_files/BCCWJ
OUTPUT_DIR=./conv_ud


while getopts "b:g:o:h" optKey; do
  case "$optKey" in
    b)
      BCCWJ_DIR=$OPTARG
      ;;
    g)
      GSD_DIR=$OPTARG
      ;;
    o)
      OUTPUT_DIR=$OPTARG
      ;;
    '-h'|'--help'|* )
      usage
      ;;
  esac
done


if [ ! -d $OUTPUT_DIR ]; then
  mkdir $OUTPUT_DIR
fi

for ttype in train dev test; do
    python merged_uds/append_luwpos.py -w $OUTPUT_DIR/ud_gsd_$ttype.cabocha.conllu $GSD_DIR/work/ud_gsd_$ttype.cabocha.conllu $GSD_DIR/work_luw/ud_gsd_$ttype.cabocha.conllu
    python merged_uds/append_luwpos.py -w $OUTPUT_DIR/ja_bccwj-ud-$ttype.csr.conllu $BCCWJ_DIR/output/ja_bccwj-ud-$ttype.csr.conllu $BCCWJ_DIR/output_luw/ja_bccwj-ud-$ttype.csr.conllu
done
