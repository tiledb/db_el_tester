import time
import shared
from machine import Pin, SPI, I2C
import sys
import uselect
from netmgr import NetManager
import secrets
import ujson
import display_task


net = NetManager(
    wifi_ssid=secrets.WIFI_SSID,
    wifi_pass=secrets.WIFI_PASS,
    mqtt_broker=secrets.MQTT_BROKER,
    mqtt_user=secrets.MQTT_USER,
    mqtt_pass=secrets.MQTT_PASS,
    mqtt_port=secrets.MQTT_PORT,
    base_topic=secrets.MQTT_BASE_TOPIC
)

def _safe_id(s):
    return (
        s.replace(".", "_")
         .replace(" ", "_")
         .replace("/", "_")
    )

import ujson
import secrets

def _safe_id(s):
    return s.replace(".", "_").replace(" ", "_")


def clear_mqtt_discovery(net, labels):
    count = 0
    device_id = f"{secrets.BOARD_NAME}_{secrets.BOARD_ID}"

    for label in labels:
        for t in [
            f"{secrets.DISCOVERY_PREFIX}/sensor/{device_id}_{label}/config",
            f"{secrets.DISCOVERY_PREFIX}/binary_sensor/{device_id}_{label}_alarm/config"
        ]:
            net.publish_raw(t.encode(), b"", retain=True)
            count += 1

    # Device-based discovery
    device_topic = f"{secrets.DISCOVERY_PREFIX}/device/{device_id}/config"
    net.publish_raw(device_topic.encode(), b"", retain=True)
    count += 1

    return count



def send_discovery(net, labels):
    device_id = f"{secrets.BOARD_NAME}_{secrets.BOARD_ID}"
    base = secrets.MQTT_BASE

    device = {
        "identifiers": [device_id],
        "name": f"{secrets.BOARD_NAME} {secrets.BOARD_ID}",
        "manufacturer": "Custom",
        "model": "Pico W ADC Monitor"
    }

    for label in labels:
        safe = _safe_id(label)

        # ---- Voltage sensor ----
        sensor_id = f"{device_id}_{safe}"
        topic = (
            f"{secrets.DISCOVERY_PREFIX}/sensor/"
            f"{sensor_id}/config"
        )

        payload = {
            "name": label,
            "state_topic": f"{base}/{label}",
            "unit_of_measurement": "V",
            "device_class": "voltage",
            "suggested_display_precision": 3,
            "unique_id": sensor_id,
            "device": device
        }

        net.publish_raw(
            topic.encode(),
            ujson.dumps(payload).encode(),
            retain=True
        )

        # ---- Alarm ----
        alarm_id = f"{sensor_id}_alarm"
        alarm_topic = (
            f"{secrets.DISCOVERY_PREFIX}/binary_sensor/"
            f"{alarm_id}/config"
        )

        alarm_payload = {
            "name": f"{label} Alarm",
            "state_topic": f"{base}/{label}/alarm",
            "payload_on": "ON",
            "payload_off": "OFF",
            "device_class": "problem",
            "unique_id": alarm_id,
            "device": device
        }

        net.publish_raw(
            alarm_topic.encode(),
            ujson.dumps(alarm_payload).encode(),
            retain=True
        )

        # Let GC breathe
        import gc
        gc.collect()

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

    discovery_sent = False
    last_mqtt = time.ticks_ms()
    
    last_mqtt = time.ticks_ms()
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

        if net.ensure_connected():
            if not discovery_sent:
                send_discovery(net, shared.channel_label)
                time.sleep(10)
                discovery_sent = True

        if time.ticks_diff(time.ticks_ms(), last_mqtt) > 1000:
            last_mqtt = time.ticks_ms()

            shared.data_lock.acquire()
            values = shared.output_adc_value_v[:]
            # Check for test mode
            if not display_task.btn_y.value() and not display_task.btn_b.value():  # both pressed
                vmin = shared.output_adc_value_min_test[:]
                vmax = shared.output_adc_value_max_test[:]
            else:
                vmin = shared.output_adc_value_min[:]
                vmax = shared.output_adc_value_max[:]

            labels = shared.channel_label[:]
            shared.data_lock.release()

            state = {}

            for i, label in enumerate(labels):
                state[label] = values[i]
                state[f"{label}_alarm"] = "ON" if not (vmin[i] <= values[i] <= vmax[i]) else "OFF"

            net.publish(
                b"state",
                ujson.dumps(state).encode()
            )

        time.sleep(0.5)

