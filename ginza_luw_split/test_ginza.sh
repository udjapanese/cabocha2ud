#!/bin/sh -x

set -e

for base_file in ud_gsd_test.cabocha bccwj_test.cabocha
do
  for model_file in bccwj_nobunsetu bccwj_bunsetu gsd_nobunsetu gsd_bunsetu
  do
    ./ginza_dummy_tok_test.sh -i $base_file -o ginza_$base_file.$model_file.out -m models/ja_luw-$model_file-4.0.0/model-final
    python show_luw_result.py ginza ginza_$base_file.$model_file.out $base_file -w ginza_$base_file.$model_file.out.res
  done
done
