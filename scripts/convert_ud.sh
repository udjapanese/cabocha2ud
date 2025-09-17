#!/bin/sh

detect_word_unit() {
  if [ $# -ne 1 ]; then
    echo "Usage: detect_word_unit <yaml-file>"
    return 1
  fi

  local file="$1"
  if grep -q "build_luw" "$file"; then
    echo "luw"
  else
    echo "suw"
  fi
}

usage () {
  cat <<EOS
Usage: $(basename "$0") -w [WORK_DIR] -c [CONF_FILE] [OPTION]...
  -h            Display help
  -w WORK_DIR   base and work directory including cabocha files
  -c CONF_FILE   cab2ud conf file
EOS

  exit 2
}

WORK_DIR=/work/hogehoge
CONF_FILE=conf/hogehoge.conf

while getopts "w:c:h" optKey; do
  case "$optKey" in
    w)
      WORK_DIR=$OPTARG
      ;;
    c)
      CONF_FILE=$OPTARG
      ;;
    '-h'|'--help'|* )
      usage
      ;;
  esac
done

if [ ! -d $WORK_DIR ]; then
  echo "ERROR: Please set WORK_DIR: you set -->" $WORK_DIR
  echo
  usage
fi

if [ ! -f $CONF_FILE ]; then
  echo "ERROR: Please set CONF_FILE: you set -->" $CONF_FILE
  echo
  usage
fi

DIR_NAME=`basename $WORK_DIR | tr 'A-Z' 'a-z'`
CAB_DIR=$WORK_DIR/cabocha
if [ ! -d $CAB_DIR ]; then
  echo "ERROR: Please create 'cabocha' in WORK_DIR: " $WORK_DIR
  echo
  usage
fi

if ! type "parallel" > /dev/null 2>&1; then
  # GNU `parallel`を使っているためパスが読み取れなければエラー
  echo "This script use GNU parallel. Please install: https://savannah.gnu.org/projects/parallel/"
  echo "   $ brew install parallel (Mac)"
  echo "   $ apt install parallel (Ubuntu)"
  exit 2
fi

# 短単位か長単位かファイルから抽出し、フォルダ名に
WORD_UNIT=`detect_word_unit $CONF_FILE`
OUTPUT_UD_DIR=$WORK_DIR/ud/$WORD_UNIT
if [ ! -d $OUTPUT_UD_DIR ]; then
  mkdir -p $OUTPUT_UD_DIR
fi

# Cabochaファイルにあるフォルダを作る
for dpath in `ls -d $CAB_DIR/*`; do
  dname=`basename $dpath`
  if [ ! -d $OUTPUT_UD_DIR/$dname ]; then
    mkdir $OUTPUT_UD_DIR/$dname
  fi
done

# CabochaからUDへの変換
ls $CAB_DIR/*/*.cabocha | \
    work_dir=$OUTPUT_UD_DIR conf_file=$CONF_FILE parallel 'python cabocha2ud {} -c $conf_file -w $work_dir/{= s:^/.*/(.*?)/(.*)\.cabocha:$1/$2:; =}.conllu'


for dpath in `ls -d $OUTPUT_UD_DIR/*`; do
  dname=`basename $dpath`
  # TODO: 指定オーダーで書き出す（いまはファイル名順で差し支えがない）
  if [ $WORD_UNIT = "luw" ]; then
    cat $OUTPUT_UD_DIR/$dname/*.conllu > $OUTPUT_UD_DIR/ja_${DIR_NAME}luw-ud-$dname.conllu
  else
    cat $OUTPUT_UD_DIR/$dname/*.conllu > $OUTPUT_UD_DIR/ja_${DIR_NAME}-ud-$dname.conllu
  fi
done
