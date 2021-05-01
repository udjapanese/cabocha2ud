# convertparen.py
# modify dependencies regarding parenthesis in UD_Japanese-PUD

import ud
import codecs
import sys

def convParen(sentences):

    parenNum = 0
    successNum = 0

    for s in sentences:
        for t in s.tokens_:
            if t.form_ in ['（' ,'(']:
                for t1 in s.tokens_[t.id_:]:
                    if t1.form_ in['）', ')']:

                        parenNum += 1
                        ret = convParen_sub(s, t, t1)
                        if ret == True:
                            successNum += 1
                            print(s.to_conllu())
                        break

    print (parenNum, successNum)

#    for s in sentences:
#        print('===AFTER CONVERSION===')
#        print(s.to_conllu())

def printTokens(sentence, a, b, start='', end=''):
    if start != '':
        print(start)
    for t in sentence.tokens_[a.id_-1: b.id_]:
        print(t.to_conllu())
    if end != '':
        print(end)

def cleanupBefore(sentence, prev, open, last, inHead, close):
    for t in sentence.tokens_[:open.id_-1]:

        if t.lemma_ in ['「', '『'] and t.head_ >= close.id_:
            t.head_ = t.id_ + 1
        elif t.lemma_ in ['」', '』'] and t.head_ >= close.id_:
            t.head_ = t.id_ - 1

        if t.head_ >= open.id_ and t.head_ <= close.id_:
            print(prev.id_, prev.lemma_, prev.head_, t.id_, t.lemma_, t.head_, inHead.id_)
            if prev.head_ == t.id_:
                pass
            elif prev.head_ > close.id_ or prev.head_ == 0:
                t.head_ = prev.id_
            else:
                t.head_ = inHead.id_
            print ('****XXXX')
            print(t.to_conllu())
#            if t.head_ == prev.id_:
#                assert False, 't_head_ == prev'


def cleanupInside(sentence, prev, open, last, inHead, close):
    for t in sentence.tokens_[open.id_: close.id_ - 1]:
        if t.head_ == open.id_:
            t.head_ = t.id_ + 1
            t.deprel_ = 'dep'
        if t.head_ == close.id_:
            t.head_ = inHead.id_


def cleanupAfter(sentence, prev, open, last, close):
    prev_head = prev.id_
    print('PREV: ' , prev.id_ , '*********' , sentence.tokens_[prev.id_-1].lemma_)
    if sentence.tokens_[prev.id_-1].lemma_ == 'さ':
        prev_head -= 1
        print('prev_head=', prev_head)
    for t in sentence.tokens_[close.id_:]:
        if t.head_ >= open.id_ and t.head_ <= close.id_:
            t.head_ = prev_head


def convParen_sub(sentence, open, close):

#    open.upos_ = 'PUNCT'
#    close.upos_ = 'PUNCT'
#    open.xpos_ = 'SYM'
#    close.xpos_ = 'SYM'

    prev = sentence.tokens_[open.id_-2]
    if prev.upos_ == 'PUNCT' and prev.lemma_ != '「':
        prev = sentence.tokens_[open.id_-3]
    elif prev.lemma_ == 'た':
        prev = sentence.tokens_[prev.head_-1]

    last = sentence.tokens_[close.id_-2]

    printTokens(sentence, prev, close)

    inHead = last

    if last.head_ != close.id_:
        if last.head_ > open.id_ and last.head_ < close.id_:
            for t in sentence.tokens_[last.head_:close.id_-1]:
                assert t.head_ == last.head_, 'wrong inparenHead 0' + t.to_conllu()
            inHead = sentence.tokens_[last.head_-1]
            if last.deprel_ == 'fixed' and inHead.deprel_ == 'case' and inHead.head_ > open.id_:
                inHead = sentence.tokens_[inHead.head_-1]
                print("****CHANGED INHEAD")
        else:
            inHead = last
            if inHead.deprel_ == 'punct':   #  for sent_id = w01020020
                sentence.tokens_[open.id_].upos_ = "NOUN"
                inHead.upos_ = "NOUN"
                print("****CHANGED INHEAD UPOS")


    print('inHead:' + inHead.to_conllu())

    print('prev:' + prev.to_conllu())
    outgoing_nodes = []
    for t in sentence.tokens_[open.id_-1:close.id_]:
        print(t.to_conllu())
        if t.head_ < open.id_ or t.head_ > close.id_:
            if t.head_ == 0:
                print('===============ROOT')
            elif t.head_ < open.id_:
                assert True, 'back outside dependency'
            print("OUTSIDE!")
            outgoing_nodes.append(t)
    print("----" + str(len(outgoing_nodes)))
    print()

    if prev.deprel_ in ['case', 'mark', 'punct'] and not prev.lemma_ in ['さ']:
        # forward modification
        print('CASE!!!!!!')
        open.head_ = inHead.id_
        open.deprel_ = 'punct'
        close.head_ = inHead.id_
        close.deprel_ = 'punct'
        if inHead.deprel_ == 'compound':
            inHead.deprel_ = 'nmod'
        elif inHead.deprel_ == 'advcl':
            inHead.head_ = close.id_ + 1  # tentative!

        print(prev.head_)
        print(sentence.tokens_[prev.head_-1].to_conllu())
        if sentence.tokens_[prev.head_-1].head_ == prev.id_:
            assert False, "ERROR"
        cleanupBefore(sentence, prev, open, last, inHead, close)
        cleanupInside(sentence, prev, open, last, inHead, close)
        cleanupAfter(sentence, prev, open, last, close)

        printTokens(sentence, prev, close, start='===0===', end='^^^^')
        return True

    elif len(outgoing_nodes) == 1:
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

                cleanupBefore(sentence, prev, open, last, inHead, close)
                cleanupInside(sentence, prev, open, last, inHead, close)
                cleanupAfter(sentence, prev, open, last, close)

                printTokens(sentence, prev, close, start='===1===', end='^^^^')
                return True
            elif prev.head_ > close.id_:
                open.head_ = last.id_
                open.deprel_ = 'punct'
                last.head_ = prev.id_
                last.deprel_ = 'appos'
                close.head_ = last.id_
                close.deprel_ = 'punct'
                cleanupBefore(sentence, prev, open, last, inHead, close)
                cleanupInside(sentence, prev, open, last, inHead, close)
                cleanupAfter(sentence, prev, open, last, close)

                printTokens(sentence, prev, close, start='===2===', end='^^^^')
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

            cleanupBefore(sentence, prev, open, last, inHead, close)
            cleanupInside(sentence, prev, open, last, inHead, close)
            cleanupAfter(sentence, prev, open, last, close)

            printTokens(sentence, prev, close, start='===5===', end='^^^^')
            return True

        else:
            assert True, 'Wrong outgoing node'
    else:
        print('OUTGOING_NUM ' + str(len(outgoing_nodes)))
        if open in outgoing_nodes:
            outgoing_nodes.remove(open)
        if close in outgoing_nodes:
            outgoing_nodes.remove(close)
        print('NEW OUTGOING_NUM ' + str(len(outgoing_nodes)))
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
            print('PC', prevCont.to_conllu())
            print('IH', inHead.to_conllu())

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
                print('changed inHead-head', prevCont.head_, inHead.head_)
                prevCont.head_ = inHead.head_
                prevCont.deprel_ = inHead.deprel_
            else:
                print('Not changed inHead-head', inHead.head_, close.head_)
            inHead.head_ = prevCont.id_
            inHead.deprel_ = 'appos'
            open.head_ = inHead.id_
            open.deprel_ = 'punct'

            cleanupBefore(sentence, prevCont, open, last, inHead, close)
            cleanupInside(sentence, prevCont, open, last, inHead, close)
            cleanupAfter(sentence, prevCont, open, last, close)

            printTokens(sentence, prev, close, start='===6===', end='^^^^')
            return True
        elif prev.head_ == outgoing_nodes[-1].id_ and close.head_ == outgoing_nodes[-1].head_:
            # for specific instance....
            prev.head_ = close.head_
            prev.deprel_ = close.deprel_
            outgoing_nodes[-1].head_ = last.id_
            last.head_ = prev.id_
            last.deprel_ = 'appos'
            open.head_ = last.id_
            close.head_ = last.id_
            close.deprel_ = 'punct'

            cleanupBefore(sentence, prev, open, last, inHead, close)
            cleanupInside(sentence, prev, open, last, inHead, close)
            cleanupAfter(sentence, prev, open, last, close)
            printTokens(sentence, prev, close, start='===7===', end='^^^^')
            return True

        else:
            assert False, '??'

    print ("FAILED!!!!")

    return False



#fn = 'D:/Corpus/UD/ja2.6/ccd_ud_pud_final.cabocha.dumped_05012255.conllu'
#fnout = 'D:/Corpus/UD/ja2.6/ccd_ud_pud_final.cabocha.dumped_paren_05020015.conllu'

if __name__ == "__main__":
    fn = sys.argv[1]
    fnout = sys.argv[2]
    pud_ss = ud.read_ud(fn)
    convParen(pud_ss)
    with codecs.open(fnout, 'w', 'utf-8') as w:
        for s in pud_ss:
            w.write(s.to_conllu())
