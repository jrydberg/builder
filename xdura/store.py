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

from datetime import datetime
from xdura.model import Build


def transaction(f):
    """Decorator that runs C{f} inside a database transaction."""
    def wrapper(self, *args, **kw):
        try:
            try:
                return f(self, *args, **kw)
            except Exception:
                self.store.rollback()
                raise
        finally:
            self.store.commit()
    return wrapper


class BuildStore(object):
    """Database facade for builds."""

    def __init__(self, clock, store):
        self.clock = clock
        self.store = store

    @transaction
    def create(self, app, name, image, pstable):
        """Create a build based on app, name, image and pstable.

        @return: The newly created L{Build}.
        """
        build = Build()
        build.app = unicode(app)
        build.name = unicode(name)
        build.image = unicode(image)
        build.pstable = pstable
        build.timestamp = datetime.utcfromtimestamp(self.clock.time())
        self.store.add(build)
        return build

    @transaction
    def remove(self, build):
        """Remove a specific build from the store."""
        self.store.remove(build)

    def builds_for_app(self, app):
        """Return an iterator-like object that will yield all builds
        for a specific app.
        """
        return self.store.find(Build, Build.app == app)

    def by_app_and_name(self, app, name):
        """Return a specific build based on app and name.

        @return: a L{Build} or C{None}.
        """
        return self.store.find(Build, (Build.app == app)
            & (Build.name == name)).one()
