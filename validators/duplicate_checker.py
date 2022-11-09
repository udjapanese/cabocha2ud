# encoding: utf8

import sys

USAGE = '''
Sentence duplication checker for "*.cabocha.dumped" files.
Specify dumped files for command line args like:
   python duplicate_checker.py *.cabocha.dumped
 or
   cat *.cabocha.dumped | python duplicate_checker.py
The main function will return non-zero exit code when one or more sentence duplication(s) found.
Please use `set -e` before executing this command.
'''

ORTH_FIELD = 0


def print_duplicated(sentence, docid1, docid2, file):
    print('Warning: duplicated sentences', file=file)
    print(sentence, file=file)
    print(docid1, file=file)
    print(docid2, file=file)
    print('---', file=file)


def duplicate_check(inf, sentences):
    dup_count = 0
    docid = None
    sentence = ''
    for line in inf:
        line = line.rstrip('\n')
        if line.startswith('#! ') or line.startswith('* ') or line == "EOS":
            if line.startswith('#! DOCID'):
                if sentence:
                    if sentence in sentences:
                        print_duplicated(sentence, sentences[sentence], docid, sys.stderr)
                        dup_count += 1
                    else:
                        sentences[sentence] = docid
                docid = line
                sentence = ''
        else:
            record = line.split('\t')
            sentence += record[ORTH_FIELD]
    if sentence:
        if sentence in sentences:
            print_duplicated(sentence, sentences[sentence], docid, sys.stderr)
            dup_count += 1
    return dup_count


def main():
    dup_count = 0
    sentences = {}
    if len(sys.argv) == 1:
        dup_count += duplicate_check(sys.stdin, sentences)
    else:
        if sys.argv[1] in ['-h', '--help']:
            print(USAGE)
            return
        for file in sys.argv[1:]:
            with open(file, 'r') as inf:
                dup_count += duplicate_check(inf, sentences)
    if dup_count:
        raise Exception('{} sentence duplication found'.format(dup_count))


if __name__ == '__main__':
    main()
