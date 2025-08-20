import struct
from .exceptions import *
from .structure import Header, Footer, crc_checker

class Stateless:
    """Stateless encoder/decoder for VESC packets."""

    @staticmethod
    def pack(payload: bytes) -> bytes:
        if not payload:
            raise InvalidPayload("Empty payload")

        header = Header.generate(payload)
        footer = Footer.generate(payload)

        header_bytes = struct.pack(Header.fmt(header.payload_index), *header)
        footer_bytes = struct.pack(Footer.fmt(), *footer)

        return header_bytes + payload + footer_bytes

    @staticmethod
    def unpack(buffer: bytes, errors="ignore"):
        if not buffer:
            return None, 0

        try:
            header = Header.parse(buffer)
        except Exception:
            return None, 0

        frame_size = (
            struct.calcsize(Header.fmt(header.payload_index)) +
            header.payload_length +
            struct.calcsize(Footer.fmt())
        )
        if len(buffer) < frame_size:
            return None, 0

        payload = buffer[header.payload_index:header.payload_index + header.payload_length]
        footer = Footer.parse(buffer, header)

        # validar CRC + terminador
        if crc_checker.calc(payload) != footer.crc:
            if errors == "ignore":
                return None, frame_size
            raise CorruptPacket("CRC inválido")
        if footer.terminator != Footer.TERMINATOR:
            raise CorruptPacket(f"Terminador inválido: {footer.terminator}")

        return payload, frame_size


# Helpers iguais ao pyvesc
def frame(payload: bytes) -> bytes:
    return Stateless.pack(payload)

def unframe(buffer: bytes, errors="ignore"):
    return Stateless.unpack(buffer, errors)
