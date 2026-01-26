#!/usr/bin/python3

import cartonnage
from ake_connections import *

import sqlite3
sqlite3Connection = sqlite3.connect(AKESQLiteConfig.DATABASE_PATH, check_same_thread=True)
sqlite3Database = SQLite(sqlite3Connection)
Record.database__  = sqlite3Database

class Departments(Record): pass

departments = Departments()
departments.all()
print(f"{'-'*80}\nDepartments:")
for employee in departments:
	print(employee.data)

departments.recordset.delete()
print(departments.query__.statement)
print(departments.query__.parameters)
assert departments.recordset.rowsCount == 11, f"Deleted rows count: {departments.recordset.rowsCount}"
print(f"{'-'*80}\n{departments.recordset.rowsCount} have been deleted.")

departments = Departments()
departments.all()
print(f"{'-'*80}")
print(f"Departments List:{departments.recordset.toLists()}")

# def initOracleConnection():
# 	oracledb.init_oracle_client(lib_dir=AKEOracleConfig.CLIENT_LIB_DIR)

# 	load_dotenv()
# 	connection = oracledb.connect(
# 		user=AKEOracleConfig.USER,
# 		password=AKEOracleConfig.PASSWORD,
# 		dsn=AKEOracleConfig.DSN
# 	)
# 	return connection

# oracleCOnnection = initOracleConnection()
# oracleDatabase = Oracle(oracleCOnnection)
# Record.database__ = oracleDatabase # change database connection
# print(f"{'-'*80}\nDatabase connection has been changed from SQLite3 to Oracle.")

# departments = Departments()
# departments.all()
# print(f"{'-'*80}\n{departments.recordset.count()} have been retreived from Oracle.")

# Record.database__  = sqlite3Database
# print(f"{'-'*80}\nDatabase connection has been changed from Oracle to SQLite3.")
# departments.recordset.insert()
# print(f"{'-'*80}\n{departments.recordset.rowsCount} have been saved to SQLite3.")

# print(f"{'-'*80}")
# print(f"Departments List:{departments.recordset.toLists()}")