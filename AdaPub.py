# Hacked by Hari Wiguna to read two buttons and publish json to adafruit.io feed.

# The MIT License (MIT)
# Copyright (c) 2019 Mike Teachman
# https://opensource.org/licenses/MIT

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
left_button = Pin(14, Pin.IN, Pin.PULL_UP)  # 13
right_button = Pin(2, Pin.IN, Pin.PULL_UP)  # 15

# === WIFI CONFIG ===
with open("config.json") as f:
    config = json.load(f)
WIFI_SSID = config["SSID"]
WIFI_PASSWORD = config["SSID_PASSWORD"]

# === MQTT CONFIG ===
ADAFRUIT_USERNAME = config["ADAFRUIT_USERNAME"]
ADAFRUIT_IO_KEY = config["ADAFRUIT_IO_KEY"]
ADAFRUIT_IO_FEEDNAME = config["ADAFRUIT_IO_FEEDNAME"]

# turn off the WiFi Access Point
ap_if = network.WLAN(network.AP_IF)
ap_if.active(False)

# connect the device to the WiFi network
print('First, connecting to {}'.format(WIFI_SSID))
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(WIFI_SSID, WIFI_PASSWORD)

# wait until the device is connected to the WiFi network
MAX_ATTEMPTS = 20
attempt_count = 0
while not wifi.isconnected() and attempt_count < MAX_ATTEMPTS:
    print('Attempt {}'.format(attempt_count))
    attempt_count += 1
    time.sleep(1)

if attempt_count == MAX_ATTEMPTS:
    print('could not connect to the WiFi network')
    sys.exit()

print("CONNECTED!")

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

print('Connecting to MQTT server {}'.format(ADAFRUIT_IO_URL))

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

print('CONNECTED')

# publish free heap statistics to Adafruit IO using MQTT
# subscribe to the same feed
#
# format of feed name:
#   "ADAFRUIT_USERNAME/feeds/ADAFRUIT_IO_FEEDNAME"
mqtt_feedname = bytes('{:s}/feeds/{:s}'.format(ADAFRUIT_USERNAME, ADAFRUIT_IO_FEEDNAME), 'utf-8')
lastp2Val = 0
lastp14Val = 0
while True:
    try:
        # Publish
        p2Val = 1 - right_button.value()
        p14Val = 1 - left_button.value()
        if p2Val != lastp2Val or p14Val != lastp14Val:
            postVal = p2Val * 2 + p14Val
            print("pin2={} pin14={} post={}".format(p2Val, p14Val, postVal))
            j = json.dumps({'left': p14Val, 'right': p2Val})
            print(j)
            client.publish(mqtt_feedname,
                           bytes(j, 'utf-8'),
                           qos=0)
            lastp2Val = p2Val
            lastp14Val = p14Val
            time.sleep(0.1)

    except KeyboardInterrupt:
        print('Ctrl-C pressed...exiting')
        client.disconnect()
        sys.exit()
