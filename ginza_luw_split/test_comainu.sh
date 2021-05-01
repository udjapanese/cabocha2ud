#!/bin/sh -x

set -e


for base_file in kc_gsd.test.txt kc_bccwj.test.txt
do
  if [ $base_file = "kc_gsd.test.txt" ]; then
    gold_file=ud_gsd_test.cabocha
  else
    gold_file=bccwj_test.cabocha
  fi
  for model_file in gsd_full_train/kc_gsd.train.txt.model bccwj_full_train/kc_bccwj.train.txt.model
  do
    # a/kc_gsd.test.txt.lout -> ../Comainu/res/$base_file.lout -> ../Comainu/res/
    cd ../Comainu
    ./script/comainu.pl kc2longout --luwmodel $model_file --input=../ginza/$base_file --output res
    cd -
    outfile=`echo $base_file.$model_file.out.res | sed -e "s#/#_#g"`
    resfile=`echo $base_file.$model_file.out | sed -e "s#/#_#g"`
    cp ../Comainu/res/$base_file.lout $resfile
    rm -f ../Comainu/res/$base_file.lout
    python show_luw_result.py kc $resfile $gold_file -w $outfile
  done
done


