# encoding: utf8
import sys


USAGE = '''
Token aggregator for arabic numbers.
This command relies on the field order of input `cabocha.dumped` format.
The 3rd field of Bunsetu header line (Shuji/Kinougo index like 1/2) will not modified even the numerical tokens merged.
Usage:
    python merge_number/merge_number.py < dev.cabocha.dumped > dev.cabocha.dumped.n
'''

# GATHER_TARGET_FIELDS = {0, 2, 6, 9}
GATHER_TARGET_FIELDS = {7, 8, 9, 10, 20, 21, 22, 23}
RM_ID_FIELDS = {27, 28}
ORTH_FIELD = 0
POS_FIELD = 3
LUW_BI_FIELD = 2  # 11
BUNSETU_BI_FIELD = 4  # 10
SUW_FORM_FILD = 1
LUW_FORM_FILD = 2
LUW_FES_FILD = 3

NUMBER_ORTH = {
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
    '０', '１', '２', '３', '４', '５', '６', '７', '８', '９',
}

NUMBER_POS = ['名詞-数詞']


def print_number_records(number_records, file):
    # print(number_records)
    print(
        "{form}\t{suw_fes}\t{luw_form}\t{luw_fes}\t{bunsetu_pos}".format(
            form="".join([r[0] for r in number_records]),
            suw_fes=','.join([
                ''.join([
                    r[SUW_FORM_FILD][idx] for r in number_records
                ]) if idx in GATHER_TARGET_FIELDS
                else '' if idx in RM_ID_FIELDS and len(number_records) > 1 else field
                for idx, field in enumerate(number_records[0][SUW_FORM_FILD])
            ]),
            luw_form=number_records[0][LUW_FORM_FILD],
            luw_fes=number_records[0][LUW_FES_FILD],
            bunsetu_pos=number_records[0][BUNSETU_BI_FIELD]
        ),
        file=file
    )


def merge_number(inf, outf):
    number_records = None
    for line in inf:
        line = line.rstrip('\n')
        if line.startswith('#! ') or line.startswith('* ') or line == "EOS":
            if number_records:
                print_number_records(number_records, outf)
                number_records = None
        else:
            record = line.split('\t')
            record[1] = record[1].split(",")
            pos = "-".join(record[1][0:2])
            # print(record[ORTH_FIELD], pos, record[ORTH_FIELD] in NUMBER_ORTH, pos in NUMBER_POS)
            if record[ORTH_FIELD] in NUMBER_ORTH and pos in NUMBER_POS:
                if number_records:
                    for idx, ref in enumerate(number_records[0]):
                        if idx == LUW_BI_FIELD and record[idx] != '':
                            # print(record, idx)
                            print_number_records(number_records, outf)
                            number_records = None
                            break
                    else:
                        number_records.append(record)
                        continue
                else:
                    number_records = [record]
                    continue
            elif number_records:
                print_number_records(number_records, outf)
                number_records = None
        print(line, file=outf)


def main():
    if len(sys.argv) > 1:
        print(USAGE)
        sys.exit(2)
    merge_number(sys.stdin, sys.stdout)


if __name__ == '__main__':
    main()
