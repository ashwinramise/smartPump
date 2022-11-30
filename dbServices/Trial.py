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
import db_config as config

conn = db.connect(DRIVER='SQL Server',
                  SERVER=config.server_name,
                  UID=config.user,
                  PWD=config.pwd,
                  DATABASE=config.database_name,)
                  # MultipleActiveResultSets=True)

# qu = f'select top (1) * from "PoC_SP_Metrics" order by "RecordID" desc'
qu = qu = f'''select * from "PoC_SP_UserLogs" order by RecordID desc'''
cur = conn.cursor()
cur.execute(qu)
df = pd.DataFrame(columns=["User", "Last_Access", "RecordID"])
# df = pd.read_sql_query(qu, conn)
for i in cur:
    log = [r for r in i]
    df.loc[len(df)] = log
print(df)