import socket
import time
from datetime import datetime
import pandas as pd
import paho.mqtt.client as mqtt
import json
import os
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
from mqttServices import mqtt_config as config

mqtt_client = mqtt.Client(config.mqtt_client)
domain = config.domain
broker = config.mqtt_broker

pumpON = {'register': [101, 104], 'bit': [0x01, 0x00]}
pumpOFF = {'register': [101, 104], 'bit': [0x01, 0x01]}


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
        # powerPump('DigitalHub', 'DH_dda001', False)
    else:
        print(f"Failed to connect, return code {rc}", "Error\t")


def on_disconnect(client, userdata, rc):
    print(f"Unexpected disconnection due to {rc}")
    try:
        print("Reconnecting...")
        mqtt_client.reconnect()
    except socket.error:
        time.sleep(5)
        mqtt_client.reconnect()


def powerPump(customer, location, pumpname, powerButton):
    topic = domain + 'edits/' + customer + '/' + location + '/' + pumpname
    if powerButton:
        package = json.dumps(pumpON)
    if not powerButton:
        package = json.dumps(pumpOFF)
    try:
        mqtt_client.loop_start()
        mqtt_client.on_connect = on_connect
        mqtt_client.publish(topic, package, qos=1)  # publish to MQTT Broker every 5s
        print(f'{datetime.now()}: publishing {package} to {topic}')
        mqtt_client.loop_stop()
    except Exception as r:
        print(f'There was an issue sending data because {r}')


def pumpSpeed(customer, location, pumpname, rate):
    topic = domain + 'edits/' + customer + '/' + location + '/' + pumpname
    package = json.dumps({'register': [104, 107], 'bit': [0x00, int(rate * 10000)]})
    try:
        mqtt_client.loop_start()
        mqtt_client.publish(topic, package, qos=1)  # publish to MQTT Broker every 5s
        print(f'{datetime.now()}: publishing {package} to {topic}')
        mqtt_client.loop_stop()
    except Exception as r:
        print(f'There was an issue sending data because {r}')


mqtt_client.tls_set()
# set username and password
mqtt_client.username_pw_set(config.mqtt_username, config.mqtt_pass)
# connect to HiveMQ Cloud on port 8883
mqtt_client.connect(broker, 8883, keepalive=60)
mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect
