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

"""The buildserver (aka builder) for Gilliam.

Usage:
  gilliam-builder -h | --help
  gilliam-builder [options] DATABASE

Options:
  -h, --help                Show this screen and exit.
  --version                 Show version and exit.
  --packs-dir PATH          Where build packs live.
                              [default: /var/lib/gilliam/packs].
  --build-script PATH       The script that is used to build the images.
                              [default: /var/lib/gilliam/build].
  --image-dir PATH          Where app images are stored
                              [default: /var/lib/gilliam/images].
  -p PORT, --port PORT      Listen port number [default: 8001].
  --server-name NAME        Hostname where the server can be reached.
                              [default: localhost].
"""

from docopt import docopt
from gevent import pywsgi, monkey
monkey.patch_all(thread=False, time=False)
import logging
import os

from glock.clock import Clock
from storm.locals import Store, create_database

from xdura.api import API
from xdura.builder import Builder
from xdura.store import BuildStore


def main():
    options = docopt(__doc__, version='0.0')
    print options
    logging.basicConfig(level=logging.DEBUG)
    store = Store(create_database(options['DATABASE']))
    clock = Clock()
    build_store = BuildStore(clock, store)
    builder = Builder(logging.getLogger('builder'),
                      options['--build-script'],
                      options['--image-dir'],
                      options['--packs-dir'])
    environ = {'SERVER_NAME': options['--server-name'],
               'SERVER_PORT': options['--port']}
    app = API(logging.getLogger('api'), environ, 
              options['--image-dir'], build_store, builder)
    pywsgi.WSGIServer(('', int(options['--port'])), app).serve_forever()
