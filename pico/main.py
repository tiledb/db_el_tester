import _thread
import data_task
import display_task
from machine import Pin
import time
import shared


# ==== Button check at startup ====
# btn_y = Pin(2, Pin.IN, Pin.PULL_UP)

# If button Y is pressed at startup, halt program
if not display_task.btn_y.value():  # active LOW
    # Optional: show a message on the display
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

elif not display_task.btn_b.value() and not display_task.btn_a.value():  # active LOW
    WIDTH, HEIGHT = display_task.display.get_bounds()

    # ---- Display setup ----
    display_task.display.set_pen(display_task.BLACK)
    display_task.display.clear()
    display_task.display.set_pen(display_task.WHITE)
    display_task.display.update()

    y0 = 10
    line_h = 16  # vertical spacing per line

    # ---- Step 1 + 2: Wi-Fi + MQTT ----
    display_task.draw_line(y0, line_h, "Checking network...")

    network_ok = False
    start = time.ticks_ms()
    timeout = 5000  # 5 seconds max to connect

    while not data_task.net.ensure_connected():
        retry_count += 1
        display_task.draw_line(y0, line_h, f"Waiting for network... Retry: {retry_count}")
        print(f"[INFO] Waiting for network, retry #{retry_count}")
        time.sleep(1)


    ip = data_task.net.wlan.ifconfig()[0]
    display_task.draw_line(y0, line_h, f"Wi-Fi connected, IP: {ip}")
    if data_task.net.mqtt:
        display_task.draw_line(y0 + line_h, line_h, f"MQTT broker connected: {data_task.net.mqtt_broker}")
    else:
        display_task.draw_line(y0 + line_h, line_h, "MQTT broker NOT connected")

    # ---- Step 3: Clear discovery ----
    clear_y = y0 + line_h * 3
    cleared = data_task.clear_mqtt_discovery(data_task.net, shared.channel_label)
    display_task.draw_line(clear_y, line_h, f"Discovery topics cleared: {cleared}")


else:

    # Start display/UI on core 1
    _thread.start_new_thread(display_task.run, ())

    # Run data acquisition on core 0 (main thread)
    data_task.run()