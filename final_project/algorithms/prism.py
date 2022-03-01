#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dataclasses import dataclass
from stringcase import camelcase
from dataclass_dict_convert import dataclass_dict_convert

from .utils import create_uuid_int64


@dataclass_dict_convert(dict_letter_case=camelcase)
@dataclass()
class Prism:
    """
    Class for defining a rectangular prism for a specific space time,
    a time and distance buffer must be provided to create the Prism
    All of the magic of this class happens in projected space

    :param x: x centerpoint
    :type x: float
    :param y: y centerpoint
    :type y: float
    :param lon: lon centerpoint
    :type lon: float
    :param lat: lat centerpoint
    :type lat: float
    :param timestamp: timestamp in seconds since epoch
    :type timestamp: float
    :param name: id of object
    :type name: str
    :param x_buffer: buffer distance in meters for x
    :type x_buffer: float
    :param y_buffer: buffer distance in meters for y
    :type y_buffer: float
    :param temporal_buffer: time buffer in seconds
    :type temporal_buffer: float
    :param uuid: unique id
    :type uuid: int
    :param crs: the crs we are in
    :type crs: str
    """

    lat: float
    lon: float
    x: float  # meters from projection origin (0 by default)
    y: float  # meters (0 by default)
    timestamp: float  # seconds since epoch
    name: str  # name
    x_buffer: float  # in meters
    y_buffer: float  # in meters
    temporal_buffer: float  # in seconds
    crs: str  # in_crs
    uuid: int = None  # uuid will be set if not specified

    def __post_init__(self):
        self.uuid = self.uuid or create_uuid_int64()

    @property
    def xmin(self):
        """x min"""
        return self.x - self.x_buffer

    @property
    def xmax(self):
        """x max"""
        return self.x + self.x_buffer

    @property
    def ymin(self):
        """y min"""
        return self.y - self.y_buffer

    @property
    def ymax(self):
        """y max"""
        return self.y + self.y_buffer

    @property
    def tmin(self):
        """min time"""
        return self.timestamp - self.temporal_buffer

    @property
    def tmax(self):
        """max time"""
        return self.timestamp + self.temporal_buffer

    @property
    def bounds(self):
        """returns tuple (xmin, ymin, tmin, xmax, ymax, tmax)"""
        return (self.xmin, self.ymin, self.tmin, self.xmax, self.ymax, self.tmax)

    @property
    def length_x(self):
        """x lenghth"""
        return self.xmax - self.xmin

    @property
    def length_y(self):
        """y lenghth"""
        return self.ymax - self.ymin

    @property
    def length_t(self):
        """time lenghth"""
        return self.tmax - self.tmin

    @property
    def volume(self):
        """Returns volume as a float"""
        return (
            (self.xmax - self.xmin) * (self.ymax - self.ymin) * (self.tmax - self.tmin)
        )
