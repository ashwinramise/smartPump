import random

from pymodbus.pdu import ModbusRequest
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
from pymodbus.transaction import ModbusRtuFramer
import time
from datetime import datetime
import pandas as pd
import paho.mqtt.client as mqtt
import json
import mqtt_config as config

mqtt_client = mqtt.Client(config.pumpName)
topic = config.domain + 'rawdata/' + config.Location + '/' + config.pumpName
broker = config.mqtt_broker
mqtt_topic = config.domain + 'edits/' + config.Location + '/' + config.pumpName

regs = pd.read_csv('RegisterData.csv')
holding = regs['Address'].tolist()

last_message = None


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
        print(f"Listening on topic: {mqtt_topic}")
    else:
        print(f"Failed to connect, return code {rc}", "Error\t")


def on_disconnect(client, userdata, rc):
    print(f"Unexpected disconnection due to {rc}")
    while True:
        conn = mqtt_client.connect(broker, keepalive=60)
        print("Reconnecting...")
        if conn:
            break
        else:
            continue
        time.sleep(5)


requirements = {
    208: [0, 63500],
    104: [0, 1],
    312: [0, 7000],
    308: [0, 20]
}
mqtt_client.connect(broker)
while True:
    metrics = []
    current = {}
    for reg in holding:
        if reg in requirements.keys():
            metrics.append({str(reg): str(random.randint(requirements[reg][0], requirements[reg][1]))})
            current.update({str(reg): str(random.randint(requirements[reg][0], requirements[reg][1]))})
        else:
            metrics.append({str(reg): str(0)})
            current.update({str(reg): str(0)})
        pub_data = {
            'site': config.Location,
            'pump': config.pumpName,
            'timestamp': str(datetime.now()),
            'metrics': metrics
        }
    if last_message is None or current != last_message:
        message = json.dumps(pub_data)
        last_message = current
        try:
            mqtt_client.publish(topic, message, qos=0)
            print(f'{datetime.now()}: published {message} to {topic}')
        except Exception as r:
            print(f'There was an issue sending data because {r}.. Reconnecting')
            connection = mqtt_client.connect(broker)
    elif current == last_message:
        continue
    time.sleep(2)  # repeat
