# -*- coding: utf-8 -*-

"""
BCCWJ DepParaPAS Annotation class
"""

from typing import Optional, Union

from collections import defaultdict
from itertools import permutations

from .word import Word


class Annotation(object):
    """
        annotation class
    """

    def __init__(self, segment_lines: list[list[str]]):
        self.segment_lines = segment_lines
        self.identifier: Optional[str] = None
        self.start_pos: int = -1
        self.end_pos: int = -1
        self.comment: Optional[str] = None
        self.name: str = ""

    def get_comment(self) -> Optional[str]:
        """ get comment """
        return self.comment

    def get_identifier(self) -> Optional[str]:
        """
            get identifier
        """
        return self.identifier

    def __str__(self) -> str:
        return "\n".join([
            " ".join(ss) for ss in self.segment_lines
        ])


class Segment(Annotation):
    """
        segment
    """

    def __init__(self, segment_lines):
        super(Segment, self).__init__(segment_lines)
        self.attributes = {}
        self.__parse()
        assert self.identifier in ["SEGMENT_S", "SEGMENT"]

    def __parse(self) -> None:
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

    def __parse(self) -> None:
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
        self.groups_ids: set[int] = set([])
        self.__parse()
        assert self.identifier in ["GROUP", "GROUP_S"]

    def __parse(self) -> None:
        self.identifier = self.segment_lines[0][1]
        self.name = self.segment_lines[0][2]
        self.groups_ids = set([
            int(s) for s in self.segment_lines[0][3:-1] if s != ""
        ])
        self.comment = self.segment_lines[0][-1]


class AnnotationList(object):
    """
        Annotation list
    """

    def __init__(self, annotation_list: list[Annotation]):
        self.seg_pos: int = 0
        self._annotation_list: list[Annotation] = annotation_list
        self._segments: list[Segment] = [
            seg for seg in self._annotation_list
            if isinstance(seg, Segment)
        ]
        self._annotation: list[Annotation] = [
            seg for seg in self._annotation_list
            if seg.get_identifier() not in ["SEGMENT_S", "SEGMENT"]
        ]
        self._seg_dict: defaultdict[tuple[int, int], int] = defaultdict(lambda: -1, {
            (s.start_pos, s.end_pos): p
            for p, s in enumerate(self._segments)
        })
        self._link_dict: dict[tuple[int, int], tuple[Annotation, Segment, Segment]] = {
            (seg.start_pos, seg.end_pos): (
                seg, self._segments[seg.start_pos], self._segments[seg.end_pos]
            ) for seg in self._annotation_list
            if seg.get_identifier() in ["LINK_S", "LINK"]
        }
        self._group_dict: dict[tuple[tuple[int, int], tuple[int, int]], Group] = {}
        for seg in self._annotation_list:
            if isinstance(seg, Group):
                for sid1, sid2 in permutations(seg.groups_ids, 2):
                    seg1, seg2 = self._segments[sid1], self._segments[sid2]
                    self._group_dict[(
                        (seg1.start_pos, seg1.end_pos), (seg2.start_pos, seg2.end_pos)
                    )] = seg

    def __len__(self) -> int:
        return len(self._annotation_list)

    def __str__(self) -> str:
        return "\n".join([str(s) for s in self._annotation_list])

    def __getitem__(self, ind: int) -> Annotation:
        return self._annotation_list[ind]

    def get_group(self, anno: str, word1_pos: tuple[int, int], word2_pos: tuple[int, int]) -> Union[int, Group]:
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

    def get_link(self, start_word_pos, end_word_pos) -> Union[int, tuple[Annotation, Segment, Segment]]:
        """
            get link
        """
        start, end = self.get_segment_pos(start_word_pos), self.get_segment_pos(end_word_pos)
        if start == -1 or end == -1:
            return -1
        if (start, end) not in self._link_dict:
            return -1
        return self._link_dict[(start, end)]

    def get_appos(self, word1_pos, word2_pos) -> Union[int, Group]:
        """
            get appos
        """
        return self.get_group("Apposition", word1_pos, word2_pos)

    def get_conj(self, word1_pos, word2_pos) -> Union[int, Group]:
        """
            get conj
        """
        return self.get_group("Parallel", word1_pos, word2_pos)

    def get_segments(self) -> list[Segment]:
        """
            get all seguments
        """
        return self._segments

    def get_segment(self, pos: tuple[int, int]) -> Union[Segment, int]:
        """
            get segment
        """
        spos = self.get_segment_pos(pos)
        if spos == -1:
            return -1
        return self._segments[spos]

    def get_segment_pos(self, pos: tuple[int, int]) -> int:
        """
            get segument
        """
        return self._seg_dict[pos]

    def get_annotations(self) -> list[Annotation]:
        """
            get full annotations
        """
        return self._annotation


def get_annotation_object(seg: list[list[str]]) -> Annotation:
    """
        get annotation object
    """
    return {
        "SEGMENT_S": Segment, "GROUP_S": Group, "LINK_S": Link,
        "SEGMENT": Segment, "GROUP": Group, "LINK": Link
    }[seg[0][1]](seg)
