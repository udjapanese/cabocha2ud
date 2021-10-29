# convertparen.py
# modify dependencies regarding parenthesis in UD_Japanese-PUD

from typing import Optional

from cabocha2ud.ud.util import Field

from cabocha2ud.ud import UniversalDependencies
from cabocha2ud.lib.logger import Logger



newline = "\n"

# Token class (copied from ud2lw.py)
class Token:
    def __init__(self, line: list[str]):
#        print (line)
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

    def __init__(self):
        self.sent_id_: str = ""
        self.text_: str = ""
        self.tokens_: list[Token] = []
        self.tar_tokens_: list[Token] = []
        self.english_text_: str = ""
        self.newdoc_id_: str = ""

    def to_conllu(self, use_target=True) -> str:
        ret: str = ""
        if self.newdoc_id_ != "":  # PUD
            ret += self.newdoc_id_ + newline
        ret += self.sent_id_ + newline + self.text_ + newline
        if self.english_text_ != "":  # PUD
            ret += self.english_text_ + newline
        if use_target == True:
            for t in self.tar_tokens_:
                ret += (t.to_conllu() + newline)
        else:
            for t in self.tokens_:
                ret += (t.to_conllu() + newline)
        ret += newline
        return ret


def convParen(sentences: list[Sentence], logger: Logger) -> None:
    parenNum, successNum = 0, 0
    for s in sentences:
        for t in s.tokens_:
            if t.form_ in ['（' ,'(']:
                for t1 in s.tokens_[t.id_:]:
                    if t1.form_ in['）', ')']:
                        parenNum += 1
                        ret = convParen_sub(s, t, t1, logger)
                        if ret == True:
                            successNum += 1
                            logger.debug(s.to_conllu())
                        break
    logger.debug(parenNum, successNum)


def printTokens(sentence: Sentence, a: Token, b: Token, logger: Logger, start: str='', end: str=''):
    if start != '':
        logger.debug(start)
    for t in sentence.tokens_[a.id_-1: b.id_]:
        logger.debug(t.to_conllu())
    if end != '':
        logger.debug(end)


def cleanupBefore(sentence: Sentence, prev: Token, open: Token, last: Token, inHead: Token, close: Token, logger: Logger) -> None:
    for t in sentence.tokens_[:open.id_-1]:
        if t.lemma_ in ['「', '『'] and t.head_ >= close.id_:
            t.head_ = t.id_ + 1
        elif t.lemma_ in ['」', '』'] and t.head_ >= close.id_:
            t.head_ = t.id_ - 1
        if t.head_ >= open.id_ and t.head_ <= close.id_:
            logger.debug(prev.id_, prev.lemma_, prev.head_, t.id_, t.lemma_, t.head_, inHead.id_)
            if prev.head_ == t.id_:
                pass
            elif prev.head_ > close.id_ or prev.head_ == 0:
                t.head_ = prev.id_
            else:
                t.head_ = inHead.id_
            logger.debug('****XXXX')
            logger.debug(t.to_conllu())


def cleanupInside(sentence: Sentence, prev: Token, open: Token, last: Token, inHead: Token, close: Token, logger: Logger):
    for t in sentence.tokens_[open.id_: close.id_ - 1]:
        if t.head_ == open.id_:
            t.head_ = t.id_ + 1
            t.deprel_ = 'dep'
        if t.head_ == close.id_:
            t.head_ = inHead.id_


def cleanupAfter(sentence: Sentence, prev: Token, open: Token, last: Token, close: Token, logger: Logger):
    prev_head = prev.id_
    logger.debug('PREV: ' , prev.id_ , '*********' , sentence.tokens_[prev.id_-1].lemma_)
    if sentence.tokens_[prev.id_-1].lemma_ == 'さ':
        prev_head -= 1
        logger.debug('prev_head=', prev_head)
    for t in sentence.tokens_[close.id_:]:
        if t.head_ >= open.id_ and t.head_ <= close.id_:
            t.head_ = prev_head


def convParen_sub(sentence: Sentence, open: Token, close: Token, logger: Logger) -> bool:

    prev = sentence.tokens_[open.id_-1-1]
    if prev.upos_ == 'PUNCT' and prev.lemma_ != '「':
        # 「XX、（」のときXXに
        prev = sentence.tokens_[open.id_-1-2]
    elif prev.lemma_ == 'た':
        # 「XX<-た（」のときはXXに
        prev = sentence.tokens_[prev.head_-1]

    # lastは「XX）」のXX
    last = sentence.tokens_[close.id_-1-1]
    printTokens(sentence, prev, last, logger, start="--aaa--", end="----bbb---")
    printTokens(sentence, open, close, logger, start="--ddd--", end="----eee---")

    inHead = last
    if last.head_ != close.id_:
        # かっこの最後の親が末尾かっこではないとき
        if last.head_ > open.id_ and last.head_ < close.id_:
            # ちゃんとかっこ内にヘッドがある
            for t in sentence.tokens_[last.head_:close.id_-1]:
                assert t.head_ == last.head_, 'wrong inparenHead 0' + t.to_conllu()
            inHead = sentence.tokens_[last.head_-1]
            if last.deprel_ == 'fixed' and inHead.deprel_ == 'case' and inHead.head_ > open.id_:
                inHead = sentence.tokens_[inHead.head_-1]
                logger.debug("****CHANGED INHEAD")
        else:
            # そうではない
            inHead = last
            if inHead.deprel_ == 'punct':   #  for sent_id = w01020020
                sentence.tokens_[open.id_].upos_ = "NOUN"
                inHead.upos_ = "NOUN"
                logger.debug("****CHANGED INHEAD UPOS")
    logger.debug('inHead:' + inHead.to_conllu())
    logger.debug('prev:' + prev.to_conllu())
    outgoing_nodes: list[Token] = []
    for t in sentence.tokens_[open.id_-1:close.id_]:
        # （）内部を確認、親がかっこの外にあるものを追加する
        logger.debug(t.to_conllu())
        if t.head_ < open.id_ or t.head_ > close.id_:
            if t.head_ == 0:
                logger.debug('===============ROOT')
            elif t.head_ < open.id_:
                assert True, 'back outside dependency'
            logger.debug("OUTSIDE!")
            outgoing_nodes.append(t)
    logger.debug("---- outgoing_nodes -> " + str(len(outgoing_nodes)))

    if prev.deprel_ in ['case', 'mark', 'punct'] and not prev.lemma_ in ['さ']:
        # forward modification
        logger.debug('CASE!!!!!!', sentence.sent_id_)
        open.head_ = inHead.id_
        open.deprel_ = 'punct'
        close.head_ = inHead.id_
        close.deprel_ = 'punct'
        if inHead.deprel_ == 'compound':
            inHead.deprel_ = 'nmod'
        elif inHead.deprel_ == 'advcl':
            inHead.head_ = close.id_ + 1  # tentative!
        logger.debug(prev.head_)
        logger.debug(sentence.tokens_[prev.head_-1].to_conllu())
        if sentence.tokens_[prev.head_-1].head_ == prev.id_:
            assert False, "ERROR"
        cleanupBefore(sentence, prev, open, last, inHead, close, logger)
        cleanupInside(sentence, prev, open, last, inHead, close, logger)
        cleanupAfter(sentence, prev, open, last, close, logger)
        printTokens(sentence, prev, close, logger, start='===0===', end='^^^^')
        return True
    elif len(outgoing_nodes) == 1:
        logger.debug("OUTGOING one ->", sentence.sent_id_)
        if outgoing_nodes[0] == close:
            if inHead.head_ == close.id_:
                outside_id = close.head_
                outside_deprel = close.deprel_
                close.head_ = inHead.id_
                close.deprel_ = 'punct'
                inHead.head_ = prev.id_
                inHead.deprel_ = 'appos'
                prev.head_ = outside_id
                prev.deprel_ = outside_deprel
                open.head_ = inHead.id_
                open.deprel_ = 'punct'

                cleanupBefore(sentence, prev, open, last, inHead, close, logger)
                cleanupInside(sentence, prev, open, last, inHead, close, logger)
                cleanupAfter(sentence, prev, open, last, close, logger)

                printTokens(sentence, prev, close, logger, start='===1===', end='^^^^')
                return True
            elif prev.head_ > close.id_:
                open.head_ = last.id_
                open.deprel_ = 'punct'
                last.head_ = prev.id_
                last.deprel_ = 'appos'
                close.head_ = last.id_
                close.deprel_ = 'punct'
                cleanupBefore(sentence, prev, open, last, inHead, close, logger)
                cleanupInside(sentence, prev, open, last, inHead, close, logger)
                cleanupAfter(sentence, prev, open, last, close, logger)

                printTokens(sentence, prev, close, logger, start='===2===', end='^^^^')
                return True
            else:
                assert True, 'WHAT HAPPENS??---------'
        elif outgoing_nodes[0] == inHead:
            if prev.xpos_ == "助動詞":
                return True
            close.head_ = inHead.id_
            close.deprel_ = 'punct'
            prev.head_ = inHead.head_
            prev.deprel_ = inHead.deprel_
            if inHead.deprel_ == 'nummod':
                prev.deprel_ = 'obl'
            inHead.head_ = prev.id_
            inHead.deprel_ = 'appos'
            open.head_ = inHead.id_
            open.deprel_ = 'punct'

            cleanupBefore(sentence, prev, open, last, inHead, close, logger)
            cleanupInside(sentence, prev, open, last, inHead, close, logger)
            cleanupAfter(sentence, prev, open, last, close, logger)

            printTokens(sentence, prev, close, logger, start='===5===', end='^^^^')
            return True
        else:
            assert True, 'Wrong outgoing node'
    else:
        logger.debug('abc OUTGOING_NUM ' + str(len(outgoing_nodes)))
        if open in outgoing_nodes:
            outgoing_nodes.remove(open)
        if close in outgoing_nodes:
            outgoing_nodes.remove(close)
        logger.debug('NEW OUTGOING_NUM ' + str(len(outgoing_nodes)))
        if len(outgoing_nodes) > 1:
            for t in outgoing_nodes[:-1]:
                t.head_ = outgoing_nodes[-1].id_
                t.deprel_ = 'compound'
                if t.upos_ in ['ADP','AUX']:
                    t.deprel_ = 'dep'
        if outgoing_nodes[-1] == inHead:
            prevCont = prev
            if prev.lemma_ == 'さ':
                prevCont = sentence.tokens_[prev.id_-2]
            logger.debug('PC', prevCont.to_conllu())
            logger.debug('IH', inHead.to_conllu())

            fChangePrevContHead = True

            if inHead.lemma_ == 'た':
                fChangePrevContHead = False
                for ii in range(close.id_-1, open.id_+1, -1):
                    tt = sentence.tokens_[ii-1]
                    if tt.upos_ == 'VERB':
                        inHead = sentence.tokens_[tt.id_-1]
                        break
                for ii in range(close.id_ - 1, open.id_ + 1, -1):
                    tt = sentence.tokens_[ii - 1]
                    if tt.id_ == inHead.id_:
                        break
                    if tt.upos_=='AUX':
                        tt.deprel_ = 'aux'
                    elif tt.upos_=='SCONJ':
                        tt.deprel_ = 'mark'
                    tt.head_ = inHead.id_
                for ii in range(open.id_ + 1, inHead.id_):
                    tt = sentence.tokens_[ii - 1]
                    if tt.id_ == inHead.id_:
                        break
                    if tt.upos_=='PROPN':
                        tt.deprel_ = 'obl'
                        if sentence.tokens_[ii].lemma_ == 'は':
                            tt.deprel_ = 'nsubj'
                        tt.head_ = inHead.id_
                    elif tt.upos_=='ADP':
                        tt.deprel_ = 'case'
                        tt.head_ = tt.id_-1
                    else:
                        tt.head_ = inHead.id_

            close.head_ = inHead.id_
            close.deprel_ = 'punct'
            if fChangePrevContHead and prevCont.head_ != 0 and (prevCont.id_ != inHead.head_):
                logger.debug('changed inHead-head', prevCont.head_, inHead.head_)
                prevCont.head_ = inHead.head_
                prevCont.deprel_ = inHead.deprel_
            else:
                logger.debug('Not changed inHead-head', inHead.head_, close.head_)
            inHead.head_ = prevCont.id_
            inHead.deprel_ = 'appos'
            open.head_ = inHead.id_
            open.deprel_ = 'punct'

            cleanupBefore(sentence, prevCont, open, last, inHead, close, logger)
            cleanupInside(sentence, prevCont, open, last, inHead, close, logger)
            cleanupAfter(sentence, prevCont, open, last, close, logger)

            printTokens(sentence, prev, close, logger, start='===6===', end='^^^^')
            return True
        else:
            assert False, '??'

    logger.debug("FAILED!!!!")

    return False


def convertUD_to_PUD(ud: UniversalDependencies) -> list[Sentence]:
    plist: list[Sentence] = []
    for ud_sent in ud.sentences():
        pud_sent = Sentence()
        header = ud_sent.get_header("newdoc id")
        if header is not None:
            pud_sent.newdoc_id_ = header.get_value()
        header = ud_sent.get_header("sent_id")
        if header is not None:
            pud_sent.sent_id_ = header.get_value()
        header = ud_sent.get_header("text")
        if header is not None:
            pud_sent.text_ = header.get_value()
        header = ud_sent.get_header("text_en")
        if header is not None:
            pud_sent.english_text_ = header.get_value()
        for uwrd in ud_sent.words():
            pud_sent.tokens_.append(Token(uwrd.get_value_str_list()))
        plist.append(pud_sent)
    return plist


def update_result_for_PUD(pud_ss: list[Sentence], ud: UniversalDependencies) -> None:
    for psent, usent in zip(pud_ss, ud.sentences()):
        assert len(psent.tokens_) == len(usent.words())
        for pwrd, uwrd in zip(psent.tokens_, usent.words()):
            uwrd.set(Field.ID, pwrd.id_)
            uwrd.set(Field.FORM, pwrd.form_)
            uwrd.set(Field.LEMMA, pwrd.lemma_)
            uwrd.set(Field.UPOS, pwrd.upos_)
            uwrd.set(Field.XPOS, pwrd.xpos_)
            uwrd.set(Field.FEATS, pwrd.feat_)
            uwrd.set(Field.HEAD, pwrd.head_)
            uwrd.set(Field.DEPREL, pwrd.deprel_)
            uwrd.set(Field.FEATS, pwrd.feat_)
            uwrd.set(Field.DEPS, pwrd.deps_)
            uwrd.set(Field.MISC, pwrd.misc_)


def do(ud: UniversalDependencies, logger: Optional[Logger]=None) -> None:
    if logger is None:
        logger = Logger()
    logger.debug("do convParen")
    pud_ss = convertUD_to_PUD(ud)
    convParen(pud_ss, logger=logger)
    update_result_for_PUD(pud_ss, ud)


def _main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("conll_file")
    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("-w", "--writer", default="-", type=str)
    args = parser.parse_args()
    logger = Logger(debug=args.debug)
    ud = UniversalDependencies(file_name=args.conll_file)
    do(ud, logger=logger)
    ud.write_ud_file(args.writer)


if __name__ == "__main__":
    _main()

