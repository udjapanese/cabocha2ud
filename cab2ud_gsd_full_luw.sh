#!/bin/sh -x

usage () {
  cat <<EOS
Usage: $(basename "$0") [OPTION]...
  -h              Display help
  -m              
  -b BASE_DIR     Directory including cabocha files
  -w WORK_DIR   Directory including conllu files
  -s SP_DIR       Directory including Space after files
EOS

  exit 2
}

BASE_DIR=../cabocha_files/GSD/UD-Japanese-GSDPUD-Cabocha
WORK_DIR=../cabocha_files/GSD/work_luw
SP_DIR=../cabocha_files/GSD/sp_data
SPETIAL_MODE=false

while getopts "p:b:s:w:hm" optKey; do
  case "$optKey" in
    b)
      BASE_DIR=$OPTARG
      ;;
    p)
      PATTERN_DIR=$OPTARG
      ;;
    w)
      WORK_DIR=$OPTARG
      ;;
    s)
      SP_DIR=$OPTARG
      ;;
    m)
      SPETIAL_MODE=true
      ;;
    '-h'|'--help'|* )
      usage
      ;;
  esac
done

set -e

if $SPETIAL_MODE; then
  echo "a expoand space mode for luw"
fi

if [ ! -d $BASE_DIR ]; then
  # clone from github
  git clone git@github.com:udjapanese/UD-Japanese-GSDPUD-Cabocha.git $BASE_DIR
fi
if [ ! -d $WORK_DIR ]; then
  # mkdir OUTPUT directory
  mkdir $WORK_DIR
fi

# GNU `parallel`を使っています

# 重複文チェック
python validators/duplicate_checker.py $BASE_DIR/*.cabocha
cp $BASE_DIR/*.cabocha $WORK_DIR/

# cabocha -> UD 作業
if $SPETIAL_MODE; then
  WORK_DIR=$WORK_DIR SP_DIR=$SP_DIR parallel 'python cabocha2ud $WORK_DIR/ud_{}.cabocha -c conf/luw_{= s:_(dev|test|train):: =}_args.yaml --sp-file $SP_DIR/SpaceAfter_{= s:gsd_:: =}.txt --remove-luw-space -w $WORK_DIR/ud_{}.cabocha.conllu' ::: gsd_dev gsd_test gsd_train pud
else
  WORK_DIR=$WORK_DIR SP_DIR=$SP_DIR parallel 'python cabocha2ud $WORK_DIR/ud_{}.cabocha -c conf/luw_{= s:_(dev|test|train):: =}_args.yaml --sp-file $SP_DIR/SpaceAfter_{= s:gsd_:: =}.txt -w $WORK_DIR/ud_{}.cabocha.conllu' ::: gsd_dev gsd_test gsd_train pud
fi

rm -f $WORK_DIR/*.cabocha

