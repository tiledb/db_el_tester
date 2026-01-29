from machine import Pin, PWM, reset
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2, PEN_P8
import time
import shared

# ==== Display setup ====
display = PicoGraphics(
    display=DISPLAY_PICO_DISPLAY_2,
    pen_type=PEN_P8
)

display.set_backlight(1.0)
WIDTH, HEIGHT = display.get_bounds()

# ==== Palette ====
display.set_palette([
    (0, 0, 0),        # 0 black
    (255, 255, 255),  # 1 white
    (0, 255, 0),      # 2 green (OK)
    (255, 255, 0),    # 3 yellow (labels)
    (255, 0, 0),      # 4 red (ALARM)
    (100, 100, 100),  # 5 grid lines
])

def draw_line(y, line_h, text):
    """Clear line first to avoid overlapping text, then draw"""
    display.set_pen(BLACK)
    display.rectangle(0, y, WIDTH, line_h)
    display.set_pen(WHITE)
    display.text(text, 10, y, WIDTH, scale=2)
    display.update()
    # print("[DISPLAY]", text)


BLACK, WHITE, GREEN, YELLOW, RED, GRID = range(6)

# ==== Buttons ====
btn_a = Pin(5, Pin.IN, Pin.PULL_UP)
btn_b = Pin(4, Pin.IN, Pin.PULL_UP)
btn_x = Pin(3, Pin.IN, Pin.PULL_UP)
btn_y = Pin(2, Pin.IN, Pin.PULL_UP)

# ==== RGB LED ====
rgb_r = PWM(Pin(6))
rgb_g = PWM(Pin(7))
rgb_b = PWM(Pin(8))

# Set frequency (typical 500Hz)
for pwm in (rgb_r, rgb_g, rgb_b):
    pwm.freq(500)


def set_rgb(r, g, b):
    # r, g, b = 0.0 → 1.0 brightness
    rgb_r.duty_u16(int((1.0 - r) * 65535))
    rgb_g.duty_u16(int((1.0 - g) * 65535))
    rgb_b.duty_u16(int((1.0 - b) * 65535))
# ==== Layout constants ====
ROWS = 13
TEXT_SCALE = 2
ROW_H = 16
HEADER_H = 24

MID_X = WIDTH // 2
LEFT_X = 2
RIGHT_X = MID_X + 2
VALUE_OFFSET = 78

START_Y = HEADER_H + 4

# ==== Blinking LED state ====
red_on = True
last_blink_time = time.ticks_ms()

# ==== Drawing function ====
def draw_frame():
    global red_on, last_blink_time

    display.set_pen(BLACK)
    display.clear()

    # ---- Headers ----
    display.set_pen(WHITE)
    display.text("DB Side A", LEFT_X + 10, 4, MID_X, scale=2)
    display.text("DB Side B", RIGHT_X + 10, 4, MID_X, scale=2)

    # ---- Copy shared data safely ----
    shared.data_lock.acquire()
    values = shared.output_adc_value_v[:]

    # Check for test mode
    if not btn_y.value() and not btn_b.value():  # both pressed
        vmin = shared.output_adc_value_min_test[:]
        vmax = shared.output_adc_value_max_test[:]
    else:
        vmin = shared.output_adc_value_min[:]
        vmax = shared.output_adc_value_max[:]

    labels = shared.channel_label[:]
    shared.data_lock.release()

    # ---- Determine overall LED status ----
    any_out_of_range = any(values[i] < vmin[i] or values[i] > vmax[i] for i in range(len(values)))

    # ---- Grid: outer border ----
    display.set_pen(GRID)
    display.rectangle(0, START_Y - 2, WIDTH, ROWS * ROW_H + 4)

    # ---- Grid: vertical divider ----
    display.line(MID_X, START_Y - 2, MID_X, START_Y + ROWS * ROW_H + 2)

    # ---- Grid: horizontal lines ----
    for i in range(ROWS + 1):
        y = START_Y + i * ROW_H
        display.line(0, y, WIDTH, y)

    # ---- Draw cells ----
    for i in range(ROWS):
        y = START_Y + i * ROW_H + 2

        # ===== LEFT COLUMN (Side A) =====
        label_a = labels[i].replace("dba_", "").replace("dbb_", "")
        display.set_pen(YELLOW)
        display.text(label_a, LEFT_X, y, MID_X, scale=TEXT_SCALE)

        pen = GREEN if vmin[i] <= values[i] <= vmax[i] else RED
        display.set_pen(pen)
        display.text(f"{values[i]:.3f}", LEFT_X + VALUE_OFFSET, y, MID_X, scale=TEXT_SCALE)

        # ===== RIGHT COLUMN (Side B) =====
        j = i + ROWS
        label_b = labels[j].replace("dba_", "").replace("dbb_", "")
        display.set_pen(YELLOW)
        display.text(label_b, RIGHT_X, y, MID_X, scale=TEXT_SCALE)

        pen = GREEN if vmin[j] <= values[j] <= vmax[j] else RED
        display.set_pen(pen)
        display.text(f"{values[j]:.3f}", RIGHT_X + VALUE_OFFSET, y, MID_X, scale=TEXT_SCALE)

    display.update()

    # ---- Update RGB LED ----
    now = time.ticks_ms()
    if any_out_of_range:
        # Blink red at 1 Hz
        if time.ticks_diff(now, last_blink_time) > 500:
            red_on = not red_on
            last_blink_time = now
        if red_on:
            set_rgb(0.5, 0, 0)
        else:
            set_rgb(0, 0, 0)
    else:
        set_rgb(0, 0.5, 0)  # green

# ==== Main loop ====

# ==== Soft reset with message ====
def soft_reset():
    # Clear screen
    display.set_pen(BLACK)
    display.clear()
    display.set_pen(WHITE)
    text = "Firmware stopped\nand Pico reset!"
    lines = text.split("\n")
    y0 = HEIGHT // 2 - len(lines) * 8
    for i, line in enumerate(lines):
        display.text(line, 10, y0 + i * 16, WIDTH, scale=2)
    display.update()

    # Flash all LEDs before reset
    for _ in range(3):
        set_rgb(1,1,1)
        time.sleep(0.1)
        set_rgb(0,0,0)
        time.sleep(0.1)

    time.sleep(0.2)
    reset()

def run():
    while True:

        if not btn_a.value() and not btn_b.value() and not btn_x.value() and not btn_y.value():
            for _ in range(4):
                set_rgb(1, 1, 1)
                time.sleep(0.1)
                set_rgb(0, 0, 0)
                soft_reset()
            reset()  # soft reset Pico
        draw_frame()
        time.sleep(0.05)  # faster refresh for smooth blinking
