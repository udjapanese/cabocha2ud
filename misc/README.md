# Misc files

## show_tab_rule_files.py

ルールファイルを少し見やすい形に変換する

```shell
> pipenv run python misc/show_tab_rule_file.py -f pos conf/bccwj_pos_suw_rule.yaml
> pipenv run python misc/show_tab_rule_file.py -f dep conf/bccwj_dep_suw_rule.yaml
```

## show_bd_position.py

単語位置などを表示する。

```shell
> pipenv run python misc/show_bd_position.py Cabochaファイル
```

## fix_overbunsetu.py

長単位で2つの文節にまたいでいるものを検出して修正する

```shell
> pipenv run python fixed_bunsetu_overluw.py Cabochaファイル -w [出力ファイル]
```
