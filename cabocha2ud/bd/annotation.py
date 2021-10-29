# -*- coding: utf-8 -*-

"""
BCCWJ DepParaPAS Annotation class
"""

from typing import Literal, Optional, Union, NamedTuple

from collections import defaultdict
from itertools import permutations


class AnnoPosition(NamedTuple):
    pos1: int
    pos2: int



class DocAnnotation(NamedTuple):
    id: int
    bibinfo: Optional[str]
    attrib: Optional[str]

    def __str__(self) -> str:
        sss = "#! DOC\t{}\n".format(self.id)
        if self.bibinfo is not None:
            sss += "#! DOCID\t{}\t{}\n".format(self.id, self.bibinfo)
        if self.attrib is not None:
            sss += "#! DOCATTR\t{}\n".format(self.attrib)
        return sss


def generate_docannotation(prefix: list[str]) -> DocAnnotation:
    _id: int = -1
    bibinfo: Optional[str] = None
    attrib: Optional[str] = None
    for ppp in prefix:
        data = ppp.split()
        assert data[0] == "#!"
        if data[1] == "DOC":
            _id = int(data[2])
        if data[1] == "DOCID":
            _id = int(data[2])
            bibinfo = data[3]
        if data[1] == "DOCATTR":
            attrib = ppp.split("\t")[1]
    return DocAnnotation(_id, bibinfo, attrib)


class Annotation(object):
    """
        annotation class
    """

    def __init__(self, segment_lines: list[list[str]]):
        self.segment_lines: list[list[str]] = segment_lines
        self.identifier: Optional[str] = None
        self.start_pos: int = -1
        self.end_pos: int = -1
        self.comment: Optional[str] = None
        self.name: str = ""

    def get_name(self) -> str:
        return self.name

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

    def __init__(self, segment_lines: list[list[str]]):
        super(Segment, self).__init__(segment_lines)
        self.attributes: dict[str, str] = {}
        self.position: AnnoPosition
        self.__parse()
        assert self.identifier in ["SEGMENT_S", "SEGMENT"]

    def get_attr(self, attr_name: str) -> Optional[str]:
        return self.attributes.get(attr_name)

    def __parse(self) -> None:
        self.identifier = self.segment_lines[0][1]
        self.name = self.segment_lines[0][2]
        self.start_pos = int(self.segment_lines[0][3])
        self.end_pos = int(self.segment_lines[0][4])
        self.position = AnnoPosition(self.start_pos, self.end_pos)
        self.comment = self.segment_lines[0][5]
        for items in self.segment_lines[1:]:
            if items[1] != "ATTR":
                raise TypeError("is not be ATTR", items[1])
            self.attributes[items[2]] = items[3]


class Link(Annotation):
    """
        link
    """
    def __init__(self, segment_lines: list[list[str]]):
        super(Link, self).__init__(segment_lines)
        # assert len(segment_lines) == 1  # 本来はこうのはず...?
        self.__parse()
        assert self.identifier in ["LINK", "LINK_S"]

    def __parse(self) -> None:
        self.identifier = self.segment_lines[0][1]
        self.name = self.segment_lines[0][2]
        self.start_pos = int(self.segment_lines[0][3])
        self.end_pos = int(self.segment_lines[0][4])
        self.position = AnnoPosition(self.start_pos, self.end_pos)
        self.comment = self.segment_lines[0][5]


class Group(Annotation):
    """
        Group
    """
    def __init__(self, segment_lines: list[list[str]]):
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
        self._annotation_list: list[Annotation] = list(annotation_list)
        self._segments: list[Segment] = [
            seg for seg in self._annotation_list if isinstance(seg, Segment)
        ]
        self._annotation: list[Annotation] = [
            seg for seg in self._annotation_list
            if seg.get_identifier() not in ["SEGMENT_S", "SEGMENT"]
        ]
        self._seg_dict: dict[AnnoPosition, int] = {
            s.position: p for p, s in enumerate(self._segments)
        }
        self._link_dict: dict[tuple[int, int], tuple[Annotation, Segment, Segment]] = {
            (seg.start_pos, seg.end_pos): (
                seg, self._segments[seg.start_pos], self._segments[seg.end_pos]
            ) for seg in self._annotation_list
            if seg.get_identifier() in ["LINK_S", "LINK"]
        }
        self._group_dict: dict[tuple[AnnoPosition, AnnoPosition], Group] = {}
        for seg in self._annotation_list:
            if isinstance(seg, Group):
                for sid1, sid2 in permutations(seg.groups_ids, 2):
                    seg1, seg2 = self._segments[sid1], self._segments[sid2]
                    self._group_dict[(seg1.position, seg2.position)] = seg

    def __len__(self) -> int:
        return len(self._annotation_list)

    def __str__(self) -> str:
        return "\n".join([str(s) for s in self._annotation_list])

    def __getitem__(self, ind: int) -> Annotation:
        return self._annotation_list[ind]

    def get_group(self, anno: str, word1_pos: tuple[int, int], word2_pos: tuple[int, int]) -> Union[Literal[-1], Group]:
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

    def get_link(self, start_word_pos: Union[tuple[int, int], AnnoPosition], end_word_pos: Union[tuple[int, int], AnnoPosition]) -> Union[Literal[-1], tuple[Annotation, Segment, Segment]]:
        """
            get link
        """
        start, end = self.get_segment_pos(start_word_pos), self.get_segment_pos(end_word_pos)
        if start == -1 or end == -1:
            return -1
        if (start, end) not in self._link_dict:
            return -1
        return self._link_dict[(start, end)]

    def get_appos(self, word1_pos: tuple[int, int], word2_pos: tuple[int, int]) -> Union[Literal[-1], Group]:
        """
            get appos
        """
        return self.get_group("Apposition", word1_pos, word2_pos)

    def get_conj(self, word1_pos: tuple[int, int], word2_pos: tuple[int, int]) -> Union[Literal[-1], Group]:
        """
            get conj
        """
        return self.get_group("Parallel", word1_pos, word2_pos)

    def get_segments(self) -> list[Segment]:
        """
            get all seguments
        """
        return self._segments

    def get_segment(self, pos: Union[tuple[int, int], AnnoPosition]) -> Union[Segment, Literal[-1]]:
        """
            get segment
        """
        spos = self.get_segment_pos(pos)
        if spos == -1:
            return -1
        return self._segments[spos]

    def get_segment_pos(self, pos: Union[tuple[int, int], AnnoPosition]) -> int:
        """
            get segument
        """
        if isinstance(pos, tuple):
            pos = AnnoPosition(pos[0], pos[1])
        if pos not in self._seg_dict:
            return -1
        return self._seg_dict[pos]

    def get_annotations(self) -> list[Annotation]:
        """
            get full annotations
        """
        return self._annotation

    def append_segment(self, seg: Union[Segment, list[list[str]]]):
        if isinstance(seg, list):
            seg = Segment(seg)
        self._annotation_list.append(seg)
        self._segments.append(seg)
        self._seg_dict = {
            s.position: p for p, s in enumerate(self._segments)
        }

    def remove_segment(self, seg: Segment):
        self._annotation_list.remove(seg)
        self._segments.remove(seg)
        self._seg_dict = {
            s.position: p for p, s in enumerate(self._segments)
        }

def get_annotation_object(seg: list[list[str]]) -> Annotation:
    """
        get annotation object
    """
    return {
        "SEGMENT_S": Segment, "GROUP_S": Group, "LINK_S": Link,
        "SEGMENT": Segment, "GROUP": Group, "LINK": Link
    }[seg[0][1]](seg)
