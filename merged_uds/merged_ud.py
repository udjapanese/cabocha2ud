# -*- coding: utf-8 -*-

"""
Library for merged some Japanese UDs (SUW, LUW, IBM)
"""

from typing import Iterator, NamedTuple, Union, Optional
from dataclasses import dataclass


COLUMN: list[str] = ["ID", "FORM", "LEMMA", "UPOS", "XPOS", "FEATS", "HEAD", "DEPREL", "DEPS", "MISC"]
ID, FORM, LEMMA, UPOS, XPOS, FEATS, HEAD, DEPREL, DEPS, MISC = range(len(COLUMN))


class Range(NamedTuple):
    start: int
    end: int


@dataclass
class Token:
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

    def __getitem__(self, x: Union[str, int]):
      if isinstance(x, int):
        x = COLUMN[x]
      return getattr(self, x)

    def __setitem__(self, x: str, y: Union[str, int]):
      if isinstance(x, int):
        x = COLUMN[x]
      setattr(self, x, y)

    def get_misc(self) -> dict[str, str]:
        _misc = self[MISC]
        return dict([m.split("=") for m in _misc.split("|")])

    def get_char_range(self):
        return self._char_pos

    def has_range(self, rng: Range):
        return self._char_pos.start <= rng.start and rng.end <= self._char_pos.end


class Sentence:
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
        conllu_s: list[str] = []
        for label in self.attrs_label:
            conllu_s.append("# {} = {}".format(label, self.attrs[label]))
        for tokens in self.sent:
            conllu_s.append(str(tokens))
        return "\n".join(conllu_s) + "\n"

    def has_token(self, tok1: Token, tok2: Token):
        return tok1.has_range(tok2.get_char_range())

    def get_token(self, indx: Union[int, str]) -> Token:
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
        return [token for token in self][rng.start:rng.end]

    def get_sentid(self) -> str:
        assert "sent_id" in self.attrs
        return self.attrs["sent_id"]

    def detect_senttype(self) -> str:
        assert "sent_id" in self.attrs
        if "_" in self.attrs["sent_id"]:
            return "bccwj"
        else:
            return "gsd"

    def get_text(self, remove_sp: bool=False) -> str:
        assert "text" in self.attrs
        if remove_sp:
            sp = {"bccwj": "　", "gsd": " "}[self.detect_senttype()]
            return self.attrs["text"].replace(sp, "")
        return self.attrs["text"]


class MatchedSentence(NamedTuple):
    sent1: Sentence
    sent2: Sentence
    tok_range_pair: list[tuple[Range, Range]]

    def get_senttype(self):
        return self.sent1.detect_senttype()

    def iter_merged_token(self) -> Iterator[tuple[list[Token], list[Token]]]:
        """ 対応付けされたトークンを返す

        Yields:
            Iterator[tuple[list[Token], Token]]: _description_
        """
        for tok1_range, tok2_range in self.tok_range_pair:
            yield self.sent1.get_tokens_from_range(tok1_range), self.sent2.get_tokens_from_range(tok2_range)


def merge_sentence(sent1: Sentence, sent2: Sentence, skip: bool=False) -> Optional[list[tuple[Range, Range]]]:
    if sent1.get_text(remove_sp=True) != sent2.get_text(remove_sp=True):
        if not skip:
            assert sent1.get_text(remove_sp=True) == sent2.get_text(remove_sp=True), "{} != {}".format(
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
                assert get_substr(sent1, apos, len(sent1)) == get_substr(sent2, bpos, len(sent2)), (get_substr(sent1, apos, len(sent1)), get_substr(sent2, bpos, len(sent2)))
                match_pair.append((Range(apos, len(sent1)), Range(bpos, len(sent2))))
                break
            else:
                assert get_substr(sent1, apos, cpos) == get_substr(sent2, bpos, dpos), (apos, cpos, bpos, dpos, get_substr(sent1, apos, cpos), get_substr(sent2, bpos, dpos))
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
    with open(conll_file, "r") as rdr:
        for line in rdr:
            line  = line.rstrip("\n")
            if line == "":
                yield Sentence(attrs, attrs_label, stack)
                attrs, stack, attrs_label = {}, [], []
                continue
            if line.startswith("# "):
                k = line.replace("# ", "").split("=")[0]
                v = "=".join(line.replace("# ", "").split("=")[1:])
                attrs[k.strip(" ")] = v.strip(" ").strip("　")
                attrs_label.append(k.strip(" "))
            else:
                line_data: dict[str, str] = dict(zip(COLUMN, line.split("\t")))
                end += len(line_data["FORM"])
                if "SpaceAfter=Yes" in line_data["MISC"]:
                    end += 1
                stack.append(Token(_char_pos=Range(start, end), **line_data))
                start = end


def get_matched_sentence(ud1_file: str, ud2_file: str) -> list[MatchedSentence]:
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
