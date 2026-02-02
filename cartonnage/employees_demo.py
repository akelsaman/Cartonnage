# #!/usr/bin/python3

import cartonnage
from ake_connections import *

import sqlite3
sqlite3Connection = sqlite3.connect(AKESQLiteConfig.DATABASE_PATH, check_same_thread=True)
sqlite3Database = SQLite(sqlite3Connection)
Record.database__  = sqlite3Database

class Employees(Record): pass

employees = Employees().all()
print(f"{'-'*80}\nEmployees:")
for employee in employees:
	print(employee.data)

employees.recordset.delete(onColumns=["employee_id"])
print(employees.query__.statement)
print(employees.query__.parameters)
assert employees.recordset.rowsCount() == 40, f"Deleted rows count: {employees.recordset.rowsCount()}"
print(f"{'-'*80}\n{employees.recordset.rowsCount()} have been deleted.")

employees = Employees().all()
print(f"{'-'*80}")
print(f"Employees List:{employees.recordset.toLists()}")

def initOracleConnection():
	oracledb.init_oracle_client(lib_dir=AKEOracleConfig.CLIENT_LIB_DIR)

	load_dotenv()
	connection = oracledb.connect(
		user=AKEOracleConfig.USER,
		password=AKEOracleConfig.PASSWORD,
		dsn=AKEOracleConfig.DSN
	)
	return connection

oracleCOnnection = initOracleConnection()
oracleDatabase = Oracle(oracleCOnnection)
Record.database__ = oracleDatabase # change database connection
print(f"{'-'*80}\nDatabase connection has been changed from SQLite3 to Oracle.")

employees = Employees().all()
print(f"{'-'*80}\n{employees.recordset.count()} have been retreived from Oracle.")

Record.database__  = sqlite3Database
print(f"{'-'*80}\nDatabase connection has been changed from Oracle to SQLite3.")
employees.recordset.insert()
print(f"{'-'*80}\n{employees.recordset.rowsCount()} have been saved to SQLite3.")

print(f"{'-'*80}")
print(f"Employees List:{employees.recordset.toLists()}")