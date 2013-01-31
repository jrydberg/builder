m# Copyright 2013 Johan Rydberg.
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

"""Functionality for serving out static files using WebOb."""

import os
from webob import Response

class FileIterable(object):

    def __init__(self, file):
        self.file = file

    def __iter__(self):
        return FileIterator(self.file)


class FileIterator(object):
    chunk_size = 4096

    def __init__(self, file):
        self.file = file

    def __iter__(self):
        return self

    def next(self):
        chunk = self.file.read(self.chunk_size)
        if not chunk:
             raise StopIteration
        return chunk


def make_response(file, content_type):
    response = Response(content_type=content_type)
    response.app_iter = FileIterable(file)
    stat = os.fstat(file.fileno())
    response.content_length = stat.st_size
    response.last_modified = stat.st_mtime
    response.etag = '%s-%s' % (stat.st_mtime, stat.st_size)
    return response
