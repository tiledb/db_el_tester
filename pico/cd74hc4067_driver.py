from machine import Pin
import time

class CD74HC4067:
    def __init__(self, s0, s1, s2, s3, en=None):
        self.select_pins = [
            Pin(s0, Pin.OUT),
            Pin(s1, Pin.OUT),
            Pin(s2, Pin.OUT),
            Pin(s3, Pin.OUT)
        ]
        self.en = Pin(en, Pin.OUT) if en is not None else None
        
        if self.en:
            self.enable()  # start enabled

    def enable(self):
        if self.en:
            self.en.value(0)  # active LOW

    def disable(self):
        if self.en:
            self.en.value(1)

    def select_channel(self, channel):
        if not 0 <= channel <= 15:
            raise ValueError("Channel must be 0–15")
        bits = [(channel >> i) & 1 for i in range(4)]
        # print(f"Selecting channel {channel} with bits {bits}")
        for pin, bit in zip(self.select_pins, bits):
            pin.value(bit)
