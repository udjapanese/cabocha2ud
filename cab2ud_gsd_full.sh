#!/bin/sh -x

usage () {
  cat <<EOS
Usage: $(basename "$0") [OPTION]...
  -h              Display help
  -b BASE_DIR     Directory including cabocha files
  -w WORK_DIR   Directory including conllu files
  -s SP_DIR       Directory including Space after files
EOS

  exit 2
}

BASE_DIR=../cabocha_files/GSD/UD_Japanese-GSDPUD-CaboCha
WORK_DIR=../cabocha_files/GSD/work
SP_DIR=../cabocha_files/GSD/sp_data
PATTERN_DIR=./convert_paren

while getopts "p:b:s:w:h" optKey; do
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
    '-h'|'--help'|* )
      usage
      ;;
  esac
done

set -e

if [ ! -d $BASE_DIR ]; then
  # clone from github
  git clone git@github.com:masayu-a/UD_Japanese-GSDPUD-CaboCha $BASE_DIR
fi
if [ ! -d $WORK_DIR ]; then
  # mkdir OUTPUT directory
  mkdir $WORK_DIR
fi

# GNU `parallel`を使っています

# 重複文チェック
python validators/duplicate_checker.py $BASE_DIR/*.cabocha
cp $BASE_DIR/*.cabocha $WORK_DIR/

# 数字まとめあげ
ls $WORK_DIR/*.cabocha | \
    parallel 'python merge_number/merge_number.py < {} > {}.n'
# cabocha -> UD 作業
ls $WORK_DIR/*.cabocha | \
    parallel 'python cabocha2ud {}.n -c conf/default_gsd_args.yaml -w {}.conllu'

# PUD作業
# 括弧の対応を直す
python $PATTERN_DIR/convertParen.py $WORK_DIR/ud_pud.cabocha.conllu $WORK_DIR/ud_pud.cabocha.conllu.p

for ttt in dev test train
do
  python merge_gsd/merge_sp_to_conll.py $WORK_DIR/ud_gsd_$ttt.cabocha.conllu $SP_DIR/SpaceAfter_$ttt.txt -w $WORK_DIR/ud_gsd_$ttt.cabocha.conllu.p
  python fixed_newdoc/fixed_newdoc.py $WORK_DIR/ud_gsd_$ttt.cabocha.conllu.p -w $WORK_DIR/ud_gsd_$ttt.cabocha.conllu.spf
  python patch_fix/patch_fix.py $WORK_DIR/ud_gsd_$ttt.cabocha.conllu.spf conf/auto_hand_fix.yaml -w $WORK_DIR/ud_gsd_$ttt.cabocha.conllu.spff
  cp $WORK_DIR/ud_gsd_$ttt.cabocha.conllu.spff $WORK_DIR/ud_gsd_$ttt.cabocha.conllu
done

python merge_gsd/merge_sp_to_conll.py $WORK_DIR/ud_pud.cabocha.conllu.p $SP_DIR/SpaceAfter_pud.txt -w $WORK_DIR/ud_pud.cabocha.conllu.sp
python fixed_newdoc/fixed_newdoc.py $WORK_DIR/ud_pud.cabocha.conllu.sp -w $WORK_DIR/ud_pud.cabocha.conllu.spf
python patch_fix/patch_fix.py $WORK_DIR/ud_pud.cabocha.conllu.spf conf/auto_hand_fix.yaml -w $WORK_DIR/ud_pud.cabocha.conllu.spff
cp $WORK_DIR/ud_pud.cabocha.conllu.spff $WORK_DIR/ud_pud.cabocha.conllu

rm -f $WORK_DIR/*.cabocha

