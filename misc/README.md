# Misc files

## show_tab_rule_files.py

ルールファイルを少し見やすい形に変換する

```shell
> python misc/show_tab_rule_file.py -f pos conf/bccwj_pos_suw_rule.json
> python misc/show_tab_rule_file.py -f dep conf/bccwj_dep_suw_rule.json
```

## replace_multi_root.py

CoNLLUファイルにマルチルートが含まれているかを確認し、
マルチルートの文を削除するか、シングルルートに変換をする

```shell
# マルチルートの文を削除する
> python misc/replace_multi_root.py [CoNLLファイル] remove -w [出力ファイル]
# マルチルートの文をシングルルートに変換する
> python misc/replace_multi_root.py [CoNLLファイル] convert -w [出力ファイル]
```
