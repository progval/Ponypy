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

import os
import math
import time
import struct
import pyglet
import logging
import threading
import itertools

from ponypy.common import conf
from ponypy.common import world
from ponypy.common import opcodes
from ponypy.common import structures

from . import mine as minepy

minepy.SECTORSIZE = world.CHUNK_SIZE

SIGTH=50

FACES = (
        ((0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)), # top
        ((0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)), # bottom
        ((0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)),
        ((0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1)),
        ((1, 0, 1), (1, 1, 1), (1, 1, 0), (1, 0, 0)),
        ((1, 0, 1), (1, 1, 1), (0, 1, 1), (0, 0, 1)),
        )

class _Textures:
    def __init__(self):
        pass
    def get(self, block):
        type_ = opcodes.BLOCKTYPES[block.blockType]
        if type_ == 'dirt':
            return minepy.GRASS
        raise NotImplementedError()
textures = _Textures()

class PygletClient:
    def __init__(self, router):
        self.router = router
        router.add_callback(self)
        self.clients = structures.ClientList()
        self.entities = structures.EntityList()
        self.entity = None
        self.world = world.World(world.get_fetch_generator(router, router._server))
        self.window = Window(self)

    def get_color_at(self, x, y):
        """Return the expected (r, g, b) color of the pixel at the given
        coordinates."""
        if not self.entity:
            return (0, 0, 0)
        (block, position) = self.world.getPointedBlock(self.entity.position,
                self.entity.direction)

    def on_Connect(self, server, opcode):
        logging.debug('Got CONNECT packet. Version: %i.%i.' %
                (opcode.protocol.majorVersion, opcode.protocol.minorVersion))
        if opcode.protocol.majorVersion != opcodes.PROTOCOL_VERSION.majorVersion:
            logging.error('Incompatible major version.')
            raise server.close_connection('Incompatible major version.')
        if opcode.protocol.minorVersion != opcodes.PROTOCOL_VERSION.minorVersion:
            logging.warning('Incompatible minor version.')

        self.clientId = opcode.clientId

        op = opcodes.Login(username='', password='')
        server.send(op)
        pyglet.app.run()

    def on_EntitySpawn(self, server, opcode):
        self.entities[opcode.entity.id] = opcode.entity
        if opcode.entity.playedBy == self.clientId:
            self.entity = opcode.entity

    def on_BlockUpdate(self, server, opcode):
        self.world.set_block(opcode.block)

class Model(minepy.Model):
    def initialize(self):
        pass
minepy.Model = Model

class Window(minepy.Window):
    def __init__(self, client, *args, **kwargs):
        super(Window, self).__init__(*args, **kwargs)
        client.router.add_callback(self)
        self.client = client
        self.flying = True

    def on_BlockUpdate(self, server, opcode):
        if opcode.block.block.blockType != 0:
            self.model.init_block(opcode.block.coordinates,
                    textures.get(opcode.block.block))

    def on_EntitySpawn(self, server, opcode):
        if opcode.entity.playedBy == self.client.clientId:
            (x, y, z) = self.position = opcode.entity.position
            for coordinates in itertools.product(range(x-SIGTH, x+SIGTH, world.CHUNK_SIZE),
                                                  range(y-SIGTH, y+SIGTH, world.CHUNK_SIZE),
                                                  range(z-SIGTH, z+SIGTH, world.CHUNK_SIZE)):
                if sum(map(lambda i:(i[0]-i[1])**2, zip(self.position, coordinates))) <= SIGTH**2:
                    self.show_chunk(coordinates)

    def show_chunk(self, coordinates, chunk=None):
        chunk = chunk or self.client.world.get_chunk(*coordinates)
        (x, y, z) = coordinates
        i = 0
        for (x2,y2,z2) in itertools.product(range(0, world.CHUNK_SIZE), range(0, world.CHUNK_SIZE), range(0, world.CHUNK_SIZE)):
            block = opcodes.Block.from_bytes(chunk[i:i+opcodes.Block.SIZE])
            i += opcodes.Block.SIZE
            if block.blockType != 0:
                self.model.init_block((x+x2, y+y2, z+z2), textures.get(block))
                self.model.show_block((x+x2, y+y2, z+z2), False)
        self.model.show_blocks()



def update(dt):
    import time
    time.sleep(0.005)
pyglet.clock.schedule_interval(update, 0.01)
