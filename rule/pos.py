# -*- coding: utf-8 -*-

"""
RULE POS
"""


import re
import json

REGEX_TYPE = type(re.compile(''))
NUM_RE = re.compile(r"\* (\d+) (-?\d+)([A-Z][A-Z]?) (\d+)/(\d+) .*$")
BUNSETU_FUNC_MATCH_RE = re.compile(
    r"(?:助詞|助動詞|接尾辞,形容詞的|接尾辞,形状詞的|接尾辞,動詞的)"
)
BUNSETU_SUBJ_MATCH_RE = re.compile(
    r"(?!助詞|助動詞|接尾辞,形容詞的|接尾辞,形状詞的|接尾辞,動詞的|空白|補助記号|記号)"
)
BUNSETU_NOHEAD_MATCH_RE = re.compile(
    r"(?!空白|補助記号|記号|URL)"
)
POS_RULE_FILE = {
    # word unit mapping
    "bccwj_suw": "conf/bccwj_pos_suw_rule.json",
    "bccwj_luw": "conf/bccwj_pos_luw_rule.json",
    "gsd_suw": "conf/bccwj_pos_suw_rule.json",
    "chj_suw": "conf/chj_pos_suw_rule.json"
}
POS_RULE_FUNC = {
    "pos": re.compile,
    "base_lexeme": re.compile,
    "parent_upos":  re.compile,
    "usage": lambda x: x,
    "luw": lambda x: x,
    "bpos": lambda x: x  # BunsetuPositonType
}
TARGET_RULE = {"pos": None, "dep": None}


def load_pos_rule(data_type, word_unit):
    """
        load rule file
    """
    rule_set = json.load(open(POS_RULE_FILE[data_type + "_" + word_unit]))
    full_rule_set = []
    for rule_pair in rule_set["rule"]:
        rule, result = rule_pair
        nrule = {}
        for name, value in list(rule.items()):
            if name != "__comment":
                nrule[name] = POS_RULE_FUNC[name](value)
        full_rule_set.append((nrule, result))
    return full_rule_set


NEG_EXP = ["非", "不", "無", "未", "反", "異"]
def is_neg(word):
    """
        否定表現かどうか
    """
    pos, pos3, base_lexeme = word.get_xpos().split("-")[0], word.get_xpos(), word.origin
    if pos == "助動詞" and (base_lexeme == "ない" or base_lexeme == "ず"):
        return True
    elif re.search(r"接尾辞", pos3) and base_lexeme == "ない":
        return True
    elif re.search(r"接頭辞", pos3) and base_lexeme in NEG_EXP:
        return True
    elif re.search(r"形容詞", pos3) and base_lexeme == "無い":
        return True
    elif re.search(r"名詞", pos3) and base_lexeme == "無し":
        return True
    return False


def add_ud_feature(word):
    """
        UD 特徴をつける
    """
    if is_neg(word):
        word.ud_feat["Polarity"] = "Neg"
    if "英単語" in word.get_xpos():
        word.ud_feat["Foreign"] = "Yes"


def detect_ud_pos(word):
    """
        detect UD POS
    """
    if TARGET_RULE["pos"] is None:
        TARGET_RULE["pos"] = list(load_pos_rule(word.data_type, word.word_unit))
    word.en_pos = []
    add_ud_feature(word)
    if word.dep_num > 0:
        parent_word = word.doc[word.sent_pos].get_word_from_tokpos(word.dep_num-1)
    else:
        # ROOTのときはないためNone
        parent_word = None
    inst = {
        "pos": word.get_xpos(), "base_lexeme": word.origin, "luw": word.luw_pos,
        "usage": word.usage, "bpos": word.ud_misc["BunsetuPositionType"],
        "parent_upos": parent_word.get_ud_pos() if parent_word is not None else "THIS_ROOT"
    }
    for rule, en_pos in list(TARGET_RULE["pos"]):
        flag_lst = []
        for name in rule:
            if isinstance(rule[name], REGEX_TYPE):
                flag_lst.append(rule[name].match(inst[name]) is not None)
            else:
                flag_lst.append(rule[name] == inst[name])
        if all(flag_lst):
            word.en_pos.extend(en_pos)
            break


if __name__ == "__main__":
    pass
