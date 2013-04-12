#!/usr/bin/env python3

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

import logging
import argparse

from ponypy.common import routers
from ponypy.client import PygletClient
from ponypy.server import CreativeServer

parser = argparse.ArgumentParser(prog='ponypy-client.py',
        description='Ponyca client written in Python.')
parser.add_argument('--log',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
args = parser.parse_args()

if args.log:
    logging.basicConfig(level=getattr(logging, args.log))

server_router = routers.LocalServerRouter()
server = CreativeServer(server_router)

client_router = routers.LocalClientRouter(server_router)
client = PygletClient(client_router)
server_router.add_client(client_router)
