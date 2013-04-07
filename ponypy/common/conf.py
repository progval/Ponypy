# This file is part of Ponypy.
# 
# Ponypy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Ponypy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Ponypy.  If not, see <http://www.gnu.org/licenses/>.

__all__ = ['acquire', 'release', 'save', 'get', 'set']

import os
import json
import logging
from threading import Lock


def get_fd(mode='w+'):
    global _path
    open(_path, 'a') # Create the file
    return open(_path, mode)

def save():
    global _conf
    conf = json.dumps(_conf, sort_keys=True, indent=4)
    with get_fd() as file:
        file.write(conf)

_path = os.path.expanduser('~/.ponypy/conf.json')
if not os.path.isfile(_path):
    logging.info('Creating new configuration file.')
    with get_fd() as file:
        file.write('{}')

try:
    with get_fd('r') as file:
        _conf = json.load(file)
except Exception as e:
    logging.error('Configuration could not be parsed. Creating backup and '
            'creating new file.')
    os.rename(_path, _path + '.bak')
    with get_fd() as file:
        file.write('{}')
    _conf = {}

_lock = Lock()

def acquire(blocking=False):
    global _lock
    _lock.acquire(blocking)

def release():
    global _lock
    _lock.release()
    save()

def get(path, default='', node=None):
    global _conf
    if isinstance(path, str):
        path = path.split('.')
    if node is None:
        node = _conf
    if path == []:
        return node
    name = path[0]
    if name not in node:
        if len(path) == 1:
            node[name] = default
            save()
        else:
            node[name] = {}
    return get(path[1:], default, node[name])

def set(path, value, node=None):
    global _conf
    if isinstance(path, str):
        path = path.split('.')
    if node is None:
        node = _conf
    name = path[0]
    path = path[1:]
    if path == []:
        node[name] = value
        save()
        return
    if name not in node:
        if path == []:
            node[name] = default
        else:
            node[name] = create_node(path[0])
    set(path, value, node[name])
