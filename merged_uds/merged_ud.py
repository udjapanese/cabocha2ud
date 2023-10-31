# -*- coding: utf-8 -*-

"""
Library for merged some Japanese UDs (SUW, LUW, IBM)
"""

from dataclasses import dataclass
from typing import Iterator, NamedTuple, Optional, Union

COLUMN: list[str] = [
    "ID", "FORM", "LEMMA", "UPOS", "XPOS", "FEATS", "HEAD", "DEPREL", "DEPS", "MISC"
]
ID, FORM, LEMMA, UPOS, XPOS, FEATS, HEAD, DEPREL, DEPS, MISC = range(len(COLUMN))


class Range(NamedTuple):
    """ Range class """
    start: int
    end: int


@dataclass
class Token:
    """ Token class """
    # pylint: disable=invalid-name
    ID: str
    FORM: str
    LEMMA: str
    UPOS: str
    XPOS: str
    FEATS: str
    HEAD: str
    DEPREL: str
    DEPS: str
    MISC: str
    _char_pos: Range

    def __iter__(self):
        return (self[c] for c in COLUMN)

    def __str__(self) -> str:
        return "\t".join([self[c] for c in COLUMN])

    def __getitem__(self, xxx: Union[str, int]):
        if isinstance(xxx, int):
            xxx = COLUMN[xxx]
        return getattr(self, xxx)

    def __setitem__(self, xxx: str, yyy: Union[str, int]):
        if isinstance(xxx, int):
            xxx = COLUMN[xxx]
        setattr(self, xxx, yyy)

    def get_misc(self) -> dict[str, str]:
        """ get misc """
        _misc = self[MISC]
        return dict([m.split("=") for m in _misc.split("|")])

    def get_char_range(self):
        """ char range """
        return self._char_pos

    def has_range(self, rng: Range):
        """ has range """
        return self._char_pos.start <= rng.start and rng.end <= self._char_pos.end


class Sentence:
    """ Sentence object """
    def __init__(self, attrs: dict[str, str], attrs_label: list[str], sents: list[Token]) -> None:
        self.attrs: dict[str, str] = attrs
        self.attrs_label: list[str] = attrs_label
        self.sent: list[Token] = sents
        assert "sent_id" in self.attrs
        assert "text" in self.attrs

    def __len__(self) -> int:
        return len(self.sent)

    def __iter__(self):
        return iter(self.sent)

    def __getitem__(self, item: int) -> Token:
        return self.sent[item]

    def to_conllu(self) -> str:
        """ to conllu """
        conllu_s: list[str] = []
        for label in self.attrs_label:
            conllu_s.append("# {} = {}".format(label, self.attrs[label]))
        for tokens in self.sent:
            conllu_s.append(str(tokens))
        return "\n".join(conllu_s) + "\n"

    def has_token(self, tok1: Token, tok2: Token):
        """ has token """
        return tok1.has_range(tok2.get_char_range())

    def get_token(self, indx: Union[int, str]) -> Token:
        """ get token """
        if isinstance(indx, str):
            indx = int(indx)
        if indx == 0:
            return Token(
                ID="0", FORM="ROOT", LEMMA="_", UPOS="_", XPOS="_",
                FEATS="_", HEAD="_", DEPREL="_", DEPS="_", MISC="_",
                _char_pos=Range(0, 0)
            )
        return self.sent[indx-1]

    def get_tokens_from_range(self, rng: Range) -> list[Token]:
        """ get tokens from range """
        return list(self)[rng.start:rng.end]

    def get_sentid(self) -> str:
        """" get sent_id """
        assert "sent_id" in self.attrs
        return self.attrs["sent_id"]

    def detect_senttype(self) -> str:
        """ detect senttype """
        assert "sent_id" in self.attrs
        if "_" in self.attrs["sent_id"]:
            return "bccwj"
        return "gsd"

    def get_text(self, remove_sp: bool=False) -> str:
        """ get text """
        assert "text" in self.attrs
        if remove_sp:
            ssp = {"bccwj": "　", "gsd": " "}[self.detect_senttype()]
            return self.attrs["text"].replace(ssp, "")
        return self.attrs["text"]


class MatchedSentence(NamedTuple):
    """ Matched Sentence object """
    sent1: Sentence
    sent2: Sentence
    tok_range_pair: list[tuple[Range, Range]]

    def get_senttype(self):
        """ get sent type """
        return self.sent1.detect_senttype()

    def iter_merged_token(self) -> Iterator[tuple[list[Token], list[Token]]]:
        """ 対応付けされたトークンを返す

        Yields:
            Iterator[tuple[list[Token], Token]]: _description_
        """
        for tok1_range, tok2_range in self.tok_range_pair:
            yield self.sent1.get_tokens_from_range(tok1_range),\
                self.sent2.get_tokens_from_range(tok2_range)


def merge_sentence(
    sent1: Sentence, sent2: Sentence, skip: bool=False
) -> Optional[list[tuple[Range, Range]]]:
    """ merge sentence """
    if sent1.get_text(remove_sp=True) != sent2.get_text(remove_sp=True):
        if not skip:
            assert sent1.get_text(remove_sp=True) == sent2.get_text(remove_sp=True),\
                "{} != {}".format(
                    sent1.get_text(remove_sp=True), sent2.get_text(remove_sp=True)
                )
        else:
            return None
    def get_substr(sent: Sentence, spos: int, epos: int) -> str:
        return "".join([t.FORM for t in sent][spos:epos]).replace(" ", "").replace("　", "")
    apos: int = 0
    bpos: int = 0
    match_pair: list[tuple[Range, Range]] = []
    while apos < len(sent1) and bpos < len(sent2):
        if sent1[apos].FORM == sent2[bpos].FORM:
            match_pair.append((Range(apos, apos+1), Range(bpos, bpos+1)))
            apos += 1
            bpos += 1
        else:
            cpos: int = apos + 1
            dpos: int = bpos + 1
            while cpos <  len(sent1) and dpos < len(sent2):
                csent, dsent = get_substr(sent1, apos, cpos), get_substr(sent2, bpos, dpos)
                if csent == dsent:
                    break
                if len(csent) < len(dsent):
                    cpos += 1
                elif len(csent) > len(dsent):
                    dpos += 1
                else:
                    assert ValueError("{} or {} ?".format(csent, dsent))
            if cpos >= len(sent1) or dpos >= len(sent2):
                assert get_substr(sent1, apos, len(sent1)) == get_substr(sent2, bpos, len(sent2)),\
                    (get_substr(sent1, apos, len(sent1)), get_substr(sent2, bpos, len(sent2)))
                match_pair.append((Range(apos, len(sent1)), Range(bpos, len(sent2))))
                break
            assert get_substr(sent1, apos, cpos) == get_substr(sent2, bpos, dpos),\
                (apos, cpos, bpos, dpos,
                    get_substr(sent1, apos, cpos), get_substr(sent2, bpos, dpos))
            match_pair.append((Range(apos, cpos), Range(bpos, dpos)))
            apos = cpos
            bpos = dpos
    return match_pair


def separate_sentence(conll_file: str) -> Iterator[Sentence]:
    """
        separete conll file by documents.
    """
    stack: list[Token] = []
    attrs: dict[str, str] = {}
    attrs_label: list[str] = []
    start, end = 0, 0
    with open(conll_file, "r", encoding="utf-8") as rdr:
        for line in rdr:
            line  = line.rstrip("\n")
            if line == "":
                yield Sentence(attrs, attrs_label, stack)
                attrs, stack, attrs_label = {}, [], []
                continue
            if line.startswith("# "):
                kkk = line.replace("# ", "").split("=")[0]
                vvv = "=".join(line.replace("# ", "").split("=")[1:])
                attrs[kkk.strip(" ")] = vvv.strip(" ").strip("　")
                attrs_label.append(kkk.strip(" "))
            else:
                line_data: dict[str, str] = dict(zip(COLUMN, line.split("\t")))
                end += len(line_data["FORM"])
                if "SpacesAfter=Yes" in line_data["MISC"]:
                    end += 1
                stack.append(Token(_char_pos=Range(start, end), **line_data))
                start = end


def get_matched_sentence(ud1_file: str, ud2_file: str) -> list[MatchedSentence]:
    """ get matched sentence """
    ud1_sents, ud2_sents = list(separate_sentence(ud1_file)), list(separate_sentence(ud2_file))
    matched_sent_data: list[MatchedSentence] = []
    assert len(ud1_sents) == len(ud2_sents)
    for ud1, ud2 in zip(ud1_sents, ud2_sents):
        rlist = merge_sentence(ud1, ud2)
        assert rlist is not None
        matched_sent_data.append(MatchedSentence(ud1, ud2, rlist))
    return matched_sent_data


def _main():
    pass


if __name__ == '__main__':
    _main()
