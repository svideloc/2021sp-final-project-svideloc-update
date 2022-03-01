#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
 Placeholder for future Algorithm definitions

"""


class Algorithm:
    """Class for running greedy apporach on a list of prisms to optimize
    querey search space

    :param name: algorithm name
    :type name: str
    """

    name: str = ""

    def __init__(self, name):
        self.name = name

    def run(self):
        raise NotImplementedError(())
