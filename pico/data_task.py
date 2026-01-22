import time
import shared
from machine import Pin, SPI, I2C
import sys
import uselect

poller = uselect.poll()
poller.register(sys.stdin, uselect.POLLIN)

def usb_connected():
    events = poller.poll(0)
    return bool(events)


# Import your drivers (make sure they are on the Pico)
from cd74hc4067_driver import CD74HC4067
from mcp3208_driver import MCP3208



# Initialize the MUX (CD74HC4067)
mux = CD74HC4067(s0=26, s1=22, s2=27, s3=28)

# Initialize the ADC (MCP3208)
spi_adc = SPI(1, baudrate=100000, polarity=0, phase=0,
             sck=Pin(14), mosi=Pin(15), miso=Pin(12))
cs_adc = Pin(13, Pin.OUT)
adc = MCP3208(spi_adc, cs_adc)


def cprint(msg):
    if shared.cprint_enabled:
        try:
            print("--" + msg + "--")
        except OSError:
            pass
def nprint(msg):
    if shared.nprint_enabled:
        try:
            print(msg)
        except OSError:
            pass

first_row, mux_row, adc_row, channel_label_row, channel_label_row_dim, info_row = "", "", "", "", "", ""
iteration = 0
max_iterations = 10

mux_settle_ms = 50  # time to wait after changing MUX channel
adc_samples = 5   # choose how many samples to average
adc_settle_ms = 5   # small delay between samples (adjust if needed)





def print_header():
    nprint(shared.delimiter_line)
    global first_row, mux_row, adc_row, channel_label_row, channel_label_row_dim, info_row


    for i in range(shared.nr_of_channels):
        first_row += f"ch_{shared.channel_label[i]}\t"
        mux_row += f"mux_ch_{shared.mux_ch[i]}\t"
        adc_row += f"adc_ch_{shared.output_adc_ch[i]}\t"
        channel_label_row += f"{shared.channel_label[i]}\t"
        channel_label_row_dim += f"{shared.channel_label[i].split('_')[1]}\t"
        info_row += f"{shared.channel_label[i]}_adc[{shared.output_adc_ch[i]}]_mux[{shared.mux_ch[i]}]\t"
        
    # first_row += "\t|||\t\t"
  
    nprint(info_row)
    nprint(first_row)



def run():
    global iteration
    print_header()
    while True:
        # ---- Local working buffers (NO LOCK) ----
        local_adc = [0] * shared.nr_of_channels
        local_adc_avg = [0] * shared.nr_of_channels
        local_v = [0.0] * shared.nr_of_channels

        # ---- ADC acquisition (NO LOCK) ----
        for i in range(shared.nr_of_channels):
            mux.select_channel(shared.mux_ch[i])
            time.sleep_ms(mux_settle_ms)

            acc = 0
            for _ in range(adc_samples):
                val = adc.read_channel_raw(shared.output_adc_ch[i])
                acc += val
                time.sleep_ms(adc_settle_ms)

            avg = acc // adc_samples
            local_adc[i] = val
            local_adc_avg[i] = avg
            local_v[i] = (
                avg *
                shared.adc_cal /
                shared.output_adc_value_v_calibration_factor[i]
            )

        # ---- Commit results atomically ----
        shared.data_lock.acquire()
        for i in range(shared.nr_of_channels):
            shared.output_adc_value[i] = local_adc[i]
            shared.output_adc_value_avg[i] = local_adc_avg[i]
            shared.output_adc_value_v[i] = local_v[i]
        shared.data_lock.release()

        nprint(channel_label_row_dim)
        # ---- Printing (NO LOCK) ----
        # if iteration < max_iterations:
        #     iteration += 1
        # else:
        #     iteration = 0
        #     nprint(channel_label_row)

        row_adc = ""
        row_v = ""
        for i in range(shared.nr_of_channels):
            row_adc += f"{local_adc[i]}\t"
            row_v += f"{local_v[i]:.3f}V\t"

        nprint(row_adc)
        nprint(row_v)

        time.sleep(0.5)

