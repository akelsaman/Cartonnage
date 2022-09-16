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
class NUL(SpecialValue, dict): #to make it json serializable using jsonifiy
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
	def __init__(self, object, fields, type=' INNER JOIN ', value=None):
		self.type = type
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
	def __init__(self, columns=None, rows=None, count=0, rowcount=0):
		self.columns	= columns
		self.rows		= rows
		self.count		= count
		self.rowcount	= rowcount
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
class Prepared():
	def __init__(self):
		self.delete()

	def delete(self):
		self.statement = ""
		self.parameters = []
		self.fieldsNames = []
#================================================================================#
class Representer:

	unsafeCharactersEncoding = {
		'%20': ' ', 
		'%22': '"', 
		'%23': '#', 
		'%25': '%', 
		'%60': '`', 
		'%3C': '<', #capital
		'%3E': '>', 
		'%7B': '{', 
		'%7D': '}', 
		'%7C': '|', 
		'%5C': '\\', 
		'%5E': '^', 
		'%7E': '~', 
		'%5B': '[', 
		'%5D': ']', 
		'%3c': '<', #small
		'%3e': '>', 
		'%7b': '{', 
		'%7d': '}', 
		'%7c': '|', 
		'%5c': '\\', 
		'%5e': '^', 
		'%7e': '~', 
		'%5b': '[', 
		'%5d': ']'
	}

	reservedCharactersEncoding = {
		'%24': '$', 
		'%26': '&', 
		'%40': '@', 
		'%2B': '+',  #captial
		'%2C': ',', 
		'%2F': '/', 
		'%3A': ':', 
		'%3B': ';', 
		'%3D': '=', 
		'%3F': '?', 
		'%40': '@', 
		'%2b': '+',  #small
		'%2c': ',', 
		'%2f': '/', 
		'%3a': ':', 
		'%3b': ';', 
		'%3d': '=', 
		'%3f': '?'
	}

	def __init__(self):
		pass
	#--------------------------------------#
	def to_xml(self, record):
		xmlRecords = "<" + record.table__() + ">"
		for r in record.recordset.iterate():
			xmlRecord = "\n\t<Record "
			attributes = ""
			for column in r.columns:
				attributes += str(column) + "='" + str(r.getField(column)) + "' "
			xmlRecord += attributes + "></Record>"
			xmlRecords += xmlRecord
		xmlRecords += "\n</" + record.table__() + ">"

		return xmlRecords
	#--------------------------------------#
	def to_html(self, record):
		htmlTable = "<table>\n\t<tr><th>" + record.table__() + "</th></tr>"
		
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
	#--------------------------------------#
	def to_json(self, record):
		recordJSON = {}
		for column in record.columns:
			recordJSON[column] = record.getField(column)
		return recordJSON
	#--------------------------------------#
	def loadDictionary(self, record, dictionary):
		for key, value in dictionary.items():
			key = key.split('.')[-1]
			record.setField(key, value)
	#--------------------------------------#
	def collectJoins(self, record, joins):
		for join in record.joins__:
			joins[join] = record.joins__[join]
			self.collectJoins(joins[join].object, joins)
	#--------------------------------------#
	def importSearchCriteria(self, record, searchCriteria):
		joins = {}
		self.collectJoins(record, joins)

		for criterion in searchCriteria:
			info = criterion.split(".")
			if(len(info) == 4):
				operator=info[0]
				alias=info[1]
				attribute=info[2]
				fieldType=info[3]
				tableObjectInstance=None

				if(record.alias.value() == alias):
					tableObjectInstance = record
				elif(alias in joins):
					tableObjectInstance = joins[alias].object

				if(tableObjectInstance):
					if(operator=="is"): tableObjectInstance.setField(attribute, searchCriteria[criterion])
					if(operator=="like"): tableObjectInstance.setField(attribute, LIKE(searchCriteria[criterion]))
					if(operator=="in"): tableObjectInstance.setField(attribute, IN(searchCriteria[criterion]))
					if(operator=="not_in"): tableObjectInstance.setField(attribute, NOT_IN(searchCriteria[criterion]))
					if(operator=="gt"): tableObjectInstance.setField(attribute, gt(searchCriteria[criterion]))
					if(operator=="ge"): tableObjectInstance.setField(attribute, ge(searchCriteria[criterion]))
					if(operator=="lt"): tableObjectInstance.setField(attribute, lt(searchCriteria[criterion]))
					if(operator=="le"): tableObjectInstance.setField(attribute, le(searchCriteria[criterion]))
					if(operator=="between"):
						betweenValues = searchCriteria[criterion]
						if(type(betweenValues) is list and len(betweenValues) == 2):
							tableObjectInstance.setField(attribute, BETWEEN(betweenValues[0], betweenValues[1]))
	#--------------------------------------#
	def getSearchURL(self, searchCriteria):
		url = ''
		for criterion in searchCriteria:
			url += criterion + "=" + str(searchCriteria[criterion]) + "&"
		return url
	#--------------------------------------#
	def deccodeURL(self, urlCriteria):
		for encodedCharacter in Representer.reservedCharactersEncoding:
			urlCriteria = urlCriteria.replace(encodedCharacter, Representer.reservedCharactersEncoding[encodedCharacter])
		for encodedCharacter in Representer.unsafeCharactersEncoding:
			urlCriteria = urlCriteria.replace(encodedCharacter, Representer.unsafeCharactersEncoding[encodedCharacter])
		return urlCriteria
	#--------------------------------------#
	def checkValueType(self, fieldName, fieldValue, fieldType):
		validatedValue = None
		if(fieldType == 'i'):
			try:
				validatedValue = int(fieldValue)
			except Exception as e: print("Error '" + fieldName + "' parsing int !") #print(str(e))
		elif(fieldType == 'f'):
			try:
				validatedValue = float(fieldValue)
			except Exception as e: print("Error '" + fieldName + "' parsing int !") #print(str(e))
		elif(fieldType == 's'):
			if(type(fieldValue) in [str, unicode] and fieldValue != ''): validatedValue = fieldValue
			else: print("Error '" + fieldName + "' parsing str !") #print(str(e))
		return validatedValue
	#--------------------------------------#
	def checkListValuesTypes(self, fieldName, listValues, fieldType):
		listValues = listValues.replace('[', '')
		listValues = listValues.replace(']', '')
		listValues = listValues.split(",")
		validatedValues = []
		for v in listValues:
			v = v.replace(' ', '')
			if(fieldType == 'i'):
				try:
					v = int(v)
					validatedValues.append(v)
				except Exception as e: print("Error '" + fieldName + "' parsing int !") #print(str(e))
			elif(fieldType == 'f'):
				try:
					v = float(v)
					validatedValues.append(v)
				except Exception as e: print("Error '" + fieldName + "' parsing float !") #print(str(e))
			elif(fieldType == 's'):
				print("|||>>>", v)
				if(type(v) in [str, unicode] and v != ''): validatedValues.append(v)
				else: print("Error in '" + fieldName + "' finiding string value to search !") #print(str(e))
		return validatedValues
	#--------------------------------------#
	#in.restaurant.Restaurant_ID=[115]&like.branch.State=Cai*&like.branch.City=Shero*&like.branch.Address=Add*&like.branch.Telephone=*&in.feature.Feature_ID=[1, 2]&
	def getURLData(self, url):
		#http://localhost:5000/userSearch?like.restaurant.Name.s=*saman*&in.feature.Feature_ID.i=[2]
		#http://localhost:5000/userSearch?like.restaurant.Name.s%3d*saman*&in.feature.Feature_ID.i%3d%5b2%5d

		searchCriteria = {}

		url = url.split("?")
		if(len(url) >= 2):
			urlCriteria = url[1]
			
			urlCriteria = self.deccodeURL(urlCriteria)
			print(urlCriteria)

			criteria = urlCriteria.split("&")
			#print(criteria)

			for criterion in criteria:
				criterion = criterion.split("=")
				if(len(criterion) == 2):
					value = criterion[1]
					criterion = criterion[0]
					info = criterion.split(".")
					if(len(info) == 4):
						operator=info[0]
						alias=info[1]
						fieldName=info[2]
						fieldType=info[3]
						tableObjectInstance=None
						#--------------------
						if(operator in ['like', 'is', 'eq', 'gt', 'ge', 'lt', 'le', 'not_like']):
							validatedValue = self.checkValueType(fieldName, value, fieldType)
							if(validatedValue): searchCriteria[criterion] = validatedValue
						#--------------------
						elif(operator in ['in', 'not_in']):
							validatedValues = self.checkListValuesTypes(fieldName, value, fieldType)
							if(len(validatedValues)): searchCriteria[criterion] = validatedValues
						#--------------------
						elif(operator=='between'):
							validatedValues = self.checkListValuesTypes(fieldName, value, fieldType)
							if(len(validatedValues) == 2): searchCriteria[criterion] = validatedValues
						#--------------------
						else:
							searchCriteria[criterion] = value
						#--------------------
			return searchCriteria
		else: return {}
#================================================================================#
class JSONRelationalMapper:
	def __init__(self): pass
	def map(self, passedObject):
		jsonDictionaryList = []
		query = passedObject.query__
		columns = query.result.columns #empty the columns of the passed object only since the new object created below for each row is empty
		if(query.result.rows):
			for row in query.result.rows:
				index = 0
				jsonDictionary = {}
				for fieldValue in row:
					if(fieldValue is None):
						fieldValue=""
					elif(type(fieldValue) == bytearray): #mysql python connector returns bytearray instead of string
						fieldValue = fieldValue.decode('utf-8')
					# str() don't use # to map Null value to None field correctly.
					jsonDictionary[query.result.columns[index]]=fieldValue
					index += 1
				jsonDictionaryList.append(jsonDictionary)
		passedObject.json = jsonDictionaryList
#================================================================================#
class ObjectRelationalMapper:
	def __init__(self): pass
	#--------------------------------------#
	def map(self, passedObject):
		object = passedObject
		query = object.query__
		passedObject.columns = [] #empty the columns of the passed object only since the new object created below for each row is empty
		if(query.result.rows):
			passedObject.recordset.empty()
			for row in query.result.rows:
				object.columns = query.result.columns
				index = 0
				for fieldValue in row:
					if(fieldValue is None):
						fieldValue=NUL()
					elif(type(fieldValue) == bytearray): #mysql python connector returns bytearray instead of string
						fieldValue = fieldValue.decode('utf-8')
					# str() don't use # to map Null value to None field correctly.
					setattr(object, query.result.columns[index], fieldValue)
					index += 1
				passedObject.recordset.add(object)
				object = passedObject.__class__() #object = Record() #bug
#================================================================================#
class DummyObjectRelationalMapper:
	def __init__(self): pass
	#--------------------------------------#
	def map(self, passedObject):
		pass
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
	#--------------------------------------#
	def __init__(self, database=None, username=None, password=None, host=None):
		self.__database		= database
		self.__username		= username
		self.__password		= password
		self.__host			= host
		self.__connection	= None
		self.__cursor		= None
		self.__placeholder	= '?'
		self.__escapeChar	= '`'
		self.operationsCount = 0
		self.user_pk		= 0
		self.connect()
	#--------------------------------------#
	def placeholder(self): return self.__placeholder
	def escapeChar(self): return self.__escapeChar
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
	def joining(self, record):
		joiners = Joiners()
		for key, join in record.joins__.items():
			#" INNER JOIN Persons pp ON "
			inner_join = join.type + join.object.table__() + ' ' + join.object.alias.value() + ' ON '		
			for foreign_key, primary_key in join.fields.items():
				#"	uu.person.fk=pp.pk AND "
				inner_join += "\n\t" + record.alias.value() + "." + self.escapeChar() + foreign_key + self.escapeChar() + "=" + join.object.alias.value() + "." + self.escapeChar() + primary_key + self.escapeChar() + " AND "
			inner_join = "\n" + inner_join[:-5]
			joiners.joinClause += inner_join
			#--------------------
			self.__prepare(Database.read , join.object)
			statement = join.object.prepared__.statement
			if(statement): joiners.preparedStatement += " AND " + statement
			joiners.parameters += join.object.prepared__.parameters
			join.object.prepared__.delete() #to be deleted after investigate dependencies
			join.object.state__.delete() #to be deleted after investigate dependencies
			#--------------------
			child_joiners = self.joining(join.object)
			joiners.joinClause += child_joiners.joinClause
			#if(child_joiners.preparedStatement): joiners.preparedStatement += child_joiners.preparedStatement
			joiners.preparedStatement += child_joiners.preparedStatement
			joiners.parameters += child_joiners.parameters

		return joiners
	#--------------------------------------#
	def secure(self, record):

		queryStatement = record.query__.statement

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
			views.query__.statement = loadViews

			# mysql.connector.errors.InterfaceError
			# InterfaceError: No result set to fetch from.
			# No parameters were provided with the prepared statement
			# "views.query__.parameters" was written by mistake "views.parameters"

			views.query__.parameters = [record.secure__.user_id] + tablesNames
			self.executeStatement(views.query__)
			Database.orm.map(views)

			#print(views.recordset.count())
			for view in views:
				#print(view.columns)
				secureViewsStatement[str(view.table_name)] = '(' + str(view.crud_statement) + '\n)'
			for tableName in tablesNames:
				if(tableName not in secureViewsStatement):
					secureViewsStatement[tableName] = f"{self.escapeChar()}{tableName}{self.escapeChar()}"

			#print(secureViewsStatement)

			queryStatementTemplate = Template(queryStatement)
			secureQuerySatement = queryStatementTemplate.safe_substitute(secureViewsStatement)
			secureQuerySatement = secureQuerySatement.replace("$|user.pk|", str(record.secure__.user_id))
			record.query__.statement = secureQuerySatement
			#return secureQuery
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

			if hasattr(self.__cursor, 'lastrowid'): lastrowid = self.__cursor.lastrowid #MySQL has last row id
			columns = []
			#cursor.description returns a tuple of information describes each column in the table.
			#(name, type_code, display_size, internal_size, precision, scale, null_ok)
			#for index, column in enumerate(self.__cursor.description): columns.append(column[0])
			
			if(self.__cursor.description): columns = [column[0] for column in self.__cursor.description]
			query.result = Result(columns, rows, count, rowcount)
			#for r in query.result.rows:
			#	print(r)
			return query
	#--------------------------------------#
	def executeMany(self, query):
		#print(query.statement)
		#print(query.parameters)
		rowcount = 0
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
	def __prepare(self, operation, record, fields_names=None):
		placeholder = self.placeholder()
		record.prepared__.delete()
		fieldsEqualPlaceholdersAnd = fieldsEqualPlaceholdersComma = fields = parametersPlaceholders = ""
		parameters = []
		fieldsNames = []
		flds=record.__dict__
		if(fields_names): flds=fields_names
		for field in flds: #for a in dir(r): println(a)
			fieldValue = record.__dict__[field]
			# any other type will be execluded Class type, None type and others ...
			if(type(fieldValue) in [str, unicode, int, float, datetime]):
				fieldsNames.append(field)
				fieldsEqualPlaceholdersAnd += f"{record.alias.value()}.{self.escapeChar()}{field}{self.escapeChar()} = {placeholder} AND "
				fieldsEqualPlaceholdersComma += f"{self.escapeChar()}{field}{self.escapeChar()} = {placeholder}, "
				fields += f"{self.escapeChar()}{field}{self.escapeChar()}, "
				parametersPlaceholders += f"{placeholder}, "
				parameters.append(fieldValue) #not used for parameterized statement #if(value): value = "'" + str(value) + "'"
			elif(isinstance(fieldValue, NUL)):
				fieldsNames.append(field)
				fieldsEqualPlaceholdersAnd += f"{record.alias.value()}.{self.escapeChar()}{field}{self.escapeChar()} {fieldValue.operator(operation)} {placeholder} AND "
				fieldsEqualPlaceholdersComma += f"{self.escapeChar()}{field}{self.escapeChar()} {fieldValue.operator(operation)} {placeholder}, "
				fields += f"{self.escapeChar()}{field}{self.escapeChar()}, "
				parametersPlaceholders += f"{placeholder}, "
				parameters.append(None)
			elif(isinstance(fieldValue, NOT_NULL)):
				fieldsNames.append(field)
				fieldsEqualPlaceholdersAnd += f"{record.alias.value()}.{self.escapeChar()}{field}{self.escapeChar()} {fieldValue.operator()} {fieldValue.placeholder(placeholder)} AND "
				fieldsEqualPlaceholdersComma += f"{self.escapeChar()}{field}{self.escapeChar()} {fieldValue.operator()} {fieldValue.placeholder(placeholder)}, "
				fields += f"{self.escapeChar()}{field}{self.escapeChar()}, "
				parametersPlaceholders += f"{placeholder}, "
			elif(isinstance(fieldValue, (gt, ge, lt, le, LIKE))):
				fieldsNames.append(field)
				fieldsEqualPlaceholdersAnd += f"{record.alias.value()}.{self.escapeChar()}{field}{self.escapeChar()} {fieldValue.operator()} {fieldValue.placeholder(placeholder)} AND "
				fieldsEqualPlaceholdersComma += f"{self.escapeChar()}{field}{self.escapeChar()} {fieldValue.operator()} {fieldValue.placeholder(placeholder)}, "
				fields += f"{self.escapeChar()}{field}{self.escapeChar()}, "
				parametersPlaceholders += f"{placeholder}, "
				parameters.append(fieldValue.value()) # the value of LIKE
			elif(isinstance(fieldValue, (IN, BETWEEN, NOT_IN))):
				if(type(fieldValue.value()) is list and len(fieldValue.value())): #to make sure it's a list and contains elements
					fieldsNames.append(field)
					fieldsEqualPlaceholdersAnd += f"{record.alias.value()}.{self.escapeChar()}{field}{self.escapeChar()} {fieldValue.operator()} {fieldValue.placeholder(placeholder)} AND "
					fieldsEqualPlaceholdersComma += f"{self.escapeChar()}{field}{self.escapeChar()} {fieldValue.operator()} {fieldValue.placeholder(placeholder)}, "
					fields += f"{self.escapeChar()}{field}{self.escapeChar()}, "
					parametersPlaceholders += f"{placeholder}, "
					for value in fieldValue.value(): parameters.append(value) # list values
		#
		if(operation==Database.insert): record.prepared__.statement = f"({fields[:-2]}) VALUES ({parametersPlaceholders[:-2]})"
		elif(operation==Database.read): record.prepared__.statement = fieldsEqualPlaceholdersAnd[:-5]
		elif(operation==Database.startUpdate): record.prepared__.statement = fieldsEqualPlaceholdersAnd[:-5]
		elif(operation==Database.update): record.prepared__.statement = fieldsEqualPlaceholdersComma[:-2]
		elif(operation==Database.delete): record.prepared__.statement = fieldsEqualPlaceholdersAnd[:-5]
		elif(operation==Database.all):
			record.prepared__.statement = "1"
			parameters = [] #iterating over Record has attributes will fill emptied parameters above with the same attributes again
		record.prepared__.fieldsNames = fieldsNames
		record.prepared__.parameters = parameters
		#
		#print(record.prepared__.statement)
		#print(parameters)
	#--------------------------------------#
	def __crud(self, operation, record, selected="*", group_by='', limit=''):
		self.__prepare(operation, record)
		joiners = self.joining(record)
		joinsCriteria = joiners.preparedStatement
		where = "1=1"
		if(record.prepared__.statement): where=record.prepared__.statement
		_where_ = record.state__.statement
		#----- #ordered by occurance propability for single record
		if(operation==Database.read):
			statement = f"SELECT {selected} FROM {record.table__()} {record.alias.value()} {joiners.joinClause} \nWHERE {where} {joinsCriteria} \n{group_by} {limit}"
		elif(operation==Database.insert):
			statement = f"INSERT INTO {record.table__()} {record.prepared__.statement}"
		elif(operation==Database.delete):
			statement = f"DELETE {selected} FROM {record.table__()} {joiners.joinClause} \nWHERE {where} {joinsCriteria}"
		elif(operation==Database.update):
			statement = f"UPDATE {record.table__()} SET {record.prepared__.statement} \nWHERE {_where_}"
		elif(operation==Database.all):
			statement = f"SELECT * FROM {record.table__()} {record.alias.value()} {joiners.joinClause}"
		#-----
		record.query__ = Query()
		record.query__.statement = statement
		record.query__.parameters = record.prepared__.parameters
		record.query__.parameters += record.state__.parameters #state.parameters must be reset to empty list [] not None for this operation to work correctly
		record.query__.parameters += joiners.parameters
		record.state__.delete()
		if(record.secure__.user_id): self.secure(record)
		self.executeStatement(record.query__)
		self.orm.map(record) #use self. instead Database. to be  able to override
	#--------------------------------------#
	def __crudMany(self, operation, record, selected="*", group_by='', limit=''):
		self.__prepare(operation, record)
		joiners = self.joining(record)
		joinsCriteria = joiners.preparedStatement
		where = "1=1"
		if(record.prepared__.statement): where=record.prepared__.statement
		_where_ = record.state__.statement
		#----- #ordered by occurance propability for many records
		if(operation==Database.insert):
			statement = f"INSERT INTO {record.table__()} {record.prepared__.statement}"
		elif(operation==Database.update):
			statement = f"UPDATE {record.table__()} SET {record.prepared__.statement} \nWHERE {_where_}"
		elif(operation==Database.read):
			statement = f"SELECT {selected} FROM {record.table__()} {record.alias.value()} {joiners.joinClause} \nWHERE {where} {joinsCriteria} \n{group_by} {limit}"
		elif(operation==Database.delete):
			statement = f"DELETE {selected} FROM {record.table__()} {joiners.joinClause} \nWHERE {where} {joinsCriteria}"
		elif(operation==Database.all):
			statement = f"SELECT * FROM {record.table__()} {record.alias.value()} {joiners.joinClause}"
		#-----
		fieldsNames = record.prepared__.fieldsNames # as record.statement__.delete() below in iteration over recordset will delete record.statement__.fieldsnames
		query=Query() # as 
		query.statement = statement
		for r in record.recordset.iterate():
			#r.insert()
			self.__prepare(operation, r, fieldsNames)
			r.prepared__.parameters = r.prepared__.parameters + r.state__.parameters #state.parameters must be reset to empty list [] not None for this operation to work correctly
			#r_joiners = self.joining(r)
			#r.query__.parameters += r_joiners.parameters # parameters need to be implemented to be retrieved in the same order from all records
			query.parameters.append(tuple(r.prepared__.parameters))
			r.state__.delete()
		#if(record.secure__.user_id): self.secure(record) #not implemented for many (insert and update)
		record.recordset.rowsCount = self.executeMany(query)
		#self.orm.map(record)  #not implemented for many (insert and update)
	#--------------------------------------#
	def all(self, record): self.__crud(Database.all, record)
	def insert(self, record): self.__crud(Database.insert, record)
	def read(self, record, selected="*", group_by='', limit=''): self.__crud(Database.read, record, selected, group_by, limit)
	def delete(self, record, selected): self.__crud(Database.delete, record, selected)
	def update(self, record): 
		if(record.state__.statement):
			self.__crud(Database.update, record)
		else:
			raise RuntimeError("The update doesn't start, no current state !")
	#--------------------------------------#
	def insertMany(self, record): self.__crudMany(Database.insert, record)
	def deleteMany(self, record, selected): self.__crudMany(Database.delete, record, selected)
	def updateMany(self, record):
		if(record.state__.statement):
			self.__crudMany(Database.update, record)
		else:
			#print("The update doesn't start, no current state !")
			raise RuntimeError("The update doesn't start, no current state !")
	#--------------------------------------#
	def startUpdate(self, record, fieldsNames=None):
		if(fieldsNames): #Recordset.startUpdate()
			self.__prepare(Database.startUpdate, record, fieldsNames)
			record.state__.parameters = record.prepared__.parameters
		else: #Record.startUpdate()
			self.__prepare(Database.startUpdate, record, fieldsNames)
			record.state__.statement = record.prepared__.statement
			record.state__.parameters = record.prepared__.parameters
	#--------------------------------------#
	def startUpdateMany(self, record):
		self.startUpdate(record)
		#self.startUpdate(record) will happen again in next line recordset iteration startUpdate process
		for r in record.recordset.iterate(): self.startUpdate(r, record.prepared__.fieldsNames)
	#--------------------------------------#
	def limit(self, pageNumber=1, recordsCount=1):
		try:
			pageNumber = int(pageNumber)
			recordsCount = int(recordsCount)
			if(pageNumber and recordsCount):
				offset = (pageNumber - 1) * recordsCount
				return self.paginationClause(offset, recordsCount)
			else:
				return ''
		except Exception as e:
			print(e)
			return ''
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
			elif(isinstance(attributeValue, NUL)):
				setattr(copy, attributeName, NUL())
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
	def __init__(self, database=None, username=None, password=None, host=None):
		Database.__init__(self, database=database, username=username, password=password, host=host)
	def connect(self):
		if(self.connectionParameters() >= 3):
			import cx_Oracle
			if(self._Database__host):
				dsn_tns = cx_Oracle.makedsn(self._Database__host, '1521', service_name=self._Database__database)
				self._Database__connection = cx_Oracle.connect(self._Database__username, self._Database__password, dsn=dsn_tns)
			else:
				self._Database__connection = cx_Oracle.connect(self._Database__username, self._Database__password, self._Database__database)
			self.cursor()
			self._Database__placeholder = ':1' #1 #start of numeric
			self._Database__escapeChar = '"'
	@staticmethod
	def paginationClause(offset=0, recordsCount=1):
		return f"OFFSET {offset} ROWS FETCH NEXT {recordsCount} ROWS ONLY"
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
	def lastTotalRows(self):
		self._Database__cursor.execute("SELECT FOUND_ROWS() AS last_total_rows")
		(last_total_rows,) = self._Database__cursor.fetchone()
		return last_total_rows
	@staticmethod
	def paginationClause(offset=0, recordsCount=1):
		return f"LIMIT {offset}, {recordsCount}"
#================================================================================#
class MySQLClient(Database):
	def __init__(self, database=None, username=None, password=None, host=None):
		Database.__init__(self, database=database, username=username, password=password, host=host)
	def connect(self):
		if(self.connectionParameters() == 4):
			import MySQLdb
			self._Database__connection = MySQLdb.connect(db=self._Database__database, user=self._Database__username, password=self._Database__password, host=self._Database__host)
			self.cursor()
			self._Database__placeholder = '%s'
	def lastTotalRows(self):
		self._Database__cursor.execute("SELECT FOUND_ROWS() AS last_total_rows")
		(last_total_rows,) = self._Database__cursor.fetchone()
		return last_total_rows
	@staticmethod
	def paginationClause(offset=0, recordsCount=1):
		return f"LIMIT {offset}, {recordsCount}"
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
	database__	= None
	representer__ = Representer()
	tableName__ = TableName()
	#--------------------------------------#
	def __init__(self, statement=None, parameters=None, alias=None, secure_by_user_id=None, **kwargs):
		self.recordset = Recordset()
		self.prepared__ = Prepared()
		self.state__ = State()
		self.columns = [] #use only after reading data from database #because it's loaded only from the query's result
		self.joins__ = {}
		self.primarykey__ = []
		self.secure__ = UserID(secure_by_user_id)

		self.alias = Alias(f"{self.database__.escapeChar()}{self.__class__.__name__}{self.database__.escapeChar()}")
		if(self.secure__.user_id):
			self.table__ = self.__tableSecure
		else:
			self.table__ = self.__table

		if(kwargs):
			for key, value in kwargs.items():
				setattr(self, key, value)

		self.query__ = Query() # must be declared before self.query__(statement)
		if(statement):
			self.query__.statement = statement
			if(parameters): self.query__.parameters = parameters #if prepared statement's parameters are passed
			#self. instead of Record. #change the static field self.__database for inherited children classes
			if(self.secure__.user_id): self.database__.secure(self)
			if(len(self.query__.parameters) and type(self.query__.parameters[0]) in (list, tuple)):
				self.database__.executeMany(self.query__)
			else:
				self.database__.executeStatement(self.query__)
			Database.orm.map(self)
	#--------------------------------------#
	def __table(self):
		if(self.tableName__.value()): return f"{self.database__.escapeChar()}{self.tableName__.value()}{self.database__.escapeChar()}"
		else: return f"{self.database__.escapeChar()}{self.__class__.__name__}{self.database__.escapeChar()}"
	#--------------------------------------#
	def __tableSecure(self):
		if(self.tableName__.value()): return "${" + self.tableName__.value() + "}"
		else: return "${" + self.__class__.__name__ + "}"
	#--------------------------------------#
	def id(self): return self.query__.result.lastrowid
	#--------------------------------------#
	def readCount(self): return self.query__.result.count
	#--------------------------------------#
	def getField(self, fieldName): return self.__dict__[fieldName]
	def setField(self, fieldName, fieldValue): self.__dict__[fieldName]=fieldValue
	#--------------------------------------#
	#def __str__(self): pass
	#--------------------------------------#
	def hash(self):
		hashedValue = ''
		for column in self.primarykey__: pass
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
	def insert(self): self.database__.insert(self)
	def read(self, selected="*", group_by='', limit=''): self.database__.read(self, selected, group_by, limit)
	def update(self): self.database__.update(self)
	def delete(self): self.database__.delete(self, selected='')
	def startUpdate(self): self.database__.startUpdate(self)
	def all(self): self.database__.all(self)
	def commit(self): self.database__.commit()
	#--------------------------------------#
	def join(self, table, fields): self.joins__[table.alias.value()] = Join(table, fields)
	#--------------------------------------#
	def rightJoin(self, table, fields): self.joins__[table.alias.value()] = Join(table, fields, ' RIGHT JOIN ')
	#--------------------------------------#
	def leftJoin(self, table, fields): self.joins__[table.alias.value()] = Join(table, fields, ' LEFT JOIN ')
	#--------------------------------------#
	def getCopyInstance(self, base=(object, ), attributesDictionary={}):
		return self.database__.getCopyInstance(self, base, attributesDictionary={})
	#--------------------------------------#
	def to_json(self): return self.representer__.to_json(self)
	def to_xml(self): return self.representer__.xml(self)
	def to_html(self): return self.representer__.html(self)
	def loadDictionary(self, dictionary): return self.representer__.loadDictionary(self, dictionary)
	def searchURL(self, url): return self.representer__.search(self, url)
	def importSearchCriteria(self, searchCriteria): return self.representer__.importSearchCriteria(self, searchCriteria)
	def search(self, searchCriteria, selected="*", group_by='', limit=''):
		self.importSearchCriteria(searchCriteria)
		self.read(selected, group_by, limit)
	def limit(self, pageNumber=1, recordsCount=1): return self.database__.limit(pageNumber, recordsCount)
	@staticmethod
	def getURLData(url): return Record.representer__.getURLData(url)
	@staticmethod
	def lastTotalRecords(): return Record.database__.lastTotalRows()
	#--------------------------------------#
#================================================================================#
class Recordset:
	def __init__(self):
		self.__records = [] #mapped objects from records
		self.rowsCount = 0
	def table(self):
		if(self.firstRecord()): return  self.firstRecord().table__()
	def empty(self): self.__records = []
	def add(self, recordObject): self.__records.append(recordObject)
	def iterate(self): return self.__records
	def firstRecord(self):
		if(len(self.__records)):
			# make sure that first record has the recordset list if it's add manually to the current recordset not read from database
			self.__records[0].recordset = self
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
		if(self.firstRecord()): self.firstRecord().database__.insertMany(self.firstRecord())
	def read(self, selected="*", group_by='', limit=''):
		if(self.firstRecord()):  self.firstRecord().database__.readMany(self.firstRecord())
	def update(self):
		if(self.firstRecord()):  self.firstRecord().database__.updateMany(self.firstRecord())
	def delete(self, selected=''):
		if(self.firstRecord()):  self.firstRecord().database__.deleteMany(self.firstRecord(), selected)
	def startUpdate(self):
		if(self.firstRecord()):  self.firstRecord().database__.startUpdateMany(self.firstRecord())
	def commit(self):
		if(self.firstRecord()):  self.firstRecord().database__.commit()
	#--------------------------------------#
	def to_json(self):
		recordsetJSONList = []
		for record in self.iterate():
			recordsetJSONList.append(record.to_json())
		return recordsetJSONList
#================================================================================#
class Collection(list): pass
#================================================================================#
class manipolatore:
	def __init__(self, dictionary):
		self.dictionary = dictionary
	#--------------------
	def path(self, path):
		return path.split(".")[::-1]
	#--------------------
	def traverse(self, path, element):
		if(len(path)):
			if(type(element) is dict):
				key=path.pop()
				if(key in element):
					return self.traverse(path, element[key])
			elif(type(element) is list):
				colection = Collection()
				for elm in element:
					newPath = list(path)
					colection.append(self.traverse(newPath, elm))
				if(len(colection)==1): return colection[0] # if list contains one element return the element itself
				elif(len(colection)>1): return colection
				#return colection
			else:
				return element
		else:
			return element
	#--------------------
	def __getValue(self, path):
		path = self.path(path)
		value = self.traverse(path, self.dictionary) ###
		return value ###
	#--------------------
	def getValue(self, path):
		value = self.__getValue(path)
		if(value): return value
		elif(value == ""): return ""
		else: return NUL()
	#--------------------
#================================================================================#