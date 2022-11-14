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

conn = db.connect(DRIVER='SQL Server',
                  SERVER=config.server_name,
                  UID=config.user,
                  PWD=config.pwd,
                  DATABASE=config.database_name,)
                  # MultipleActiveResultSets=True)


def createTable(db_name, tablename, columns, conn=conn):
    insertCMD = f'''CREATE TABLE "{tablename}" ({columns});'''
    cur = conn.cursor()
    try:
        cur.execute(insertCMD)
        conn.commit()
        print(f"Table {tablename} was created in DB {db_name}")
    except(Exception, db.DatabaseError) as error:
        print(error)


def writeValues(metrics, table, conn=conn):
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
    except (Exception, db.DatabaseError) as error:
        print(error)


def getData(tablename, orderby, conn=conn):
    qu = f'select * from "{tablename}" order by "{orderby}" desc'
    alldata = pd.read_sql_query(qu, conn)
    return alldata


def delData(tablename, conn=conn):
    try:
        cur = conn.cursor()
        q = f"delete from {tablename};"
        cur.execute(q)
        l = getData(tablename, conn)
        if len(l['Address'].tolist()) == 0:
            print("Delete Succesful")
    except (Exception, db.DatabaseError) as error:
        print(error)
