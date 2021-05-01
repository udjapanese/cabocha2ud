#!/bin/sh -x

set -e

TRAIN_FILE=train.conllu
DEV_FILE=dev.conllu
WRD_MODEL=models/ja_vectors_chive_mc90_35k
OUTPUT_DIR=models/ja_luw-4.0.0
IT_CNT=50


usage () {
  cat <<EOS
Usage: $(basename "$0") [OPTION]...
  -h            Display help
  -b BASE_DIR   base directory including cabocha files (default: ${BASE_DIR})
  -o OUTPUT_DIR   base directory including cabocha files (default: ${OUTPUT_DIR})

Requirements:

> pip install -U ginza
> wget https://raw.githubusercontent.com/megagonlabs/ginza/develop/ginza_util/conllu_to_json.py -O conllu_to_json.py
> wget https://github.com/megagonlabs/ginza/releases/download/ja_luw-4.0.0/ja_vectors_chive_mc90_35k.tgz
> tar xvf ja_vectors_chive_mc90_35k.tgz  # the command create `models/ja_vectors_chive_mc90_35k` directory

EOS

  exit 2
}

while getopts "b:o:h" optKey; do
  case "$optKey" in
    b)
      BASE_DIR=$OPTARG
      ;;
    o)
      OUTPUT_DIR=$OPTARG
      ;;
    '-h'|'--help'|* )
      usage
      ;;
  esac
done


python conllu_to_json.py -l -e $TRAIN_FILE > $TRAIN_FILE.luw.json
python conllu_to_json.py -l -e $DEV_FILE > $DEV_FILE.luw.json
python -m spacy train ja $OUTPUT_DIR $TRAIN_FILE.luw.json $DEV_FILE.luw.json -v $WRD_MODEL/ -VV --gold-preproc -n $IT_CNT

