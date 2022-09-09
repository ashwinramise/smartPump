# File contains all services required of the middleware
import pandas as pd
from datetime import datetime, timedelta
import psycopg2 as pg
import numpy as np
from Services import db_config
import smip_connect as smip

username = db_config.user
password = db_config.password
host = db_config.host
port = db_config.port


# Function to get all equipment types from the database to display machine names
def getEqtypes():
    conn = pg.connect(f"host = {host} port = {port} user={username} "
                      f"password={password}")
    CMD = "select datname from pg_database"
    eq_types = pd.read_sql_query(CMD, conn)
    return eq_types['datname'].tolist()


# Function to get the machine names relative to the machine type
def getEq(db_name):
    conn = pg.connect(f"host = {host} dbname = {db_name} port = {port} user={username} "
                       f"password={password}")
    CMD = "select * from information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'"
    eq = pd.read_sql_query(CMD, conn)
    equipment = eq['table_name'].tolist()
    return equipment


# Function to get all variable names from the table and display them - first run
def getVarsFirst(db_name, mc_name):
    conn = pg.connect(f"host = {host} dbname = {db_name} port = {port} user={username} "
                      f"password={password}")
    qu = f'select * from "{mc_name}"'
    cols = pd.read_sql_query(qu, conn)
    col = pd.DataFrame(cols.columns.tolist(), columns=['Parameter'])
    return col


# Write table to display current publishing status
def getPubStatus(host2, db_name, mc_name):
    df = getVarsFirst(db_name, mc_name)
    vars = df['Parameter'].tolist()
    conn = pg.connect(f"host = {host2} dbname = {mc_name} port = {port} user={username} "
                      f"password={password}")
    qu = f'select * from "{mc_name}"'
    vars_2 = pd.read_sql_query(qu, conn)['Parameter'].tolist()
    status = []
    for i in vars:
        if i in vars_2:
            status.append("Active")
        else:
            status.append("Inactive")
    statusBoard = pd.DataFrame()
    statusBoard['Parameter'] = vars
    statusBoard['Status'] = status
    return statusBoard


# Creates a new table to record data for a machine
def createDbTable(host2, db_name, mc_name):
    conn = pg.connect(f"host = {host2} dbname = {db_name} port = {port} user={username} "
                      f"password={password}")
    try:
        cur = conn.cursor()
        print("Subscriber connection established")
    except (Exception, pg.DatabaseError) as error:
        print(error)

    topic = mc_name
    while True:
        try:
            colnames = smip.getAttributeID(mc_name)
            break
        except ValueError:
            print("Machine Unavailable")
    columns = ""
    for col in colnames['relativeName']:
        columns = f'{columns}, "{col}" text'

    def createTable():
        insertCMD = f'CREATE TABLE IF NOT EXISTS public."{topic}" ({columns});'
        cur.execute(insertCMD)

    try:
        createTable()
        conn.commit()
        print(f"Table {topic} was created in DB {db_name}")
    except(Exception, pg.DatabaseError) as error:
        print(error)

