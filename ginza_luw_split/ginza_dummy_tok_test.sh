#!/bin/sh

set -e

MODEL_DIR=models/ja_luw-4.0.0/model-final
INPUT_FILE=test.cabocha
OUTPUT_FILE=output.conllu

usage () {
  cat <<EOS
Usage: $(basename "$0") [OPTION]...
  -h            Display help
  -i INPUT_FILE  Input cabocha file (default: ${INPUT_FILE})
  -o OUTPUT_FILE  Output conllu file (default: ${INPUT_FILE})
  -m MODEL_DIR  Spacy model directory, including meta.json (default: ${MODEL_DIR})
EOS
  exit 2
}

while getopts "i:m:o:h" optKey; do
  case "$optKey" in
    m)
      MODEL_DIR=$OPTARG
      ;;
    i)
      INPUT_FILE=$OPTARG
      ;;
    o)
      OUTPUT_FILE=$OPTARG
      ;;
    '-h'|'--help'|* )
      usage
      ;;
  esac
done

python merge_oneline_sentence.py $INPUT_FILE | python -m ginza -b $MODEL_DIR >| $OUTPUT_FILE

echo "create " $OUTPUT_FILE "done."

