# Misc files

## merge_pud_text_en.py

UD-Japanese PUDのIDをv2.5を元に付与する
（ややゴリ押し）

```shell
> python merge_luw_gsd/merge_pud_text_en.py [変換したPUD conlluファイル] [v2.5のconllu]
```

## extract_gsd_info_for_dump.py

長単位のデータとSpaceAfterと対応付ファイルなどを用いて
`cab2ud.py`に入力できる*.cabocha.dumpedファイルをつくる

```shell
(*にはtestやtrainをいれる)
>  python merge_luw_gsd/extract_gsd_info_for_dump.py \
        -i ../cabocha_files/GSD/delete_txt_id/new_ud_*_align.txt \
        -d ../cabocha_files/GSD/delete_txt_id/ud_*_align.txt -a \
        ../cabocha_files/GSD/luw_dump/bcpExport_CCD_UD-*.txt \
        ../cabocha_files/GSD/sp_data/SpaceAfter_*.txt \
        ../cabocha_files/GSD/ccd_ud_*_final.cabocha
```
