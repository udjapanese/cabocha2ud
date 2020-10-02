# cab2ud.py

## 動作環境

Python3.7（3.7.2）にて動作確認済み。
pipで必要なライブラリをインストールします

```zsh
pip install configargparse pyyaml tqdm
```

（Pipenvを導入済みの場合、Pipfileで上記ライブラリがインストール可能）（おそらく）

```zsh
pipenv --install
```

## 動かし方

完全に再現するためにば、現在長単位データつきのcabochaファイルが必要です。
（現在のルールの一部が長単位を参照しているため）
長単位つきcabochaファイルは`../cabocha_files`ディレクトリをみてください。

```text
../cabocha_files/GSD/*.cabocha.dumped: GSDとPUDの長単位情報つきcabocha
../cabocha_files/BCCWJ/*.cabocha.dumped: BCCWJの長単位情報つきcabocha
```

```zsh
python cab2ud.py [長単位つきcabochaファイル] -c conf/default_(bccwj|gsd)_args.yaml --debug -w [出力ファイル名(指定しない場合標準出力)]
```

`conf/default_(bccwj|gsd)_args.yaml`はそれぞれのコーパス名を指定してください
（PUDはGSDを指定してください）
（現在コーパスで入力フォーマットが違うなどがあり、コーパスごとで設定が分れてます）

とりあえずGSDファイルは以下のスクリプトで一括変換できます
(`parallel`コマンドを使っているため、ない場合自力でお願いします）

```shell
# GSDの変換
./cab2ud_gsd_full.sh
# BCCWJの変換
./cab2ud_bccwj_full.sh
```

`-a`をつけると`.cabocha`ファイルから`.cabocha.dumped`（文削除して長単位データを付与したもの）へ変換できます
`.cabocha.dumped`ファイルに変更がないかぎりしなくて大丈夫です。

GSDの場合

```shell
./cab2ud_gsd_full.sh -a
```

BCCWJの場合（要修正）

```shell
./cab2ud_bccwj_full.sh -a
```

## 出力ファイルについて

BCCWJについては[/cabocha_files/BCCWJ/README.md](/cabocha_files/BCCWJ/README.md)を参照のこと

## 変換ルールについて

プログラム全体が分からなくても、
とりあえず以下のjsonファイルを参照して書き直してもらうだけでも
おおまかなルールは変更されます。
（係り関係の入れ替えなどには現状別個対応しているため、プログラムの書き換えがいります）
ルールは上から順番に対応がとれたものを採用して返します。

```text
conf/bccwj_pos_suw_rule.json: UD POSの変換
conf/bccwj_dep_suw_rule.json: UD labelの変換
```

（ファイル名は現状suwのものを使っているのでそちらを参照してください）

一応、タブ形式に変換できます。

```shell
> python misc/show_tab_rule_file.py -f pos conf/bccwj_pos_suw_rule.json
> python misc/show_tab_rule_file.py -f dep conf/bccwj_dep_suw_rule.json
```

## 長単位情報つき単語のフォーマットの仕様

下記に揃えていく

<https://github.com/masayu-a/UD_Japanese-GSDPUD-CaboCha>

```text
3列目：長単位書字形出現形
    空列だった場合、短単位中での長単位の先頭の語ではない
```

### 現行対応状況

徐々に対応

- BCCWJ: ×
- GSD: ×

（詳しい説明は適宜）
