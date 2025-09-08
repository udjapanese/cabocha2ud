#!/bin/sh -x

set -e

BASE_DIR=../cabocha_files/BCCWJ
OUTPUT_DIR=../cabocha_files/BCCWJ/output_luw


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


if [ ! -d $OUTPUT_DIR ]; then
  # mkdir OUTPUT directory
  mkdir $OUTPUT_DIR
fi

cp -r $BASE_DIR/train/ $OUTPUT_DIR/
cp -r $BASE_DIR/test/ $OUTPUT_DIR/
cp -r $BASE_DIR/dev/ $OUTPUT_DIR/

# GNU `parallel`を使っています

# CabochaからUDへの変換
ls $OUTPUT_DIR/*/*.cabocha | \
    parallel 'python cabocha2ud {} -c conf/luw_bccwj_args.yaml -w {}.conllu.mr'

# シングルルートに変換
ls $OUTPUT_DIR/*/*.conllu.mr | \
    parallel 'python cabocha2ud/pipeline/replace_multi_root.py {} convert | python cabocha2ud/pipeline/patch_fix.py - conf/auto_hand_fix_luw.yaml -w {}.csr'
ls $OUTPUT_DIR/*/*.conllu.mr | \
    parallel 'python cabocha2ud/pipeline/replace_multi_root.py {} remove | python cabocha2ud/pipeline/patch_fix.py - conf/auto_hand_fix_luw.yaml -w {}.rsr'

# マルチルートが残ったまま  *.conllu.mr
cat $OUTPUT_DIR/dev/*.mr > $OUTPUT_DIR/ja_bccwj-ud-dev.mr.conllu
cat $OUTPUT_DIR/train/*.mr > $OUTPUT_DIR/ja_bccwj-ud-train.mr.conllu
cat $OUTPUT_DIR/test/*.mr > $OUTPUT_DIR/ja_bccwj-ud-test.mr.conllu

# シングルルートに変換したもの  *.conllu.mr.csr
cat $OUTPUT_DIR/dev/*.csr > $OUTPUT_DIR/ja_bccwj-ud-dev.csr.conllu
cat $OUTPUT_DIR/train/*.csr > $OUTPUT_DIR/ja_bccwj-ud-train.csr.conllu
cat $OUTPUT_DIR/test/*.csr > $OUTPUT_DIR/ja_bccwj-ud-test.csr.conllu

# マルチルートのものを削除したもの *.conllu.mr.rsr
cat $OUTPUT_DIR/dev/*.rsr > $OUTPUT_DIR/ja_bccwj-ud-dev.rsr.conllu
cat $OUTPUT_DIR/train/*.rsr > $OUTPUT_DIR/ja_bccwj-ud-train.rsr.conllu
cat $OUTPUT_DIR/test/*.rsr > $OUTPUT_DIR/ja_bccwj-ud-test.rsr.conllu

# rm -rf $BASE_DIR/*/*.n
