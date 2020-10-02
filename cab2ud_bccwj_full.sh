#!/bin/sh -x


usage () {
  cat <<EOS
Usage: $(basename "$0") [OPTION]...
  -h            Display help
  -b BASE_DIR   base directory including cabocha files
EOS

  exit 2
}

BASE_DIR=../cabocha_files/BCCWJ

while getopts "b:h" optKey; do
  case "$optKey" in
    b)
      BASE_DIR=$OPTARG
      ;;
    '-h'|'--help'|* )
      usage
      ;;
  esac
done

# GNU `parallel`を使っています
set -e

# 数字まとめ上げ
ls $BASE_DIR/*/*.cabocha | \
    parallel 'python merge_number/merge_number.py < {} > {}.n'

# CabochaからUDへの変換
ls $BASE_DIR/*/*.cabocha | \
    parallel 'python cab2ud.py {}.n -c conf/default_bccwj_args.yaml -s -m "　" -w {}.conllu.mr'

# シングルルートに変換
ls $BASE_DIR/*/*.conllu.mr | \
    parallel python misc/replace_multi_root.py {} convert -w {}.csr --debug
ls $BASE_DIR/*/*.conllu.mr | \
    parallel python misc/replace_multi_root.py {} remove -w {}.rsr --debug

# マルチルートが残ったまま  *.conllu.mr
cat $BASE_DIR/dev/*.mr > $BASE_DIR/ja_bccwj-ud-dev.mr.conllu
cat $BASE_DIR/train/*.mr > $BASE_DIR/ja_bccwj-ud-train.mr.conllu
cat $BASE_DIR/test/*.mr > $BASE_DIR/ja_bccwj-ud-test.mr.conllu

# シングルルートに変換したもの  *.conllu.mr.csr
cat $BASE_DIR/dev/*.csr > $BASE_DIR/ja_bccwj-ud-dev.csr.conllu
cat $BASE_DIR/train/*.csr > $BASE_DIR/ja_bccwj-ud-train.csr.conllu
cat $BASE_DIR/test/*.csr > $BASE_DIR/ja_bccwj-ud-test.csr.conllu

# マルチルートのものを削除したもの *.conllu.mr.rsr
cat $BASE_DIR/dev/*.rsr > $BASE_DIR/ja_bccwj-ud-dev.rsr.conllu
cat $BASE_DIR/train/*.rsr > $BASE_DIR/ja_bccwj-ud-train.rsr.conllu
cat $BASE_DIR/test/*.rsr > $BASE_DIR/ja_bccwj-ud-test.rsr.conllu
