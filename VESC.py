#!/usr/bin/env python3
from typing import Optional, Dict, Any
import struct
import serial
from VESC.Transport.serial_io import send_and_recv_frame
from VESC.Proto.messages import (
    VedderCmd,
    build_get_values_req,
    decode_get_values_pre_v3_33,
    build_set_duty_payload,
    build_set_rpm_payload,
    build_set_current_payload,
)

def build_set_servo_payload(pos: float) -> bytes:
    """
    pos: posição normalizada [0.0 .. 1.0]
    VESC espera uint16 de 0..1000 (big-endian)
    """
    pos = max(0.0, min(1.0, float(pos)))
    val = int(round(pos * 1000.0))
    return bytes([VedderCmd.COMM_SET_SERVO_POS]) + struct.pack(">H", val)

class VESCClient:
    """Cliente alto nível para FW 2.x (pré 3.33)."""

    def __init__(self, ser: serial.Serial):
        self.ser = ser

    # -------- GETTERS --------
    def get_values(self, rx_timeout: float = 3.0) -> Optional[Dict[str, Any]]:
        pay = send_and_recv_frame(self.ser, build_get_values_req(), rx_timeout=rx_timeout)
        if not pay or pay[0] != VedderCmd.COMM_GET_VALUES:
            return None
        return decode_get_values_pre_v3_33(pay[1:])

    # -------- SETTERS --------
    def set_duty(self, duty: float) -> bool:
        pkt = build_set_duty_payload(duty)
        return bool(send_and_recv_frame(self.ser, pkt, rx_timeout=0.2) or True)  # não exige resposta

    def set_current(self, amps: float) -> bool:
        pkt = build_set_current_payload(amps)
        return bool(send_and_recv_frame(self.ser, pkt, rx_timeout=0.2) or True)

    def set_rpm(self, rpm: int) -> bool:
        pkt = build_set_rpm_payload(rpm)
        return bool(send_and_recv_frame(self.ser, pkt, rx_timeout=0.2) or True)

    def set_servo(self, pos: float) -> bool:
        """
        Controla o canal de servo do VESC (PWM) — pos ∈ [0.0 .. 1.0]
        """
        pkt = build_set_servo_payload(pos)
        return bool(send_and_recv_frame(self.ser, pkt, rx_timeout=0.2) or True)

    def ramp_duty(self, start: float, end: float, steps: int = 20, step_delay: float = 0.05):
        if steps <= 0: steps = 1
        delta = (end - start) / steps
        d = start
        for _ in range(steps + 1):
            self.set_duty(d)
            vals = self.get_values(rx_timeout=0.4)
            if vals:
                print(f"[ramp] V={vals['v_in']:.1f} Duty={vals['duty_now']:.3f} "
                      f"eRPM={int(vals['rpm'])} I={vals['current_motor']:.2f}")
            import time; time.sleep(step_delay)
            d += delta

    def safe_stop(self):
        self.set_duty(0.0)
        self.set_current(0.0)
