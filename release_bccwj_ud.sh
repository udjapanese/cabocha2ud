#!/bin/sh -x

"""
    BCCWJ convert shell script
"""

BASE_DIR=.
UD_TOOL_DIR=../../UD-TOOLS
CONLLU_FILE_DIR=../cabocha_files
CORE_BCCWJ_FILE=../../core_SUW.txt

usage () {
  cat <<EOS
Usage: $(basename "$0") [OPTION]...
  -h                    Display help
  -b BASE_DIR           OUTPUT directory (default: $BASE_DIR)
  -u UD_TOOL_DIR        directory includeing validate.py (default: $UD_TOOL_DIR)
  -s CORE_BCCWJ_FILE    PATH core_SUW.txt (default: $CORE_BCCWJ_FILE)
  -c CONLLU_FILE_DIR    PATH conllu files (default: $CONLLU_FILE_DIR)
EOS

  exit 2
}

while getopts "b:u:s:c:h" optKey; do
  case "$optKey" in
    u)
      UD_TOOL_DIR=$OPTARG
      ;;
    s)
      CORE_BCCWJ_FILE=$OPTARG
      ;;
    c)
      CONLLU_FILE_DIR=$OPTARG
      ;;
    b)
      BASE_DIR=$OPTARG
      ;;
    '-h'|'--help'|* )
      usage
      ;;
  esac
done

set -e

BASE_BCCWJ_DIR=$CONLLU_FILE_DIR/BCCWJ
MISC_DATA=$BASE_DIR/misc_mapping.pkl
ERROR_RESULT=$BASE_DIR/error_res.txt
ERROR_SENT_LIST=$BASE_DIR/error_sentid_lst.txt

# create filtered sentence
cat $BASE_BCCWJ_DIR/*/*.csr | python $UD_TOOL_DIR/validate.py --lang ja --max-err 0 - 1>| $ERROR_RESULT 2>&1
grep Sent $ERROR_RESULT | cut -d " " -f 4  | grep -v with | sort | uniq >| $ERROR_SENT_LIST

# create blank data
cat $BASE_BCCWJ_DIR/*/*.csr | python ud_bccwj_conv/extract_misc_information.py - -w $MISC_DATA
python ud_bccwj_conv/convert_core_suw_pkl.py $CORE_BCCWJ_FILE

TARGET=dev test train

for ttt in train test dev; do
  cat $BASE_BCCWJ_DIR/$ttt/*.csr | \
    python ud_bccwj_conv/replace_word_unit_bccwj.py - $MISC_DATA $CORE_BCCWJ_FILE ${ttt}_pos.pkl >| ${ttt}.conllu
done

# filter error sentences
for ttt in train test dev; do
  python ud_bccwj_conv/filter_sentence_by_id.py ${ttt}.conllu $ERROR_SENT_LIST >| ja_bccwj-ud-${ttt}.conllu
done


