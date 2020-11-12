# -*- coding: utf-8 -*-

"""
BCCWJ DepParaPAS Annotation class
"""

from collections import defaultdict
from itertools import permutations


def get_annotation_object(seg):
    """
        get annotation object
    """
    return {
        "SEGMENT_S": Segment, "GROUP_S": Group, "LINK_S": Link,
        "SEGMENT": Segment, "GROUP": Group, "LINK": Link
    }[seg[0][1]](seg)


class AnnotationList(object):
    """
        Annotation list
    """

    def __init__(self, annotation_list):
        self.seg_pos = 0
        self._annotation_list = annotation_list
        self._segments = [
            seg for seg in self._annotation_list
            if seg.get_identifier() in ["SEGMENT_S", "SEGMENT"]
        ]
        self._annotation = [
            seg for seg in self._annotation_list
            if seg.get_identifier() not in ["SEGMENT_S", "SEGMENT"]
        ]
        self._seg_dict = defaultdict(lambda: -1, {
            (s.start_pos, s.end_pos): p
            for p, s in enumerate(self._segments)
        })
        self._link_dict = {
            (seg.start_pos, seg.end_pos): (
                seg, self._segments[seg.start_pos], self._segments[seg.end_pos]
            ) for seg in self._annotation_list
            if seg.get_identifier() in ["LINK_S", "LINK"]
        }
        self._group_dict = {}
        for seg in self._annotation_list:
            if seg.get_identifier() in ["GROUP_S", "GROUP"]:
                for sid1, sid2 in permutations(seg.groups_ids, 2):
                    seg1, seg2 = self._segments[sid1], self._segments[sid2]
                    self._group_dict[(
                        (seg1.start_pos, seg1.end_pos), (seg2.start_pos, seg2.end_pos)
                    )] = seg

    def __len__(self):
        return len(self._annotation_list)

    def __unicode__(self):
        return "\n".join([str(s) for s in self._annotation_list])

    def __getitem__(self, ind):
        return self._annotation_list[ind]

    def get_group(self, anno, word1_pos, word2_pos):
        """
            get anno for the two words
        """
        for seg_key, seg in list(self._group_dict.items()):
            if seg.name != anno:
                continue
            seg1_key, seg2_key = seg_key
            seg1_start_pos, seg1_end_pos = seg1_key
            seg2_start_pos, seg2_end_pos = seg2_key
            ff1 = seg1_start_pos <= word1_pos[0] and word1_pos[1] <= seg1_end_pos
            ff2 = seg2_start_pos <= word2_pos[0] and word2_pos[1] <= seg2_end_pos
            if ff1 and ff2:
                return seg
        return -1

    def get_link(self, start_word_pos, end_word_pos):
        """
            get link
        """
        start, end = self.get_segment_pos(start_word_pos), self.get_segment_pos(end_word_pos)
        if start == -1 or end == -1:
            return -1
        if (start, end) not in self._link_dict:
            return -1
        return self._link_dict[(start, end)]

    def get_appos(self, word1_pos, word2_pos):
        """
            get appos
        """
        return self.get_group("Apposition", word1_pos, word2_pos)

    def get_conj(self, word1_pos, word2_pos):
        """
            get conj
        """
        return self.get_group("Parallel", word1_pos, word2_pos)

    def get_segments(self):
        """
            get all seguments
        """
        return self._segments

    def get_segment(self, pos):
        """
            get segment
        """
        spos = self.get_segment_pos(pos)
        if spos == -1:
            return -1
        return self._segments[spos]

    def get_segment_pos(self, pos):
        """
            get segument
        """
        return self._seg_dict[pos]

    def get_annotations(self):
        """
            get full annotations
        """
        return self._annotation


class Annotation(object):
    """
        annotation class
    """

    def __init__(self, segment_lines):
        self.segment_lines = segment_lines
        self.seg_type = None
        self.identifier = None
        self.tag = None
        self.start_pos, self.end_pos = None, None
        self.comment = None

    def __parse(self, xxx):
        raise NotImplementedError

    def get_comment(self):
        """ get comment """
        return self.comment

    def __unicode__(self):
        return "\n".join([
            " ".join(ss) for ss in self.segment_lines
        ])

    def get_identifier(self):
        """
            get identifier
        """
        return self.identifier


class Segment(Annotation):
    """
        segment
    """

    def __init__(self, segment_lines):
        super(Segment, self).__init__(segment_lines)
        self.attributes = {}
        self.__parse()
        assert self.identifier in ["SEGMENT_S", "SEGMENT"]

    def __parse(self):
        self.identifier = self.segment_lines[0][1]
        self.name = self.segment_lines[0][2]
        self.start_pos = int(self.segment_lines[0][3])
        self.end_pos = int(self.segment_lines[0][4])
        self.comment = self.segment_lines[0][5]
        for items in self.segment_lines[1:]:
            if items[1] != "ATTR":
                raise TypeError("is not be ATTR", items[1])
            self.attributes[items[2]] = items[3]


class Link(Annotation):
    """
        link
    """
    def __init__(self, segment_lines):
        super(Link, self).__init__(segment_lines)
        # assert len(segment_lines) == 1  # 本来はこうのはず...?
        self.__parse()
        assert self.identifier in ["LINK", "LINK_S"]

    def __parse(self):
        self.identifier = self.segment_lines[0][1]
        self.name = self.segment_lines[0][2]
        self.start_pos = int(self.segment_lines[0][3])
        self.end_pos = int(self.segment_lines[0][4])
        self.comment = self.segment_lines[0][5]


class Group(Annotation):
    """
        Group
    """
    def __init__(self, segment_lines):
        super(Group, self).__init__(segment_lines)
        # assert len(segment_lines) == 1  # 本来はこうのはず...?
        self.groups_ids = set([])
        self.__parse()
        assert self.identifier in ["GROUP", "GROUP_S"]

    def __parse(self):
        self.identifier = self.segment_lines[0][1]
        self.name = self.segment_lines[0][2]
        self.groups_ids = set([
            int(s) for s in self.segment_lines[0][3:-1] if s != ""
        ])
        self.comment = self.segment_lines[0][-1]


class AbstractPosition(object):
    """
        Annotation list
    """

    def __init__(self, obj_type):
        # doc or sent ?
        self.obj_type = obj_type
        self.abs_pos_list = []
        self.abs_pos_dict = {}

    def set_position(self, pos):
        """
            set position
        """
        self.abs_pos_list.append(pos)

    def get_pos_from_word(self, word):
        """
            word の位置を返す
        """
        if self.obj_type == "doc":
            return self.abs_pos_list[word.sent_pos][word.token_pos-1]
        elif self.obj_type == "sent":
            return self.abs_pos_list[word.token_pos-1]
        else:
            raise NotImplementedError
