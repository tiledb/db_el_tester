import _thread
import data_task
import display_task
from machine import Pin
import time

# ==== Button check at startup ====
btn_y = Pin(2, Pin.IN, Pin.PULL_UP)

# If button Y is pressed at startup, halt program
if not btn_y.value():  # active LOW
    # Optional: show a message on the display
    import display_task
    WIDTH, HEIGHT = display_task.display.get_bounds()
    display_task.display.set_pen(display_task.BLACK)
    display_task.display.clear()
    display_task.display.set_pen(display_task.WHITE)
    text = "Firmware stopped\nAt Startup (BtnY)!"
    lines = text.split("\n")
    y0 = HEIGHT // 2 - len(lines) * 8
    for i, line in enumerate(lines):
        display_task.display.text(line, 10, y0 + i * 16, WIDTH, scale=2)
    display_task.display.update()





    
else:

    # Start display/UI on core 1
    _thread.start_new_thread(display_task.run, ())

    # Run data acquisition on core 0 (main thread)
    data_task.run()