#!/bin/sh -x


UD_TOOL_DIR=../../UD-TOOLS
CONLLU_FILE_DIR=../cabocha_files
OUTPUT_FILE=error_res

usage () {
  cat <<EOS
Usage: $(basename "$0") [OPTION]...
  -h            Display help
  -u UD_TOOL_DIR   UniversalDependencies/tools directory (default:${UD_TOOL_DIR})
  -c CONLLU_FILE_DIR   conllu base directory (default:${CONLLU_FILE_DIR})
  -o OUTPUT_FILE   output file   (default:${OUTPUT_FILE})
EOS

  exit 2
}

while getopts "c:o:u:h" optKey; do
  case "$optKey" in
    u)
      UD_TOOL_DIR=$OPTARG
      ;;
    c)
      CONLLU_FILE_DIR=$OPTARG
      ;;
    o)
      OUTPUT_FILE=$OPTARG
      ;;
    '-h'|'--help'|* )
      usage
      ;;
  esac
done

ls $CONLLU_FILE_DIR/BCCWJ/*/*.csr $CONLLU_FILE_DIR/GSD/work/ud_*.conllu |\
  parallel "python $UD_TOOL_DIR/validate.py --lang ja --max-err 0" >| $OUTPUT_FILE.s.tmp 2>&1 &

ls $CONLLU_FILE_DIR/BCCWJ/output_luw/*/*.csr $CONLLU_FILE_DIR/GSD/work_luw/ud_*.conllu |\
	  parallel "python $UD_TOOL_DIR/validate.py --lang ja --max-err 0" >| $OUTPUT_FILE.l.tmp 2>&1

grep Sent $OUTPUT_FILE.s.tmp | sort >| $OUTPUT_FILE.suw.txt
c=`grep 'with' $OUTPUT_FILE.s.tmp | awk -F" " 'BEGIB{a=0}{a+=$5}END{print a}'`
echo "*** FAILED *** with $c errors" >> $OUTPUT_FILE.suw.txt

grep Sent $OUTPUT_FILE.l.tmp | sort >| $OUTPUT_FILE.luw.txt
c=`grep 'with' $OUTPUT_FILE.l.tmp | awk -F" " 'BEGIB{a=0}{a+=$5}END{print a}'`
echo "*** FAILED *** with $c errors" >> $OUTPUT_FILE.luw.txt

echo "output" $OUTPUT_FILE.suw.txt $OUTPUT_FILE.luw.txt

