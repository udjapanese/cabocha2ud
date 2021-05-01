# Ginzaによる長単位解析メモ

## とりあえず

- モデルがよければ`./ginza_dummy_tok_test.sh`で長単位解析ができそう

## 訓練

固有表現抽出ラベルを長単位として置き換えることで長単位解析を実現している（と思う）
具体的には以下のデータを訓練として与えている（と思う）
（Uがひとつ、Bが先頭、Lが途中）

```text
ホッケー  U-名詞-普通名詞-一般
に   U-助詞-格助詞
は  U-助詞-係助詞
デンジャラス B-名詞-普通名詞-一般
プレー  L-名詞-普通名詞-一般
の     U-助詞-格助詞
```

### 訓練の事前準備

[ここから](https://github.com/megagonlabs/ginza/blob/develop/ginza_util/conllu_to_json.py )、`conllu_to_json.py`ダウンロードしておく。
`models/ja_vectors_chive_mc90_35k`を[ここから](https://github.com/megagonlabs/ginza/releases/tag/ja_luw-4.0.0 )からダウンロードして、`models`ディレクトリにおいておく。

### 訓練コマンド

```shell
> pip install -U ginza
> python conllu_to_json.py -l -e train.conllu > train.luw.json
> python conllu_to_json.py -l -e dev.conllu > dev.luw.json
> python -m spacy train ja models/ja_luw-4.0.0 train.luw.json dev.luw.json -v models/ja_vectors_chive_mc90_35k/ --gold-preproc -n 50 -V 4.0.0
```

上を実行するとモデルディレクトリとして`models/ja_luw-4.0.0`される。

## テスト

### テストの事前準備

1. [ここから](https://github.com/megagonlabs/ginza/releases/tag/ja_luw-4.0.0 ) `dummy_sudachipy.20200911-1.tgz`をダウンロードして`sudachipy`ディレクトリを作成（(実行ディレクトリに`sudachipy`があって上書きされる）
2. このディレクトリにある`tokenizer.py`を`sudachipy`へ入れて上書きしておく（BCCWJのテストデータ用に小さい修正）

### 実行

入力フォーマットはひとまずUD_Japanese-GSDPUD-CaboChaと同じCabocha形式である。
`merge_online_sent.py`によって`ginza`へ入力できるフォーマットにする。
（ginzaが一文一行としてしか読み込まない（？）ため1文一行で情報をまとめる必要がある）
以下を実行するとtest.conlluが生成される。

```shell
> ./ginza_dummy_tok_test.sh -i test.cabocha -o test.conllu -m 学習したモデル
```

### 出力

`test.conllu`の中身は以下のとおり。これの`ENE`が長単位情報（のはず）

```text
# text = これに不快感を示す住民はいましたが,現在,表立って反対や抗議の声を挙げている住民はいないようです。
1    これ    コレ    PRON    代名詞    _    9    obl_bunsetu    _    SpaceAfter=No|Inf=,,,此れ,これ,コレ,これ,,和,,,,,,,,,,,コレ,,,,3599534815060480,13095|Reading=これ|NE=B-OTHERS|ENE=B-代名詞
2    に    ニ    ADP    助詞-格助詞    _    1    case    _    SpaceAfter=No|Inf=,,,に,に,ニ,に,,和,,,,,,,,,,,ニ,,,,7745518285496832,28178|Reading=に|NE=B-OTHERS|ENE=B-助詞-格助詞
3    不快    フカイ    NOUN    名詞-普通名詞-形状詞可能    _    4    compound    _    SpaceAfter=No|Inf=,,,不快,不快,フカイ,不快,,漢,,,,,,,,,,,フカイ,,,,8938488401633792,32518|Reading=不快|NE=B-OTHERS|ENE=B-名詞-普通名詞-一般
4    感    カン    NOUN    名詞-普通名詞-一般    _    6    obj_bunsetu    _    SpaceAfter=No|Inf=,,,感,感,カン,感,,漢,,,,,,,,,,,カン,,,,2050322931524096,7459|Reading=感|NE=I-OTHERS|ENE=I-名詞-普通名詞-一般
5    を    ヲ    ADP    助詞-格助詞    _    4    case    _    SpaceAfter=No|Inf=,,,を,を,オ,を,,和,,,,,,,,,,,ヲ,,,,11381878116459008,41407|Reading=を|NE=B-OTHERS|ENE=B-助詞-格助詞
6    示す    シメス    VERB    動詞-一般    _    7    acl_bunsetu    _    SpaceAfter=No|Inf=五段-サ行,連体形-一般,,示す,示す,シメス,示す,,和,,,,,,,,,,,シメス,,,,4340055929922241,15789|Reading=示す|NE=B-OTHERS|ENE=B-動詞-一般
7    住民    ジュウミン    NOUN    名詞-普通名詞-一般    _    9    nsubj_bunsetu    _    SpaceAfter=No|Inf=,,,住民,住民,ジューミン,住民,,漢,,,,,,,,,,,ジュウミン,,,,5014056524194304,18241|Reading=住民|NE=B-OTHERS|ENE=B-名詞-普通名詞-一般
8    は    ハ    ADP    助詞-係助詞    _    7    case    _    SpaceAfter=No|Inf=,,,は,は,ワ,は,,和,,,,,,,,,,,ハ,,,,8059703733133824,29321|Reading=は|NE=B-OTHERS|ENE=B-助詞-係助詞
9    い    イル    VERB    動詞-非自立可能    _    29    advcl_bunsetu    _    SpaceAfter=No|Inf=上一段-ア行,連用形-一般,,居る,い,イ,いる,,和,,,,,,,,,,,イル,,,,710568013079169,2585|Reading=い|NE=B-OTHERS|ENE=B-動詞-一般
10    まし    マス    AUX    助動詞    _    9    aux    _    SpaceAfter=No|Inf=助動詞-マス,連用形-一般,,ます,まし,マシ,ます,,和,,,,,,,,,,,マス,,,,9812325267808897,35697|Reading=まし|NE=B-OTHERS|ENE=B-助動詞
11    た    タ    AUX    助動詞    _    9    aux    _    SpaceAfter=No|Inf=助動詞-タ,終止形-一般,,た,た,タ,た,,和,,,,,,,,,,,タ,,,,5948916285711019,21642|Reading=た|NE=B-OTHERS|ENE=B-助動詞
12    が    ガ    SCONJ    助詞-接続助詞    _    9    mark    _    SpaceAfter=No|Inf=,,,が,が,ガ,が,,和,,,,,,,,,,,ガ,,,,2168245553603072,7888|Reading=が|NE=B-OTHERS|ENE=B-助詞-接続助詞
13    ,    ,    PUNCT    補助記号-読点    _    9    punct    _    SpaceAfter=No|Inf=,,,，,,,,,,,記号,,,,,,,,,,,,,,,13752552530432,50|Reading=,|NE=B-OTHERS|ENE=B-補助記号-読点
14    現在    ゲンザイ    NOUN    名詞-普通名詞-副詞可能    _    24    advmod_bunsetu    _    SpaceAfter=No|Inf=,,,現在,現在,ゲンザイ,現在,,漢,,,,,,,,,,,ゲンザイ,,,,3206742875972096,11666|Reading=現在|NE=B-OTHERS|ENE=B-副詞
15    ,    ,    PUNCT    補助記号-読点    _    14    punct    _    SpaceAfter=No|Inf=,,,，,,,,,,,記号,,,,,,,,,,,,,,,13752552530432,50|Reading=,|NE=B-OTHERS|ENE=B-補助記号-読点
16    表立っ    オモテダツ    VERB    動詞-一般    _    24    advcl_bunsetu    _    SpaceAfter=No|Inf=五段-タ行,連用形-促音便,,表立つ,表立っ,オモテダッ,表立つ,,和,,,,,,,,,,,オモテダツ,,,,1449164949037700,5272|Reading=表立っ|NE=B-OTHERS|ENE=B-動詞-一般
17    て    テ    SCONJ    助詞-接続助詞    _    16    mark    _    SpaceAfter=No|Inf=,,,て,て,テ,て,,和,,,,,,,,,,,テ,,,,6837321680953856,24874|Reading=て|NE=B-OTHERS|ENE=B-助詞-接続助詞
18    反対    ハンタイ    NOUN    名詞-普通名詞-サ変形状詞可能    _    20    nmod_bunsetu    _    SpaceAfter=No|Inf=,,,反対,反対,ハンタイ,反対,,漢,,,,,,,,,,,ハンタイ,,,,8356022116819456,30399|Reading=反対|NE=B-OTHERS|ENE=B-名詞-普通名詞-一般
19    や    ヤ    ADP    助詞-副助詞    _    18    case    _    SpaceAfter=No|Inf=,,,や,や,ヤ,や,,和,,,,,,,,,,,ヤ,,,,10468183953777152,38083|Reading=や|NE=B-OTHERS|ENE=B-助詞-副助詞
20    抗議    コウギ    NOUN    名詞-普通名詞-サ変可能    _    22    nmod_bunsetu    _    SpaceAfter=No|Inf=,,,抗議,抗議,コーギ,抗議,,漢,,,,,,,,,,,コウギ,,,,3293595704631808,11982|Reading=抗議|NE=B-OTHERS|ENE=B-名詞-普通名詞-一般
21    の    ノ    ADP    助詞-格助詞    _    20    case    _    SpaceAfter=No|Inf=,,,の,の,ノ,の,,和,,,,,,,,,,,ノ,,,,7968444268028416,28989|Reading=の|NE=B-OTHERS|ENE=B-助詞-格助詞
22    声    コエ    NOUN    名詞-普通名詞-一般    _    24    obj_bunsetu    _    SpaceAfter=No|Inf=,,,声,声,コエ,声,,和,,,,,,,,,,,コエ,,,,3423612954616320,12455|Reading=声|NE=B-OTHERS|ENE=B-名詞-普通名詞-一般
23    を    ヲ    ADP    助詞-格助詞    _    22    case    _    SpaceAfter=No|Inf=,,,を,を,オ,を,,和,,,,,,,,,,,ヲ,,,,11381878116459008,41407|Reading=を|NE=B-OTHERS|ENE=B-助詞-格助詞
24    挙げ    アゲル    VERB    動詞-非自立可能    _    27    acl_bunsetu    _    SpaceAfter=No|Inf=下一段-ガ行,連用形-一般,,上げる,挙げ,アゲ,挙げる,,和,,,,,,,,,,,アゲル,,,,144044747530881,524|Reading=挙げ|NE=B-OTHERS|ENE=B-動詞-一般
25    て    テ    SCONJ    助詞-接続助詞    _    24    mark    _    SpaceAfter=No|Inf=,,,て,て,テ,て,,和,,,,,,,,,,,テ,,,,6837321680953856,24874|Reading=て|NE=B-OTHERS|ENE=B-助動詞
26    いる    イル    AUX    動詞-非自立可能    _    25    fixed    _    SpaceAfter=No|Inf=上一段-ア行,連体形-一般,,居る,いる,イル,いる,,和,,,,,,,,,,,イル,,,,710568013079233,2585|Reading=いる|NE=I-OTHERS|ENE=I-助動詞
27    住民    ジュウミン    NOUN    名詞-普通名詞-一般    _    29    nsubj_bunsetu    _    SpaceAfter=No|Inf=,,,住民,住民,ジューミン,住民,,漢,,,,,,,,,,,ジュウミン,,,,5014056524194304,18241|Reading=住民|NE=B-OTHERS|ENE=B-名詞-普通名詞-一般
28    は    ハ    ADP    助詞-係助詞    _    27    case    _    SpaceAfter=No|Inf=,,,は,は,ワ,は,,和,,,,,,,,,,,ハ,,,,8059703733133824,29321|Reading=は|NE=B-OTHERS|ENE=B-助詞-係助詞
29    い    イル    VERB    動詞-非自立可能    _    0    root    _    SpaceAfter=No|Inf=上一段-ア行,未然形-一般,,居る,い,イ,いる,,和,,,,,,,,,,,イル,,,,710568013079105,2585|Reading=い|NE=B-OTHERS|ENE=B-動詞-一般
...
```

### 結果

以下実行でひとまず結果がでる。

```shell
> python show_luw_result.py test.cabocha test.conllu
```

ラベルと区間が一致しているか（LAS）と区間が一致しているか（UAS）しか現状計算してない。
