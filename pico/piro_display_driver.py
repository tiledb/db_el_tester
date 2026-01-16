from machine import Pin, SPI, PWM
import framebuf
import time

# === ST7789 Commands ===
_SWRESET = 0x01
_SLPOUT  = 0x11
_COLMOD  = 0x3A
_MADCTL  = 0x36
_CASET   = 0x2A
_RASET   = 0x2B
_RAMWR   = 0x2C
_DISPON  = 0x29

class pim580:
    WIDTH  = 320
    HEIGHT = 240

    def __init__(self, spi_id=0, baudrate=62500000):
        # SPI
        self.spi = SPI(
            spi_id,
            baudrate=baudrate,
            polarity=1,
            phase=1,
            sck=Pin(18),
            mosi=Pin(19)
        )

        # Control pins
        self.cs  = Pin(17, Pin.OUT, value=1)
        self.dc  = Pin(16, Pin.OUT)
        self.rst = Pin(20, Pin.OUT)

        # Backlight
        self.bl = PWM(Pin(21))
        self.bl.freq(1000)
        self.set_backlight(1.0)

        # Buttons
        self.btn_a = Pin(12, Pin.IN, Pin.PULL_UP)
        self.btn_b = Pin(13, Pin.IN, Pin.PULL_UP)
        self.btn_x = Pin(14, Pin.IN, Pin.PULL_UP)
        self.btn_y = Pin(15, Pin.IN, Pin.PULL_UP)

        # RGB LED
        self.led_r = Pin(6, Pin.OUT)
        self.led_g = Pin(7, Pin.OUT)
        self.led_b = Pin(8, Pin.OUT)

        # Framebuffer
        self.buffer = bytearray(self.WIDTH * self.HEIGHT * 2)
        self.fb = framebuf.FrameBuffer(
            self.buffer,
            self.WIDTH,
            self.HEIGHT,
            framebuf.RGB565
        )

        self.reset()
        self.init_display()

    # === Low-level helpers ===
    def reset(self):
        self.rst.value(0)
        time.sleep_ms(50)
        self.rst.value(1)
        time.sleep_ms(50)

    def write_cmd(self, cmd):
        self.cs.value(0)
        self.dc.value(0)
        self.spi.write(bytearray([cmd]))
        self.cs.value(1)

    def write_data(self, data):
        self.cs.value(0)
        self.dc.value(1)
        self.spi.write(data)
        self.cs.value(1)

    # === Display init ===
    def init_display(self):
        self.write_cmd(_SWRESET)
        time.sleep_ms(150)

        self.write_cmd(_SLPOUT)
        time.sleep_ms(10)

        self.write_cmd(_COLMOD)
        self.write_data(b'\x55')  # RGB565

        self.write_cmd(_MADCTL)
        self.write_data(b'\x00')

        self.write_cmd(_DISPON)
        time.sleep_ms(100)

    # === Drawing ===
    def show(self):
        self.write_cmd(_CASET)
        self.write_data(b'\x00\x00\x01\x3F')  # 0..319

        self.write_cmd(_RASET)
        self.write_data(b'\x00\x00\x00\xEF')  # 0..239

        self.write_cmd(_RAMWR)
        self.write_data(self.buffer)

    def clear(self, color=0x0000):
        self.fb.fill(color)

    # === Backlight ===
    def set_backlight(self, value):
        value = max(0.0, min(1.0, value))
        self.bl.duty_u16(int(value * 65535))

    # === Buttons ===
    def button_a(self): return not self.btn_a.value()
    def button_b(self): return not self.btn_b.value()
    def button_x(self): return not self.btn_x.value()
    def button_y(self): return not self.btn_y.value()

    # === RGB LED ===
    def set_led(self, r, g, b):
        self.led_r.value(1 if r else 0)
        self.led_g.value(1 if g else 0)
        self.led_b.value(1 if b else 0)
