__all__ = ['Structure', 'Opcode', 'read', 'write']

import io
import yaml
import struct
import logging
import operator
import functools
import pkg_resources

logging.info('Loading opcodes.')

_document = yaml.load(pkg_resources.resource_stream('ponypy.common', 'opcodes.yml'))

class ProtocolError(Exception):
    pass

class classproperty:
    def __init__(self, getter):
        self.getter= getter
    def __get__(self, instance, owner):
        return self.getter(owner)

TYPE_TO_CHAR = {
        'int8': ('b', 1),
        'uint8': ('B', 1),
        'bool': ('?', 1),
        'int16': ('h', 2),
        'uint16': ('H', 2),
        'int32': ('i', 4),
        'uint32': ('I', 4),
        'int64': ('q', 8),
        'uint64': ('Q', 8),
        'float32': ('f', 4),
        'float64': ('d', 8),
        'coordinates': ('HHH', 3*2),
        'position': ('ddd', 3*8),
        'direction': ('HH', 2*2),
        }

def pack(format_, buf, *data):
    buf.write(struct.pack('<' + format_, *data))
def unpack(format_, buf):
    data = buf.read(struct.calcsize(format_))
    return struct.unpack('<' + format_, data)
def unpack_one(format_, buf):
    return unpack(format_, buf)[0]

def _encode_string(buf, x):
    if isinstance(x, str):
        x = x.encode()
    length = len(x)
    x = list(map(lambda y:bytes([y]), x)) # b'foo' -> [b'f', b'o', b'o']
    pack('H' + ('c'*length), buf, length, *x)
def _decode_string(buf):
    length = unpack('H', buf)[0]
    string = b''.join(unpack('c'*length, buf))
    return string.decode()

def _decode_list(buf):
    length = unpack('H', buf)[0]
    return List(buf.read(length))

class types:
    _encoders = {}
    _decoders = {}
    for (type_, (char, length))  in TYPE_TO_CHAR.items():
        _encoders[type_] = functools.partial(pack, char)
        _decoders[type_] = functools.partial(unpack_one, char)
    _encoders['string'] = _encode_string
    _decoders['string'] = _decode_string

    _decoders['list'] = _decode_list

    @classmethod
    def encode(cls, type_, buf, obj):
        if isinstance(obj, Structure):
            obj.to_buffer(buf)
        else:
            cls._encoders[type_](buf, obj)
    @classmethod
    def decode(cls, type_, buf):
        if isinstance(type_, type):
            assert issubclass(type_, Structure)
            return type_.from_buffer(buf)
        else:
            return cls._decoders[type_](buf)

    for (key, value) in _document['aliases'].items():
        _encoders[key] = _encoders[value]
        _decoders[key] = _decoders[value]

class Structure:
    def __init__(self, **kwargs):
        if set(kwargs.keys()) != set(self.field_names):
            raise ProtocolError('%r != %r' % (set(kwargs), set(self.field_names)))
        self._attributes = kwargs.copy()

    @classproperty
    def fields(cls):
        return list(cls._fields)
    @classproperty
    def field_names(cls):
        return list(map(operator.itemgetter(0), cls.fields))

    @property
    def attributes(self):
        return self._attributes.copy()

    @classmethod
    def from_buffer(cls, buf):
        attributes = {}
        for (name, type_) in cls.fields:
            attributes[name] = types.decode(type_, buf)
        return cls(**attributes)
    def to_buffer(self, buf):
        attributes = {}
        for (name, type_) in self.fields:
            types.encode(type_, buf, self.attributes[name])

    def __getitem__(self, name):
        if name not in self.field_names:
            raise ProtocolError('%r has no field %r' % (self, name))
        return self._attributes[name]
    def __getattr__(self, name):
        return self[name]

    def __repr__(self):
        return 'ponypy.common.opcodes.%s(%s)' % \
                (self.__class__.__name__,
                 ', '.join(map(lambda x:'%s=%r' % (x, self[x]), self.field_names)))

class Opcode(Structure):
    _opcodes = {}
    @classproperty
    def opcode(cls):
        return cls._opcode

    @classmethod
    def get_subclass(cls, buf):
        if isinstance(buf, int):
            if buf not in cls._opcodes:
                raise ProtocolError('Unknown opcode: %i' % buf)
            return cls._opcodes[buf]
        elif hasattr(buf, 'read'):
            opcode = unpack('H', buf)[0]
            return Opcode.get_subclass(opcode)
        else:
            raise ValueError('Cannot get opcode from %r' % buf)

    def to_buffer(self, buf):
        pack('H', buf, int(self._opcode, 0))
        super(Opcode, self).to_buffer(buf)

def upfirst(name):
    return name[0].upper() + name[1:]

def define_structure(name, fields, opcode=None):
    name = upfirst(name)
    fields = map(lambda field:list(field.items())[0], fields)
    fields = map(lambda x:(x[0],
        STRUCTURES[x[1]] if x[1] in STRUCTURES else x[1]), fields)
    attributes = {'_fields': list(fields)}
    if opcode:
        attributes['_opcode'] = opcode
    structure = type(name, (Opcode if opcode else Structure,), attributes)
    globals()[name] = structure
    __all__.append(name)
    return structure
    
STRUCTURES = {}

for structure in _document['structures']:
    (name, fields) = list(structure.items())[0]
    structure = define_structure(name, fields)
    STRUCTURES[name] = structure

for opcode in _document['opcodes']:
    (opcode, data) = list(opcode.items())[0]
    fields = data['fields'] or []
    name = data['name']
    structure = define_structure(name, fields, opcode)
    Opcode._opcodes[int(opcode, 0)] = structure

class PosBytesIO(io.BytesIO):
    # In order not to have to handle (length, data) return values,
    # we use this fake buffer to store the length in the case of
    # list items.
    _pos = 0
    def write(self, data):
        super(PosBytesIO, self).write(data)
        self._pos += len(data)
    def read(self, length):
        self._pos += length
        return super(PosBytesIO, self).read(length)
    def seek(self, pos):
        self._pos = pos
        super(PosBytesIO, self).seek(pos)

class List(Structure):
    _fields = None
    def __init__(self, data):
        self._length = len(data)
        self._buf = PosBytesIO(data)
        self._items = None
    def set_item_type(self, type_):
        self._items = []
        self._type = type_
        if isinstance(type_, type):
            assert issubclass(type_, Structure)
            while self._buf._pos < self._length:
                self._items.append(type_.from_buffer(self._buf))
        else:
            while self._buf._pos < self._length:
                self._items.append(types.decode(type_, self._buf))
    def to_buffer(self, buf):
        assert self._items is not None
        tempbuf = PosBytesIO()
        for x in self._items:
            types.encode(self._type, tempbuf, x)
        length = tempbuf._pos
        pack('H', buf, length)
        tempbuf.seek(0)
        buf.write(tempbuf.read(length))
    def __repr__(self):
        if self._items is None:
            return 'ponyca.common.opcodes.List()'
        else:
            return 'ponyca.common.opcodes.List(%r)' % self._items

def read(buf):
    cls = Opcode.get_subclass(buf)
    return cls.from_buffer(buf)

def write(opcode, buf):
    buf.write(bytes(opcode))

logging.info('Opcodes loaded')
