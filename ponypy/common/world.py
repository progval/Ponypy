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

__all__ = ['World', 'flat_generator', 'get_fetch_generator']

import threading
import itertools

from . import opcodes
from . import routers

CHUNK_SIZE = 10

def get_chunk_id(x, y, z):
    return (x//CHUNK_SIZE, y//CHUNK_SIZE, z//CHUNK_SIZE)
def get_block_index(x, y, z):
    (x, y, z) = (x%CHUNK_SIZE, y%CHUNK_SIZE, z%CHUNK_SIZE)
    return ((x*CHUNK_SIZE + y)*CHUNK_SIZE + z)*opcodes.Block.SIZE

class World:
    def __init__(self, generator):
        self.chunks = {}
        self._generator = generator
    def generate_chunk(self, coordinates):
        self._generator(self, get_chunk_id(*coordinates))

    def set_block(self, block, coordinates=None):
        if not coordinates:
            coordinates = block.coordinates
            block = block.block
        chunk_id = get_chunk_id(*coordinates)
        if chunk_id not in self.chunks:
            return
        i = get_block_index(*coordinates)
        self.chunks[chunk_id][i:i+opcodes.Block.SIZE] = bytes(block)
    
    def set_chunk(self, x, y, z, chunk):
        if isinstance(chunk, bytes):
            chunk = bytearray(chunk)
        self.chunks[get_chunk_id(x, y, z)] = chunk
    def get_chunk(self, x, y, z):
        id_ = get_chunk_id(x, y, z)
        if id_ not in self.chunks:
            return self._generator(self, *id_)
        else:
            return self.chunks[id_]

    def __contains__(self, coordinates):
        return get_block_index(*coordinates) in self.chunks

    def _get_raw(self, coordinates):
        assert isinstance(coordinates, tuple), coordinates
        assert len(coordinates) == 3, coordinates
        chunk_id = get_chunk_id(*coordinates)
        if chunk_id not in self.chunks:
            self._generator(self, *chunk_id)
        index = get_block_index(*coordinates)
        data = self.chunks[chunk_id][index:index+opcodes.Block.SIZE]
        return data
    def __getitem__(self, coordinates):
        return opcodes.Block.from_bytes(self._get_raw(coordinates))

    def __iter__(self):
        for (x,y,z) in self.chunks:
            for coord in itertools.product(range(x*CHUNK_SIZE, (x+1)*CHUNK_SIZE),
                                           range(y*CHUNK_SIZE, (y+1)*CHUNK_SIZE),
                                           range(z*CHUNK_SIZE, (z+1)*CHUNK_SIZE)
                                           ):
                if self._get_raw(coord) != b'\x00\x00\x00\x00':
                    yield coord

    def __len__(self):
        return len(self.chunks)*(CHUNK_SIZE**3)

class _WorldFetcher:
    def __init__(self, router):
        assert isinstance(router, routers.AbstractServerRepresentation)
        self._router = router
        self._events = {}
        self._results = {}
    def on_ChunkUpdate(self, server, opcode):
        coordinates = get_chunk_id(*opcode.coordinates)
        if coordinates not in self._events:
            return
        self._results[coordinates] = opcode.chunk
        self._events[coordinates].set()
    def get(self, world, x, y, z):
        coordinates = get_chunk_id(x, y, z)
        if coordinates in self._results:
            return self._results[coordinates]
        op = opcodes.ChunkRequest(coordinates=coordinates)
        self._events[coordinates] = threading.Event()
        self._router.send(op)
        self._events[coordinates].wait()
        if coordinates not in self._results:
            # Another thread already removed it
            return self.world.get_chunk(x, y, z)
        chunk = self._results[coordinates]
        world.set_chunk(x, y, z, chunk)
        del self._events[coordinates]
        del self._results[coordinates]
        return chunk
    def __del__(self):
        self._router.remove_callback(self)


def get_fetch_generator(client, server):
    assert isinstance(client, routers.AbstractClientRepresentation)
    generator = _WorldFetcher(server)
    client.add_callback(generator)
    return generator.get

def flat_generator(world, xmin, ymin, zmin):
    (x, y, z) = get_chunk_id(xmin, ymin, zmin)
    air = opcodes.Block(blockType=opcodes.BLOCKTYPES['air'], blockVariant=0)
    dirt = opcodes.Block(blockType=opcodes.BLOCKTYPES['dirt'], blockVariant=0)
    airline = bytes(air)*CHUNK_SIZE
    dirtline = bytes(dirt)*CHUNK_SIZE
    if y == 0:
        chunk = (dirtline + airline*(CHUNK_SIZE-1))*CHUNK_SIZE
    else:
        chunk = airline*CHUNK_SIZE*CHUNK_SIZE
    assert len(chunk) == (CHUNK_SIZE**3)*opcodes.Block.SIZE
    world.set_chunk(xmin, ymin, zmin, chunk)
    return chunk
