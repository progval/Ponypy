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

from ponypy.common import world
from ponypy.common import opcodes
from ponypy.common import structures

class CreativeServer:
    def __init__(self, router):
        self._router = router
        router.add_callback(self)
        self.world = world.World(world.flat_generator)
        self.clients = structures.ClientList()
        self.entities = structures.EntityList()

    def do_handshake(self, client):
        client.instance = self.clients.spawn()
        op = opcodes.Connect(protocol=opcodes.PROTOCOL_VERSION, extensions=[],
                clientId=client.instance.id)
        client.send(op)

    def on_Login(self, client, opcode):
        op = opcodes.WorldCreation(id=1, name='World 1')
        client.send(op)

        entity = self.entities.spawn(position=(0, 0, 10), direction=(0, 0),
                name=opcode.username, playedBy=client.instance.id,
                entityType=1, metadata=[], world=1)
        op = opcodes.EntitySpawn(entity=entity)
        client.send(op)

        # DEBUG
        block = opcodes.PlacedBlock(
                block=opcodes.Block(blockType=opcodes.BLOCKTYPES['dirt'],
                    blockVariant=0),
                world=1,
                coordinates=(3, 3, 3))
        op = opcodes.BlockUpdate(block=block)
        client.send(op)

    def on_ChunkRequest(self, client, opcode):
        client.send(opcodes.ChunkUpdate(coordinates=opcode.coordinates,
            chunk=self.world.get_chunk(*opcode.coordinates)))
