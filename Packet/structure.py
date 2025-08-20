import collections
import struct
from .exceptions import *
from crccheck.crc import CrcXmodem

crc_checker = CrcXmodem()

class Header(collections.namedtuple("Header", ["payload_index", "payload_length"])):
    @staticmethod
    def generate(payload: bytes):
        n = len(payload)
        if n < 256:
            return Header(0x2, n)
        elif n < 65536:
            return Header(0x3, n)
        else:
            raise InvalidPayload("Payload must be < 65536 bytes.")

    @staticmethod
    def parse(buffer: bytes):
        return Header._make(struct.unpack_from(Header.fmt(buffer[0]), buffer, 0))

    @staticmethod
    def fmt(start_byte: int):
        if start_byte == 0x2:
            return ">BB"   # start(0x02) + len(1B)
        elif start_byte == 0x3:
            return ">BH"   # start(0x03) + len(2B)
        else:
            raise CorruptPacket(f"Invalid start byte: {start_byte}")


class Footer(collections.namedtuple("Footer", ["crc", "terminator"])):
    TERMINATOR = 0x03

    @staticmethod
    def generate(payload: bytes):
        return Footer(crc_checker.calc(payload), Footer.TERMINATOR)

    @staticmethod
    def parse(buffer: bytes, header: Header):
        return Footer._make(struct.unpack_from(Footer.fmt(), buffer, header.payload_index + header.payload_length))

    @staticmethod
    def fmt():
        return ">HB"
