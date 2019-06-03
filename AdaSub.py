# Hacked by Hari Wiguna to control two leds based on data published at adafruit.io feed.

# The MIT License (MIT)
# Copyright (c) 2019 Mike Teachman
# https://opensource.org/licenses/MIT
#
# Example MicroPython and CircuitPython code showing how to use the MQTT protocol to
# subscribe to an Adafruit IO feed

import network
import time
from umqtt.robust import MQTTClient
import os
import sys
import json

# === PINS ===
from machine import Pin
left_button = Pin(13, Pin.IN, Pin.PULL_UP)
right_button = Pin(15, Pin.IN, Pin.PULL_UP)
left_led = Pin(12, Pin.OUT)
right_led = Pin(2, Pin.OUT)

# === WIFI CONFIG ===
with open("config.json") as f:
    config = json.load(f)
WIFI_SSID = config["SSID"]
WIFI_PASSWORD = config["SSID_PASSWORD"]

# === MQTT CONFIG ===
ADAFRUIT_USERNAME = config["ADAFRUIT_USERNAME"]
ADAFRUIT_IO_KEY = config["ADAFRUIT_IO_KEY"]
ADAFRUIT_IO_FEEDNAME = config["ADAFRUIT_IO_FEEDNAME"]

# the following function is the callback which is
# called when subscribed data is received
def cb(topic, msg):
    print('Received Data:  Topic = {}, Msg = {}'.format(topic, msg))
    j = json.loads(msg)
    print("left is {}, right is {}".format(j["left"], j["right"]))
    left_led.value(1 - j["left"])
    right_led.value(1 - j["right"])

# WiFi connection information
# WIFI_SSID = '<ENTER_WIFI_SSID>'
# WIFI_PASSWORD = '<ENTER_WIFI_PASSWORD>'

# turn off the WiFi Access Point
ap_if = network.WLAN(network.AP_IF)
ap_if.active(False)

# connect the device to the WiFi network
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(WIFI_SSID, WIFI_PASSWORD)

# wait until the device is connected to the WiFi network
MAX_ATTEMPTS = 20
attempt_count = 0
while not wifi.isconnected() and attempt_count < MAX_ATTEMPTS:
    attempt_count += 1
    time.sleep(1)

if attempt_count == MAX_ATTEMPTS:
    print('could not connect to the WiFi network')
    sys.exit()

# create a random MQTT clientID
random_num = int.from_bytes(os.urandom(3), 'little')
mqtt_client_id = bytes('client_' + str(random_num), 'utf-8')

# connect to Adafruit IO MQTT broker using unsecure TCP (port 1883)
#
# To use a secure connection (encrypted) with TLS:
#   set MQTTClient initializer parameter to "ssl=True"
#   Caveat: a secure connection uses about 9k bytes of the heap
#         (about 1/4 of the micropython heap on the ESP8266 platform)
ADAFRUIT_IO_URL = b'io.adafruit.com'
# ADAFRUIT_USERNAME = b'<ENTER_ADAFRUIT_USERNAME>'
# ADAFRUIT_IO_KEY = b'<ENTER_ADAFRUIT_IO_KEY>'
# ADAFRUIT_IO_FEEDNAME = b'freeHeap'

client = MQTTClient(client_id=mqtt_client_id,
                    server=ADAFRUIT_IO_URL,
                    user=ADAFRUIT_USERNAME,
                    password=ADAFRUIT_IO_KEY,
                    ssl=False)

try:
    client.connect()
except Exception as e:
    print('could not connect to MQTT server {}{}'.format(type(e).__name__, e))
    sys.exit()

mqtt_feedname = bytes('{:s}/feeds/{:s}'.format(ADAFRUIT_USERNAME, ADAFRUIT_IO_FEEDNAME), 'utf-8')
client.set_callback(cb)
client.subscribe(mqtt_feedname)

# following two lines is an Adafruit-specific implementation of the Publish "retain" feature
# which allows a Subscription to immediately receive the last Published value for a feed,
# even if that value was Published two hours ago.
# Described in the Adafruit IO blog, April 22, 2018:  https://io.adafruit.com/blog/
mqtt_feedname_get = bytes('{:s}/get'.format(mqtt_feedname), 'utf-8')
client.publish(mqtt_feedname_get, '\0')

# wait until data has been Published to the Adafruit IO feed
while True:
    try:
        client.wait_msg()
    except KeyboardInterrupt:
        print('Ctrl-C pressed...exiting')
        client.disconnect()
        sys.exit()