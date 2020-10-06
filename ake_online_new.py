#!/usr/bin/python

#version: 202010060113
#================================================================================#
from string import Template
from datetime import datetime
import re
#================================================================================#
#Object attributes types and instance type affect the following classes function:
#Database.prepare()	#ObjectRelationalMapper.map()
#Record.parameters()			#Record.getCopyInstance()
#================================================================================#
#python2 has two classes represent strings (str) and (unicode)
#python3 has only one class represents string (str) and has no (unicode) class
#the following code is for python3 and python2 compatibility-back
#without it in Database().Prepare() check attribute/value using
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
# for new SpecialValue review
# Database() #Database.parameterize() #Database.getCopyInstance()
# for NULL review ObjectRelationalMapper also
class SpecialValue:
	def __init__(self, value=None): self.__value = value
	def value(self): return self.__value
	def operator(self): return "="
	def placeholder(self, placeholder): return placeholder
#--------------------------------------#
class TableName(SpecialValue): pass
class Alias(SpecialValue): pass
class UserID(SpecialValue):
	def __init__(self, value=None):
		self.user_id = value
#--------------------------------------#
class LIKE(SpecialValue):
	def __init__(self, value):
		self.__value = value.replace("*","%")
		SpecialValue.__init__(self, self.__value)
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
		if(operation==Database.update):
			return "="
		else:
			return " IS "
	def placeholder(self, placeholder): return "NULL"
	def __str__(self): return "NULL"
	def __repr__(self): return "NULL"
	def __eq__(self, other): return "NULL"==other
#--------------------
class NOT_NULL(SpecialValue):
	def __init__(self): self.__value = "NOT NULL"
	def operator(self): return " IS "
	def placeholder(self, placeholder): return "NOT NULL"
	def __str__(self): return "NOT NULL"
	def __repr__(self): return "NOT NULL"
	def __eq__(self, other): return "NOT NULL"==other
#--------------------
class Join(SpecialValue):
	def __init__(self, object, fields, value=None):
		self.object = object
		self.fields = fields
		self.__value = value
		SpecialValue.__init__(self, value)
#--------------------
class Joiners(SpecialValue):
	def __init__(self, value=None):
		self.joinClause = ''
		self.preparedStatement = ''
		self.parameters = []
		self.__value = value
		SpecialValue.__init__(self, value)
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
		self.statement = None
		self.parameters = []
#================================================================================#
class Statement:
	def __init__(self):
		self.delete()

	def delete(self):
		self.fieldsNames = []
		self.fieldsEqualPlaceholdersComma = ""
		self.fieldsEqualPlaceholdersAnd	= ""
		self.fields = ""
		self.parametersPlaceholders = ""

	def insertStatement(self): return '(' + self.fields[:-2] + ') VALUES (' + self.parametersPlaceholders[:-2] + ')'
	def readStatement(self): return self.fieldsEqualPlaceholdersAnd[:-5]
	def updateStatement(self): return self.fieldsEqualPlaceholdersComma[:-2]
	def deleteStatement(self): return self.fieldsEqualPlaceholdersAnd[:-5]
	def startUpdateStatement(self): return self.fieldsEqualPlaceholdersAnd[:-5]
#================================================================================#
class Representer:
	def __init__(self):
		pass

	def xml(self, record):
		xmlRecords = "<" + record.table() + ">"
		for r in record.recordset.iterate():
			xmlRecord = "\n\t<Record "
			attributes = ""
			for column in r.columns:
				attributes += str(column) + "='" + str(r.getField(column)) + "' "
			xmlRecord += attributes + "></Record>"
			xmlRecords += xmlRecord
		xmlRecords += "\n</" + record.table() + ">"

		return xmlRecords

	def html(self, record):
		htmlTable = "<table>\n\t<tr><th>" + record.table() + "</th></tr>"
		
		th = "\n\t<tr>"
		for column in record.columns:
			th += "<th>" + str(column) + "</th>"
		th += "</tr>"
		htmlTable += th

		for r in record.recordset.iterate():
			tr = "\n\t<tr>"
			for column in r.columns:
				tr += "\n\t\t<td>" + str(r.getField(column)) + "</td>"
			tr += "\n\t</tr>"
			htmlTable += tr

		htmlTable += "\n</table>"

		return htmlTable

	def json(self, record):
		jsonString = '{'
		for r in record.recordset.iterate():
			jsonString += '\n\t{'
			for column in r.columns:
				jsonString += '"' + column + '":"' + str(r.getField(column)) + '", '
			jsonString = jsonString[:-2] + '}, '
		if(jsonString=='{'):
			jsonString +=  '}'
		else:
			jsonString = jsonString[:-2] + '\n}'
		return jsonString

	def loadDictionary(self, record, dictionary):
		for key, value in dictionary.items():
			key = key.split('.')[-1]
			record.setField(key, value)

	def search(self, record, url):

		#http://localhost:5000/personsSearch?name_last=eq*Fe*h*&persons.name_first=eqMostafa&created_by_fk=ge1
		#http://localhost:5000/personsSearch?name_last=eq*Fe*h*&persons.name_first=eqMostafa&created_by_fk=ge1&start_date=null
		#http://localhost:5000/personsSearch?start_date=null
		dictionary = {}

		url = url.split("?")
		searchCriteria = url[1]
		criteria = searchCriteria.split("&")
		#print(criteria)
		for c in criteria:
			c = c.split("=")
			dictionary[c[0]] = c[1]

		for key, value in dictionary.items():
			key = key.split('.')[-1] #persons.name_last => name_last
			operator = value[:2]
			value = value[2:]
			if(operator=="ge"):	value = ge(value)
			if(operator=="gt"): value = gt(value)
			if(operator=="lt"): value = lt(value)
			if(operator=="le"): value = le(value)
			if(operator=="nu"): value = NULL()
			if(operator=="no"): value = NOT_NULL()
			if(operator=="eq"):
				if("*" in value):
					value = LIKE(str(value).replace("*", "%"))
			record.setField(key, value)
#================================================================================#
class ObjectRelationalMapper:
	def __init__(self): pass
	#--------------------------------------#
	def map(self, passedObject):
		object = passedObject
		query = object.query
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
						fieldValue = fieldValue.decode()
					# str() don't use # to map Null value to None field correctly.
					setattr(object, query.result.columns[index], fieldValue)
					index += 1
				passedObject.recordset.add(object)
				object = passedObject.__class__() #object = Record() #bug
#================================================================================#
class Database:

	# ------
	orm	= ObjectRelationalMapper()
	# ------
	NA			= 0
	insert		= 1
	read		= 2
	update		= 3
	delete		= 4
	startUpdate	= 5
	all	= 6
	# ------
	selectPreparedStatementTemplate	= Template('''SELECT ${selected} FROM ${table} ${alias} ${joiners} \nWHERE ${parameterizedStatement} ${joinsCriteria} \n${group_by}''')
	deletePreparedStatementTemplate	= Template('''DELETE FROM ${table} \nWHERE ${parameterizedStatement}''')
	insertPreparedStatementTemplate	= Template('''INSERT INTO ${table}${parameterizedStatement}''')
	updatePreparedStatementTemplate	= Template('''UPDATE ${table} SET ${parameterizedStatement} \nWHERE ${_parameterizedStatement_}''')
	# ------
	selectAllPreparedStatementTemplate	= Template('''SELECT * FROM ${table} ${alias} ${joiners} \nWHERE 1''')
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
		self.user_pk		= 0
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
			print(query.statement)
			print(query.parameters)
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
			if hasattr(self.__cursor, 'lastrowid'): lastrowid = self.__cursor.lastrowid #MySQL has last row id
			columns = []
			#cursor.description returns a tuple of information describes each column in the table.
			#(name, type_code, display_size, internal_size, precision, scale, null_ok)
			#for index, column in enumerate(self.__cursor.description): columns.append(column[0])
			
			if(self.__cursor.description): columns = [column[0] for column in self.__cursor.description]
			print(columns)
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
	#--------------------------------------#
	def statement(self, template, selected, table, statement, alias='', joiners='', joinsCriteria='', group_by='', _statement_=None):
		return template.substitute({'selected': selected,'table': table, 'alias': alias, 'joiners': joiners,'parameterizedStatement': statement, 'joinsCriteria': joinsCriteria, 'group_by': group_by, '_parameterizedStatement_': _statement_})
	#--------------------------------------#
	def __prepare(self, record, field, placeholder, operator='='):
		record.statement.fieldsNames.append(field)
		record.statement.fieldsEqualPlaceholdersComma += field + operator + placeholder + ', '
		record.statement.fieldsEqualPlaceholdersAnd += '`' + record.alias.value() + '`' + '.' + '`' + field + '`' + operator + placeholder + ' AND '
		record.statement.fields += field + ', '
		record.statement.parametersPlaceholders += placeholder + ', '
	#--------------------------------------#
	def prepare(self, operation, record):
		placeholder = self.placeholder()
		record.statement.delete()
		#placeholderVariableNumber = 0
		for attributeName, attributeValue in record.__dict__.items(): #for a in dir(r): println(a)
			# any other type will be execluded Class type, None type and others ...
			if(type(attributeValue) in [str, unicode, int, float, datetime]):
				self.__prepare(record, attributeName, placeholder)
			elif(isinstance(attributeValue, NULL)):
				self.__prepare(record, attributeName, "NULL", attributeValue.operator(operation))
			elif(isinstance(attributeValue, (IN, gt, ge, lt, le, LIKE, NOT_NULL, BETWEEN, NOT_IN))):
				self.__prepare(record, attributeName, attributeValue.placeholder(placeholder), attributeValue.operator())
	#--------------------------------------#
	def parameterize(self, record, fieldsNames=None):
		if(not fieldsNames):
			fieldsNames = record.statement.fieldsNames

		record.query.parameters = []
		if(fieldsNames):
			for field in fieldsNames:
				fieldValue = record.__dict__[field]
				if(isinstance(fieldValue, (NULL, NOT_NULL))):
					pass
					#record.query.parameters.append(None)
				elif(isinstance(fieldValue, (IN, BETWEEN, NOT_IN))):
					for value in fieldValue.value(): record.query.parameters.append(value) # list values
				elif(isinstance(fieldValue, (gt, ge, lt, le, LIKE))):
					record.query.parameters.append(fieldValue.value()) # the value of LIKE
				else:
					record.query.parameters.append(fieldValue) #not used for parameterized statement #if(value): value = "'" + str(value) + "'"
	#--------------------------------------#
	def joining(self, record):
		joiners = Joiners()
		for key, join in record.joins.items():
			#" INNER JOIN Persons pp ON "
			inner_join = ' INNER JOIN ' + join.object.table() + " " + join.object.alias.value() + ' ON '			
			for foreign_key, primary_key in join.fields.items():
				#"	uu.person.fk=pp.pk AND "
				inner_join += "\n\t" + record.alias.value() + "." + foreign_key + "=" + join.object.alias.value() + "." + primary_key + " AND "
			inner_join = "\n" + inner_join[:-5]
			joiners.joinClause += inner_join
			#--------------------
			self.prepare(Database.read, join.object)
			statement = join.object.statement.readStatement()
			if(statement): joiners.preparedStatement += " AND " + statement
			self.parameterize(join.object)
			joiners.parameters += join.object.query.parameters
			join.object.statement.delete()
			join.object.state.delete()
			#--------------------
			child_joiners = self.joining(join.object)
			joiners.joinClause += child_joiners.joinClause
			#if(child_joiners.preparedStatement): joiners.preparedStatement += child_joiners.preparedStatement
			joiners.preparedStatement += child_joiners.preparedStatement
			joiners.parameters += child_joiners.parameters

		return joiners
	#--------------------------------------#
	def secure(self, record):

		queryStatement = record.query.statement

		#aa = re.search('{([a-zA-Z0-9_]+)}', query, re.IGNORECASE)
		#if (aa): print(a.groups(1))
		tablesNames = re.findall(r"\${([a-zA-Z0-9_]+)}", queryStatement)

		tables_names_placeholders = ', '.join('?'*len(tablesNames))
		
		loadViews = """SELECT V.view, V.table_name, V.crud_statement
		FROM Policys_Views_Authoritys PVA
		INNER JOIN Users_Policys UP ON PVA.policy_fk = UP.policy_fk
		INNER JOIN Views V ON PVA.view_fk = V.pk
		WHERE UP.user_fk = ?
			AND V.table_name IN (""" + tables_names_placeholders + ")"

		#https://forums.mysql.com/read.php?100,630131,630158#msg-630158
		secureViewsStatement = {}
		if(tables_names_placeholders):
			
			class Views(Record): pass
			views = Views()
			views.query.statement = loadViews

			# mysql.connector.errors.InterfaceError
			# InterfaceError: No result set to fetch from.
			# No parameters were provided with the prepared statement
			# "views.query.parameters" was written by mistake "views.parameters"

			views.query.parameters = [record.secure.user_id] + tablesNames
			self.executeStatement(views.query)
			Database.orm.map(views)

			#print(views.recordset.count())
			for view in views:
				#print(view.columns)
				secureViewsStatement[str(view.table_name)] = '(' + str(view.crud_statement) + '\n)'
			for tableName in tablesNames:
				if(tableName not in secureViewsStatement):
					secureViewsStatement[tableName] = tableName

			#print(secureViewsStatement)

			queryStatementTemplate = Template(queryStatement)
			secureQuerySatement = queryStatementTemplate.safe_substitute(secureViewsStatement)
			secureQuerySatement = secureQuerySatement.replace("$|user.pk|", str(record.secure.user_id))
			record.query.statement = secureQuerySatement
			#return secureQuery
	#--------------------------------------#
	def __crud(self, operation, record, selected="*", group_by=''):
		
		table = record.table()
		self.prepare(operation, record)
		alias = record.alias.value()

		_statement_ = None
		joiners = self.joining(record)

		if(operation==Database.insert):
			template = Database.insertPreparedStatementTemplate
			statement = record.statement.insertStatement()
		elif(operation==Database.read):
			template = Database.selectPreparedStatementTemplate
			statement = record.statement.readStatement()
			if not (statement): statement="1" #to simulate read all if no criteria exists
		elif(operation==Database.update):
			template = Database.updatePreparedStatementTemplate
			statement = record.statement.updateStatement()
			_statement_ = record.state.statement
		elif(operation==Database.delete):
			template = Database.deletePreparedStatementTemplate
			statement = record.statement.deleteStatement()
		elif(operation==Database.all):
			template = Database.selectAllPreparedStatementTemplate
			statement = "NA" #useless just for the next condition: no statement keyword in "selectAllPreparedStatementTemplate"

		if(statement): #if not empty string
			joinsCriteria = joiners.preparedStatement
			record.query.statement = self.statement(template=template, selected=selected, table=table, alias=alias, joiners=joiners.joinClause, statement=statement, joinsCriteria=joinsCriteria, group_by=group_by, _statement_=_statement_)
			self.parameterize(record)
			record.query.parameters += record.state.parameters #state.parameters must be reset to empty list [] not None for this operation to work correctly
			record.query.parameters += joiners.parameters
			record.statement.delete()
			record.state.delete()
			if(record.secure.user_id): self.secure(record)
			self.executeStatement(record.query)
			Database.orm.map(record)
	#--------------------------------------#
	def __crudMany(self, operation, record, selected="*", group_by=''):

		table = record.table()
		self.prepare(operation, record)

		_statement_ = None
		if(operation==Database.insert):
			template = Database.insertPreparedStatementTemplate
			statement = record.statement.insertStatement()
		elif(operation==Database.read):
			template = Database.selectPreparedStatementTemplate
			statement = record.statement.readStatement()
		elif(operation==Database.update):
			template = Database.updatePreparedStatementTemplate
			statement = record.statement.updateStatement()
			_statement_ = record.state.statement
		elif(operation==Database.delete):
			template = Database.deletePreparedStatementTemplate
			statement = record.statement.deleteStatement()

		fieldsNames = record.statement.fieldsNames # as record.statement.delete() below in iteration over recordset will delete record.statement.fieldsnames
		query=Query() # as 

		if(statement): #if not empty string
			query.statement = self.statement(template=template, selected=selected, table=table, statement=statement, group_by=group_by, _statement_=_statement_)
			for r in record.recordset.iterate():
				#r.insert()
				self.parameterize(r, fieldsNames)
				r.query.parameters = r.query.parameters + r.state.parameters #state.parameters must be reset to empty list [] not None for this operation to work correctly
				query.parameters.append(tuple(r.query.parameters))
				r.statement.delete()
				r.state.delete()
			record.recordset.rowsCount = self.executeMany(query)
	#--------------------------------------#
	def insert(self, record): self.__crud(Database.insert, record)
	def read(self, record, selected="*", group_by=''): self.__crud(Database.read, record, selected, group_by)
	def delete(self, record): self.__crud(Database.delete, record)
	def update(self, record): 
		if(record.state.statement):
			self.__crud(Database.update, record)
		else:
			raise RuntimeError("The update doesn't start, no current state !")
	def all(self, record): self.__crud(Database.all, record)
	#--------------------------------------#
	def insertMany(self, record): self.__crudMany(Database.insert, record)
	def deleteMany(self,record): self.__crudMany(Database.delete, record)
	def updateMany(self, record):
		if(record.state.statement):
			self.__crudMany(Database.update, record)
		else:
			#print("The update doesn't start, no current state !")
			raise RuntimeError("The update doesn't start, no current state !")
	#--------------------------------------#
	def startUpdate(self, record, fieldsNames=None):
		if(fieldsNames): #Recordset.startUpdate()
			self.parameterize(record, fieldsNames)
			#record.state.statement = None
			record.state.parameters = record.query.parameters
		else: #Record.startUpdate()
			self.prepare(Database.startUpdate, record)
			self.parameterize(record)
			record.state.statement = record.statement.startUpdateStatement()
			record.state.parameters = record.query.parameters
	#--------------------------------------#
	def startUpdateMany(self, record):
		self.startUpdate(record)
		#self.startUpdate(record) will happen again in next line recordset iteration startUpdate process
		for r in record.recordset.iterate(): self.startUpdate(r, record.statement.fieldsNames)
	#--------------------------------------#
	def getCopyInstance(self, record, base=(object, ), attributesDictionary={}):
		if(base):
			Copy = createTableClass(record.__class__.__name__, base, attributesDictionary)
			copy = Copy()
		else:
			copy = record.__class__() #object = Record() #bug
		
		for attributeName, attributeValue in record.__dict__.items(): #for a in dir(r): println(a)
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
		copy.columns = list(record.columns)
		return copy
	#--------------------------------------#
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
class Record:
	database	= None
	representer = Representer()
	tableName	= TableName()
	#--------------------------------------#
	def __init__(self, statement=None, parameters=None, alias=None, secure_by_user_id=None, **kwargs):
		self.recordset = Recordset()
		self.statement = Statement()
		self.state = State()
		self.columns = [] #use only after reading data from database #because it's loaded only from the query's result
		self.joins = {}
		self.primarykey = []
		self.secure = UserID(secure_by_user_id)

		self.alias = Alias(self.__class__.__name__)
		if(self.secure.user_id):
			self.table = self.__tableSecure
		else:
			self.table = self.__table

		if(kwargs):
			for key, value in kwargs.items():
				setattr(self, key, value)

		self.query = Query() # must be declared before self.query(statement)
		if(statement):
			self.query.statement = statement
			if(parameters): self.query.parameters = parameters #if prepared statement's parameters are passed
			#self. instead of Record. #change the static field self.__database for inherited children classes
			if(self.secure.user_id): self.database.secure(self)
			self.database.executeStatement(self.query)
			Database.orm.map(self)
	#--------------------------------------#
	def __table(self):
		if(self.tableName.value()): return self.tableName.value()
		else: return self.__class__.__name__
	#--------------------------------------#
	def __tableSecure(self):
		if(self.tableName.value()): return "${" + self.tableName.value() + "}"
		else: return "${" + self.__class__.__name__ + "}"
	#--------------------------------------#
	def id(self): return self.query.result.lastrowid
	#--------------------------------------#
	def readCount(self): return self.query.result.count
	#--------------------------------------#
	def getField(self, fieldName): return self.__dict__[fieldName]
	def setField(self, fieldName, fieldValue): self.__dict__[fieldName]=fieldValue
	#--------------------------------------#
	#def __str__(self): pass
	#--------------------------------------#
	def hash(self):
		hashedValue = ''
		for column in self.primarykey: pass
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
	def insert(self): self.database.insert(self)
	def read(self, selected="*", group_by=''): self.database.read(self, selected, group_by)
	def update(self): self.database.update(self)
	def delete(self): self.database.delete(self)
	def startUpdate(self): self.database.startUpdate(self)
	def all(self): self.database.all(self)
	def commit(self): self.database.commit()
	#--------------------------------------#
	def join(self, table, fields):
		if not (table.alias): raise AttributeError("No alias for table")
		self.joins[table.alias.value()] = Join(table, fields)
	#--------------------------------------#
	def getCopyInstance(self, base=(object, ), attributesDictionary={}):
		return self.database.getCopyInstance(self, base, attributesDictionary={})
	#--------------------------------------#
	def json(self): return self.representer.json(self)
	def xml(self): return self.representer.xml(self)
	def html(self): return self.representer.html(self)
	def loadDictionary(self, dictionary): return self.representer.loadDictionary(self, dictionary)
	def search(self, url): return self.representer.search(self, url)
	#--------------------------------------#
#================================================================================#
class Recordset:
	def __init__(self):
		self.__records = [] #mapped objects from records
		self.rowsCount = 0
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
	def affectedRowsCount(self): return self.rowsCount
	#--------------------------------------#
	def insert(self):
		if(self.firstRecord()): self.firstRecord().database.insertMany(self.firstRecord())
	def read(self, selected="*", group_by=''):
		if(self.firstRecord()):  self.firstRecord().database.readMany(self.firstRecord())
	def update(self):
		if(self.firstRecord()):  self.firstRecord().database.updateMany(self.firstRecord())
	def delete(self):
		if(self.firstRecord()):  self.firstRecord().database.deleteMany(self.firstRecord())
	def startUpdate(self):
		if(self.firstRecord()):  self.firstRecord().database.startUpdateMany(self.firstRecord())
	def commit(self):
		if(self.firstRecord()):  self.firstRecord().database.commit()
#================================================================================#