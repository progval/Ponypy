from ponypy.common import opcodes

import unittest
from io import BytesIO

class TestOpcodes(unittest.TestCase):
    def assertRepr(self, obj, s):
        self.assertEqual(repr(obj), s)

    def testRepr(self):
        self.assertRepr(opcodes.Block(blockType='foo', blockVariant='bar'),
            "ponypy.common.opcodes.Block(blockType='foo', blockVariant='bar')")
        self.assertRepr(opcodes.Connect(
            protocol=opcodes.ProtocolVersion(majorVersion=0, minorVersion=1),
            extensions=[], clientId=1),
            "ponypy.common.opcodes.Connect("
                "protocol=ponypy.common.opcodes.ProtocolVersion(majorVersion=0, minorVersion=1), "
                "clientId=1, extensions=[])")
    def testRead(self):
        packet = b'\x00\x00\x01\x00\x01\x00\x01\x00\x00\x00\x0D\x00\x03\x00foo\x06\x00barbaz'
        buf = BytesIO(packet)
        op = opcodes.read(buf)
        op.extensions.set_item_type('string')
        self.assertEqual(op.opcode, '0x0000')
        self.assertEqual(op.protocol.majorVersion, 1)
        self.assertEqual(op.protocol.minorVersion, 1)
        buf = BytesIO()
        op.to_buffer(buf)
        buf.seek(0)
        self.assertEqual(buf.read(), packet)


if __name__ == '__main__':
    unittest.main()
