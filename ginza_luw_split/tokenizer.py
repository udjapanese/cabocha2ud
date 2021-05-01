from enum import Enum

from spacy.lang import ja
from spacy.symbols import POS, PUNCT, INTJ, ADJ, AUX, ADP, PART, SCONJ, NOUN
from spacy.symbols import SYM, PRON, VERB, ADV, PROPN, NUM, DET, SPACE, CCONJ
from spacy.lang.ja import TAG_MAP
for k, v in {
    "URL": {POS: SYM},
    "英単語": {POS: PROPN},
    "web誤脱": {POS: NOUN},
    "言いよどみ": {POS: NOUN}
}.items():
    TAG_MAP[k] = v

def dummy_dtokens_and_spaces(dtokens, text, gap_tag="空白"):
    text = "".join([x.surface for x in dtokens])
    return origin_get_dtokens_and_spaces(dtokens, text, gap_tag)

origin_get_dtokens_and_spaces = ja.get_dtokens_and_spaces
ja.get_dtokens_and_spaces = dummy_dtokens_and_spaces

class Tokenizer:
    SplitMode = Enum("SplitMode", "A B C")

    def __init__(self, **dummy):
        # print("dummy SudachiPy tokenizer created", file=sys.stderr)
        pass

    def tokenize(self, text):
        fields = text.split("\t")
        return [Token(*fields[i * 4: i * 4 + 4]) for i in range(len(fields) // 4)]


class Token:
    def __init__(self, surface, pos, dictionary_form, reading_form):
        self._surface = surface
        self._pos = pos.split(",")
        self._dictionary_form = dictionary_form
        self._reading_form = reading_form

    def surface(self):
        return self._surface

    def part_of_speech(self):
        return self._pos

    def dictionary_form(self):
        return self._dictionary_form

    def reading_form(self):
        return self._reading_form

    def split(self, mode):
        return [self]
