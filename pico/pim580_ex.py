from piro_display_driver import pim580
import time

disp = pim580()

disp.clear(0x0000)
disp.fb.text("Hello Pico W!", 20, 20, 0xFFFF)
disp.fb.rect(10, 60, 100, 50, 0xF800)
disp.show()

while True:
    if disp.button_a():
        disp.set_led(1,0,0)
    elif disp.button_b():
        disp.set_led(0,1,0)
    elif disp.button_x():
        disp.set_led(0,0,1)
    elif disp.button_y():
        disp.set_led(1,1,1)
    else:
        disp.set_led(0,0,0)

    time.sleep(0.05)
