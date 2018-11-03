import cx_Oracle
import sqlite3
from query import *
#========================================
class Oracle:
	def __init__(self):
		self.__connection = cx_Oracle.connect('cerner_ro', 'readonly', 'prod1.world')
		self.__cursor = self.__connection.cursor()
	#--------------------
	def select(self, query):
        	records = self.__cursor.execute(query)
        	recordset = records.fetchall()
		return recordset

	def close(self):
		self.__connection.close()
#========================================
class SQLite3:
	def __init__(self, database=None):
		self.__database = database
		if(self.__database is not None):
			self.__connection = sqlite3.connect(self.__database)
			self.__cursor = self.__connection.cursor()
	#--------------------
	def sqlScriptExecute(self, sqlScriptFileName):
		sqlScriptFile = open(sqlScriptFileName,'r')
		sql = sqlScriptFile.read()
		self.__cursor.executescript(sql)
		return self

	def select(self, query):
		records = self.__cursor.execute(query)
		recordset = records.fetchall()
		return recordset

	def insertTableRecords(self, tableName, records):
		columnsCount = len(records[0])
		questionMarks = 'NULL, '
		for columnNumber in range(0, columnsCount):
			questionMarks += '?,'
		questionMarksLastCommaStripped = questionMarks[:-1]
		statement = 'INSERT INTO ' + tableName + ' VALUES (' + questionMarksLastCommaStripped + ')'
		for record in records:
		        self.__cursor.execute(statement, record)
		return self

	def isTableExist(self, tableName):
		query = self.__cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tableName, ))
		records = query.fetchall()
		if(records):
			isTable = records[0][0]
			return True
		else:
			return False
	#--------------------
	def logDatabase(self, databaseName, timestamp):
		records = [(databaseName, timestamp)]
		self.insertTableRecords('databases', records)
		return self
	#--------------------
	def getLastDatabase(self):
		lastDatabase = self.select(lastDatabaseQuery)
		firstRowFirstColumn = lastDatabase[0][0]
		return firstRowFirstColumn
	#--------------------
	def commit(self): self.__connection.commit()
	def close(self): self.__connection.close()
#========================================
