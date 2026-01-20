from machine import Pin
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2, PEN_P8
import time

# ==== Display setup ====
display = PicoGraphics(
    display=DISPLAY_PICO_DISPLAY_2,
    pen_type=PEN_P8
)

# Backlight ON (0.0 – 1.0)
display.set_backlight(1.0)

# Display size
WIDTH, HEIGHT = display.get_bounds()

# ==== DEFINE PALETTE (REQUIRED FOR P8) ====
display.set_palette([
    (0, 0, 0),        # 0 = black
    (255, 255, 255),  # 1 = white
    (255, 0, 0),      # 2 = red
    (0, 255, 0),      # 3 = green
    (0, 0, 255),      # 4 = blue
    (255, 255, 0),    # 5 = yellow
    (255, 0, 255),    # 6 = magenta
    (0, 255, 255),    # 7 = cyan
])

# ==== Button setup (active LOW) ====
btn_a = Pin(5, Pin.IN, Pin.PULL_UP)
btn_b = Pin(4, Pin.IN, Pin.PULL_UP)
btn_x = Pin(3, Pin.IN, Pin.PULL_UP)
btn_y = Pin(2, Pin.IN, Pin.PULL_UP)

# ==== RGB LED setup ====
rgb_r = Pin(6, Pin.OUT)
rgb_g = Pin(7, Pin.OUT)
rgb_b = Pin(8, Pin.OUT)

def set_rgb(r, g, b):
    rgb_r.value(r)
    rgb_g.value(g)
    rgb_b.value(b)

# ==== Drawing function ====
def draw_frame(counter):
    # Clear screen (black)
    display.set_pen(0)
    display.clear()

    # Draw text (white)
    display.set_pen(1)
    display.text("Counter: {}".format(counter), 10, 10, WIDTH, scale=0.5)
    display.text("Line", 10, 10 + 8 * 3, WIDTH, scale=3)

    # Draw rectangle (yellow)
    display.set_pen(5)
    display.rectangle(10, 50, 80, 40)

    # Push framebuffer to display
    display.update()

# ==== Main loop ====
count = 0

while True:
    print("Frame:", count)
    draw_frame(count)

    # Button handling
    if not btn_a.value():
        print("Button A")
        set_rgb(1, 0, 0)   # Red
    elif not btn_b.value():
        print("Button B")
        set_rgb(0, 1, 0)   # Green
    elif not btn_x.value():
        print("Button X")
        set_rgb(0, 0, 1)   # Blue
    elif not btn_y.value():
        print("Button Y")
        set_rgb(1, 1, 1)   # White
    else:
        set_rgb(0, 0, 0)   # LED off

    count += 1
    time.sleep(0.1)
