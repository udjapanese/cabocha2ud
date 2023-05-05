#!/bin/sh -x

set -e

BASE_DIR=../../NIKKEI/06final_conv
OUTPUT_SUW_DIR=../../NIKKEI/06final_conv_ud/SUW
OUTPUT_LUW_DIR=../../NIKKEI/06final_conv_ud/LUW

usage () {
  cat <<EOS
Usage: $(basename "$0") [OPTION]...
  -h            Display help
  -b BASE_DIR   base directory including cabocha files (default: ${BASE_DIR})
  -o OUTPUT_DIR   base directory including cabocha files (default: ${OUTPUT_DIR})
EOS

  exit 2
}

while getopts "b:o:h" optKey; do
  case "$optKey" in
    b)
      BASE_DIR=$OPTARG
      ;;
    o)
      OUTPUT_DIR=$OPTARG
      ;;
    '-h'|'--help'|* )
      usage
      ;;
  esac
done

# GNU `parallel`を使っています

if [ ! -d $OUTPUT_SUW_DIR ]; then
  mkdir -p $OUTPUT_SUW_DIR
fi
if [ ! -d $OUTPUT_LUW_DIR ]; then
  mkdir -p $OUTPUT_LUW_DIR
fi

rm -f $OUTPUT_SUW_DIR/*.conllu $OUTPUT_LUW_DIR/*.conllu

# CabochaからUDへの変換
ls $BASE_DIR/*.cabocha | \
    OUTPUT_SUW_DIR=$OUTPUT_SUW_DIR parallel 'python cabocha2ud {} -c conf/default_nikkei_args.yaml -w $OUTPUT_SUW_DIR/{/.}.mr'

# シングルルートに変換
ls $OUTPUT_SUW_DIR/*.mr | \
    OUTPUT_SUW_DIR=$OUTPUT_SUW_DIR parallel 'python cabocha2ud/pipeline/replace_multi_root.py {} convert -w $OUTPUT_SUW_DIR/{/.}.csr.conllu'

rename 's/.mr/.mr.conllu/g' $OUTPUT_SUW_DIR/*.mr

# CabochaからUDへの変換
ls $BASE_DIR/*.cabocha | \
    OUTPUT_LUW_DIR=$OUTPUT_LUW_DIR parallel 'python cabocha2ud {} -c conf/luw_nikkei_args.yaml -w $OUTPUT_LUW_DIR/{/.}.mr'

# シングルルートに変換
ls $OUTPUT_LUW_DIR/*.mr | \
    OUTPUT_LUW_DIR=$OUTPUT_LUW_DIR parallel 'python cabocha2ud/pipeline/replace_multi_root.py {} convert -w $OUTPUT_LUW_DIR/{/.}.csr.conllu'

rename 's/.mr/.mr.conllu/g' $OUTPUT_LUW_DIR/*.mr


