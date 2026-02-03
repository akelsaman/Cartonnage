#!/usr/bin/python3

def mysqlConnection():
	import mysql.connector

	connection = mysql.connector.connect(
		host="",
		port=,
		user="",
		password="",
		database="",
		ssl_ca="",
		ssl_verify_cert=True,
	)

	cursor = connection.cursor()
	return connection, cursor

def postgresConnection():
	import psycopg2

	connection = psycopg2.connect(
		host="",
		port=,
		user="",
		password="",
		database="",
		sslmode="", 
		sslrootcert=""
	)

	cursor = connection.cursor()
	return connection, cursor

def azureConnection():
	import pyodbc
	
	# SQL_CONNECTION_STRING="Server=cartonnage.database.windows.net;Database=<database_name>;Encrypt=yes;TrustServerCertificate=no;Authentication=ActiveDirectoryInteractive"
	server = ''
	database = ''
	username = ''
	password = ''
	
	connection_string = (
		f'DRIVER={{ODBC Driver 18 for SQL Server}};'
		f'SERVER={server};'
		f'DATABASE={database};'
		f'UID={username};'
		f'PWD={password};'
		f'Encrypt=yes;'
		f'TrustServerCertificate=no;'
	)

	connection = pyodbc.connect(connection_string)
	cursor = connection.cursor()
	return connection, cursor

connection, cursor = mysqlConnection()
# connection, cursor = postgresConnection()
# connection, cursor = azureConnection()

with open("hr_mysql_postgres_azuresql.sql", "r") as f:
	sql_script = f.read()

# Remove comment lines and split by semicolon
lines = [line for line in sql_script.splitlines() if not line.strip().startswith('--')]
clean_script = '\n'.join(lines)
statements = [s.strip() for s in clean_script.split(';') if s.strip()]

for statement in statements:
	cursor.execute(statement)
	print(f"OK: {statement[:50]}...")

connection.commit()
cursor.close()
connection.close()