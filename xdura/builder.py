# Copyright 2013 Johan Rydberg.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from functools import partial
import gevent
import tempfile
import shutil
import yaml
import hashlib
import errno
import os
from gevent.event import AsyncResult
from gevent import subprocess


class _BuildProcess(object):

    def __init__(self, popen, app, commit, text):
        self.popen = popen
        self.app = app
        self.commit = commit
        self.text = text

    def start(self, input_file):
        def _pipe():
            try:
                for data in input_file:
                    self.popen.stdin.write(data)
            finally:
                self.popen.stdin.close()
        gevent.spawn(_pipe)

    def __iter__(self):
        return iter(self.popen.stdout)


class Builder(object):
    """Something that builds images."""

    def __init__(self, log, build_script):
        self.log = log
        self.build_script = build_script

    def __call__(self, app, commit, text, input_file):
        """Issue a build request."""
        build_script = os.path.join(os.getcwd(), self.build_script)
        popen = subprocess.Popen([build_script, app, commit, text],
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 cwd=os.getcwd())
        process = _BuildProcess(popen, app, commit, text)
        process.start(input_file)
        return process
