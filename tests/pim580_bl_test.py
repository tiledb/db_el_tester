from machine import Pin, PWM
import time

lcdte = Pin(21,Pin.OUT)
lcdte.on()

bl = Pin(20,Pin.OUT)
bl.on()

# bl = PWM(Pin(20))
# bl.freq(1000)
# bl.duty_u16(65535)  # FULL BRIGHTNESS

while True:
    time.sleep(1)
    lcdte.on()
    print("LCD TE ON")
    bl.on()
    time.sleep(1)
    lcdte.off()
    print("LCD TE OFF")
    bl.off()
    