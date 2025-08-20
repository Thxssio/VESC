#!/usr/bin/env python3
import time
import serial
from typing import Optional, Tuple
from VESC.Packet.codec import frame, unframe

DEFAULT_TIMEOUT = 1.2

def open_serial(port: str, baud: int = 115200, timeout: float = DEFAULT_TIMEOUT) -> serial.Serial:
    ser = serial.Serial(port, baud, timeout=timeout, write_timeout=1.0)
    # acorda CDC-ACM e limpa buffers
    try:
        ser.dtr = True
        ser.rts = False
    except Exception:
        pass
    time.sleep(0.2)
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    return ser

def send_and_recv_frame(ser: serial.Serial, payload: bytes, rx_timeout: float = 3.0) -> Optional[bytes]:
    """Envia payload (sem frame) e aguarda 1 pacote válido. Retorna payload decodificado (cmd+data)."""
    ser.write(frame(payload))
    ser.flush()

    buf = b""
    t0 = time.time()
    while True:
        chunk = ser.read(64)
        if chunk:
            buf += chunk
            pay, consumed = unframe(buf)
            if pay:
                return pay
        if time.time() - t0 > rx_timeout:
            return None

def recv_frame(ser: serial.Serial, rx_timeout: float = 3.0) -> Optional[bytes]:
    """Apenas recebe 1 pacote válido (útil após um comando já enviado)."""
    buf = b""
    t0 = time.time()
    while True:
        chunk = ser.read(64)
        if chunk:
            buf += chunk
            pay, consumed = unframe(buf)
            if pay:
                return pay
        if time.time() - t0 > rx_timeout:
            return None
