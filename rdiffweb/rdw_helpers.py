#!/usr/bin/python
# -*- coding: utf-8 -*-
# rdiffweb, A web interface to rdiff-backup repositories
# Copyright (C) 2014 rdiffweb contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import sys
import calendar
import os
import time
import urllib

# Get the system encoding
system_charset = sys.getfilesystemencoding()


def decode_s(value, errors='strict'):
    """
    Convert charset to system unicode. Default is 'strict'. Other possible
    values are 'ignore' and 'replace'.
    """
    assert isinstance(value, str)
    return value.decode(system_charset, errors)


def encode_s(value):
    """Convert unicode to system charset."""
    if value is None:
        return None
    assert isinstance(value, unicode)
    return value.encode(system_charset)


def quote_url(url, safe=None):
    """encode URL but try to keep encoding (unicode vs str)"""
    # If URL is None, return None
    if not url:
        return url

    # If safe is define, make sure it's the same object type (either unicode
    # or str)
    if safe:
        assert type(url) == type(safe)

    # Handle case when URL is unicode.
    is_unicode = False
    if isinstance(url, unicode):
        is_unicode = True
        url = url.encode('utf8')
    if safe and isinstance(safe, unicode):
        safe = safe.encode('utf8')

    if not safe:
        safe = b"/"

    # URL encode
    value = urllib.quote(url, safe)

    if is_unicode:
        value = value.decode('utf8')

    return value


def unquote_url(encodedUrl):
    if not encodedUrl:
        return encodedUrl
    return urllib.unquote(encodedUrl)


class rdwTime:

    """Time information has two components: the local time, stored in GMT as
    seconds since Epoch, and the timezone, stored as a seconds offset. Since
    the server may not be in the same timezone as the user, we cannot rely on
    the built-in localtime() functions, but look at the rdiff-backup string
    for timezone information.  As a general rule, we always display the
    "local" time, but pass the timezone information on to rdiff-backup, so
    it can restore to the correct state"""

    def __init__(self, seconds=0):
        assert isinstance(seconds, int)
        self.timeInSeconds = seconds
        self.tzOffset = 0

    def initFromInt(self, seconds):
        assert isinstance(seconds, int)
        self.timeInSeconds = seconds
        self.tzOffset = 0

    def initFromMidnightUTC(self, daysFromToday):
        self.timeInSeconds = time.time()
        self.timeInSeconds -= self.timeInSeconds % (24 * 60 * 60)
        self.timeInSeconds += daysFromToday * 24 * 60 * 60
        self.tzOffset = 0

    def initFromString(self, timeString):
        try:
            date, daytime = timeString[:19].split("T")
            year, month, day = map(int, date.split("-"))
            hour, minute, second = map(int, daytime.split(":"))
            assert 1900 < year < 2100, year
            assert 1 <= month <= 12
            assert 1 <= day <= 31
            assert 0 <= hour <= 23
            assert 0 <= minute <= 59
            assert 0 <= second <= 61  # leap seconds

            timetuple = (year, month, day, hour, minute, second, -1, -1, 0)
            self.timeInSeconds = calendar.timegm(timetuple)
            self.tzOffset = self._tzdtoseconds(timeString[19:])
            self.getTimeZoneString()  # to get assertions there

        except (TypeError, ValueError, AssertionError):
            raise ValueError(timeString)

    def getLocalDaysSinceEpoch(self):
        return self.getLocalSeconds() // (24 * 60 * 60)

    def getLocalSeconds(self):
        return self.timeInSeconds

    def getSeconds(self):
        return self.timeInSeconds - self.tzOffset

    def getDisplayString(self):
        return decode_s(time.strftime(encode_s(u"%Y-%m-%d %H:%M:%S"),
                                      time.gmtime(self.getLocalSeconds())))

    def getTimeZoneString(self):
        if self.tzOffset:
            tzinfo = self._getTimeZoneDisplayInfo()
            return "%s%s:%s" % (tzinfo["plusMinus"], tzinfo["hours"], tzinfo["minutes"])
        else:
            return "Z"

    def setTime(self, hour, minute, second):
        year = time.gmtime(self.timeInSeconds)[0]
        month = time.gmtime(self.timeInSeconds)[1]
        day = time.gmtime(self.timeInSeconds)[2]
        self.timeInSeconds = calendar.timegm(
            (year, month, day, hour, minute, second, -1, -1, 0))

    def _getTimeZoneDisplayInfo(self):
        hours, minutes = divmod(abs(self.tzOffset) / 60, 60)
        assert 0 <= hours <= 23
        assert 0 <= minutes <= 59

        if self.tzOffset > 0:
            plusMinus = "+"
        else:
            plusMinus = "-"
        return {"plusMinus": plusMinus,
                "hours": "%02d" % hours,
                "minutes": "%02d" % minutes}

    def _tzdtoseconds(self, tzd):
        """Given w3 compliant TZD, converts it to number of seconds from UTC"""
        if tzd == "Z":
            return 0
        assert len(tzd) == 6  # only accept forms like +08:00 for now
        assert (tzd[0] == "-" or tzd[0] == "+") and tzd[3] == ":"

        if tzd[0] == "+":
            plusMinus = 1
        else:
            plusMinus = -1

        return plusMinus * 60 * (60 * int(tzd[1:3]) + int(tzd[4:]))

    def __cmp__(self, other):
        assert isinstance(other, rdwTime)
        return cmp(self.getSeconds(), other.getSeconds())

    def __eq__(self, other):
        return (isinstance(other, rdwTime) and
                self.getSeconds() == other.getSeconds())

    def __hash__(self):
        return hash(self.getSeconds())

    def __str__(self):
        """return utf-8 string"""
        return str(self.getDisplayString())

    def __unicode__(self):
        return self.getDisplayString()

    def __repr__(self):
        """return second since epoch"""
        return str(self.getSeconds())

# Taken from ASPN:
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/259173


class groupby(dict):

    def __init__(self, seq, key=lambda x: x):
        for value in seq:
            k = key(value)
            self.setdefault(k, []).append(value)
    __iter__ = dict.iteritems
