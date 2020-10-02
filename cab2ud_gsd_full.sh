#!/bin/sh -x

usage () {
  cat <<EOS
Usage: $(basename "$0") [OPTION]...
  -h            Display help
  -b BASE_DIR   Directory including cabocha files
  -s SP_DIR     Directory including Space after files
EOS

  exit 2
}

BASE_DIR=../cabocha_files/UD_Japanese-GSDPUD-CaboCha
SP_DIR=../cabocha_files/GSD/sp_data

while getopts "b:s:h" optKey; do
  case "$optKey" in
    b)
      BASE_DIR=$OPTARG
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

# GNU `parallel`を使っています

# 重複文チェック
python validators/duplicate_checker.py $BASE_DIR/*.cabocha
# 数字まとめあげ
ls $BASE_DIR/*.cabocha | \
    parallel 'python merge_number/merge_number.py < {} > {}.n'
# cabocha -> UD 作業
ls $BASE_DIR/*.cabocha | \
    parallel 'python cab2ud.py {}.n -c conf/default_gsd_args.yaml -w {}.conllu'

# PUD作業
# 括弧の対応を直す
python ../UDJapaneseGSD/convertParen2.6.py $BASE_DIR/ud_pud.cabocha.conllu $BASE_DIR/ud_pud.cabocha.conllu.p

for ttt in dev test train
do
  python merge_luw_gsd/merge_sp_to_conll.py $BASE_DIR/ud_gsd_$ttt.cabocha.conllu $SP_DIR/SpaceAfter_$ttt.txt -w $BASE_DIR/ud_gsd_$ttt.cabocha.conllu.p
  cp $BASE_DIR/ud_gsd_$ttt.cabocha.conllu.p $BASE_DIR/ud_gsd_$ttt.cabocha.conllu
done

python merge_luw_gsd/merge_sp_to_conll.py $BASE_DIR/ud_pud.cabocha.conllu.p $SP_DIR/SpaceAfter_pud.txt -w $BASE_DIR/ud_pud.cabocha.conllu.sp
cp $BASE_DIR/ud_pud.cabocha.conllu.sp $BASE_DIR/ud_pud.cabocha.conllu

# rm -f $BASE_DIR/*.n $BASE_DIR/*.p $BASE_DIR/*.sp

