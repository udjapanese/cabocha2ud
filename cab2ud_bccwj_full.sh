#!/bin/sh -x

set -e

BASE_DIR=../cabocha_files/BCCWJ
OUTPUT_DIR=../cabocha_files/BCCWJ/output

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

if [ ! -d $OUTPUT_DIR ]; then
  # mkdir OUTPUT directory
  mkdir $OUTPUT_DIR
fi

# 数字まとめ上げ
ls $BASE_DIR/*/*.cabocha | \
    parallel 'python merge_number/merge_number.py < {} > {}.n'

# CabochaからUDへの変換
ls $BASE_DIR/*/*.cabocha | \
    parallel 'python cabocha2ud {}.n -c conf/default_bccwj_args.yaml -w {}.conllu.mr'

# シングルルートに変換
ls $BASE_DIR/*/*.conllu.mr | \
    parallel 'python misc/replace_multi_root.py {} convert --debug | python patch_fix/patch_fix.py - conf/auto_hand_fix.yaml -w {}.csr'
ls $BASE_DIR/*/*.conllu.mr | \
    parallel 'python misc/replace_multi_root.py {} remove --debug | python patch_fix/patch_fix.py - conf/auto_hand_fix.yaml -w {}.rsr'

# マルチルートが残ったまま  *.conllu.mr
cat $BASE_DIR/dev/*.mr > $OUTPUT_DIR/ja_bccwj-ud-dev.mr.conllu
cat $BASE_DIR/train/*.mr > $OUTPUT_DIR/ja_bccwj-ud-train.mr.conllu
cat $BASE_DIR/test/*.mr > $OUTPUT_DIR/ja_bccwj-ud-test.mr.conllu

# シングルルートに変換したもの  *.conllu.mr.csr
cat $BASE_DIR/dev/*.csr > $OUTPUT_DIR/ja_bccwj-ud-dev.csr.conllu
cat $BASE_DIR/train/*.csr > $OUTPUT_DIR/ja_bccwj-ud-train.csr.conllu
cat $BASE_DIR/test/*.csr > $OUTPUT_DIR/ja_bccwj-ud-test.csr.conllu

# マルチルートのものを削除したもの *.conllu.mr.rsr
cat $BASE_DIR/dev/*.rsr > $OUTPUT_DIR/ja_bccwj-ud-dev.rsr.conllu
cat $BASE_DIR/train/*.rsr > $OUTPUT_DIR/ja_bccwj-ud-train.rsr.conllu
cat $BASE_DIR/test/*.rsr > $OUTPUT_DIR/ja_bccwj-ud-test.rsr.conllu

rm -rf $BASE_DIR/*/*.n
