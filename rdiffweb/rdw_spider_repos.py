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

import os
import librdiff
import logging
import threading
from rdiffweb.rdw_helpers import encode_s

# Define the logger
logger = logging.getLogger(__name__)


# Returns pid of started process, or 0 if no process was started
def start_repo_spider_thread(killEvent, app):
    # Get refresh interval from app config.
    spiderInterval = app.cfg.get_config_bool("autoUpdateRepos", "False")

    # Start the thread.
    newThread = SpiderReposThread(killEvent, app, spiderInterval)
    newThread.start()


class SpiderReposThread(threading.Thread):

    def __init__(self, killEvent, app, spiderInterval=False):
        """Create a new SpiderRepo to refresh the users repositories."""
        self.killEvent = killEvent
        self.app = app
        # Make sure it's an integer.
        if spiderInterval:
            assert isinstance(spiderInterval, int)
        self.spiderInterval = spiderInterval
        threading.Thread.__init__(self)

    def run(self):
        if self.spiderInterval:
            while True:
                find_repos_for_all_users(self.app)
                self.killEvent.wait(60 * self.spiderInterval)
                if self.killEvent.isSet():
                    return


def _find_repos(dirToSearch, depth=3):
    # TODO Should be a configuration
    # Limit the depthness
    if depth <= 0:
        return

    try:
        dirEntries = os.listdir(dirToSearch)
    except:
        # Ignore error.
        return
    if librdiff.RDIFF_BACKUP_DATA in dirEntries:
        yield dirToSearch

    for entry in dirEntries:
        entryPath = os.path.join(dirToSearch, entry)
        if os.path.isdir(entryPath) and not os.path.islink(entryPath):
            for x in _find_repos(entryPath, depth - 1):
                yield x


def find_repos_for_user(user, userdb):
    logger.debug("find repos for [%s]" % user)
    user_root = encode_s(userdb.get_user_root(user))
    repo_paths = list(_find_repos(user_root))

    def striproot(path):
        if not path[len(user_root):]:
            return "/"
        return path[len(user_root):]
    repo_paths = map(striproot, repo_paths)
    logger.debug("set user [%s] repos: %s " % (user, repo_paths))
    userdb.set_repos(user, repo_paths)


def find_repos_for_all_users(app):
    """Refresh all users repositories using the given `app`."""
    user_db = app.userdb
    if not user_db.supports('set_repos'):
        return

    users = user_db.list()
    for user in users:
        find_repos_for_user(user, user_db)
