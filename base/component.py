# -*- coding: utf-8 -*-

"""
Component
"""

from abc import ABCMeta

JP_SP_MARK = "[JSP]"


class Component(object, metaclass=ABCMeta):
    """
    Abstract class
        this object has below members:
            self.base_file_name: original file name
            self.data_type: data type which used swich the difference format
    """

    def __init__(
            self, data_type, base_file_name=None, word_unit="suw",
            bunsetu_func="none"
    ):
        self.base_file_name = base_file_name
        self.data_type = data_type
        self.word_unit = word_unit
        self.bunsetu_func = bunsetu_func
        self.debug = False

    def __unicode__(self):
        raise NotImplementedError

    def set_debug(self, debug):
        self.debug = debug

    def get_word_unit(self):
        """
            get word unit
        """
        return self.word_unit

    def __parse(self, *args, **kwargs):
        raise NotImplementedError

    def convert(self, is_skip_space=True, sep="\t"):
        """
            sep: separator
        """
        raise NotImplementedError
