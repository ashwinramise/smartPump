from pymodbus.pdu import ModbusRequest
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
from pymodbus.transaction import ModbusRtuFramer
import time
from datetime import datetime
import pandas as pd
import os
import sys
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
from dbServices import dbServices as db

dbCon = dbServices.conn

# Connect To Client and Get Data
client = ModbusClient(method='rtu', port='/dev/ttyUSB0', parity='N', baudrate=9600, stopbits=2, auto_open=True)
try:
    conn = client.connect()
    if conn:
        print('Connected')
        registers = [int(i) for i in db.getData('PoC_SP_MonitoringTags', dbCon)['Address'].tolist()]
        while True:
            publish = []
            for reg in registers:
                read = client.read_holding_registers(address=reg, count=1,
                                                     unit=27)
                publish.append({str(reg) : str(read.registers[0])})
            db.writeValues(publish)
            time.sleep(5)
except Exception as e:
    print(e)
