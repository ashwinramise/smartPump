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
mqtt_client.connect(broker)

pumpON = {'register': [100, 103], 'bit': [0x01, 0x00]}
pumpOFF = {'register': [100, 103], 'bit': [0x01, 0x01]}


def powerPump(location, pumpname, powerButton):
    topic = domain + 'edits/' + location + '/' + pumpname
    if powerButton:
        package = json.dumps(pumpON)
    if not powerButton:
        package = json.dumps(pumpOFF)
    try:
        mqtt_client.publish(topic, package, qos=0)  # publish to MQTT Broker every 5s
        print(f'{datetime.now()}: publishing {package} to {topic}')
    except Exception as e:
        print(e)


def pumpSpeed(location, pumpname, rate):
    topic = domain + 'edits/' + location + '/' + pumpname
    package = json.dumps({'register': [104, 106], 'bit': [0x00, int(rate * 10000)]})
    try:
        mqtt_client.publish(topic, package, qos=0)  # publish to MQTT Broker every 5s
        print(f'{datetime.now()}: publishing {package} to {topic}')
    except Exception as e:
        print(e)
