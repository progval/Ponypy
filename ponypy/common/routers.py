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

__all__ = ['AbstractRouter', 'LocalServerRouter', 'LocalClientRouter', 'get_local_pair']

import threading

class AbstractRouter:
    """Base class for interfacing a core with another core (via network or
    running locally."""
    def __init__(self):
        self._callbacks = set()
    @property
    def callbacks(self):
        return self._callbacks
    def add_callback(self, callback):
        self._callbacks.add(callback)
    def remove_callback(self, callback):
        self._callbacks.remove(callback)
    def dispatch(self, from_representation, opcode):
        for callback in self.callbacks:
            if hasattr(callback, 'on_' + opcode.name):
                method = getattr(callback, 'on_' + opcode.name)
                thread = threading.Thread(target=method,
                        args=(from_representation, opcode),
                        name='Event thread for %r' % opcode)
                thread.start()

class AbstractServerRepresentation:
    """Represents a server on the client side."""
    pass
class AbstractClientRepresentation:
    """Represents a client on the server side."""
    pass

class LocalServerRouter(AbstractRouter, AbstractServerRepresentation):
    """Represents a server running locally."""
    def __init__(self):
        super(LocalServerRouter, self).__init__()
        self._client = None
    def send(self, opcode):
        self.dispatch(self._client, opcode)
    def add_client(self, client):
        assert isinstance(client, LocalClientRouter)
        assert self._client is None, self._client
        self._client = client
        for callback in self.callbacks:
            if hasattr(callback, 'do_handshake'):
                callback.do_handshake(client)
    def close_connection(self, message):
        exit()

        
class LocalClientRouter(AbstractRouter, AbstractClientRepresentation):
    """Represents a client running locally."""
    def __init__(self, server_router):
        super(LocalClientRouter, self).__init__()
        assert isinstance(server_router, LocalServerRouter), server_router.__class__
        self._server = server_router
    def send(self, opcode):
        self.dispatch(self._server, opcode)
    def close_connection(self, message):
        exit()

