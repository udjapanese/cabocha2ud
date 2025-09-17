# cabocha2ud

## 動作環境

Python3.13（3.13.X）にて動作確認済み。
pipで必要なライブラリをインストールします

```zsh
pip install configargparse pyyaml tqdm ruamel.yaml tomli
```

Pipenvを導入済みの場合、Pipfileで上記ライブラリがインストール可能

```zsh
pipenv install
```

## 動かし方

現在入力には、長単位データつきのcabochaファイルが必要です。
フォーマットは以下を確認してください。

```zsh
python -m cabocha2ud [長単位つきcabochaファイル] -c conf/(default|bccwj|gsd)_suw_args.yaml -w [出力ファイル名(指定しない場合は標準出力)]
```

`conf/(default|bccwj|gsd)_suw_args.yaml`などを使います。
（現在コーパスで若干変換内容が異なるなどがあり、コーパスごとで設定が分かれています）

以下のスクリプトで一括変換できます
(`parallel`コマンドを使っているため、ない場合自力でお願いします）

```shell
./scripts/convert_ud.sh -w [WORK_DIR] -c [CONF_FILE]
```

- `WORK_DIR`: 変換したいcabochaファイルが入っていてUDを保存するディレクトリ
  - `$WORK_DIR/cabocha`: 変換したいcabochaファイルを入れる
- `CONF_FILE`: 変換設定ファイル (`conf/default_suw_args.yaml`)

## CONF_FILEの中身

CONF_FILEの中身は以下のようになっています

```yaml
skip-space: True
space-marker: hankaku
pipeline: extract_sp_to_cabocha,merge_number,change_dep_det,replace_multi_root
rep-multi-root-mode: convert
```

長単位の場合、`pipeline`に`build_luw`を指定します。（変更予定）

```yaml
skip-space: True
space-marker: hankaku
pipeline: extract_sp_to_cabocha,merge_number,change_dep_det,build_luw,replace_multi_root
rep-multi-root-mode: convert
```

## 変換ルールについて

プログラム全体が分からなくても、とりあえず以下のyamlファイルを参照して書き直してもらうだけでもおおまかなルールは変更されます。
（係り関係の入れ替えなどには現状別個対応しているため、プログラムの書き換えがいります）
ルールは上から順番に対応がとれたものを先に採用して返します。

```text
conf/pos_suw_rule.yaml: UD POSの変換
conf/dep_suw_rule.yaml: UD labelの変換
```

### 変換ルール詳細

#### UD POS編

`rule:`以下に以下のような表現を追加することでルールが追加されます。
ルールは上から先に適応できたものを返します。

```yaml
- rule

# ルール (「品詞が"^動詞-.*"で、かつ文節のタイプがROOT」ならば「VERB」)
- - pos: "^動詞-.*"
    bpos: ROOT
  - - VERB

# ルール (「品詞が"^動詞-.*"で、かつ文節のタイプがSEM_HEAD」ならば「VERB」)
- - pos: "^動詞-.*"
    bpos: SEM_HEAD
  - - VERB

# ルール (「品詞が"^形容詞-非自立可能"で、かつ長単位の品詞が助動詞」ならば「AUX」)
- - pos: "^形容詞-非自立可能"
    luw: "助動詞"
  - - AUX

...
```

現在使えるルール名は以下のとおりです。

```yaml
- pos           # （短単位の）品詞 (正規表現)
- base_lexeme   # （短単位の）原型 (文字列)
- luw           # 長単位の品詞 (正規表現)
- bpos          # BunsetuPositionType (文字列)
- parent_upos   # かかり先の（短単位の）品詞 (正規表現)
```

#### UD label編

`order_rule:` 以降に以下のようにルールを追加していくことでルールが追加されます
上のルールが優先になります。YAMLのコメントも参照ください。

サンプル

```yaml
order_rule:

# ROOTはroot
- rule: [
    [include_word_bpos, ["ROOT"]],
  ]
  res: root


# NO_HEADのためのルール
- rule: [
    [include_word_bpos, ["NO_HEAD"]],
    [match_word_depnum, 0],
  ]
  res: root


# PUNCTはpunct
- rule: [
    [include_word_upos, ["PUNCT"]],
  ]
  res: punct

....
```

ひとつのルールは以下のように書きます。ルール名は必ず`func_args_elements`という形になります。

```yaml

- rule: [
     [ルール1の名前名, 引数(正規表現or文字列or配列)],
     [ルール2の名前名, 引数(正規表現or文字列or配列)],
     ....
   ]
   res: UD label名

```

ルール名は以下の通りで構成されています。ただし実装されているのとないのがあるのでない場合現状エラーを吐くかと思います。

```yaml

#  ルールの書き方
#  すべてのルールは  `func`_`args`_`elements`で構成されている
#  argsからelementsを取り出した中でfuncの形で該当するならば、と読み替える
# （実装されてないものはルールファイル読み込み時点でエラーになる）

func:
- include    # 指定したリストのいずれかに該当する、かならず引数は配列[]
- match      # 指定したリストのいずれかに該当する、かならず引数は文字列（か数字）
- regex      # 指定したリストのいずれかに該当する、かならず引数は正規表現

args:
# word: 対象自身
- word
# parent: wordの親
- parent
# semhead: wordを含んでいる文節のSEM_HEADであるword
- semhead
# synhead: wordを含んでいる文節のSYN_HEADであるword
- synhead
# child: wordを親とする子単語のリスト（そのうちのひとつが該当すればよい）
- child
# parentchild: wordを親とする子単語のリスト（そのうちのひとつが該当すればよい）
- parentchild

elements:
# 文節タイプ: bpos (ex. SEM_HEAD, SYM_HEAD, FUNC, CONT....)
- bpos
# 日本語（短単位）品詞: xpos (ex. "助詞-格助詞", "接続詞"...)
- xpos
# 日本語原型: lemma (ex. "だ", "と", "ない", ...)
- lemma
# UD品詞: upos (ex. ROOT, ADP, ...)
- upos
# かかり先の番号 (現状0以外使えない)
- depnum
# segment (拡張CabochaのSegment, ex. "Disfluency")
- segment
# 文末表現 suffixstring: (該当のwordの"文節末尾"文字列を確認している ex.)
- suffixstring
# 該当単語が(格)助詞の品詞を持っている  ※ include_child_caseでの （子の単語の中に該当する助詞があるか） 使用想定
- case
```

- `bpos`: 対象の単語が文節タイプ`bpos`を持っている
  - ex. `[include_word_bpos, ["SEM_HEAD", "CONT"]]`: 対象単語wordが文節タイプ`SEM_HEAD`か`CONT`であればマッチ
- `depnum`: wordの掛かり先番号（親の単語の番号）が指定の番号である（差などを見ているわけではないのでROOTである0以外では現状使えないと思われる）
  - ex. `[match_word_depnum, 0]`: wordの掛かり先が0だ
- `suffixstring`: 対象の単語の「文節の末尾表現」が「S」である
  - ex. `[regex_word_suffixstring, "^.*だと$"]` : 対象単語wordの文節末尾表現が「XXだと」という形であればマッチ
- `case` : 対象の単語が「（係格副）助詞」の品詞である単語であればマッチ
  - ex. `[include_child_case, ["と"]]` : 格助詞「と」が子（child）単語にあればマッチ
  - ※ 品詞の確認だけなら `(xpos|luwpos)` 辺りを使えばいいので `include_child_case`（子の単語の中に該当する助詞があるか）での想定

## 長単位情報つき単語のフォーマットの仕様

下記に揃えていく、フォーマットは以下参照

<https://github.com/udjapanese/UD-Japanese-GSDPUD-Cabocha>
