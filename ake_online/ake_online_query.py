#!/usr/bin/python

#================================================================================#
from string import Template
#================================================================================#
class Query:
	def __init__(self):
		self.statement	= None
		self.result		= None
#================================================================================#
class Result:
	def __init__(self, columns=None, rows=None, count=0, rowcount=0, lastrowid=0):
		self.columns	= columns
		self.rows		= rows
		self.count		= count
		self.rowcount	= rowcount
		self.lastrowid	= lastrowid
#================================================================================#
class Recordset:
	def __init__(self): self.__records = []
	def empty(self): self.__records = []
	def add(self, record): self.__records.append(record)
	def iterate(self): return self.__records
	def insert(self):
		for record in self.__records: record.insert()
#================================================================================#
class Database:
	def __init__(self, database=None, username=None, password=None, host=None):
		self.__database		= database
		self.__username		= username
		self.__password		= password
		self.__host			= host
		self.__connection	= None
		self.__cursor		= None
		self.connect()
	#--------------------------------------#
	def connect(self):
		if(self.__database):
			if(self.__username):
				if(self.__password):
					if(self.__host):
						import mysql.connector
						self.__connection = mysql.connector.connect(database=self.__database, user=self.__username, password=self.__password, host=self.__host)
					else:
						import cx_Oracle
						self.__connection = cx_Oracle.connect(self.__username, self.__password, self.__database)
			else:
				import sqlite3
				self.__connection = sqlite3.connect(self.__database)
		self.cursor()
		
	def cursor(self): self.__cursor	= self.__connection.cursor()
	def commit(self): self.__connection.commit()
	def rollback(self): self.__connection.rollback()
	def close(self): self.__connection.close()
	#--------------------------------------#
	def execute(self, query):
		if(query.statement is not None):
			#print(query.statement)
			#result is a cursor object instance contains the returned records of select statement
			#None is the returned value in case of insert/update/delete.
			self.__cursor.execute(query.statement)
			rows=None
			count=None
			if(str((query.statement.strip())[:6]).lower()=="select"):
				rows = self.__cursor.fetchall()
				count = len(rows)
			#rowcount is readonly attribute
			#rowcount contains the count/number of the inserted/updated/deleted records/rows.
			#rowcount is -1 in case of rows/records select.
			rowcount = self.__cursor.rowcount

			#if(self.__cursor.lastrowid): lastrowid = self.__cursor.lastrowid
			columns = []
			#cursor.description returns a tuple of information describes each column in the table.
			#(name, type_code, display_size, internal_size, precision, scale, null_ok)
			#for index, column in enumerate(self.__cursor.description): columns.append(column[0])
			
			if(self.__cursor.description is not None): columns = [column[0] for column in self.__cursor.description]
			#query.result = Result(columns, rows, count, rowcount, lastrowid)
			query.result = Result(columns, rows, count, rowcount)
			return query
	#--------------------------------------#
        def executeScript(self, sqlScriptFileName):
                sqlScriptFile = open(sqlScriptFileName,'r')
                sql = sqlScriptFile.read()
                return self.__cursor.executescript(sql)
#================================================================================#
class ObjectRelationalMapper:
	def __init__(self): pass
	#--------------------------------------#
	def map(self, query, passedObject):
		object = passedObject
		if(query.result.rows): #if(query.result is not None):
			for row in query.result.rows:
				index = 0
				for fieldValue in row:
					# str() don't use # to map Null value to None field correctly. 
					setattr(object, query.result.columns[index], fieldValue)
					index += 1
				passedObject.mappedObjectsFromRecords.append(object)
				object = passedObject.__class__() #object = Record() #bug
#================================================================================#
class State:
	def __init__(self): self.current = None
#================================================================================#
class Record:
	database						= None
	orm								= ObjectRelationalMapper()
	# select, update and delete
	fieldValueTemplate				= Template('''${field}=${value}${separator}''')
	# insert
	field							= Template('''${field}, ''')
	value							= Template('''${value}, ''')
	fieldsValuesTemplate			= Template('''(${fields}) VALUES (${values})''')
	# ------
	selectStatementTemplate			= Template('''SELECT * FROM ${table} WHERE ${fieldsValues}''')
	deleteStatementTemplate			= Template('''DELETE FROM ${table} WHERE ${fieldsValues}''')
	insertStatementTemplate			= Template('''INSERT INTO ${table}${fieldsValues}''')
	updateStatementTemplate			= Template('''UPDATE ${table} SET ${fieldsValues} WHERE ${_fieldsValues_}''')
	#--------------------------------------#
	def __init__(self, statement=None, **kwargs):
		self.mappedObjectsFromRecords = []
		self.__state = State()
		if(kwargs is not None):
			for key, value in kwargs.items():
				setattr(self, key, value)
		self.__query = Query() # must be declared before self.queryObject(statement)
		if(statement is not None):
			self.__query.statement = statement
			#self. instead of Record. #change the static field self.__database for inherited children classes
			self.database.execute(self.__query)
			Record.orm.map(self.__query, self)
	#--------------------------------------#
	def __iter__(self): 
		self.__iterationIndex = 0
		self.__iterationBound = len(self.mappedObjectsFromRecords)
		return self
	#--------------------------------------#
	def __next__(self): #python 3 compatibility
		if(self.__iterationIndex < self.__iterationBound):
			currentItem = self.mappedObjectsFromRecords[self.__iterationIndex]
			self.__iterationIndex += 1
			return currentItem
		else:
			del(self.__iterationIndex) # to prevent using them as database's column
			del(self.__iterationBound) # to prevent using them as database's column
			raise StopIteration
	#--------------------------------------#
	def next(self): return self.__next__() #python 2 compatibility
	#--------------------------------------#
	def table(self): return self.__class__.__name__
	#--------------------------------------#
	def recordset(self): return self.mappedObjectsFromRecords #in PHP instead of #implements Iterator|IteratorAggregate
	#--------------------------------------#
	def fieldsEqualValues(self, separator=' AND ', fieldsValues = ''):
		separatorLength = len(separator)
		for attribute, value in self.__dict__.items(): #for a in dir(r): print(a)
			if(type(value) in [str, int]): # any other type will be execluded Class type, None type and others ...
				if(value != 'Null'): value = "'" + str(value) + "'"
				fieldsValues += Record.fieldValueTemplate.substitute({'field': attribute, 'value': value, 'separator': separator})
		if(fieldsValues): return fieldsValues[:-separatorLength]
		else: return None
	#--------------------------------------#
	def fieldsThenValues(self, fields='', values=''):
		for attribute, value in self.__dict__.items(): #for a in dir(r): print(a)
			if(type(value) in [str, int]): # any other type will be execluded Class type, None type and others ...
				if(value != 'Null'): value = "'" + str(value) + "'"
				fields += Record.field.substitute({'field': attribute})
				values += Record.value.substitute({'value': value})
		fields = fields[:-2]
		values = values[:-2]
		fieldsValues = Record.fieldsValuesTemplate.substitute({'fields': fields, 'values': values})
		if(fieldsValues): return fieldsValues
		else: return None
	#--------------------------------------#
	def __crd(self, template, fieldsValues, _fieldsValues_=None):
		if(fieldsValues is not None):
			self.__query.statement = template.substitute({'table': self.table(), 'fieldsValues': fieldsValues, '_fieldsValues_': _fieldsValues_})
			self.__state.current = None
			self.database.execute(self.__query)
			Record.orm.map(self.__query, self)
	#--------------------------------------#
	def startUpdate(self): self.__state.current = self.fieldsEqualValues()
	#--------------------------------------#
	def insert(self): self.__crd(Record.insertStatementTemplate, self.fieldsThenValues())
	def read(self)  : self.__crd(Record.selectStatementTemplate, self.fieldsEqualValues())
	def delete(self): self.__crd(Record.deleteStatementTemplate, self.fieldsEqualValues())
	def update(self):
		if(self.__state.current is not None):
			self.__crd(Record.updateStatementTemplate, self.fieldsEqualValues(', '), self.__state.current)
		else:
			print("The update doesn't start, no current state !")
	#--------------------------------------#
#================================================================================#
