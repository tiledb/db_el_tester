import sys
import os

# Add parent directory to Python path
sys.path.append('..')  # or '../' or the relative path to your libs

import time
import shared
from machine import Pin, SPI
import sys
import uselect

poller = uselect.poll()
poller.register(sys.stdin, uselect.POLLIN)

def usb_connected():
    events = poller.poll(0)
    return bool(events)

# Import your drivers
from cd74hc4067_driver import CD74HC4067
from mcp3208_driver import MCP3208

# Initialize the MUX (CD74HC4067)
mux = CD74HC4067(s0=26, s1=22, s2=27, s3=28)

# Initialize the ADC (MCP3208)
spi_adc = SPI(1, baudrate=100000, polarity=0, phase=0,
             sck=Pin(14), mosi=Pin(15), miso=Pin(12))
cs_adc = Pin(13, Pin.OUT)
adc = MCP3208(spi_adc, cs_adc)

# Test parameters
test_channel_index = 9  # Change this to test different channels (0-15)

mux_settle_ms = 50
adc_samples = 5
adc_settle_ms = 5

print(f"Testing single channel: {shared.channel_label[test_channel_index]}")
print(f"MUX channel: {shared.mux_ch[test_channel_index]}")
print(f"ADC channel: {shared.output_adc_ch[test_channel_index]}")
print("-" * 40)


# Select the MUX channel
mux.select_channel(shared.mux_ch[test_channel_index])
time.sleep_ms(mux_settle_ms)

while True:

    
    # Read ADC samples
    acc = 0
    raw_readings = []
    
    for _ in range(adc_samples):
        val = adc.read_channel_raw(shared.output_adc_ch[test_channel_index])
        acc += val
        raw_readings.append(val)
        time.sleep_ms(adc_settle_ms)
    
    avg = acc // adc_samples
    voltage = avg * shared.adc_cal / shared.output_adc_value_v_calibration_factor[test_channel_index]
    
    # Print the results
    print(f"Channel: {shared.channel_label[test_channel_index]}")
    print(f"MUX channel: {shared.mux_ch[test_channel_index]}")
    print(f"ADC channel: {shared.output_adc_ch[test_channel_index]}")
    print(f"Raw readings: {raw_readings}")
    print(f"Average RAW: {avg}")
    print(f"Voltage: {voltage:.3f}V")
    print("-" * 20)
    
    time.sleep(1)  # Wait 1 second between readings