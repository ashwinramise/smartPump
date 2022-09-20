import paho.mqtt.client as mqtt
import json
import os
import sys
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
from dbServices import db_config, dbServices as db


mqttClient = mqtt.Client("hubMemphis")
mqtt_topic = db_config.topic
mqttBroker = db_config.broker
dbCon = db.conn


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
    print("Unexpected disconnection.")


def on_message(client, userdata, msg):
    x = msg.payload
    load = json.loads(x)['metrics']
    metrics = getDict(load)
    db.writeValues(metrics, dbCon, db_config.dataTable)


mqttClient.connect(mqttBroker)
mqttClient.on_connect = on_connect
mqttClient.on_message = on_message
mqttClient.on_disconnect = on_disconnect
mqttClient.subscribe(mqtt_topic)
mqttClient.loop_forever()
