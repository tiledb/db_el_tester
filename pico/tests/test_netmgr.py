import time
from netmgr import NetManager
import secrets

print("Starting NetManager test...")

net = NetManager(
    wifi_ssid=secrets.WIFI_SSID,
    wifi_pass=secrets.WIFI_PASS,
    mqtt_broker=secrets.MQTT_BROKER,
    mqtt_user=secrets.MQTT_USER,
    mqtt_pass=secrets.MQTT_PASS,
    mqtt_port=secrets.MQTT_PORT,
    base_topic=secrets.MQTT_BASE_TOPIC
)

counter = 0

while True:
    # Ensure connections
    if net.ensure_connected():
        print("Connected ✓")

        # Publish test messages
        net.publish(b"test/status", b"online")
        net.publish(b"test/counter", str(counter).encode())

        print("Published counter:", counter)
        counter += 1
    else:
        print("Not connected ✗")

    time.sleep(2)
