#!/bin/sh -x

set -e

usage () {
  cat <<EOS
Usage: $(basename "$0") [OPTION]...
  -h              Display help
  -b BASE_CABOCHA_DIR     Directory including cabocha files
  -w WORK_DIR   Directory including conllu files
EOS

  exit 2
}

BASE_CABOCHA_DIR=../../CEJC_data/output_cabocha
WORK_DIR=../../CEJC_data/output_conll

while getopts "b:w:h" optKey; do
  case "$optKey" in
    b)
      BASE_CABOCHA_DIR=$OPTARG
      ;;
    w)
      WORK_DIR=$OPTARG
      ;;
    '-h'|'--help'|* )
      usage
      ;;
  esac
done

if [ ! -d $WORK_DIR ]; then
  mkdir -p $WORK_DIR/SUW $WORK_DIR/LUW
fi

# cabocha -> UD 作業

ls $BASE_CABOCHA_DIR/*.cabocha | \
  WORK_DIR=$WORK_DIR parallel 'pipenv run python cabocha2ud {} -w $WORK_DIR/SUW/{/.}.conllu -c conf/default_cejc_args.yaml'
ls $BASE_CABOCHA_DIR/*.cabocha | \
  WORK_DIR=$WORK_DIR parallel 'pipenv run python cabocha2ud {} -w $WORK_DIR/LUW/{/.}.conllu -c conf/luw_cejc_args.yaml'
pipenv run python ud_cejc_scirpt/split_train_cejc.py $WORK_DIR -i ud_cejc_scirpt/core_sp_info.tsv

if [ ! -d ${WORK_DIR}_mr ]; then
  mkdir -p ${WORK_DIR}_mr/SUW ${WORK_DIR}_mr/LUW
fi

ls $BASE_CABOCHA_DIR/*.cabocha | \
  WORK_DIR=$WORK_DIR parallel 'pipenv run python cabocha2ud {} -w "$WORK_DIR"_mr/SUW/{/.}.mr.conllu -c conf/default_cejc_args.yaml -p merge_number,fix_stutters'
ls $BASE_CABOCHA_DIR/*.cabocha | \
  WORK_DIR=$WORK_DIR parallel 'pipenv run python cabocha2ud {} -w "$WORK_DIR"_mr/LUW/{/.}.mr.conllu -c conf/luw_cejc_args.yaml -p build_luw,fix_stutters'
pipenv run python ud_cejc_scirpt/split_train_cejc.py "$WORK_DIR"_mr --col-suffix="-dialog.mr.conllu" -i ud_cejc_scirpt/core_sp_info.tsv

