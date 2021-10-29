#!/bin/sh -x

# BCCWJ convert shell script


BASE_DIR=.
UD_TOOL_DIR=../../UD-TOOLS
CONLLU_FILE_DIR=../cabocha_files
WORD_UNIT=suw
CORE_BCCWJ_FILE=../../core_SUW.txt

usage () {
  cat <<EOS
Usage: $(basename "$0") [OPTION]...
  -h                    Display help
  -b BASE_DIR           OUTPUT directory (default: $BASE_DIR)
  -u UD_TOOL_DIR        directory includeing validate.py (default: $UD_TOOL_DIR)
  -w WORD_UNIT          WORD Unit [suw|luw] (default: $WORD_UNIT)
  -s CORE_BCCWJ_FILE    PATH core_SUW.txt (default: $CORE_BCCWJ_FILE)
  -c CONLLU_FILE_DIR    PATH conllu files (default: $CONLLU_FILE_DIR)
EOS

  exit 2
}

while getopts "b:u:s:c:h:w:" optKey; do
  case "$optKey" in
    u)
      UD_TOOL_DIR=$OPTARG
      ;;
    w)
      WORD_UNIT=$OPTARG
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

BASE_BCCWJ_DIR=$CONLLU_FILE_DIR/BCCWJ
if [ $WORD_UNIT = luw ]; then
  BASE_BCCWJ_DIR=$CONLLU_FILE_DIR/BCCWJ/output_luw
fi

OUTPUT_DIR=OUTPUT_BCCWJ_$WORD_UNIT
if [ ! -d $OUTPUT_DIR ]; then
  mkdir $OUTPUT_DIR
fi

MISC_DATA=$OUTPUT_DIR/misc_mapping_$WORD_UNIT.pkl
ERROR_RESULT=$OUTPUT_DIR/error_bccwj_res.txt
ERROR_SENT_LIST=$OUTPUT_DIR/error_sentid_lst.txt

# create filtered sentence
ls $BASE_BCCWJ_DIR/*/*.csr | parallel "python $UD_TOOL_DIR/validate.py --lang ja --max-err 0" >| $ERROR_RESULT 2>&1
grep Sent $ERROR_RESULT | cut -d " " -f 4  | grep -v with | sort | uniq >| $ERROR_SENT_LIST

# convert core file to pkl format
python ud_bccwj_conv/convert_core_bccwj_pkl.py $CORE_BCCWJ_FILE $WORD_UNIT

# extract for misc information for replacement
cat $BASE_BCCWJ_DIR/*/*.csr | python ud_bccwj_conv/extract_misc_information.py - -w $MISC_DATA

# create blank data and need data (train|test|dev)_pos.pkl
for ttt in train test dev; do
  cat $BASE_BCCWJ_DIR/$ttt/*.csr | \
    python ud_bccwj_conv/replace_word_unit_bccwj.py - $MISC_DATA $ERROR_SENT_LIST $CORE_BCCWJ_FILE $OUTPUT_DIR/${ttt}_pos.pkl >| $OUTPUT_DIR/ja_bccwj-ud-${ttt}.conllu
done
