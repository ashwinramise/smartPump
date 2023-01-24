import socket
import time
import paho.mqtt.client as mqtt
import json
import os
import sys
import inspect
import pandas as pd
import warnings
import pyodbc as dbc

warnings.filterwarnings("ignore")

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
from dbServices import db_config as config
from dbServices import dbServices as db

mqttClient = mqtt.Client("hubMemphis", clean_session=False)
mqtt_topic = config.topic
mqttBroker = config.broker
dbCon = dbc.connect(DRIVER='SQL Server',
                      SERVER=config.server_name,
                      UID=config.user,
                      PWD=config.pwd,
                      DATABASE=config.database_name, )


def getDict(metrics):
    cols = [list(i.keys())[0] for i in metrics]
    vals = [list(i.values())[0] for i in metrics]
    dataDict={}
    for i in range(len(cols)):
        dataDict.update({cols[i]: vals[i]})
    return dataDict


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print(f"Failed to connect, return code {rc}", "Error\t")


def on_disconnect(client, userdata, rc):
    print(f"Unexpected disconnection due to {rc}")
    try:
        print("Reconnecting...")
        mqttClient.reconnect()
    except socket.error:
        time.sleep(5)
        mqttClient.reconnect()


def on_message(client, userdata, msg):
    x = msg.payload
    incoming = json.loads(x)
    load = incoming['metrics']
    load.append({'Timestamp': incoming['timestamp']})
    load.append({'site': incoming['site']})
    load.append({'pumpID': incoming['pump']})
    history = db.getRecordID('PoC_SP_Metrics')
    if history is None:
        record = 1
    else:
        record = history + 1
    load.append({'RecordID': record})
    metrics = getDict(load)
    db.writeValues(metrics, config.dataTable)


mqttClient.connect(mqttBroker)
mqttClient.on_connect = on_connect
mqttClient.on_message = on_message
mqttClient.on_disconnect = on_disconnect
mqttClient.subscribe(mqtt_topic, qos=1)
mqttClient.loop_forever()
