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
from gevent import subprocess


class _BuildProcess(object):

    def __init__(self, popen, name, image, pstable):
        self.popen = popen
        self.result = popen.result
        self.name = name
        self.image = image
        self.pstable = pstable
        self.links = []
        popen.rawlink(partial(gevent.spawn, self._finish))

    def link(self, fn):
        """Call C{fn} when the process has finished."""
        self.error = self.popen.returncode
        self.links.append(fn)

    def _finish(self, event):
        self._run_links()

    def _run_links(self):
        for link in self.links:
            link(self)

    def __iter__(self):
        return self

    def next(self):
        """Return output."""
        return next(self.popen.stdout)
        print "READ DATA"
        data = self.popen.stdout.read(1024)
        print "GOT DATA", repr(data)
        if not data:
            raise StopIteration
        return data


class Builder(object):
    """Something that builds images."""

    def __init__(self, log, build_script, image_dir, packs_dir):
        self.log = log
        self.dir = tempfile.mkdtemp()
        self.build_script = build_script
        self.image_dir = image_dir
        self.packs_dir = packs_dir

    def _cleanup(self, *args):
        """Clean up the working directory."""
        # FIXME: should we do this in an async friendly manner?
        shutil.rmtree(self.dir)

    def _checkout_repository(self, repository, commit):
        """Checkout given repository into I{self.dir}."""
        try:
            subprocess.check_call(['git', 'clone', repository, self.dir])
            subprocess.check_call(['git', 'checkout', commit], cwd=self.dir)
        except subprocess.CalledProcessError, cpe:
            raise Exception(cpe.output)

    def _make_name(self):
        """Construct and return a proper name for the build."""
        try:
            output = subprocess.check_output(
                ['git', 'describe', '--tags', '--always'], cwd=self.dir)
        except subprocess.CalledProcessError, cpe:
            self.log.exception(cpe)
            raise
        else:
            print "OUTPUT FROM MAKE NAME", output
            return output.strip()

    def _read_pstable(self):
        """Return the process table."""
        try:
            with open(os.path.join(self.dir, 'Procfile')) as fp:
                return yaml.load(fp)
        except OSError, err:
            if err.errno == errno.ENOENT:
                return {}
            raise

    def issue_build(self, repository, commit):
        """Issue a build request."""
        self._checkout_repository(repository, commit)
        name = self._make_name()
        image = hashlib.md5(repository + commit).hexdigest()
        pstable = self._read_pstable()
        popen = subprocess.Popen([self.build_script, self.dir,
                                  self.packs_dir, os.path.join(
                                      self.image_dir, image)],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 cwd=self.dir)
        process = _BuildProcess(popen, name, image, pstable)
        process.link(self._cleanup)
        return process

        
    
