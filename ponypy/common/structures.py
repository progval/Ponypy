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

__all__ = ['ClientsList', 'EntitiesList']

from . import opcodes

class AbstractStructureList(dict):
    def spawn(self, **kwargs):
        for x in range(1, 2**32): # IDs are stored in uint32_t
            if x not in self:
                struct = self._Class(id=x, **kwargs)
                self[x] = struct
                return struct
        raise OverflowError(repr(self))

class EntityList(AbstractStructureList):
    _Class = opcodes.Entity
class ClientList(AbstractStructureList):
    _Class = opcodes.Client

