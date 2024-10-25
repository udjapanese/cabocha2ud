"""RULE POS."""


import re
from typing import TYPE_CHECKING, Generator, NamedTuple, TypedDict, cast

from cabocha2ud.lib.yaml_dict import YamlDict

if TYPE_CHECKING:
    from cabocha2ud.bd.word import Word


REGEX_TYPE = type(re.compile(""))
BUNSETU_FUNC_MATCH_RE = re.compile(
    r"(?:助詞|助動詞|接尾辞,形容詞的|接尾辞,形状詞的|接尾辞,動詞的)"
)
BUNSETU_SUBJ_MATCH_RE = re.compile(
    r"(?!助詞|助動詞|接尾辞,形容詞的|接尾辞,形状詞的|接尾辞,動詞的|空白|補助記号|記号)"
)
BUNSETU_NOHEAD_MATCH_RE = re.compile(
    r"(?!空白|補助記号|記号|URL)"
)

POS_RULE_FILE = "conf/bccwj_pos_suw_rule.yaml"

POS_RULE_FUNC: dict = {
    "pos": re.compile,
    "base_lexeme": re.compile,
    "parent_upos":  re.compile,
    "luw": re.compile,
    "bpos": lambda x: x  # BunsetuPositonType
}
TARGET_POS_RULE = None

class POSRule(NamedTuple):
    """POS rule."""

    rule: dict[str, str]
    res: str


class POSRuleBase(TypedDict):
    """POS rule list."""

    default: list[str]
    rule: list[POSRule]


def load_pos_rule(file_name: str=POS_RULE_FILE) -> list[tuple]:
    """Load rule file."""
    rule_set: POSRuleBase = cast(POSRuleBase, dict(YamlDict(file_name=file_name, auto_load=True)))
    full_rule_set: list[tuple] = []
    for rule_pair in rule_set["rule"]:
        rule, result = rule_pair
        nrule = {}
        for name, value in list(rule.items()):
            if name != "__comment":
                nrule[name] = POS_RULE_FUNC[name](value)
        full_rule_set.append((nrule, result))
    return full_rule_set


NEG_EXP = ["非", "不", "無", "未", "反", "異"]
RE_NEG_SETUBI_EXP = re.compile(r"接尾辞")
RE_NEG_SETTOU_EXP = re.compile(r"接頭辞")
RE_NOUN_NEG_EXP = re.compile(r"名詞")
def is_neg(word: "Word") -> bool:
    """否定表現かどうか."""
    pos, pos3, base_lexeme = word.get_xpos().split("-")[0], word.get_xpos(), word.get_jp_origin()
    if pos == "助動詞" and base_lexeme in ["ない", "ず", "ぬ"]:
        return True
    if RE_NEG_SETUBI_EXP.search(pos3) and base_lexeme == "ない":
        return True
    if RE_NEG_SETTOU_EXP.search(pos3) and base_lexeme in NEG_EXP:
        return True
    return bool(RE_NOUN_NEG_EXP.search(pos3) and base_lexeme == "無し")


def add_ud_feature(word: "Word") -> None:
    """UD 特徴をつける."""
    if is_neg(word):
        word.ud_feat["Polarity"] = "Neg"
    if "英単語" in word.get_xpos():
        word.ud_feat["Foreign"] = "Yes"


def detect_ud_pos(word: "Word", target_pos_rule: list) -> None:
    """Detect UD POS."""
    word.en_pos = []
    add_ud_feature(word)
    inst = word.get_instance_for_pos()
    word.logger.debug(inst)
    word.logger.debug(target_pos_rule)
    for rule, en_pos in list(target_pos_rule):
        flag_lst: Generator[bool, None, None] = (
            rule[name].match(inst[name]) is not None
            if isinstance(rule[name], REGEX_TYPE)
            else rule[name] == inst[name]
            for name in rule
        )
        if all(flag_lst):
            word.en_pos.extend(en_pos)
            break


if __name__ == "__main__":
    pass
