
import re
import codecs

newline = "\n"
labelset = set()

# Token class (copied from ud2lw.py)
class Token:
    def __init__(self, line):
#        print (line)
        self.id_ = int(line[0])
        self.form_ = line[1]
        self.lemma_ = line[2]
        self.upos_ = line[3]
        self.xpos_ = line[4]
        self.feat_ = line[5]
        self.head_ = int(line[6])
        self.deprel_ = line[7]
        self.deps_ = line[8]
        self.misc_ = line[9]

        self.line_ = line
        self.posi_ = (-1, -1)
        self.hposi_ = (-1, -1)

        self.tar_id_ = -1

    def __repr__(self):
        return str(self.id_) + self.form_ + str(self.head_)

    def isForm(self, forms):
        if isinstance(forms, list):
            for f in forms:
                if f == self.form_:
                    return True
            return False
        else:
            if forms == self.form_:
                return True
            return False

    def isLemma(self, lemmas):
        if isinstance(lemmas, list):
            for f in lemmas:
                if f == self.lemma_:
                    return True
            return False
        else:
            if lemmas == self.lemma_:
                return True
            return False

    def isPos(self, poss):
        if isinstance(poss, list):
            for p in poss:
                if p == self.upos_:
                    return True
            return False
        else:
            if poss == self.upos_:
                return True
            return False

    def isRel(self, rels):
        if isinstance(rels, list):
            for r in rels:
                if r == self.deprel_:
                    return True
            return False
        else:
            if rels == self.deprel_:
                return True
            return False

    def testPosRel(self, pos, deprel):
        if self.isPos(pos) and self.isRel(deprel):
            return True
        else:
            return False

    def to_conllu(self):
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


# CompoundToken (ID is specified as '1-2')
class CompoundToken:
    def __init__(self, line):
        self.id_start_ = int(line[0].split('-')[0])
        self.id_end_ = int(line[0].split('-')[1])
        self.form_ = line[1]
        self.lemma_ = line[2]
        self.upos_ = line[3]
        self.xpos_ = line[4]
        self.feat_ = line[5]
        self.head_ = line[6]
        self.deprel_ = line[7]
        self.deps_ = line[8]
        self.misc_ = line[9]

        self.line_ = line
        self.posi_ = (-1, -1)
#        self.hposi_ = (-1, -1)

        self.tar_id_ = -1

    def __repr__(self):
        return str(self.id_) + self.form_ + str(self.head_)

    def isForm(self, forms):
        if isinstance(forms, list):
            for f in forms:
                if f == self.form_:
                    return True
            return False
        else:
            if forms == self.form_:
                return True
            return False


    def to_conllu(self):
        rtn_line = self.line_
        rtn_line[0] = str(self.id_start_) + '-' + str(self.id_end_)
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
        self.sent_id_ = ""
        self.text_ = ""
        self.tokens_ = []
        self.tar_tokens_ = []
        self.compound_tokens_ = []
        self.english_text_ = ""
        self.newdoc_id_ = ""

    def check_proj(self):
        for c in self.tar_tokens_:

            headId = int(c.head_)
            childId = int(c.id_)
            if c.head_ == 0 or abs(headId - childId) == 1:
                continue

            if headId > childId:
                for i in range(childId, headId - 1):
                    if int(self.tar_tokens_[i].head_) < int(c.id_) or int(self.tar_tokens_[i].head_) > int(c.head_):
                        return False
            else:
                for i in range(headId, childId - 1):
                    if int(self.tar_tokens_[i].head_) < int(c.head_) or int(self.tar_tokens_[i].head_) > int(c.id_):
                        return False
        return True

    def find_nonproj(self):
        ret = []
        for c in self.tar_tokens_:

            headId = int(c.head_)
            childId = int(c.id_)
            if c.head_ == 0 or abs(headId - childId) == 1:
                continue

            if headId > childId:
                for i in range(childId, headId - 1):
                    if int(self.tar_tokens_[i].head_) < childId or int(self.tar_tokens_[i].head_) > headId:
                        ret.append(['A', childId, self.tar_tokens_[childId-1].deprel_, headId,
                                    self.tar_tokens_[i].id_, self.tar_tokens_[i].deprel_, self.tar_tokens_[i].head_])

#                        print ('! cross in ' + str(c) + "->" + str(i) + str(self.tar_tokens_[i].head_))
                        break
            else:
                for i in range(headId, childId - 1):
                    if int(self.tar_tokens_[i].head_) < headId or int(self.tar_tokens_[i].head_) > childId:
                        ret.append(['B', childId, self.tar_tokens_[childId-1].deprel_,headId,
                                    self.tar_tokens_[i].id_, self.tar_tokens_[i].deprel_, self.tar_tokens_[i].head_])
#                        print ('# cross in ' + str(c) + "->" +  str(i) + str(self.tar_tokens_[i].head_))
                        break
        return ret


    def to_conllu(self, use_target=True):
        ret = ""
        if self.newdoc_id_ != "":  # PUD
            ret += self.newdoc_id_ + newline
        ret += self.sent_id_ + newline + self.text_ + newline
        if self.english_text_ != "":  # PUD
            ret += self.english_text_ + newline
        if use_target == True:
            for t in self.tar_tokens_:

                for ct in self.compound_tokens_:
                    if ct.id_start_ == t.id_:
                        ret += (ct.to_conllu() + newline)

                ret += (t.to_conllu() + newline)
        else:
            for t in self.tokens_:

                for ct in self.compound_tokens_:
                    if ct.id_start_ == t.id_:
                        ret += (ct.to_conllu() + newline)

                ret += (t.to_conllu() + newline)

        ret += newline
        return ret


def read_ud(conllufile, retain_compound = False):
    print('reading + ', conllufile)
    ss = []
    s = Sentence()

    tar_id = 1
    position = 0
    tar_position = 0
    looking_compound = False
    compound_end = ""
    compound_form = ""
    compound_flagments = []
    with codecs.open(conllufile, 'r', 'utf-8') as f:

        for line in f:
            if re.match("\n", line) or re.match("\r\n", line):
                for idx, t in enumerate(s.tokens_):
                    t.hposi_ = s.tokens_[t.head_ - 1].posi_

                for idx, t in enumerate(s.tar_tokens_, start=1):
                    t.id_ = idx
                    t.hposi_ = s.tokens_[t.head_ - 1].posi_
                    for idx_h, h in enumerate(s.tar_tokens_, start=1):
                        if h.posi_ == t.hposi_ and t.head_ != 0:
                            t.head_ = idx_h

                if s.text_ is "":
                    #					print ('#text!!')
                    this_text = "# text = "
                    for t in s.tokens_:
                        this_text += t.form_
                        #						print ("(" + t.misc_ +")")
                        if t.misc_.find("SpaceAfter=No"):
                            pass
                        else:
                            this_text += " "
                    s.text_ = this_text
                #					print ("text -> " + this_text)
                #				else:
                #					print ('# text = ', s.text_)

                #					print ("text = " + s.text_)

                ss.append(s)
                s = Sentence()
                tar_id = 1
                position = 0
                tar_position = 0
            elif line[0] == "#":
                if line[2:9] == "sent_id":
                    s.sent_id_ = line.strip()
                elif line[2:7] == "text ":
                    s.text_ = line.strip()
                elif line[2:11] == "newdoc id":
                    s.newdoc_id_ = line.strip()
                elif line[2:9] == "text_en":
                    s.english_text_ = line.strip()

            else:

                line_spl = line.split("\t")

                if retain_compound == True:

                    if "-" in line_spl[0]:
                        print('Compound: ============')
                        print(line_spl)
                        t = CompoundToken(line_spl)
                        s.compound_tokens_.append(t)

                    elif "." in line_spl[0]:
                        continue
                    else:
                        t = Token(line_spl)
                        t.tar_id_ = tar_id
                        t.posi_ = (position, position + len(t.form_))
                        position += len(t.form_)
                        tar_position += len(t.form_)
                        s.tokens_.append(t)
                        s.tar_tokens_.append(t)

                else:
                    if "-" in line_spl[0]:
                        looking_compound = True
                        compound_end = line_spl[0].split("-")[1]
                        compound_form = line_spl[1]
                        continue
                    elif "." in line_spl[0]:
                        continue
                    else:
                        ### Save ordinal tokens (i.e. other than "-" or ".")
                        t = Token(line_spl)
                        t.tar_id_ = tar_id
                        t.posi_ = (position, position + len(t.form_))
                        position += len(t.form_)
                        s.tokens_.append(t)
                        labelset.add(t.deprel_.split(":")[0])

                        ### Save target tokens (i.e. use compound if its surface is different)
                        if looking_compound is True:
                            compound_flagments.append(t)
                            if line_spl[0] == compound_end:
                                if compound_form == "".join([i.form_ for i in compound_flagments]):
                                    for f in compound_flagments:
                                        f.posi_ = (tar_position, tar_position + len(f.form_))
                                        tar_position += len(f.form_)
                                        s.tar_tokens_.append(f)
                                else:
                                    head = [i for i in compound_flagments if
                                            i.head_ not in [j.id_ for j in compound_flagments]]
                                    t.form_ = compound_form
                                    t.head_ = head[0].head_
                                    t.posi_ = (tar_position, tar_position + len(t.form_))
                                    tar_position += len(t.form_)
                                    s.tar_tokens_.append(t)

                                looking_compound = False
                                compound_form = ""
                                compound_flagments = []
                        else:
                            t.posi_ = (tar_position, tar_position + len(t.form_))
                            tar_position += len(t.form_)
                            s.tar_tokens_.append(t)

    return ss
