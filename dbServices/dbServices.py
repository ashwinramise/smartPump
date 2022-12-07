import pandas as pd
import pyodbc as db
import numpy as np
import time
import os
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
from dbServices import db_config as config
                  # MultipleActiveResultSets=True)


def createTable(db_name, tablename, columns):
    conn = db.connect(DRIVER='SQL Server',
                      SERVER=config.server_name,
                      UID=config.user,
                      PWD=config.pwd,
                      DATABASE=config.database_name, )
    insertCMD = f'''CREATE TABLE "{tablename}" ({columns});'''
    cur = conn.cursor()
    try:
        cur.execute(insertCMD)
        conn.commit()
        print(f"Table {tablename} was created in DB {db_name}")
        conn.close()
    except(Exception, db.DatabaseError) as error:
        print(error)


def writeValues(metrics, table):
    conn = db.connect(DRIVER='SQL Server',
                      SERVER=config.server_name,
                      UID=config.user,
                      PWD=config.pwd,
                      DATABASE=config.database_name, )
    try:
        cur = conn.cursor()
    except (Exception, db.DatabaseError) as error:
        print(error)
    keys = list(metrics.keys())
    values = tuple(metrics.values())
    cols = '"' + ('","').join(keys) + '"'
    s_lens = "?," * len(keys)
    s = s_lens.split(",")
    s = (",").join(s[:-1])
    insertQ = f""" INSERT INTO {table} ({cols})
                    VALUES({s})"""
    try:
        cur.execute(insertQ, values)
        conn.commit()
        print(f'Values Inserted: {values}')
        cur.close()
        conn.close()
    except (Exception, db.DatabaseError) as error:
        print(error)


def getData(tablename, orderby):
    conn = db.connect(DRIVER='SQL Server',
                      SERVER=config.server_name,
                      UID=config.user,
                      PWD=config.pwd,
                      DATABASE=config.database_name, )
    qu = f'select * from "{tablename}" order by "{orderby}" desc'
    alldata = pd.read_sql_query(qu, conn)
    conn.close()
    return alldata

def getRecordID(tablename):
    conn = db.connect(DRIVER='SQL Server',
                      SERVER=config.server_name,
                      UID=config.user,
                      PWD=config.pwd,
                      DATABASE=config.database_name, )
    qu = f'select MAX(RecordID) as RecordID FROM {tablename}'
    cur = conn.cursor()
    cur.execute(qu)
    k = None
    for i in cur:
        k=i[0]
    cur.close()
    conn.close()
    return k

def getSpeedTime(site, pump):
    conn = db.connect(DRIVER='SQL Server',
                      SERVER=config.server_name,
                      UID=config.user,
                      PWD=config.pwd,
                      DATABASE=config.database_name, )
    qu = f'''select top(1) "208", Timestamp from "PoC_SP_Metrics" WHERE site like '{site}' AND pumpID like '{pump}' 
    order by RecordID desc;'''
    cur = conn.cursor()
    cur.execute(qu)
    speed = None
    timestamp=None
    for i in cur:
        speed = int(i[0])/10000
        timestamp = pd.to_datetime(i[1])
    cur.close()
    conn.close()
    return speed, timestamp


def getPowerStatus(site, pump):
    conn = db.connect(DRIVER='SQL Server',
                      SERVER=config.server_name,
                      UID=config.user,
                      PWD=config.pwd,
                      DATABASE=config.database_name, )
    qu = f'''select top(1) 104 from "PoC_SP_Metrics" WHERE site like '{site}' AND pumpID like '{pump}' 
        order by RecordID desc;'''
    cur = conn.cursor()
    cur.execute(qu)
    for i in cur:
        power = int(i[0])
        conn.close()
        return power

def getDashData(site, pump):
    conn = db.connect(DRIVER='SQL Server',
                      SERVER=config.server_name,
                      UID=config.user,
                      PWD=config.pwd,
                      DATABASE=config.database_name, )
    qu = f'''select top(1) "104", "312", "208", Timestamp from "PoC_SP_Metrics" WHERE site like '{site}' AND pumpID 
    like '{pump}' order by RecordID desc;'''
    cur = conn.cursor()
    cur.execute(qu)
    speed = None
    timestamp = None
    for i in cur:
        status = int(i[0])
        pressure = float(i[1])/1000
        speed = int(i[2]) / 10000
        timestamp = pd.to_datetime(i[3])
    cur.close()
    conn.close()
    return status, pressure, speed, timestamp


def delData(tablename):
    conn = db.connect(DRIVER='SQL Server',
                      SERVER=config.server_name,
                      UID=config.user,
                      PWD=config.pwd,
                      DATABASE=config.database_name, )
    try:
        cur = conn.cursor()
        q = f"delete from {tablename};"
        cur.execute(q)
        l = getData(tablename, conn)
        if len(l['Address'].tolist()) == 0:
            print("Delete Succesful")
            conn.close()
    except (Exception, db.DatabaseError) as error:
        print(error)


def getAssetData():
    conn = db.connect(DRIVER='SQL Server',
                      SERVER=config.server_name,
                      UID=config.user,
                      PWD=config.pwd,
                      DATABASE=config.database_name, )
    qu = f'''select * from "PoC_SP_Assets" order by RecordID desc'''
    cur = conn.cursor()
    cur.execute(qu)
    df = pd.DataFrame(columns=['Location', 'PumpName'])
    for i in cur:
        df.loc[len(df)] = [i[0], i[1]]
    cur.close()
    conn.close()
    return df


def getUserLogs():
    conn = db.connect(DRIVER='SQL Server',
                      SERVER=config.server_name,
                      UID=config.user,
                      PWD=config.pwd,
                      DATABASE=config.database_name, )
    qu = f'''select * from "PoC_SP_UserLogs" order by RecordID desc'''
    cur = conn.cursor()
    cur.execute(qu)
    df = pd.DataFrame(columns=["User", "Last_Access", "RecordID"])
    for i in cur:
        log = [r for r in i]
        df.loc[len(df)] = log
    cur.close()
    conn.close()
    return df.to_dict('records')

