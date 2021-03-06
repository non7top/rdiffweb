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

import pkg_resources
import unittest

from rdiffweb.librdiff import RdiffPath, FileStatisticsEntry, RdiffRepo, \
    DirEntry, IncrementEntry
import os
from rdiffweb.rdw_helpers import rdwTime

"""
Created on Oct 3, 2015

Module used to test the librdiff.

@author: Patrik Dufresne
"""


class MockRdiffRepo(RdiffRepo):

    def __init__(self):
        self.encoding = 'utf8'
        self.repo_root = pkg_resources.resource_filename(b'rdiffweb', b'tests')  # @UndefinedVariable
        self.data_path = os.path.join(self.repo_root, b'rdiff-backup-data')
        self.root_path = MockRdiffPath(self)


class MockRdiffPath(RdiffPath):

    def __init__(self, repo):
        self.repo = repo
        self.path = pkg_resources.resource_filename(b'rdiffweb', b'tests')  # @UndefinedVariable


class DirEntryTest(unittest.TestCase):

    def setUp(self):
        self.repo = MockRdiffRepo()
        backup_dates = [
            1414871387, 1414871426, 1414871448, 1414871475, 1414871489, 1414873822,
            1414873850, 1414879639, 1414887165, 1414887491, 1414889478, 1414937803,
            1414939853, 1414967021, 1415047607, 1415059497, 1415221262, 1415221470,
            1415221495, 1415221507]
        self.repo.backup_dates = [rdwTime(x) for x in backup_dates]
        self.root_path = self.repo.root_path

    def test_change_dates(self):
        """Check if dates are properly sorted."""
        increments = [
            IncrementEntry(self.root_path, b'my_filename.txt.2014-11-02T17:23:41-05:00.diff.gz'),
            IncrementEntry(self.root_path, b'my_filename.txt.2014-11-02T09:16:43-05:00.missing'),
            IncrementEntry(self.root_path, b'my_filename.txt.2014-11-03T19:04:57-05:00.diff.gz')]
        entry = DirEntry(self.root_path, b'my_filename.txt', False, increments)

        self.assertEquals(
            [rdwTime(1414939853),
             rdwTime(1414967021),
             rdwTime(1415059497)],
            entry.change_dates)

    def test_change_dates_with_exists(self):
        """Check if dates are properly sorted."""
        increments = [
            IncrementEntry(self.root_path, b'my_filename.txt.2014-11-02T17:23:41-05:00.diff.gz'),
            IncrementEntry(self.root_path, b'my_filename.txt.2014-11-02T09:16:43-05:00.missing'),
            IncrementEntry(self.root_path, b'my_filename.txt.2014-11-03T19:04:57-05:00.diff.gz')]
        entry = DirEntry(self.root_path, b'my_filename.txt', True, increments)

        self.assertEquals(
            [rdwTime(1414939853),
             rdwTime(1414967021),
             rdwTime(1415059497),
             rdwTime(1415221507)],
            entry.change_dates)

    def test_restore_dates(self):
        increments = [
            IncrementEntry(self.root_path, b'my_dir.2014-11-05T16:04:30-05:00.dir'),
            IncrementEntry(self.root_path, b'my_dir.2014-11-05T16:04:55-05:00.dir')]
        entry = DirEntry(self.root_path, b'my_dir', False, increments)
        self.assertEquals(
            [rdwTime(1415221470),
             rdwTime(1415221495),
             ],
            entry.restore_dates)

    def test_restore_dates_with_exists(self):
        increments = [
            IncrementEntry(self.root_path, b'my_dir.2014-11-05T16:04:30-05:00.dir'),
            IncrementEntry(self.root_path, b'my_dir.2014-11-05T16:04:55-05:00.dir')]
        entry = DirEntry(self.root_path, b'my_dir', True, increments)
        self.assertEquals(
            [rdwTime(1415221470),
             rdwTime(1415221495),
             rdwTime(1415221507),
             ],
            entry.restore_dates)


class FileStatisticsEntryTest(unittest.TestCase):
    """
    Test the file statistics entry.
    """

    def setUp(self):
        self.repo = MockRdiffRepo()
        self.root_path = self.repo.root_path

    def test_get_mirror_size(self):
        entry = FileStatisticsEntry(self.root_path, b'file_statistics.2014-11-05T16:05:07-05:00.data')
        size = entry.get_mirror_size(b'<F!chïer> (@vec) {càraçt#èrë} $épêcial')
        self.assertEqual(143, size)

    def test_get_source_size(self):
        entry = FileStatisticsEntry(self.root_path, b'file_statistics.2014-11-05T16:05:07-05:00.data')
        size = entry.get_source_size(b'<F!chïer> (@vec) {càraçt#èrë} $épêcial')
        self.assertEqual(286, size)

    def test_get_mirror_size_gzip(self):
        entry = FileStatisticsEntry(self.root_path, b'file_statistics.2014-11-05T16:05:07-05:00.data.gz')
        size = entry.get_mirror_size(b'<F!chïer> (@vec) {càraçt#èrë} $épêcial')
        self.assertEqual(143, size)

    def test_get_source_size_gzip(self):
        entry = FileStatisticsEntry(self.root_path, b'file_statistics.2014-11-05T16:05:07-05:00.data.gz')
        size = entry.get_source_size(b'<F!chïer> (@vec) {càraçt#èrë} $épêcial')
        self.assertEqual(286, size)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
