# -*- coding: utf-8 -*-

"""
BCCWJ DepParaPAS Annotation class
"""

from dataclasses import dataclass
from itertools import permutations
from typing import Literal, NamedTuple, Optional, Union


class AnnoPosition(NamedTuple):
    """ AnnoPosition """
    pos1: int
    pos2: int


@dataclass
class DocAnnotation:
    """ DocAnnotation """
    _id: int
    bibinfo: Optional[str]
    attrib: Optional[str]

    def __str__(self) -> str:
        sss = "#! DOC\t{}\n".format(self._id)
        if self.bibinfo is not None:
            sss += "#! DOCID\t{}\t{}\n".format(self._id, self.bibinfo)
        if self.attrib is not None:
            sss += "#! DOCATTR\t{}\n".format(self.attrib)
        return sss


def generate_docannotation(prefix: list[str]) -> DocAnnotation:
    """ generate doc annotation """
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


class Attribute:
    """
        Attribute class
        #! ATTR <Key> <Value> "<Comment>"
    """

    def __init__(self, items: list[str]):
        assert items[0] == '#!' and items[1] == "ATTR"
        self.items: list[str] = items
        self.full_key = items[2]
        self.label: str = items[2].split(":")[1] if len(items[2].split(":")) == 2 else items[2]
        self.value: str = items[3].strip('"')
        self.namespace: Optional[str] = None
        self.namespace = items[2].split(":")[0] if len(items[2].split(":")) == 2 else None
        self.comment: str = items[4].strip('"') if len(items) == 5 else ""

    def __str__(self) -> str:
        __l = '#! ATTR {key} "{value}"'.format(key=self.get_full_key(), value=self.get_value())
        if self.get_comment() != "":
            __l = __l + " " + '"{}"'.format(self.get_comment())
        return __l

    def get_label(self) -> str:
        """ get label """
        return self.label

    def get_full_key(self) -> str:
        """ get key with namespaced """
        return self.full_key

    def get_value(self) -> str:
        """ <value> """
        return self.value

    def get_comment(self) -> str:
        """ <comment> """
        return self.comment


class Annotation:
    """
        Annotation class
    """

    def __init__(self):
        self.identifier: Optional[str] = None
        self.attributes: dict[str, Attribute] = {}
        self.attrs_list: list[str] = []
        self.pos: AnnoPosition
        self.comment: str = ""
        self.name: str = ""

    def _parse(self, segment_lines: list[list[str]]) -> None:
        self.identifier = segment_lines[0][1]
        self.name = segment_lines[0][2]
        for items in segment_lines[1:]:
            if items[1] != "ATTR":
                raise TypeError("is not be ATTR", items[1])
            attr = Attribute(items)
            self.attributes[attr.get_label()] = attr
            self.attributes[attr.get_full_key()] = attr
            self.attrs_list.append(attr.get_full_key())
        self.comment = segment_lines[0][-1]

    def get_attr_value(self, attr_name: str) -> Optional[str]:
        """ get attribute's value """
        assert self.attributes is not None
        if self.attributes.get(attr_name) is None:
            return None
        _val = self.attributes.get(attr_name)
        if _val:
            return _val.get_value()
        return None

    def get_name(self) -> str:
        """ get name """
        return self.name

    def get_comment(self) -> Optional[str]:
        """ get comment """
        return self.comment.strip('"')

    def get_identifier(self) -> Optional[str]:
        """
            get identifier
        """
        return self.identifier

    def __str__(self) -> str:
        raise NotImplementedError


class Segment(Annotation):
    """
        Segment
        #! SEGMENT_S <TagName> <StartPos> <EndPos> "<Comment>"
    """

    def __init__(self, segment_lines: Optional[list[list[str]]]):
        super().__init__()
        if segment_lines:
            self._parse(segment_lines)
        assert self.identifier in ["SEGMENT_S", "SEGMENT"]

    def _parse(self, segment_lines: list[list[str]]) -> None:
        super()._parse(segment_lines)
        _start_pos = int(segment_lines[0][3])
        _end_pos = int(segment_lines[0][4])
        self.pos = AnnoPosition(_start_pos, _end_pos)

    @property
    def start_pos(self) -> int:
        """ start pos """
        return self.pos.pos1

    @property
    def end_pos(self) -> int:
        """ start pos """
        return self.pos.pos2

    def __str__(self) -> str:
        _sss = '#! {iden} {full_name} {spos} {epos} "{comment}"'.format(
            iden=self.get_identifier(), full_name=self.get_name(),
            spos=self.pos.pos1, epos=self.pos.pos2, comment=self.get_comment()
        )
        if len(self.attrs_list) > 0:
            _sss += "\n" + "\n".join([str(self.attributes[attr]) for attr in self.attrs_list])
        return _sss


class Link(Annotation):
    """
        Link object
        #! LINK_S <TagName> <FromSegNo> <ToSegNo> "<Comment>"
    """
    def __init__(self, segment_lines: Optional[list[list[str]]]):
        super().__init__()
        if segment_lines:
            self._parse(segment_lines)
        assert self.identifier in ["LINK", "LINK_S"]

    def _parse(self, segment_lines: list[list[str]]) -> None:
        super()._parse(segment_lines)
        _start_pos = int(segment_lines[0][3])
        _end_pos = int(segment_lines[0][4])
        self.pos = AnnoPosition(_start_pos, _end_pos)

    @property
    def start_pos(self) -> int:
        """ start pos """
        return self.pos.pos1

    @property
    def end_pos(self) -> int:
        """ start pos """
        return self.pos.pos2

    def __str__(self) -> str:
        _sss = '#! {iden} {full_name} {spos} {epos} "{comment}"'.format(
            iden=self.get_identifier(), full_name=self.get_name(),
            spos=self.pos.pos1, epos=self.pos.pos2, comment=self.get_comment()
        )
        if len(self.attrs_list) > 0:
            _sss += "\n" + "\n".join([str(self.attributes[attr]) for attr in self.attrs_list])
        return _sss


class Group(Annotation):
    """
        Group
        #! GROUP_S <TagName> <SegNo>... "<Comment>"
    """
    def __init__(self, segment_lines: Optional[list[list[str]]]):
        super().__init__()
        self.groups_ids: list[int] = []
        if segment_lines:
            self._parse(segment_lines)
        assert self.identifier in ["GROUP", "GROUP_S"]

    def _parse(self, segment_lines: list[list[str]]) -> None:
        super()._parse(segment_lines)
        self.groups_ids = [int(s) for s in segment_lines[0][3:-1] if s != ""]
        if len(self.groups_ids) == 1:
            self.pos = AnnoPosition(self.groups_ids[0], self.groups_ids[0])
        else:
            self.pos = AnnoPosition(self.groups_ids[0], self.groups_ids[1])

    def __str__(self) -> str:
        _sss = '#! {iden} {full_name} {rpos} "{comment}"'.format(
            iden=self.get_identifier(), full_name=self.get_name(),
            rpos=" ".join([str(s) for s in self.groups_ids]), comment=self.get_comment()
        )
        if len(self.attrs_list) > 0:
            _sss += "\n" + "\n".join([str(self.attributes[attr]) for attr in self.attrs_list])
        return _sss


class AnnotationList:
    """
        Annotation list
    """

    def __init__(self, annotation_list: Optional[list[Annotation]]):
        self._annotation_list: list[Annotation] = []
        if annotation_list is not None:
            self._annotation_list.extend(annotation_list)
        self._segments: list[Segment] = [
            seg for seg in self._annotation_list if isinstance(seg, Segment)
        ]
        self._seg_dict: dict[AnnoPosition, int] = {
            s.pos: p for p, s in enumerate(self._segments)
        }
        self._link_dict: dict[tuple[int, int], tuple[Annotation, Segment, Segment]] = {
            (seg.pos.pos1, seg.pos.pos2): (
                seg, self._segments[seg.pos.pos1], self._segments[seg.pos.pos2]
            ) for seg in self._annotation_list
            if seg.get_identifier() in ["LINK_S", "LINK"]
        }
        self._group_dict: dict[tuple[AnnoPosition, AnnoPosition], Group] = {}
        for seg in self._annotation_list:
            if isinstance(seg, Group):
                for sid1, sid2 in permutations(seg.groups_ids, 2):
                    seg1, seg2 = self._segments[sid1], self._segments[sid2]
                    self._group_dict[(seg1.pos, seg2.pos)] = seg

    def __len__(self) -> int:
        return len(self._annotation_list)

    def __str__(self) -> str:
        return "\n".join([str(s) for s in self._annotation_list])

    def __getitem__(self, ind: int) -> Annotation:
        return self._annotation_list[ind]

    def get_group(
        self, anno: str, word1_pos: tuple[int, int], word2_pos: tuple[int, int]
    ) -> Union[Literal[-1], Group]:
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

    def get_link(
        self, start_word_pos: Union[tuple[int, int], AnnoPosition],
        end_word_pos: Union[tuple[int, int], AnnoPosition]
    ) -> Union[Literal[-1], tuple[Annotation, Segment, Segment]]:
        """
            get link
        """
        start, end = self.get_segment_pos(start_word_pos), self.get_segment_pos(end_word_pos)
        if start == -1 or end == -1:
            return -1
        if (start, end) not in self._link_dict:
            return -1
        return self._link_dict[(start, end)]

    def get_appos(
        self, word1_pos: tuple[int, int], word2_pos: tuple[int, int]
    ) -> Union[Literal[-1], Group]:
        """
            get appos
        """
        return self.get_group("Apposition", word1_pos, word2_pos)

    def get_conj(
        self, word1_pos: tuple[int, int], word2_pos: tuple[int, int]
    ) -> Union[Literal[-1], Group]:
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
        return self._annotation_list

    def find_key_annotations(self, key: str) -> list[Annotation]:
        """
            get full annotations
        """
        return [a for a in self._annotation_list if a.get_attr_value(key)]

    def append_segment(self, seg: Union[Segment, list[list[str]]]):
        """ append segment """
        if isinstance(seg, list):
            seg = Segment(seg)
        self._annotation_list.append(seg)
        self._segments.append(seg)
        self._seg_dict = {s.pos: p for p, s in enumerate(self._segments)}

    def remove_segment(self, seg: Segment):
        """ remove segment """
        self._annotation_list.remove(seg)
        self._segments.remove(seg)
        self._seg_dict = {s.pos: p for p, s in enumerate(self._segments)}


def get_annotation_object(seg: list[list[str]]) -> Annotation:
    """
        get annotation object
    """
    return {
        "SEGMENT_S": Segment, "GROUP_S": Group, "LINK_S": Link,
        "SEGMENT": Segment, "GROUP": Group, "LINK": Link
    }[seg[0][1]](seg)
