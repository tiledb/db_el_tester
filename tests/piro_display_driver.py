from machine import Pin, SPI, PWM
import framebuf
import time

# ST7789 commands
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

    def __init__(self, tile_height=20):
        self.tile_height = tile_height

        # SPI
        self.spi = SPI(
            0,
            baudrate=62_500_000,
            polarity=1,
            phase=1,
            sck=Pin(18),
            mosi=Pin(19)
        )

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

        # Tile framebuffer (RAM SAFE)
        self.buffer = bytearray(self.WIDTH * self.tile_height * 2)
        self.fb = framebuf.FrameBuffer(
            self.buffer,
            self.WIDTH,
            self.tile_height,
            framebuf.RGB565
        )

        self.reset()
        self.init_display()

    # --- Low level ---
    def reset(self):
        self.rst.value(0)
        time.sleep_ms(50)
        self.rst.value(1)
        time.sleep_ms(50)

    def cmd(self, c):
        self.cs.value(0)
        self.dc.value(0)
        self.spi.write(bytearray([c]))
        self.cs.value(1)

    def data(self, d):
        self.cs.value(0)
        self.dc.value(1)
        self.spi.write(d)
        self.cs.value(1)

    def init_display(self):
        self.cmd(_SWRESET)
        time.sleep_ms(150)

        self.cmd(_SLPOUT)
        time.sleep_ms(10)

        self.cmd(_COLMOD)
        self.data(b'\x55')  # RGB565

        self.cmd(_MADCTL)
        self.data(b'\x00')

        self.cmd(_DISPON)
        time.sleep_ms(100)

    # --- Drawing ---
    def draw_tile(self, y, draw_fn):
        self.fb.fill(0)
        draw_fn(self.fb, y)

        self.cmd(_CASET)
        self.data(b'\x00\x00\x01\x3F')

        self.cmd(_RASET)
        self.data(bytes([0, y, 0, y + self.tile_height - 1]))

        self.cmd(_RAMWR)
        self.data(self.buffer)

    # --- Backlight ---
    def set_backlight(self, v):
        self.bl.duty_u16(int(max(0, min(1, v)) * 65535))

    # --- Buttons ---
    def button_a(self): return not self.btn_a.value()
    def button_b(self): return not self.btn_b.value()
    def button_x(self): return not self.btn_x.value()
    def button_y(self): return not self.btn_y.value()

    # --- RGB LED ---
    def set_led(self, r, g, b):
        self.led_r.value(r)
        self.led_g.value(g)
        self.led_b.value(b)
