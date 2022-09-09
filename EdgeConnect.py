#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  EdgeConnect.py
#  
#  Copyright 2022 SMartPump <smartpump@smartpump-desktop>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.


from pymodbus.pdu import ModbusRequest
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
from pymodbus.transaction import ModbusRtuFramer
import time
from datetime import datetime
import pandas as pd
import paho.mqtt.client as mqtt
import json
import pyodbc

# MQTT defenitions
mqtt_client = mqtt.Client('BuckmanDigital')
mqtt_broker = 'broker.hivemq.com'
topic = 'buckman/ackumen/ddapump'
mqtt_client.connect(mqtt_broker)


def translator(data):
    reg = {}
    i = 201
    for c in range(len(data)):
        reg.update({i: data[c]})
        i += 1
    return reg


# Connect To Client and Get Data
client = ModbusClient(method='rtu', port='/dev/ttyUSB0', parity='N', baudrate=9600, stopbits=2, auto_open=True)
try:
    conn = client.connect()
    if conn:
        print('Connected')
        while True:
            read = client.read_holding_registers(address=201, count=100,
                                                 unit=27)  # read holding registers from device number 27
            metrics = translator(read.registers)  # formulate data dictionary
            # define data in SparkPlugB structure
            pub_data = {
                'site': 'digitalHUB',
                'timestamp': str(datetime.now()),
                'metrics': metrics
            }
            message = json.dumps(pub_data)
            try:
                mqtt_client.publish(topic, message, qos=0)  # publish to MQTT Broker every 5s
                print(f'{datetime.now()}: publishing {message} to {topic}')
            except:
                print('There was an issue sending data')
            time.sleep(5)
except Exception as e:
    print(e)
