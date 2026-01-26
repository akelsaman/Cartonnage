#!/usr/bin/python

#version: 201909091800
#================================================================================#
from string import Template
from datetime import datetime
#================================================================================#
#Object attributes types and instance type affect the following classes function:
#PreparedStatement.prepare()	#ObjectRelationalMapper.map()
#Record.parameters()			#Record.getCopyInstance()
#================================================================================#
#python2 has two classes represent strings (str) and (unicode)
#python3 has only one class represents string (str) and has no (unicode) class
#the following code is for python3 and python2 compatibility-back
#without it in PreparedStatement().Prepare() check attribute/value using
#type(value) in [str,] only will ignore unicode attributes/values if not casting
# using str() explicity when assigning object.attribute = value of unicode()
try:
	a = unicode()
except Exception as e:
	unicode = str
#================================================================================#
def createTableClass(tableName, base=(object, ), attributesDictionary={}):
	return type(str(tableName), base, attributesDictionary) #str() to prevent any error from missed type casting/conversion
#================================================================================#
class Database:

	# ------
	selectPreparedStatementTemplate	= Template('''SELECT * FROM ${table} WHERE ${parameterizedStatement}''')
	deletePreparedStatementTemplate	= Template('''DELETE FROM ${table} WHERE ${parameterizedStatement}''')
	insertPreparedStatementTemplate	= Template('''INSERT INTO ${table}${parameterizedStatement}''')
	updatePreparedStatementTemplate	= Template('''UPDATE ${table} SET ${parameterizedStatement} WHERE ${_parameterizedStatement_}''')
	# ------
	selectAllPreparedStatementTemplate	= Template('''SELECT * FROM ${table}''')
	#--------------------------------------#
	def __init__(self, database=None, username=None, password=None, host=None):
		self.__database		= database
		self.__username		= username
		self.__password		= password
		self.__host			= host
		self.__connection	= None
		self.__cursor		= None
		self.__placeholder	= '?'
		self.operationsCount = 0
		self.connect()
	#--------------------------------------#
	def placeholder(self): return self.__placeholder
	#--------------------------------------#
	def connectionParameters(self):
		if(self.__database):
			if(self.__username):
				if(self.__password):
					if(self.__host): return 4
					else: return 3
			else: return 1
	#--------------------------------------#
	def cursor(self): self.__cursor	= self.__connection.cursor()
	def commit(self): self.__connection.commit()
	def rollback(self): self.__connection.rollback()
	def close(self): self.__connection.close()
	#--------------------------------------#
	def operationsCountReset(self):
		operationsCount = self.operationsCount
		self.operationsCount = 0
		return operationsCount
	#--------------------------------------#
	def executeStatement(self, query):
		if(query.statement):
			#print(query.statement)
			#print(query.parameters)
			#result is a cursor object instance contains the returned records of select statement
			#None is the returned value in case of insert/update/delete.
			self.__cursor.execute(query.statement, tuple(query.parameters))
			self.operationsCount +=1
			rows=None
			count=None
			if(str((query.statement.strip())[:6]).lower()=="select"):
				rows = self.__cursor.fetchall()
				count = len(rows)
			#rowcount is readonly attribute
			#rowcount contains the count/number of the inserted/updated/deleted records/rows.
			#rowcount is -1 in case of rows/records select.
			rowcount = self.__cursor.rowcount

			lastrowid = 0
			#lastrowid inserted by this connection
			#if(self.__connection.insert_id()): lastrowid = self.__connection.insert_id()
			#lastrowid inserted by this cursor
			if(self.__cursor.lastrowid): lastrowid = self.__cursor.lastrowid
			columns = []
			#cursor.description returns a tuple of information describes each column in the table.
			#(name, type_code, display_size, internal_size, precision, scale, null_ok)
			#for index, column in enumerate(self.__cursor.description): columns.append(column[0])
			
			if(self.__cursor.description): columns = [column[0] for column in self.__cursor.description]
			query.result = Result(columns, rows, count, rowcount, lastrowid)
			#query.result = Result(columns, rows, count, rowcount)
			#for r in query.result.rows:
			#	print(r)
			return query
	#--------------------------------------#
	def executeMany(self, query):
		#print(query.statement)
		#print(query.parameters)
		if(query.statement):
			self.__cursor.executemany(query.statement, query.parameters)
			self.operationsCount +=1
			rowcount = self.__cursor.rowcount
		return rowcount
	#--------------------------------------#
	def executeScript(self, sqlScriptFileName):
		sqlScriptFile = open(sqlScriptFileName,'r')
		sql = sqlScriptFile.read()
		return self.__cursor.executescript(sql)
#================================================================================#
class SQLite(Database):
	def __init__(self, database=None, checkSameThread=True):
		self.__checkSameThread = checkSameThread
		Database.__init__(self, database=database)
	def connect(self):
		if(self.connectionParameters() == 1):
			import sqlite3
			self._Database__connection = sqlite3.connect(self._Database__database, check_same_thread=self.__checkSameThread)
			self.cursor()
#================================================================================#
class Oracle(Database):
	def __init__(self, database=None, username=None, password=None):
		Database.__init__(self, database=database, username=username, password=password)
	def connect(self):
		if(self.connectionParameters() == 3):
			import cx_Oracle
			self._Database__connection = cx_Oracle.connect(self._Database__username, self._Database__password, self._Database__database)
			self.cursor()
			self._Database__placeholder = ':1' #1 #start of numeric 
#================================================================================#
class MySQL(Database):
	def __init__(self, database=None, username=None, password=None, host=None):
		Database.__init__(self, database=database, username=username, password=password, host=host)
	def connect(self):
		if(self.connectionParameters() == 4):
			import mysql.connector
			self._Database__connection = mysql.connector.connect(database=self._Database__database, user=self._Database__username, password=self._Database__password, host=self._Database__host)
			self.cursor()
			self._Database__cursor = self._Database__connection.cursor(prepared=True)
	def prepared(self, prepared=True):
		self._Database__cursor = self._Database__connection.cursor(prepared=prepared)
#================================================================================#
class Postgres(Database):
	def __init__(self, database=None, username=None, password=None, host=None):
		Database.__init__(self, database=database, username=username, password=password, host=host)
	def connect(self):
		if(self.connectionParameters() == 4):
			import psycopg2
			self._Database__connection = psycopg2.connect(database=self._Database__database, user=self._Database__username, password=self._Database__password, host=self._Database__host)
			self.cursor()
			self._Database__placeholder = '%s'
#================================================================================#
class MicrosoftSQL(Database):
	def __init__(self, database=None, username=None, password=None, host=None):
		Database.__init__(self, database=database, username=username, password=password, host=host)
	def connect(self):
		if(self.connectionParameters() == 4):
			import pyodbc
			self._Database__connection = pyodbc.connect(Driver='{ODBC Driver 17 for SQL Server}',database=self._Database__database, user=self._Database__username, password=self._Database__password, host=self._Database__host)
			#self._Database__connection = pyodbc.connect('Driver={ODBC Driver 17 for SQL Server};Server=tcp:example.database.windows.net,1433;Database=example_db;;;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;')
			self.cursor()
#================================================================================#
# for new SpecialValue review
# PreparedStatement() #Record.parameters() #Record.getCopyInstance()
# for NULL review ObjectRelationalMapper also
class SpecialValue:
	def __init__(self, value=None): self.__value = value
	def value(self): return self.__value
	def operator(self): return "="
	def placeholder(self, placeholder): return placeholder
#--------------------------------------#
class TableName(SpecialValue): pass
#--------------------------------------#
class LIKE(SpecialValue):
	def operator(self): return " LIKE "
#--------------------
class IN(SpecialValue):
	def operator(self): return " IN "
	def placeholder(self, placeholder): return '(' + ','.join([placeholder]*len(self._SpecialValue__value)) + ')'
#--------------------
class NOT_IN(SpecialValue):
	def operator(self): return " NOT IN "
	def placeholder(self, placeholder): return '(' + ','.join([placeholder]*len(self._SpecialValue__value)) + ')'
#--------------------
class BETWEEN(SpecialValue):
	def __init__(self, minValue, maxValue):
		self.__minValue = minValue
		self.__maxValue = maxValue

	def value(self): return [self.__minValue, self.__maxValue]
	def operator(self): return " BETWEEN "
	def placeholder(self, placeholder): return placeholder + " AND " + placeholder
#--------------------
class gt(SpecialValue):
	def operator(self): return " > "
#--------------------
class ge(SpecialValue):
	def operator(self): return " >= "
#--------------------
class lt(SpecialValue):
	def operator(self): return " < "
#--------------------
class le(SpecialValue):
	def operator(self): return " <= "
#--------------------
class NULL(SpecialValue): 
	def __init__(self): self.__value = None
	def operator(self, operation):
		if(operation==PreparedStatement.update):
			return "="
		else:
			return " IS "
	def __str__(self): return "NULL"
	def __repr__(self): return "NULL"
	def __eq__(self, other): return "NULL"==other
#--------------------
class NOT_NULL(SpecialValue):
	def __init__(self): self.__value = "NOT NULL"
	def operator(self): return " IS NOT "
	def __str__(self): return "NOT NULL"
	def __repr__(self): return "NOT NULL"
	def __eq__(self, other): return "NOT NULL"==other
#================================================================================#
class PreparedStatement:
	NA			= 0
	insert		= 1
	read		= 2
	delete		= 3
	update		= 4
	startUpdate	= 5

	def __init__(self, recordObject, operation):
		self.__fieldsNames = []
		self.__fieldsEqualPlaceholdersComma = ''
		self.__fieldsEqualPlaceholdersAnd = ''
		self.__fields = ''
		self.__parametersPlaceholders = ''
		self.__string = ''
		self.__recordObject = recordObject
		self.__operation = operation

		self.prepare()

		if(self.__operation==1): self.fieldsThenPlaceholders()
		if(self.__operation==2): self.fieldsEqualPlaceholdersAnd()
		if(self.__operation==3): self.fieldsEqualPlaceholdersAnd()
		if(self.__operation==4): self.fieldsEqualPlaceholdersComma()
		if(self.__operation==5): self.fieldsEqualPlaceholdersAnd()

	def fieldsNames(self): return self.__fieldsNames
	def string(self): return self.__string
	def parameterizedStatement(self, string):
		self.__string = string
		return self
	def fieldsEqualPlaceholdersComma(self): return self.parameterizedStatement(self.__fieldsEqualPlaceholdersComma[:-2])
	def fieldsEqualPlaceholdersAnd(self): return self.parameterizedStatement(self.__fieldsEqualPlaceholdersAnd[:-5])
	def fieldsThenPlaceholders(self): return self.parameterizedStatement('(' + self.__fields[:-2] + ') VALUES (' + self.__parametersPlaceholders[:-2] + ')')

	def __add(self, field, placeholder, operator='='):
		self.__fieldsNames.append(field)
		self.__fieldsEqualPlaceholdersComma += field + operator + placeholder + ', '
		self.__fieldsEqualPlaceholdersAnd += field + operator + placeholder + ' AND '
		self.__fields += field + ', '
		self.__parametersPlaceholders += placeholder + ', '

	def prepare(self):
		placeholder = self.__recordObject.database.placeholder()
		#placeholderVariableNumber = 0
		for attributeName, attributeValue in self.__recordObject.__dict__.items(): #for a in dir(r): println(a)
			# any other type will be execluded Class type, None type and others ...
			if(type(attributeValue) in [str, unicode, int, float, datetime]):
				self.__add(attributeName, placeholder)
			elif(isinstance(attributeValue, NULL)):
				self.__add(attributeName, placeholder, attributeValue.operator(self.__operation))
			elif(isinstance(attributeValue, (IN, gt, ge, lt, le, LIKE, NOT_NULL, BETWEEN, NOT_IN))):
				self.__add(attributeName, attributeValue.placeholder(placeholder), attributeValue.operator())
		return self
#================================================================================#
class ObjectRelationalMapper:
	def __init__(self): pass
	#--------------------------------------#
	def map(self, query, passedObject):
		object = passedObject
		passedObject.columns = [] #empty the columns of the passed object only since the new object created below for each row is empty
		if(query.result.rows):
			passedObject.recordset.empty()
			for row in query.result.rows:
				object.columns = query.result.columns
				index = 0
				for fieldValue in row:
					if(fieldValue is None):
						fieldValue=NULL()
					elif(type(fieldValue) == bytearray): #mysql python connector returns bytearray instead of string
						fieldValue = str(fieldValue)
					# str() don't use # to map Null value to None field correctly.
					setattr(object, query.result.columns[index], fieldValue)
					index += 1
				passedObject.recordset.add(object)
				object = passedObject.__class__() #object = Record() #bug
#================================================================================#
class Result:
	def __init__(self, columns=None, rows=None, count=0, rowcount=0, lastrowid=0):
		self.columns	= columns
		self.rows		= rows
		self.count		= count
		self.rowcount	= rowcount
		self.lastrowid	= lastrowid
#================================================================================#
class Query:
	def __init__(self):
		self.statement	= None
		self.result		= Result()
		self.parameters	= [] #to prevent #ValueError: parameters are of unsupported type in line #self.__cursor.execute(query.statement, tuple(query.parameters))
#================================================================================#
class State:
	def __init__(self):
		self.delete()

	def delete(self):
		self.currentStatement = None
		self.currentParameters = None
#================================================================================#
class Record:
	database						= None
	tableName						= TableName()
	orm								= ObjectRelationalMapper()
	#--------------------------------------#
	def __init__(self, statement=None, parameters=None, **kwargs):
		self.columns = [] #use only after reading data from database #because it's loaded only from the query's result
		self.recordset = Recordset()
		self.__state = State()
		self.primarykey = []
		if(kwargs):
			for key, value in kwargs.items():
				setattr(self, key, value)
		self.__query = Query() # must be declared before self.query(statement)
		if(statement):
			self.__query.statement = statement
			if(parameters): self.__query.parameters = parameters #if prepared statement's parameters are passed
			#self. instead of Record. #change the static field self.__database for inherited children classes
			self.database.executeStatement(self.__query)
			Record.orm.map(self.__query, self)
	#--------------------------------------#
	def __str__(self):
		pass
	#--------------------------------------#
	def __iter__(self): 
		self.__iterationIndex = 0
		self.__iterationBound = len(self.recordset.iterate())
		return self
	#--------------------------------------#
	def __next__(self): #python 3 compatibility
		if(self.__iterationIndex < self.__iterationBound):
			currentItem = self.recordset.iterate()[self.__iterationIndex]
			self.__iterationIndex += 1
			return currentItem
		else:
			del(self.__iterationIndex) # to prevent using them as database's column
			del(self.__iterationBound) # to prevent using them as database's column
			raise StopIteration
	#--------------------------------------#
	def next(self): return self.__next__() #python 2 compatibility
	#--------------------------------------#
	def table(self):
		if(self.tableName.value()): return self.tableName.value()
		else: return self.__class__.__name__
	#--------------------------------------#
	def getField(self, fieldName): return self.__dict__[fieldName]
	def setField(self, fieldName, fieldValue): self.__dict__[fieldName]=fieldValue
	#--------------------------------------#
	def readCount(self): return self.__query.result.count
	#--------------------------------------#
	def id(self): return self.__query.result.lastrowid
	#--------------------------------------#
	def hash(self):
		hashedValue = ''
		for column in self.primarykey: pass
	#--------------------------------------#
	def statement(self, template, parameterizedStatement, _parameterizedStatement_=None):
		return template.substitute({'table': self.table(), 'parameterizedStatement': parameterizedStatement, '_parameterizedStatement_': _parameterizedStatement_})
	#--------------------------------------#
	def parameters(self, fieldsNames):
		parameters = []
		if(fieldsNames):
			for field in fieldsNames:
				fieldValue = self.__dict__[field]
				if(isinstance(fieldValue, (NULL, NOT_NULL))):
					parameters.append(None)
				elif(isinstance(fieldValue, (IN, BETWEEN, NOT_IN))):
					for value in fieldValue.value(): parameters.append(value) # list values
				elif(isinstance(fieldValue, (gt, ge, lt, le, LIKE))):
					parameters.append(fieldValue.value()) # the value of LIKE
				else:
					parameters.append(fieldValue) #not used for parameterized statement #if(value): value = "'" + str(value) + "'"
		return parameters
	#--------------------------------------#
	def __crud(self, template, parameterizedStatement, _parameterizedStatement_=None):
		if(parameterizedStatement.string()): #if not empty string
			self.__query.statement = self.statement(template, parameterizedStatement.string(), _parameterizedStatement_)
			self.__query.parameters = self.parameters(parameterizedStatement.fieldsNames())
			if(self.__state.currentParameters): self.__query.parameters += self.__state.currentParameters
			self.__state.delete()
			self.database.executeStatement(self.__query)
			Record.orm.map(self.__query, self)
	#--------------------------------------#
	def insert(self): self.__crud(Database.insertPreparedStatementTemplate, PreparedStatement(self, PreparedStatement.insert))
	def read(self): self.__crud(Database.selectPreparedStatementTemplate, PreparedStatement(self, PreparedStatement.read))
	def delete(self): self.__crud(Database.deletePreparedStatementTemplate, PreparedStatement(self, PreparedStatement.delete))
	def update(self): 
		if(self.__state.currentStatement):
			self.__crud(Database.updatePreparedStatementTemplate, PreparedStatement(self, PreparedStatement.update), self.__state.currentStatement)
		else:
			raise RuntimeError("The update doesn't start, no current state !")
	#--------------------------------------#
	def startUpdate(self, fieldsNames=None):
		if(fieldsNames): #Recordset.startUpdate()
			self.__state.currentStatement = None
			self.__state.currentParameters = self.parameters(fieldsNames)
		else: #Record.startUpdate()
			parameterizedStatement = PreparedStatement(self, PreparedStatement.startUpdate)
			self.__state.currentStatement = parameterizedStatement.string()
			self.__state.currentParameters = self.parameters(parameterizedStatement.fieldsNames())
	#--------------------------------------#
	def state(self): return self.__state
	#--------------------------------------#
	def getCopyInstance(self, base=(object, ), attributesDictionary={}):
		if(base):
			Copy = createTableClass(self.__class__.__name__, base, attributesDictionary)
			copy = Copy()
		else:
			copy = self.__class__() #object = Record() #bug
		
		for attributeName, attributeValue in self.__dict__.items(): #for a in dir(r): println(a)
			# any other type will be execluded Class type, None type and others ...
			if(type(attributeValue) in [str, unicode, int, float, datetime]):
				setattr(copy, attributeName, attributeValue)
			elif(isinstance(attributeValue, IN)):
				setattr(copy, attributeName, IN(list(attributeValue.value())))
			elif(isinstance(attributeValue, NULL)):
				setattr(copy, attributeName, NULL())
			elif(isinstance(attributeValue, NOT_NULL)):
				setattr(copy, attributeName, NOT_NULL())
			elif(isinstance(attributeValue, LIKE)):
				setattr(copy, attributeName, LIKE(attributeValue.value()))
		copy.columns = list(self.columns)
		return copy
	#--------------------------------------#
	def selectAll(self):
		self.__query.statement = Database.selectAllPreparedStatementTemplate.substitute({'table': self.table()})
		self.database.executeStatement(self.__query)
		Record.orm.map(self.__query, self)
#================================================================================#
class Recordset:
	def __init__(self):
		self.__records = [] #mapped objects from records
		self.__rowsCount = 0
	def table(self):
		if(self.firstRecord()): return  self.firstRecord().table()
	def empty(self): self.__records = []
	def add(self, recordObject): self.__records.append(recordObject)
	def iterate(self): return self.__records
	def firstRecord(self):
		if(len(self.__records)):
			return self.__records[0]
		else:
			return None
	def count(self): return len(self.__records)
	def columns(self): return self.firstRecord().columns
	def setField(self, fieldName, fieldValue):
		for record in self.__records: record.__dict__[fieldName] = fieldValue
	def affectedRowsCount(self): return self.__rowsCount
	#--------------------------------------#
	def __crud(self, template, parameterizedStatement, _parameterizedStatement_=None):
		query = Query()
		query.statement = self.firstRecord().statement(template, parameterizedStatement.string(), _parameterizedStatement_) ##
		#print(query.statement)
		query.parameters = []
		for record in self.__records:
			#record.insert()
			recordParameters = record.parameters(parameterizedStatement.fieldsNames())
			if(record.state().currentParameters): recordParameters += record.state().currentParameters ##
			query.parameters.append(tuple(recordParameters))
			record.state().delete() ##
		self.__rowsCount = self.firstRecord().database.executeMany(query)
	#--------------------------------------#
	def insert(self): self.__crud(Database.insertPreparedStatementTemplate, PreparedStatement(self.firstRecord(), PreparedStatement.insert))
	def delete(self): self.__crud(Database.deletePreparedStatementTemplate, PreparedStatement(self.firstRecord(), PreparedStatement.delete))
	def update(self):
		if(self.firstRecord()):
			if(self.firstRecord().state().currentStatement):
				self.__crud(Database.updatePreparedStatementTemplate, PreparedStatement(self.firstRecord(), PreparedStatement.update), self.firstRecord().state().currentStatement)
			else:
				print("The update doesn't start, no current state !")
	#--------------------------------------#
	def startUpdate(self):
		if(self.firstRecord()):
			parameterizedStatement = PreparedStatement(self.firstRecord(), PreparedStatement.startUpdate)
			for record in self.__records: record.startUpdate(parameterizedStatement.fieldsNames())
			self.firstRecord().startUpdate()
	#--------------------------------------#
	def copy(self): pass
	#--------------------------------------#
#================================================================================#