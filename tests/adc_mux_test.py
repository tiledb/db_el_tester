from machine import Pin, SPI, I2C
import sys
import uselect
import time

poller = uselect.poll()
poller.register(sys.stdin, uselect.POLLIN)

# Import your drivers (make sure they are on the Pico)
from cd74hc4067_driver import CD74HC4067
from mcp3208_driver import MCP3208

cprint_enabled = False


# Initialize the MUX (CD74HC4067)
mux = CD74HC4067(s0=26, s1=22, s2=27, s3=28)

# Initialize the ADC (MCP3208)
spi_adc = SPI(1, baudrate=100000, polarity=0, phase=0,
             sck=Pin(14), mosi=Pin(15), miso=Pin(12))
cs_adc = Pin(13, Pin.OUT)
adc = MCP3208(spi_adc, cs_adc)


nr_of_channels = 26
mux_ch = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 , # 13, 14, 15,
          0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12   #, 13, 14, 15
            ]

output_adc_ch = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,# 1, 1, 1
                0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,# 0, 0, 0, 
                ]

output_adc_value = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 0, 0, 0, 
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0#, 0, 0, 0
                        ]

output_adc_value_avg = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 0, 0, 0, 
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0#, 0, 0, 0
                        ]


output_adc_value_v = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 0, 0, 0, 
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 #, 0, 0, 0
                        ]

adc_resolution = 4096  # 12-bit ADC
adc_reference_voltage = 3.3  # Reference voltage for ADC in volts
adc_cal = adc_reference_voltage / adc_resolution  # Volts per ADC count





db_1v2_cal = 0.8291 # 3300./(680.+3300)
db_5v0_cal = 0.5 # 3300./(3300.+3300)
db_1v5_cal = 0.8291 # 3300./(680.+3300)
db_3v3_cal = 0.5 # 3300./(3300.+3300)
db_pg_cal = 0.5 # 3300./(3300.+3300)
db_5v0pp_cal = 0.5 # 3300./(3300.+3300)
db_2v5_cal = 0.8291 # 3300./(680.+3300)
db_1v8_cal = 0.8291 # 3300./(680.+3300)
db_1v0_cal = 0.8291 # 3300./(680.+3300)
db_0v95_cal = 0.8291 # 3300./(680.+3300)

output_adc_value_v_calibration_factor = [db_1v2_cal, db_5v0_cal, db_1v5_cal, db_3v3_cal, db_pg_cal, db_pg_cal, db_pg_cal, db_pg_cal, db_5v0pp_cal, db_2v5_cal, db_1v8_cal, db_1v0_cal, db_0v95_cal,
                                            db_1v2_cal, db_5v0_cal, db_1v5_cal, db_3v3_cal, db_pg_cal, db_pg_cal, db_pg_cal, db_pg_cal, db_5v0pp_cal, db_2v5_cal, db_1v8_cal, db_1v0_cal, db_0v95_cal]


channel_label = ["dba_1v2", "dba_5v0", "dba_1v5", "dba_3v3", "dba_pg2", "dba_pg3", "dba_pg4", "dba_pg1", "dba_5v0p", "dba_2v5", "dba_1v8", "dba_1v0",  "dba_0v95",
                "dbb_1v2", "dbb_5v0", "dbb_1v5", "dbb_3v3", "dbb_pg2", "dbb_pg3", "dbb_pg4", "dbb_pg1", "dbb_5v0p", "dbb_2v5", "dbb_1v8", "dbb_1v0",  "dbb_0v95"
                ]


# DAC sweep range (0-4095 for 12-bit DAC)

delimiter_line = "=========="
first_row = ""
mux_row = ""
adc_row = ""
channel_label_row = ""
info_row = ""


def print_header():
    print(delimiter_line)
    global first_row, mux_row, adc_row, channel_label_row, info_row


    for i in range(nr_of_channels):
        first_row += f"ch_{channel_label[i]}\t"
        mux_row += f"mux_ch_{mux_ch[i]}\t"
        adc_row += f"adc_ch_{output_adc_ch[i]}\t"
        channel_label_row += f"{channel_label[i]}\t"
        info_row += f"{channel_label[i]}_adc[{output_adc_ch[i]}]_mux[{mux_ch[i]}]\t"
        
    # first_row += "\t|||\t\t"
  
    print(info_row)
    print(first_row)

phase=0
iteration = 0
max_iterations = 10

mux_settle_ms = 50  # time to wait after changing MUX channel
adc_samples = 5   # choose how many samples to average
adc_settle_ms = 5   # small delay between samples (adjust if needed)

def db_el_test():
    global iteration, info_row, channel_label_row
    global phase

    if iteration < max_iterations:
        iteration += 1
    else:
        iteration = 0
        print(channel_label_row)
        phase=not phase
        
    for i in range(nr_of_channels):
        mux.select_channel(mux_ch[i])
        time.sleep_ms(mux_settle_ms)  # Allow settling time
        acc = 0.
        for _ in range(adc_samples):
            output_adc_value[i] = adc.read_channel_raw(output_adc_ch[i])
            acc += output_adc_value[i]
            time.sleep_ms(adc_settle_ms)


        
        output_adc_value_avg[i] = acc // adc_samples  # integer average

       
        output_adc_value_v[i] = output_adc_value_avg[i] * adc_cal * output_adc_value_v_calibration_factor[i] # * voltage_calibration_value
    row_adc = ""
    row_v = ""
    for i in range(nr_of_channels):
        row_adc += f"{output_adc_value[i]}\t"
        row_v += f"{output_adc_value_v[i]:.3f}V\t"
    print(f"{row_adc}")
    cprint(f"{row_v}")


def cprint(msg):
    if cprint_enabled:
        print("--" + msg + "--")

waiting_interval = 180  # seconds

def main():
    print_header()
    cprint(channel_label_row)
    while True:

        # print(delimiter_line + delimiter_line)
        db_el_test()
        if poller.poll(0):          # non-blocking
            cmd = sys.stdin.read(1)

            if cmd == 't':
                print("CMD: t")

            elif cmd == 'f':
                print("CMD: f")
        # print(delimiter_line + delimiter_line)



if __name__ == "__main__":
    main()
    
    