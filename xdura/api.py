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
from routes import Mapper, URLGenerator
from webob import Response
from webob.dec import wsgify
from webob.exc import HTTPNotFound, HTTPInternalServerError
import errno
import hashlib
import os.path

from xdura import static


class ImageResource(object):
    """Resource handler that is responsible for serving out image
    files.  The only allowed operation is C{GET}.
    """
    CONTENT_TYPE = 'application/octet-stream'

    def __init__(self, image_dir):
        self.image_dir = image_dir

    def show(self, request, image, format=None):
        """Return content of image or 404."""
        try:
            fp = open(os.path.join(self.image_dir, image))
            return static.make_response(fp, self.CONTENT_TYPE)
        except OSError, err:
            if err.errno == errno.ENOENT:
                raise HTTPNotFound()
            else:
                raise HTTPInternalServerError()


class BuildResource(object):
    """Resource handler for our builds."""

    def __init__(self, log, url, builder):
        self.log = log
        self.url = url
        self.builder = builder

    def create(self, request):
        app, commit, text = self._assert_request_params(
            request, 'app', 'commit', 'text')
        self.log.info(dict(request.headers))
        #request.is_body_readable = True
        process = self.builder(app, commit, text, request.body_file)
        response = Response(status=200)
        response.app_iter = process
        return response

    def _assert_request_params(self, request, *params):
        values = []
        for param in params:
            if not param in request.params:
                raise HTTPBadRequest()
            values.append(request.params[param])
        return values


class API(object):
    """The REST API that we expose."""

    def __init__(self, log, environ, image_dir, builder):
        self.mapper = Mapper()
        self.url = URLGenerator(self.mapper, environ)
        self.resources = {
            'image': ImageResource(image_dir),
            'build': BuildResource(log, self.url, builder)
            }
        self.mapper.connect("build", "/build", controller="build",
                            action="create")
        self.mapper.collection("images", "image", controller='image',
            path_prefix='/image', collection_actions=[],
            member_actions=['show'], member_prefix='/{image}')

    @wsgify
    def __call__(self, request):
        route = self.mapper.match(request.path, request.environ)
        if route is None:
            raise HTTPNotFound()
        resource = self.resources[route.pop('controller')]
        action = route.pop('action')
        return getattr(resource, action)(request, **route)
