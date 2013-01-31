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


class ImageResource(object):
    """Resource handler that is responsible for serving out image
    files.  The only allowed operation is C{GET}."""
    CONTENT_TYPE = 'application/octet-stream'

    def __init__(self, image_dir):
        self.image_dir = image_dir

    def show(self, request, image, format=None):
        """Return content of image or 404."""
        try:
            with open(os.path.join(self.image_dir, image)) as fp:
                return static.make_response(fp, self.CONTENT_TYPE)
        except OSError, err:
            if err.errno == errno.ENOENT:
                raise HTTPNotFound()
            else:
                raise HTTPInternalServerError()


class BuildResource(object):
    """Resource handler for our builds."""
    ITEM_KIND = 'gilliam#build'
    COL_KIND = 'gilliam#collection+build'

    def __init__(self, log, url, store, builder):
        self.log = log
        self.url = url
        self.store = store
        self.builder = builder

    def _make_build(self, build):
        """Create a representation of a build."""
        return dict(app=build.app, name=build.name,
                    image=self.url('image', image=build.image,
                                   qualified=True),
                    pstable=build.pstable,
                    created_at=build.timestamp.isoformat(' '),
                    self=self.url('build', app=build.app,
                                  name=build.name))

    def _get(self, app, name):
        build = self.store.by_app_and_name(app, name)
        if build is None:
            raise HTTPNotFound()
        return build

    def _assert_request_data(self, request):
        if not request.json:
            raise HTTPBadRequest()
        return request.json

    def _build_done(self, app, process):
        """The process was done."""
        # FIXME: what about the case if this fails?  maybe that is not
        # the end of the world.
        if not process.error:
            self.store.create(app, process.name,
                              process.image, process.pstable)

    def create(self, request, app, format=None):
        data = self._assert_request_data(request)
        process = self.builder.issue_build(data['repository'],
             data.get('commit', 'master'))
        process.link(partial(self._build_done, app))
        response = Response(status=202)
        response.headers.add('Location', self.url('build', app=app,
            name=process.name))
        response.app_iter = process
        return response

    def index(self, request, app, format=None):
        items = []
        for build in self.store.builds_for_app(app):
            items.append(self._make_build(build))
        collection = {'kind': self.COL_KIND, 'items': items}
        return Response(json=collection, status=200)

    def show(self, request, app, name, format=None):
        build = self._get(app, name)
        return Response(json=self._make_build(build), status=200)

    def delete(self, request, id, format=None):
        # FIXME: this does not remove the image for some reason.
        self.store.remove(self._get(app, name))
        return Response(status=204)


class API(object):
    """The REST API that we expose."""

    def __init__(self, log, environ, image_dir, build_store, builder):
        self.mapper = Mapper()
        self.url = URLGenerator(self.mapper, environ)
        self.resources = {
            'image': ImageResource(image_dir),
            'build': BuildResource(log, self.url, build_store, builder)
            }
        self.mapper.collection("builds", "build", controller='build',
            path_prefix='/build/{app}', collection_actions=['index', 'create'],
            member_actions=['show', 'delete'], member_prefix='/{name}')
        # FIXME: maybe it is better to just do a simple mapper.connect
        self.mapper.collection("images", "image", controller='build',
            path_prefix='/build', collection_actions=[],
            member_actions=['show'], member_prefix='/{image}')

    @wsgify
    def __call__(self, request):
        route = self.mapper.match(request.path, request.environ)
        if route is None:
            raise HTTPNotFound()
        resource = self.resources[route.pop('controller')]
        action = route.pop('action')
        return getattr(resource, action)(request, **route)
