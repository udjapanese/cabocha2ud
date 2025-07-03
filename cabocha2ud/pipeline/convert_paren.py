"""Modify dependencies regarding parenthesis in UD_Japanese-PUD."""

import argparse
from typing import Union

from cabocha2ud.lib.logger import Logger, LogLevel
from cabocha2ud.lib.yaml_dict import YamlDict
from cabocha2ud.pipeline.component import UDPipeLine
from cabocha2ud.ud import UniversalDependencies
from cabocha2ud.ud.util import Field

NEWLINE = "\n"

# Token class (copied from ud2lw.py)
class Token:
    """Token object."""

    def __init__(self, line: list[str]):
        self.id_: int = int(line[0])
        self.form_: str = line[1]
        self.lemma_: str = line[2]
        self.upos_: str = line[3]
        self.xpos_: str = line[4]
        self.feat_: str = line[5]
        self.head_: int = int(line[6])
        self.deprel_: str = line[7]
        self.deps_: str = line[8]
        self.misc_: str = line[9]

        self.line_: list[str] = line

    def __repr__(self) -> str:
        return str(self.id_) + self.form_ + str(self.head_)

    def to_conllu(self) -> str:
        """ to conllu """
        rtn_line = self.line_
        rtn_line[0] = str(self.id_)
        rtn_line[1] = self.form_
        rtn_line[2] = self.lemma_
        rtn_line[3] = self.upos_
        rtn_line[4] = self.xpos_
        rtn_line[5] = self.feat_
        rtn_line[6] = str(self.head_)
        rtn_line[7] = self.deprel_
        rtn_line[8] = self.deps_
        rtn_line[9] = self.misc_
        return "\t".join(rtn_line).strip()


# Sentence class (copied from ud2lw.py)
class Sentence:
    """Sentence object."""

    def __init__(self):
        self.sent_id_: str = ""
        self.text_: str = ""
        self.tokens_: list[Token] = []


def conv_paren(sentences: list[Sentence], logger: Logger) -> None:
    """Convert paren.

    （）を含んでいた場合に処理をする
    """
    paren_num, success_num = 0, 0
    for sent in sentences:
        for ttok in sent.tokens_:
            if ttok.form_ not in ["（" ,"("]:  # noqa: RUF001
                continue
            for tt1 in sent.tokens_[ttok.id_:]:
                if tt1.form_ not in ["）", ")"]:  # noqa: RUF001
                    continue
                paren_num += 1
                ret = convparen_sub(sent, ttok, tt1, logger)
                if ret:
                    success_num += 1
                break


def print_tokens(sent: Sentence, atk: Token, btk: Token, lgr: Logger, start: str="", end: str=""):
    """Print tokens."""
    if start != "":
        lgr.debug(start)
    for tok in sent.tokens_[atk.id_-1: btk.id_]:
        lgr.debug(tok.to_conllu())
    if end != "":
        lgr.debug(end)


def cleanup_before(
    sent: Sentence, prev: Token, open_t: Token, in_head: Token, close: Token, logger: Logger
) -> None:
    """Clean before."""
    for tok in sent.tokens_[:open_t.id_-1]:
        if tok.lemma_ in ["「", "『"] and tok.head_ >= close.id_:
            tok.head_ = tok.id_ + 1
        elif tok.lemma_ in ["」", "』"] and tok.head_ >= close.id_:
            tok.head_ = tok.id_ - 1
        if not (tok.head_ >= open_t.id_ and tok.head_ <= close.id_):
            continue
        logger.debug(
            prev.id_, prev.lemma_, prev.head_, tok.id_, tok.lemma_, tok.head_, in_head.id_
        )
        if prev.head_ == tok.id_:
            pass
        elif prev.head_ > close.id_ or prev.head_ == 0:
            tok.head_ = prev.id_
        else:
            tok.head_ = in_head.id_
        logger.debug("****XXXX")
        logger.debug(tok.to_conllu())


def cleanup_inside(sentence: Sentence, open_t: Token, in_head: Token, close: Token):
    """Cleanup inside."""
    for tok in sentence.tokens_[open_t.id_: close.id_ - 1]:
        if tok.head_ == open_t.id_:
            tok.head_ = tok.id_ + 1
            tok.deprel_ = "dep"
        if tok.head_ == close.id_:
            tok.head_ = in_head.id_


def cleanup_after(
    sentence: Sentence, prev: Token, open_t: Token, close: Token, logger: Logger
):
    """Cleanup after."""
    prev_head = prev.id_
    logger.debug("PREV: " , prev.id_ , "*********" , sentence.tokens_[prev.id_-1].lemma_)
    if sentence.tokens_[prev.id_-1].lemma_ == "さ":
        prev_head -= 1
        logger.debug("prev_head=", prev_head)
    for tok in sentence.tokens_[close.id_:]:
        if tok.head_ >= open_t.id_ and tok.head_ <= close.id_:
            tok.head_ = prev_head


def check_outgoing_nodes(sent: Sentence, open_t: Token, close_t: Token, lgr: Logger) -> list[Token]:
    """外に出ていくトークンを抽出する.

    Args:
        sentence (Sentence): _description_
        open_t (Token): _description_
        close_t (Token): _description_
        logger (Logger): _description_

    Returns:
        list[Token]: _description_

    """
    outgoing_nodes: list[Token] = []
    for tok in sent.tokens_[open_t.id_-1:close_t.id_]:
        # （）内部を確認、親がかっこの外にあるものを追加する
        lgr.debug(tok.to_conllu())
        if tok.head_ < open_t.id_ or tok.head_ > close_t.id_:
            if tok.head_ == 0:
                lgr.debug("===============ROOT")
            elif tok.head_ < open_t.id_:
                assert True, "back outside dependency"
            lgr.debug("OUTSIDE!")
            outgoing_nodes.append(tok)
    lgr.debug("---- outgoing_nodes -> " + str(len(outgoing_nodes)))
    return outgoing_nodes


def convparen_sub(sentence: Sentence, open_t: Token, close_t: Token, logger: Logger) -> bool:
    """ convert paren sub function """

    prev_t = sentence.tokens_[open_t.id_-1-1]
    if prev_t.upos_ == "PUNCT" and prev_t.lemma_ != "「":
        # 「XX/、/（」のときはXXに変更
        prev_t = sentence.tokens_[open_t.id_-1-2]
    elif prev_t.lemma_ == "た":
        # 「XX/た/（」のときはXXに
        prev_t = sentence.tokens_[prev_t.head_-1]

    # last_t は「XX/）」のXX
    last_t = sentence.tokens_[close_t.id_-1-1]

    print_tokens(sentence, prev_t, last_t, logger, start="--aaa--", end="----bbb---")
    print_tokens(sentence, open_t, close_t, logger, start="--ddd--", end="----eee---")

    inhead = last_t
    if last_t.head_ != close_t.id_:
        # かっこの最後の親が末尾かっこではないとき
        if last_t.head_ > open_t.id_ and last_t.head_ < close_t.id_:
            # ちゃんとかっこ内にヘッドがある
            for tok in sentence.tokens_[last_t.head_:close_t.id_-1]:
                assert tok.head_ == last_t.head_, "wrong inparenHead 0" + tok.to_conllu()
            inhead = sentence.tokens_[last_t.head_-1]
            if last_t.deprel_ == "fixed" and inhead.deprel_ == "case" and inhead.head_ > open_t.id_:
                inhead = sentence.tokens_[inhead.head_-1]
                logger.debug("****CHANGED INHEAD")
        else:
            # そうではない
            inhead = last_t
            if inhead.deprel_ == "punct":   #  for sent_id = w01020020
                sentence.tokens_[open_t.id_].upos_ = "NOUN"
                inhead.upos_ = "NOUN"
                logger.debug("****CHANGED INHEAD UPOS")

    logger.debug("inHead:" + inhead.to_conllu())
    logger.debug("prev:" + prev_t.to_conllu())

    outgoing_nodes: list[Token] = []
    for tok in sentence.tokens_[open_t.id_-1:close_t.id_]:
        # （）内部を確認、親がかっこの外にあるものを追加する
        logger.debug(tok.to_conllu())
        if tok.head_ < open_t.id_ or tok.head_ > close_t.id_:
            if tok.head_ == 0:
                logger.debug("===============ROOT")
            elif tok.head_ < open_t.id_:
                assert True, "back outside dependency"
            logger.debug("OUTSIDE!")
            outgoing_nodes.append(tok)
    logger.debug("---- outgoing_nodes -> " + str(len(outgoing_nodes)))

    if prev_t.deprel_ in ["case", "mark", "punct"] and prev_t.lemma_ not in ["さ"]:
        # forward modification
        logger.message("CASE!!!!!!", sentence.sent_id_, mode=LogLevel.DEBUG)
        open_t.head_ = inhead.id_
        open_t.deprel_ = "punct"
        close_t.head_ = inhead.id_
        close_t.deprel_ = "punct"
        if inhead.deprel_ == "compound":
            inhead.deprel_ = "nmod"
        elif inhead.deprel_ == "advcl":
            inhead.head_ = close_t.id_ + 1  # tentative!
        logger.debug(prev_t.head_)
        logger.debug(sentence.tokens_[prev_t.head_-1].to_conllu())
        if sentence.tokens_[prev_t.head_-1].head_ == prev_t.id_:
            assert False, "ERROR"
        cleanup_before(sentence, prev_t, open_t, inhead, close_t, logger)
        cleanup_inside(sentence, open_t, inhead, close_t)
        cleanup_after(sentence, prev_t, open_t, close_t, logger)

        print_tokens(sentence, prev_t, close_t, logger, start="===0===", end="^^^^")
        return True

    if len(outgoing_nodes) == 1:
        logger.debug("OUTGOING one ->", sentence.sent_id_)
        if outgoing_nodes[0] == close_t:
            if inhead.head_ == close_t.id_:
                outside_id = close_t.head_
                outside_deprel = close_t.deprel_
                close_t.head_ = inhead.id_
                close_t.deprel_ = "punct"
                inhead.head_ = prev_t.id_
                inhead.deprel_ = "appos"
                prev_t.head_ = outside_id
                prev_t.deprel_ = outside_deprel
                open_t.head_ = inhead.id_
                open_t.deprel_ = "punct"

                cleanup_before(sentence, prev_t, open_t, inhead, close_t, logger)
                cleanup_inside(sentence, open_t, inhead, close_t)
                cleanup_after(sentence, prev_t, open_t, close_t, logger)

                print_tokens(sentence, prev_t, close_t, logger, start="===1===", end="^^^^")
                return True
            elif prev_t.head_ > close_t.id_:
                open_t.head_ = last_t.id_
                open_t.deprel_ = "punct"
                last_t.head_ = prev_t.id_
                last_t.deprel_ = "appos"
                close_t.head_ = last_t.id_
                close_t.deprel_ = "punct"
                cleanup_before(sentence, prev_t, open_t, inhead, close_t, logger)
                cleanup_inside(sentence, open_t, inhead, close_t)
                cleanup_after(sentence, prev_t, open_t, close_t, logger)

                print_tokens(sentence, prev_t, close_t, logger, start="===2===", end="^^^^")
                return True
            else:
                assert True, "WHAT HAPPENS??---------"
        elif outgoing_nodes[0] == inhead:
            if prev_t.xpos_ == "助動詞":
                return True
            close_t.head_ = inhead.id_
            close_t.deprel_ = "punct"
            prev_t.head_ = inhead.head_
            prev_t.deprel_ = inhead.deprel_
            if inhead.deprel_ == "nummod":
                prev_t.deprel_ = "obl"
            inhead.head_ = prev_t.id_
            inhead.deprel_ = "appos"
            open_t.head_ = inhead.id_
            open_t.deprel_ = "punct"

            cleanup_before(sentence, prev_t, open_t, inhead, close_t, logger)
            cleanup_inside(sentence, open_t, inhead, close_t)
            cleanup_after(sentence, prev_t, open_t, close_t, logger)

            print_tokens(sentence, prev_t, close_t, logger, start="===5===", end="^^^^")
            return True
        else:
            assert True, "Wrong outgoing node"
    else:
        logger.debug("abc OUTGOING_NUM " + str(len(outgoing_nodes)))
        if open_t in outgoing_nodes:
            outgoing_nodes.remove(open_t)
        if close_t in outgoing_nodes:
            outgoing_nodes.remove(close_t)
        logger.debug("NEW OUTGOING_NUM " + str(len(outgoing_nodes)))
        if len(outgoing_nodes) > 1:
            for tok in outgoing_nodes[:-1]:
                tok.head_ = outgoing_nodes[-1].id_
                tok.deprel_ = "compound"
                if tok.upos_ in ["ADP","AUX"]:
                    tok.deprel_ = "dep"
        if outgoing_nodes[-1] == inhead:
            prev_cnt = prev_t
            if prev_t.lemma_ == "さ":
                prev_cnt = sentence.tokens_[prev_t.id_-2]
            logger.debug("PC", prev_cnt.to_conllu())
            logger.debug("IH", inhead.to_conllu())

            f_change_prev_cont_head = True

            if inhead.lemma_ == "た":
                f_change_prev_cont_head = False
                for iii in range(close_t.id_-1, open_t.id_+1, -1):
                    ttok = sentence.tokens_[iii-1]
                    if ttok.upos_ == "VERB":
                        inhead = sentence.tokens_[ttok.id_-1]
                        break
                for iii in range(close_t.id_ - 1, open_t.id_ + 1, -1):
                    ttok = sentence.tokens_[iii - 1]
                    if ttok.id_ == inhead.id_:
                        break
                    if ttok.upos_=="AUX":
                        ttok.deprel_ = "aux"
                    elif ttok.upos_=="SCONJ":
                        ttok.deprel_ = "mark"
                    ttok.head_ = inhead.id_

                for iii in range(open_t.id_ + 1, inhead.id_):
                    ttok = sentence.tokens_[iii - 1]
                    if ttok.id_ == inhead.id_:
                        break
                    if ttok.upos_=="PROPN":
                        ttok.deprel_ = "obl"
                        if sentence.tokens_[iii].lemma_ == "は":
                            ttok.deprel_ = "nsubj"
                        ttok.head_ = inhead.id_
                    elif ttok.upos_=="ADP":
                        ttok.deprel_ = "case"
                        ttok.head_ = ttok.id_-1
                    else:
                        ttok.head_ = inhead.id_

            close_t.head_ = inhead.id_
            close_t.deprel_ = "punct"
            if f_change_prev_cont_head and prev_cnt.head_ != 0 and (prev_cnt.id_ != inhead.head_):
                logger.debug("changed inHead-head", prev_cnt.head_, inhead.head_)
                prev_cnt.head_ = inhead.head_
                prev_cnt.deprel_ = inhead.deprel_
            else:
                logger.debug("Not changed inHead-head", inhead.head_, close_t.head_)
            inhead.head_ = prev_cnt.id_
            inhead.deprel_ = "appos"
            open_t.head_ = inhead.id_
            open_t.deprel_ = "punct"

            cleanup_before(sentence, prev_cnt, open_t, inhead, close_t, logger)
            cleanup_inside(sentence, open_t, inhead, close_t)
            cleanup_after(sentence, prev_cnt, open_t, close_t, logger)

            print_tokens(sentence, prev_t, close_t, logger, start="===6===", end="^^^^")
            return True

    logger.debug("FAILED!!!!")
    return False


def convert_ud_to_pud(_ud: UniversalDependencies) -> list[Sentence]:
    """ UD to PUD sentence """
    plist: list[Sentence] = []
    for ud_sent in _ud.sentences():
        pud_sent = Sentence()
        header = ud_sent.get_header("sent_id")
        if header is not None:
            pud_sent.sent_id_ = header.get_value()
        header = ud_sent.get_header("text")
        if header is not None:
            pud_sent.text_ = header.get_value()
        for uwrd in ud_sent.words():
            pud_sent.tokens_.append(Token(uwrd.get_value_str_list()))
        plist.append(pud_sent)
    return plist


def update_result_for_pud(pud_ss: list[Sentence], _ud: UniversalDependencies) -> None:
    """ update result for PUD """
    for psent, usent in zip(pud_ss, _ud.sentences()):
        assert len(psent.tokens_) == len(usent.words())
        for pwrd, uwrd in zip(psent.tokens_, usent.words()):
            pairs: list[tuple[Field, Union[str, int]]] = [
                (Field.ID, pwrd.id_), (Field.FORM, pwrd.form_), (Field.LEMMA, pwrd.lemma_),
                (Field.UPOS, pwrd.upos_), (Field.XPOS, pwrd.xpos_), (Field.FEATS, pwrd.feat_),
                (Field.HEAD, pwrd.head_), (Field.DEPREL, pwrd.deprel_),
                (Field.FEATS, pwrd.feat_), (Field.DEPS, pwrd.deps_), (Field.MISC, pwrd.misc_)
            ]
            for www, pww in pairs:
                uwrd.set(www, pww)


class ConvertParenComponent(UDPipeLine):
    """Convert paren Component."""

    name = "convert_paren"

    def prepare(self) -> None:
        """Prepare."""

    def __call__(self) -> None:
        """Call."""
        assert isinstance(self.target, UniversalDependencies)
        self.logger.message(f"do {self.name}", mode=LogLevel.DEBUG)
        pud_ss = convert_ud_to_pud(self.target)
        conv_paren(pud_ss, logger=self.logger)
        update_result_for_pud(pud_ss, self.target)


COMPONENT = ConvertParenComponent


def _main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("conll_file")
    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("-w", "--writer", default="-", type=str)
    args = parser.parse_args()
    options = YamlDict(
        init={"logger": Logger(debug=args.debug)}
    )
    _ud = UniversalDependencies(file_name=args.conll_file, options=options)
    COMPONENT(_ud, options)()
    _ud.write_ud_file(args.writer)


if __name__ == "__main__":
    _main()
