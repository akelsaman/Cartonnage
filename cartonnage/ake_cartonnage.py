#!/usr/bin/python

#version: 202601250248
#================================================================================#
from datetime import datetime
#================================================================================#
NoneType = type(None)
#================================================================================#
class Field:
	def __init__(self, cls, name, value):
		self.cls = cls
		self.name = name
		self.value = value
		self.placeholder = cls.database__.placeholder()

	def _field_name(self):
		return f"{self.cls.__name__}.{self.name}"

	def _resolve_value(self, value):
		"""Returns (sql_value, parameters)"""
		if type(value) == Field:
			return (f"{value.cls.__name__}.{value.name}", [])
		elif isinstance(value, Expression):
			return (value.value, value.parameters)
		else:
			return (self.placeholder, [value])

	def __eq__(self, value):
		sql_val, params = self._resolve_value(value)
		return Expression(f"{self._field_name()} = {sql_val}", params)
	def __ne__(self, value):
		sql_val, params = self._resolve_value(value)
		return Expression(f"{self._field_name()} <> {sql_val}", params)
	def __gt__(self, value):
		sql_val, params = self._resolve_value(value)
		return Expression(f"{self._field_name()} > {sql_val}", params)
	def __ge__(self, value):
		sql_val, params = self._resolve_value(value)
		return Expression(f"{self._field_name()} >= {sql_val}", params)
	def __lt__(self, value):
		sql_val, params = self._resolve_value(value)
		return Expression(f"{self._field_name()} < {sql_val}", params)
	def __le__(self, value):
		sql_val, params = self._resolve_value(value)
		return Expression(f"{self._field_name()} <= {sql_val}", params)
	def __add__(self, value):
		sql_val, params = self._resolve_value(value)
		return Expression(f"{self._field_name()} + {sql_val}", params)
	def __sub__(self, value):
		sql_val, params = self._resolve_value(value)
		return Expression(f"{self._field_name()} - {sql_val}", params)
	def __mul__(self, value):
		sql_val, params = self._resolve_value(value)
		return Expression(f"{self._field_name()} * {sql_val}", params)
	def __truediv__(self, value):
		sql_val, params = self._resolve_value(value)
		return Expression(f"{self._field_name()} / {sql_val}", params)

	# SQL-specific methods
	def is_null(self):
		return Expression(f"{self._field_name()} IS NULL", [])
	def is_not_null(self):
		return Expression(f"{self._field_name()} IS NOT NULL", [])
	def like(self, pattern):
		return Expression(f"{self._field_name()} LIKE {self.placeholder}", [pattern])
	def in_(self, values):
		placeholders = ', '.join([self.placeholder] * len(values))
		return Expression(f"{self._field_name()} IN ({placeholders})", list(values))
	def not_in(self, values):
		placeholders = ', '.join([self.placeholder] * len(values))
		return Expression(f"{self._field_name()} NOT IN ({placeholders})", list(values))
	def between(self, low, high):
		return Expression(f"{self._field_name()} BETWEEN {self.placeholder} AND {self.placeholder}", [low, high])

	# Subquery methods - take a Record instance and generate SQL
	def in_subquery(self, record, selected="*"):
		"""field IN (SELECT ... FROM ...)"""
		query = Database.crud(operation=Database.read, record=record, selected=selected, group_by='', limit='')
		return Expression(f"{self._field_name()} IN (\n{query.statement}\n)", query.parameters)

	def not_in_subquery(self, record, selected="*"):
		"""field NOT IN (SELECT ... FROM ...)"""
		query = Database.crud(operation=Database.read, record=record, selected=selected, group_by='', limit='')
		return Expression(f"{self._field_name()} NOT IN (\n{query.statement}\n)", query.parameters)

	@staticmethod
	def exists(record, selected="1"):
		"""EXISTS (SELECT ... FROM ... WHERE ...)"""
		query = Database.crud(operation=Database.read, record=record, selected=selected, group_by='', limit='')
		return Expression(f"EXISTS (\n{query.statement}\n)", query.parameters)

	@staticmethod
	def not_exists(record, selected="1"):
		"""NOT EXISTS (SELECT ... FROM ... WHERE ...)"""
		query = Database.crud(operation=Database.read, record=record, selected=selected, group_by='', limit='')
		return Expression(f"NOT EXISTS (\n{query.statement}\n)", query.parameters)
#================================================================================#
class Dummy:
	def __init__(self, value):
		self.value = value
#--------------------------------------#
# for new SpecialValue review
# Database() #Database.parameterize() #Database.getCopyInstance()
# for NULL review ObjectRelationalMapper also
class SpecialValue:
	def __init__(self, value=None): self.__value = value
	def value(self): return self.__value
	def operator(self): return "="
	def placeholder(self, placeholder): return placeholder
	def condition(self): return self.__condition
#--------------------------------------#
class TableName(SpecialValue): pass
class Alias(SpecialValue): pass
#--------------------------------------#
class Expression():
	def __init__(self, value, parameters=None):
		self.value = value
		self.parameters = parameters if parameters is not None else []
	def fltr(self, field, placeholder): return self.value
	def parametersAppend(self, parameters): parameters.extend(self.parameters)
	def __str__(self): return self.value
	def __repr__(self): return self.value
	def __and__(self, other): return Expression(f"({self.value} AND {other.value})", self.parameters + other.parameters)
	def __or__(self, other): return Expression(f"({self.value} OR {other.value})", self.parameters + other.parameters)
# #--------------------------------------#
class Join():
	def __init__(self, object, fields, type=' INNER JOIN ', value=None):
		self.type = type
		self.object = object
		self.predicates = fields
		self.__value = value
#--------------------
class Joiners():
	def __init__(self, value=None):
		self.joinClause = ''
		self.preparedStatement = ''
		self.parameters = []
		self.__value = value
#================================================================================#
class Result:
	def __init__(self, columns=None, rows=None, count=0):
		self.columns	= columns
		self.rows		= rows
		self.count		= count
#================================================================================#
class Query:
	def __init__(self):
		self.parent = None
		self.statement	= None
		self.result		= Result()
		self.parameters	= [] #to prevent #ValueError: parameters are of unsupported type in line #self.__cursor.execute(query.statement, tuple(query.parameters))
		self.operation	= None
#================================================================================#
class Set:
	def __init__(self, parent):
		self.__dict__['parent'] = parent
		self.empty()

	def empty(self):
		self.__dict__['new'] = {}

	def setFields(self):
		statement = ''
		for field in self.new.keys():
			# some databases reject tablename. or alias. before field in set clause as they are don't implement join update
			# statement += f"{self.parent.alias.value()}.{field}={self.parent.database__.placeholder()}, "
			value = self.new[field]
			if isinstance(value, Expression):
				statement += f"{field}={value.value}, " # Expression directly # value.value = Expression.value
			else:
				statement += f"{field}={self.parent.database__.placeholder()}, "
		return statement[:-2]
	
	def parameters(self, fieldsNames=None):
		fields = fieldsNames if(fieldsNames) else list(self.new.keys())
		parameters = []
		for field in fields:
			value = self.new[field]
			if isinstance(value, Expression):  # Skip expressions
				parameters.extend(value.parameters) # value.parameters = Expression.parameters
			else:
				parameters.append(value) #	if type(value) != Expression:
		return parameters

	def __setattr__(self, name, value):
		# if(name=="custom"): self.__dict__["custom"] = value
		if(type(value) in [NoneType, str, int, float, datetime, bool] or isinstance(value, Expression)):
			self.__dict__["new"][name] = value
		else:
			object.__setattr__(self, name, value)
#================================================================================#
class Values:
	# Usage of Values:
	#	1. insert FIELDS NAMES and VALUES
	#	2. Where exact values
	#--------------------------------------#
	@staticmethod
	def fields(record):
		fields = []
		# for field in record.__dict__: 
		# 	value = record.__dict__[field]
		for field in record.data: 
			value = record.data[field]
			if(type(value) in [str, int, float, datetime, bool]):
				fields.append(field)
		return fields
	#--------------------------------------#
	@staticmethod
	def where(record, fieldsNames=None):
		#getStatement always used to collect exact values not filters so no "NOT NULL", "LIKE", ... but only [str, int, float, datetime, bool] values.
		statement = ''
		# fields = Values.fields(record)
		fields = fieldsNames if (fieldsNames) else Values.fields(record)
		for field in fields:
			value = record.getField(field)
			placeholder = record.database__.placeholder()
			statement += f"{record.alias.value()}.{field} = {placeholder} AND "
		return statement[:-5]
	#--------------------------------------#
	@staticmethod
	def parameters(record, fieldsNames=None):
		#getStatement always used to collect exact values not filters so no "NOT NULL", "LIKE", ... but only [str, int, float, datetime, bool] values.
		fields = fieldsNames if (fieldsNames) else Values.fields(record)
		return list(map(record.getField, fields))
	#--------------------------------------#
#================================================================================#
class Filter:
	def __init__(self, parent):
		self.__dict__['parent'] = parent
		self.empty()

	def empty(self):
		self.__where = ''
		self.__parameters = []
	
	def read(self, selected="*", group_by='', order_by='', limit=''): self.parent.database__.read(operation=Database.read,  record=self.parent, selected=selected, group_by=group_by, order_by=order_by, limit=limit)
	def delete(self): self.parent.database__.delete(operation=Database.delete, record=self.parent)
	def update(self): self.parent.database__.update(operation=Database.update, record=self.parent)

	def fltr(self, field, placeholder): return self.where__()
	def parametersAppend(self, parameters): parameters.extend(self.parameters__())
	def where__(self): return self.__where[:-5]
	def parameters__(self): return self.__parameters
	def combine(self, filter1, filter2, operator):
		w1 = filter1.where__()
		w2 = filter2.where__()
		if(w1 and w2):
			self.__where = f"(({w1}) {operator} ({w2})) AND "
			self.__parameters.extend(filter1.parameters__())
			self.__parameters.extend(filter2.parameters__())
		elif(w1):
			self.__where = f"({w1}) AND "
			self.__parameters.extend(filter1.parameters__())
		elif(w2):
			self.__where = f"({w2}) AND "
			self.__parameters.extend(filter2.parameters__())

	def __or__(self, filter2):
		filter = Filter(self.parent)
		filter.combine(self, filter2, "OR")
		return filter
	def __and__(self, filter2):
		filter = Filter(self.parent)
		filter.combine(self, filter2, "AND")
		return filter
	
	def filter(self, *args, **kwargs):
		for exp in args:
			self.addCondition('_', exp)
		for field, value in kwargs.items():
			self.addCondition(field, value)
		return self
		
	def addCondition(self, field, value):
		placeholder = self.parent.database__.placeholder()
		field = f"{self.parent.alias.value()}.{field}"
		if(type(value) in [str, int, float, datetime, bool]):
			self.__where += f"{field} = {placeholder} AND "
			self.__parameters.append(value)
		else:
			self.__where += f"{value.fltr(field, placeholder)} AND "
			value.parametersAppend(self.__parameters)

	#'record' parameter to follow the same signature/interface of 'Values.where' function design pattern
	#Both are used interchangeably in 'Database.__crud' function
	def where(self, record=None):
		#because this is where so any NULL | NOT_NULL values will be evaluated to "IS NULL" | "IS NOT NULL"
		where = ''
		# where = self.parent.values.where(self.parent)
		# where = f"{where} AND " if (where) else ""
		# Return combined where without modifying self.__where
		# combined_where = where + self.__where
		# print(">>>>>>>>>>>>>>>>>>>>", combined_where)
		# return combined_where[:-5]
		return self.__where[:-5]
	
	#This 'Filter.parameters' function follow the same signature/interface of 'Values.parameters' function design pattern
	#Both are used interchangeably in 'Database.__crud' function
	def parameters(self, record=None):
		# parameters = []
		# parameters = self.parent.values.parameters(self.parent)
		# Return combined parameters without modifying self.__parameters
		# print(">>>>>>>>>>>>>>>>>>>>", parameters + self.__parameters)
		# return parameters + self.__parameters
		return self.__parameters
	#--------------------------------------#
	def in_subquery(self, selected="*", **kwargs):
		for field, value in kwargs.items():
			self.filter(Field(self.parent.__class__, field, None).in_subquery(value, selected=selected))
		return self
	def exists(self, **kwargs):
		for field, value in kwargs.items():
			self.filter(Field.exists(value))
		return self
	def not_exists(self, **kwargs):
		for field, value in kwargs.items():
			self.filter(Field.not_exists(value))
		return self
	def in_(self, **kwargs):
		for field, value in kwargs.items():
			self.filter(Field(self.parent.__class__, field, None).in_(value))
		return self
	def not_in(self, **kwargs):
		for field, value in kwargs.items():
			self.filter(Field(self.parent.__class__, field, None).not_in(value))
		return self
	def like(self, **kwargs):
		for field, value in kwargs.items():
			self.filter(Field(self.parent.__class__, field, None).like(value))
		return self
	def is_null(self, **kwargs):
		for field, value in kwargs.items():
			self.filter(Field(self.parent.__class__, field, None).is_null())
		return self
	def is_not_null(self, **kwargs):
		for field, value in kwargs.items():
			self.filter(Field(self.parent.__class__, field, None).is_not_null())
		return self
	def between(self, **kwargs):
		for field, value in kwargs.items():
			self.filter(Field(self.parent.__class__, field, None).between(value[0], value[1]))
		return self
	def gt(self, **kwargs):
		for field, value in kwargs.items():
			self.filter(Field(self.parent.__class__, field, None) > value)
		return self
	def ge(self, **kwargs):
		for field, value in kwargs.items():
			self.filter(Field(self.parent.__class__, field, None) >= value)
		return self
	def lt(self, **kwargs):
		for field, value in kwargs.items():
			self.filter(Field(self.parent.__class__, field, None) < value)
		return self
	def le(self, **kwargs):
		for field, value in kwargs.items():
			self.filter(Field(self.parent.__class__, field, None) <= value)
		return self
	#--------------------------------------#
#================================================================================#
# fieldValue = fieldValue.decode('utf-8') # mysql python connector returns bytearray instead of string
class ObjectRelationalMapper:
	def __init__(self): pass
	#--------------------------------------#
	def map(self, passedObject):
		query = passedObject.query__
		rows = query.result.rows
		columns = query.result.columns
		passedObject.recordset.data.extend(rows)
		if(passedObject.recordset.count()):
			object = passedObject.__class__() #object = Record() #bug
		else:
			object = passedObject
		for row in rows:
			object.data = row
			object.columns = columns
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
	values = Values
	# ------
	all				= 0
	insert			= 1
	read			= 2
	update			= 4
	delete			= 5
	upsert			= 6
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
		self.batchSize = 10000
		# self.connect()
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
	def joining(record):
		joiners = Joiners()
		quoteChar = '' #cls.escapeChar()
		for key, join in record.joins__.items():
			#" INNER JOIN Persons pp ON "
			joiners.joinClause += f"{join.type}{join.object.table__()} {join.object.alias.value()} ON {join.predicates.value}"
			#--------------------
			# Include both values (exact field matches) and filter conditions from joined object
			valuesStatement = join.object.values.where(join.object)
			filterStatement = join.object.filter_.where(join.object)
			if valuesStatement and filterStatement:
				statement = f"{valuesStatement} AND {filterStatement}"
			elif valuesStatement:
				statement = valuesStatement
			else:
				statement = filterStatement
			if(statement): joiners.preparedStatement += f" AND {statement}"
			joiners.parameters.extend(join.object.values.parameters(join.object))
			joiners.parameters.extend(join.object.filter_.parameters(join.object))
			#--------------------
			child_joiners = Database.joining(join.object)
			joiners.joinClause += child_joiners.joinClause
			joiners.preparedStatement += child_joiners.preparedStatement
			joiners.parameters.extend(child_joiners.parameters)
		return joiners
	#--------------------------------------#
	def executeStatement(self, query):
		if(query.statement):
			# print(f"<s|{'-'*3}")
			# print(" > Execute statement: ", query.statement)
			# print(" > Execute parameters: ", query.parameters)
			# print(f"{'-'*3}|e>")
			#
			self.__cursor.execute(query.statement, tuple(query.parameters))
			self.operationsCount +=1
			#
			count=0
			columns = []

			parent = query.parent
			parent.recordset = Recordset() # initiating recordset once for parent not for every new record so here is better.

			if(query.operation in [Database.all, Database.read]):
				# for index, column in enumerate(self.__cursor.description): columns.append(column[0].lower())
				columns = [column[0].lower() for column in self.__cursor.description] #lower() to low column names
				query.result.columns = columns
				
				while True:
					fetchedRows = [dict(zip(columns, row)) for row in self.__cursor.fetchmany(self.batchSize)]
					query.result.rows = fetchedRows
					count += len(fetchedRows)
					self.orm.map(parent)
					if not fetchedRows:
						break
			else:
				count = self.__cursor.rowcount
			#rowcount is readonly attribute and it contains the count/number of the inserted/updated/deleted records/rows.
			#rowcount is -1 in case of rows/records select.

			if hasattr(self.__cursor, 'lastrowid'): lastrowid = self.__cursor.lastrowid #MySQL has last row id
			#cursor.description returns a tuple of information describes each column in the table.
			#(name, type_code, display_size, internal_size, precision, scale, null_ok)
			rows = []
			query.result = Result(columns, rows, count)
			return query
	#--------------------------------------#
	def executeMany(self, query):
		# print(f"<s|{'-'*3}")
		# print(" > Execute statement: ", query.statement)
		# print(" > Execute parameters: ", query.parameters)
		# print(f"{'-'*3}|e>")
		rowcount = 0
		if(query.statement):
			self.__cursor.executemany(query.statement, query.parameters)
			self.operationsCount +=1
			rowcount = self.__cursor.rowcount
			query.parent.recordset.rowsCount = rowcount
		return rowcount
	#--------------------------------------#
	def executeScript(self, sqlScriptFileName):
		sqlScriptFile = open(sqlScriptFileName,'r')
		sql = sqlScriptFile.read()
		return self.__cursor.executescript(sql)
	#--------------------------------------#
	@staticmethod
	def crud(operation, record, selected="*", group_by='', order_by='', limit=''):
		current = []
		whereValues = record.values.where(record)
		whereFilter = record.filter_.where(record)
		if whereValues and whereFilter:
			where = f"{whereValues} AND {whereFilter}"
		elif whereValues:
			where = whereValues
		else:
			where = whereFilter

		joiners = Database.joining(record)
		joinsCriteria = joiners.preparedStatement
		#----- #ordered by occurance propability for single record
		if(operation==Database.read):
			group_clause = f"GROUP BY {group_by}" if group_by else ''
			order_clause = f"ORDER BY {order_by}" if order_by else ''
			statement = f"SELECT {selected} FROM {record.table__()} {record.alias.value()} {joiners.joinClause} \nWHERE {where if (where) else '1=1'} {joinsCriteria} \n{group_clause} {order_clause} {limit}"
		#-----
		elif(operation==Database.insert):
			fieldsValuesClause = f"({', '.join(record.values.fields(record))}) VALUES ({', '.join([record.database__.placeholder() for i in range(0, len(record.values.fields(record)))])})"
			statement = f"INSERT INTO {record.table__()} {fieldsValuesClause}"
		#-----
		elif(operation==Database.update):
			setFields = record.set.setFields()
			statement = f"UPDATE {record.table__()} SET {setFields} {joiners.joinClause} \nWHERE {where} {joinsCriteria}" #no 1=1 to prevent "update all" by mistake if user forget to set filters
		#-----
		elif(operation==Database.delete):
			statement = f"DELETE FROM {record.table__()} {joiners.joinClause} \nWHERE {where} {joinsCriteria}" #no 1=1 to prevent "delete all" by mistake if user forget to set values
		#-----
		elif(operation==Database.all):
			statement = f"SELECT * FROM {record.table__()} {record.alias.value()} {joiners.joinClause}"
		#-----
		record.query__ = Query()
		record.query__.parent = record
		record.query__.statement = statement
		record.query__.parameters = []
		record.query__.parameters.extend(record.set.parameters()) # if update extend with fields set values first
		record.query__.parameters.extend(record.values.parameters(record) + record.filter_.parameters(record)) #state.parameters must be reset to empty list [] not None for this operation to work correctly
		record.query__.parameters.extend(joiners.parameters)
		record.query__.operation = operation
		return record.query__
	#--------------------------------------#
	def crudMany(self, operation, record, selected="*", onColumns=None, group_by='', limit=''):
		joiners = Database.joining(record)
		joinsCriteria = joiners.preparedStatement
		#
		fieldsNames = onColumns if onColumns else list(record.values.fields(record))
		whereValues = record.values.where(record, fieldsNames)
		whereFilter = record.filter_.where(record)
		if whereValues and whereFilter:
			where = f"{whereValues} AND {whereFilter}"
		elif whereValues:
			where = whereValues
		else:
			where = whereFilter
		#----- #ordered by occurance propability for single record
		if(operation==Database.insert):
			fieldsValuesClause = f"({', '.join(record.values.fields(record))}) VALUES ({', '.join([self.placeholder() for i in range(0, len(record.values.fields(record)))])})"
			statement = f"INSERT INTO {record.table__()} {fieldsValuesClause}"
		#-----
		elif(operation==Database.update):
			setFields = record.set.setFields()
			statement = f"UPDATE {record.table__()} SET {setFields} {joiners.joinClause} \nWHERE {where} {joinsCriteria}" #no 1=1 to prevent "update all" by mistake if user forget to set filters
		#-----
		elif(operation==Database.delete):
			statement = f"DELETE FROM {record.table__()} {joiners.joinClause} \nWHERE {where} {joinsCriteria}" #no 1=1 to prevent "delete all" by mistake if user forget to set values
		#-----
		record.query__ = Query() # as 
		record.query__.parent = record
		record.query__.statement = statement
		filterParamters = record.filter_.parameters(record)
		for r in record.recordset.iterate():
			#no problem with r.set.parameters() as it's emptied after sucessful update
			params = []
			params.extend(r.set.parameters())
			params.extend(r.values.parameters(r, fieldsNames=fieldsNames) )
			params.extend(filterParamters)
			record.query__.parameters.append(tuple(params))
		record.query__.operation = operation
		return record.query__
	#--------------------------------------#
	def all(self, record): self.executeStatement(self.crud(operation=Database.all, record=record))
	def insert(self, record): self.executeStatement(self.crud(operation=Database.insert, record=record))
	def read(self, operation, record, selected="*", group_by='', order_by='', limit=''): self.executeStatement(self.crud(operation=operation, record=record, selected=selected, group_by=group_by, order_by=order_by, limit=limit))
	def delete(self, operation, record): self.executeStatement(self.crud(operation=operation, record=record))
	def update(self, operation, record):
		self.executeStatement(self.crud(operation=operation, record=record))
		for field, value in record.set.new.items():
			record.setField(field, value)
			record.set.empty()
	def upsert(self, record, onColumns):
		self.executeStatement(self._upsert(operation=Database.upsert, record=record, onColumns=onColumns))
		for field, value in record.set.new.items():
			record.setField(field, value)
			record.set.empty()
	#--------------------------------------#
	def insertMany(self, record): self.executeMany(self.crudMany(operation=Database.insert, record=record))
	def deleteMany(self, record, onColumns): self.executeMany(self.crudMany(operation=Database.delete, record=record, onColumns=onColumns))
	def updateMany(self, record, onColumns):
		self.executeMany(self.crudMany(operation=Database.update, record=record, onColumns=onColumns))
		for r in record.recordset.iterate():
			for field, value in r.set.new.items():
				r.setField(field, value)
				r.set.empty()
	def upsertMany(self, record, onColumns):
		self.executeMany(self._upsertMany(operation=Database.upsert, record=record, onColumns=onColumns))
		for field, value in record.set.new.items():
			record.setField(field, value)
			record.set.empty()
	#--------------------------------------#
	def paginate(self, pageNumber=1, recordsCount=1):
		try:
			pageNumber = int(pageNumber)
			recordsCount = int(recordsCount)
			if(pageNumber and recordsCount):
				offset = (pageNumber - 1) * recordsCount
				return self.limit(offset, recordsCount)
			else:
				return ''
		except Exception as e:
			print(e)
			return ''
	#--------------------------------------#
#================================================================================#
class SQLite(Database):
	def __init__(self, connection):
		Database.__init__(self)
		self.name = "SQLite3"
		self._Database__connection = connection
		self.cursor()
		
	@staticmethod
	def limit(offset=0, recordsCount=1):
		return f"LIMIT {offset}, {recordsCount}"
	
	def upsertStatement(self, operation, record, onColumns):
		keys = list(record.set.new.keys())
		fields = ', '.join(keys)
		updateSet = ', '.join(f'{k} = EXCLUDED.{k}' for k in keys if k not in onColumns.split(','))
		values = ', '.join('?' for _ in keys)
		# Build WHERE clause from filter_ if present
		whereFilter = record.filter_.where(record)
		whereClause = f"\n\t\tWHERE {whereFilter}" if whereFilter else ''
		sql = f"""
		INSERT INTO {record.table__()} ({fields})
		VALUES ({values})
		ON CONFLICT ({onColumns})
		DO UPDATE SET {updateSet}{whereClause}
		"""
		record.query__ = Query()
		record.query__.parent = record
		record.query__.statement = sql
		record.query__.operation = operation
		return record

	def _upsert(self, operation, record, onColumns):
		self.upsertStatement(operation, record, onColumns)
		record.query__.parameters = list(record.set.new.values())
		record.query__.parameters.extend(record.filter_.parameters(record))
		return record.query__

	def _upsertMany(self, operation, record, onColumns):
		self.upsertStatement(operation, record, onColumns)
		for r in record.recordset.iterate():
			params = r.set.parameters() + record.filter_.parameters(record)
			record.query__.parameters.append(tuple(params))
		return record.query__

	### SQLite
	# raw_sql = """
	# INSERT INTO Employees (employee_id, first_name, salary)
	# VALUES (?, ?, ?)
	# ON CONFLICT (employee_id)
	# DO UPDATE SET 
	#     first_name = EXCLUDED.first_name,
	#     salary = EXCLUDED.salary
	# """
#================================================================================#
class Oracle(Database):
	def __init__(self, connection):
		Database.__init__(self)
		self.name = "Oracle"
		self._Database__connection = connection
		self.cursor()
		self._Database__placeholder = ':1' #1 #start of numeric
		self._Database__escapeChar = "'"

	@staticmethod
	def limit(offset=0, recordsCount=1):
		return f"OFFSET {offset} ROWS FETCH NEXT {recordsCount} ROWS ONLY"

	### Oracle
	# raw_sql = """
	# MERGE INTO Employees t
	# USING (SELECT :1 AS employee_id,:1 AS first_name, :1 AS salary FROM dual) s
	# ON (t.employee_id = s.employee_id)
	# WHEN MATCHED THEN
	#     UPDATE SET t.first_name = s.first_name, t.salary = s.salary
	# WHEN NOT MATCHED THEN
	#     INSERT (employee_id, first_name, salary) VALUES (:1, :1, :1)
	# """

	### oracle ai23+
	# raw_sql = """
	# INSERT INTO Employees (employee_id, first_name, salary)
	# VALUES (:1, :2, :3)
	# ON CONFLICT (employee_id)
	# DO UPDATE SET
	#     first_name = :2,
	#     salary = :3
	# """

	def upsertStatement(self, operation, record, onColumns):
		keys = list(record.set.new.keys())
		fields = ', '.join(keys)
		# Oracle uses :1, :2, :3 style placeholders
		source_fields = ', '.join(f':1 AS {k}' for k in keys)
		on_clause = ' AND '.join(f't.{col} = s.{col}' for col in onColumns.split(','))
		update_set = ', '.join(f't.{k} = s.{k}' for k in keys if k not in onColumns.split(','))
		insert_fields = ', '.join(keys)
		insert_values = ', '.join(f's.{k}' for k in keys)

		sql = f"""
		MERGE INTO {record.table__()} t
		USING (SELECT {source_fields} FROM dual) s
		ON ({on_clause})
		WHEN MATCHED THEN
			UPDATE SET {update_set}
		WHEN NOT MATCHED THEN
			INSERT ({insert_fields}) VALUES ({insert_values})
		"""
		record.query__ = Query()
		record.query__.parent = record
		record.query__.statement = sql
		record.query__.operation = operation
		return record

	def _upsert(self, operation, record, onColumns):
		self.upsertStatement(operation, record, onColumns)
		record.query__.parameters = list(record.set.new.values())
		return record.query__

	def _upsertMany(self, operation, record, onColumns):
		self.upsertStatement(operation, record, onColumns)
		for r in record.recordset.iterate():
			params = r.set.parameters()
			record.query__.parameters.append(tuple(params))
		return record.query__
#================================================================================#
class MySQL(Database):
	def __init__(self, connection):
		Database.__init__(self)
		self.name = "MySQL"
		self._Database__connection = connection
		self._Database__placeholder = '%s'  # MySQL uses %s, not ?
		self.cursor()
	def prepared(self, prepared=True):
		self._Database__cursor = self._Database__connection.cursor(prepared=prepared)
	def lastTotalRows(self):
		self._Database__cursor.execute("SELECT FOUND_ROWS() AS last_total_rows")
		(last_total_rows,) = self._Database__cursor.fetchone()
		return last_total_rows

	@staticmethod
	def limit(offset=0, recordsCount=1):
		return f"LIMIT {offset}, {recordsCount}" # f"LIMIT {recordsCount} OFFSET {offset}"

	### MySQL
	# raw_sql = """
	# INSERT INTO Employees (employee_id, first_name, salary)
	# VALUES (%s, %s, %s)
	# ON DUPLICATE KEY UPDATE
	#     first_name = VALUES(first_name),
	#     salary = VALUES(salary)
	# """

	### Or with MySQL 8.0.19+ alias syntax:

	# raw_sql = """
	# INSERT INTO Employees (employee_id, first_name, salary)
	# VALUES (%s, %s, %s) AS new
	# ON DUPLICATE KEY UPDATE
	#     first_name = new.first_name,
	#     salary = new.salary
	# """

	def upsertStatement(self, operation, record, onColumns):
		keys = list(record.set.new.keys())
		fields = ', '.join(keys)
		values = ', '.join('%s' for _ in keys)
		# MySQL uses VALUES(column) to reference the new values
		update_set = ', '.join(f'{k} = VALUES({k})' for k in keys if k not in onColumns.split(','))

		sql = f"""
		INSERT INTO {record.table__()} ({fields})
		VALUES ({values})
		ON DUPLICATE KEY UPDATE {update_set}
		"""
		record.query__ = Query()
		record.query__.parent = record
		record.query__.statement = sql
		record.query__.operation = operation
		return record

	def _upsert(self, operation, record, onColumns):
		self.upsertStatement(operation, record, onColumns)
		record.query__.parameters = list(record.set.new.values())
		return record.query__

	def _upsertMany(self, operation, record, onColumns):
		self.upsertStatement(operation, record, onColumns)
		for r in record.recordset.iterate():
			params = r.set.parameters()
			record.query__.parameters.append(tuple(params))
		return record.query__
#================================================================================#
class Postgres(Database):
	def __init__(self, connection):
		Database.__init__(self)
		self.name = "Postgres"
		self._Database__connection = connection
		self._Database__placeholder = '%s'  # MySQL uses %s, not ?
		self.cursor()
		
	@staticmethod
	def limit(offset=0, recordsCount=1):
		return f"LIMIT {recordsCount} OFFSET {offset}"

	### Postgres
	# raw_sql = """
	# INSERT INTO Employees (employee_id, first_name, salary)
	# VALUES (%s, %s, %s)
	# ON CONFLICT (employee_id)
	# DO UPDATE SET
	#     first_name = EXCLUDED.first_name,
	#     salary = EXCLUDED.salary
	# """

	def upsertStatement(self, operation, record, onColumns):
		keys = list(record.set.new.keys())
		fields = ', '.join(keys)
		values = ', '.join('%s' for _ in keys)
		# Postgres uses EXCLUDED.column to reference the new values
		update_set = ', '.join(f'{k} = EXCLUDED.{k}' for k in keys if k not in onColumns.split(','))

		sql = f"""
		INSERT INTO {record.table__()} ({fields})
		VALUES ({values})
		ON CONFLICT ({onColumns})
		DO UPDATE SET {update_set}
		"""
		record.query__ = Query()
		record.query__.parent = record
		record.query__.statement = sql
		record.query__.operation = operation
		return record

	def _upsert(self, operation, record, onColumns):
		self.upsertStatement(operation, record, onColumns)
		record.query__.parameters = list(record.set.new.values())
		return record.query__

	def _upsertMany(self, operation, record, onColumns):
		self.upsertStatement(operation, record, onColumns)
		for r in record.recordset.iterate():
			params = r.set.parameters()
			record.query__.parameters.append(tuple(params))
		return record.query__
#================================================================================#
class MicrosoftSQL(Database):
	def __init__(self, connection):
		Database.__init__(self)
		self.name = "MicrosoftAzureSQL"
		self._Database__connection = connection
		self.cursor()
		self._Database__cursor.fast_executemany = True
		
	@staticmethod
	def limit(offset=0, recordsCount=1):
		return f"OFFSET {offset} ROWS FETCH NEXT {recordsCount} ROWS ONLY"

	### MSSQL
	# raw_sql = """
	# MERGE INTO Employees AS t
	# USING (SELECT ? AS employee_id, ? AS first_name, ? AS salary) AS s
	# ON (t.employee_id = s.employee_id)
	# WHEN MATCHED THEN
	#     UPDATE SET t.first_name = s.first_name, t.salary = s.salary
	# WHEN NOT MATCHED THEN
	#     INSERT (employee_id, first_name, salary) VALUES (s.employee_id, s.first_name, s.salary);
	# """

	def upsertStatement(self, operation, record, onColumns):
		keys = list(record.set.new.keys())
		fields = ', '.join(keys)
		# MSSQL uses ? placeholders
		source_fields = ', '.join(f'? AS {k}' for k in keys)
		on_clause = ' AND '.join(f't.{col} = s.{col}' for col in onColumns.split(','))
		update_set = ', '.join(f't.{k} = s.{k}' for k in keys if k not in onColumns.split(','))
		insert_fields = ', '.join(keys)
		insert_values = ', '.join(f's.{k}' for k in keys)

		sql = f"""
		MERGE INTO {record.table__()} AS t
		USING (SELECT {source_fields}) AS s
		ON ({on_clause})
		WHEN MATCHED THEN
			UPDATE SET {update_set}
		WHEN NOT MATCHED THEN
			INSERT ({insert_fields}) VALUES ({insert_values});
		"""
		record.query__ = Query()
		record.query__.parent = record
		record.query__.statement = sql
		record.query__.operation = operation
		return record

	def _upsert(self, operation, record, onColumns):
		self.upsertStatement(operation, record, onColumns)
		record.query__.parameters = list(record.set.new.values())
		return record.query__

	def _upsertMany(self, operation, record, onColumns):
		self.upsertStatement(operation, record, onColumns)
		for r in record.recordset.iterate():
			params = r.set.parameters()
			record.query__.parameters.append(tuple(params))
		return record.query__
#================================================================================#
class RecordMeta(type):
	def __getattr__(cls, field):
		# Don't cache Field on class - return new Field each time
		# This prevents Field objects from shadowing instance data attributes
		return Field(cls, field, None)
#================================================================================#
class Record(metaclass=RecordMeta):
	database__	= None
	tableName__ = TableName()
	#--------------------------------------#
	def __init__(self, statement=None, parameters=None, alias=None, **kwargs):
		self.values = Database.values
		self.set = Set(self)
		self.filter_ = Filter(self)
		self.columns = [] #use only after reading data from database #because it's loaded only from the query's result
		self.joins__ = {}
		self.data = {}
		
		self.setupTableNameAndAlias()
		# self.alias = Alias(f"{quoteChar}{self.__class__.__name__}{quoteChar}")

		self.table__ = self.__table

		if(kwargs):
			for key, value in kwargs.items():
				setattr(self, key, value)

		if(statement):
			self.query__ = Query() # must be declared before self.query__(statement)
			self.query__.parent = self
			self.query__.statement = statement
			if(parameters): self.query__.parameters = parameters #if prepared statement's parameters are passed
			#self. instead of Record. #change the static field self.__database for inherited children classes
			if(str((statement.strip())[:6]).lower()=="select"):
				self.query__.operation = Database.read
			if(len(self.query__.parameters) and type(self.query__.parameters[0]) in (list, tuple)):
				self.database__.executeMany(self.query__)
			else:
				self.database__.executeStatement(self.query__)
			Database.orm.map(self)
	#--------------------------------------#
	def __getattr__(self, name):
		# if(name=="custom"): return self.__dict__["custom"]
		try:
			return self.__dict__["data"][name]
		except:
			try:
				return object.__getattribute__(self, name)
			# except:
			# 	return None
			# except KeyError:
			# 		raise AttributeError(f"'{self.__class__.__name__}' has no field '{name}'")
			except KeyError:
				# Only return None if columns haven't been loaded yet
				if self.columns and name not in self.columns:
					raise AttributeError(f"'{self.__class__.__name__}' has no field '{name}'")
				return None

	def __setattr__(self, name, value):
		# if(name=="custom"): self.__dict__["custom"] = value
		if(type(value) in [str, int, float, datetime, bool]):
			self.__dict__["data"][name] = value
		else:
			object.__setattr__(self, name, value)
	#--------------------------------------#
	def setupTableNameAndAlias(self):
		quoteChar = '' #self.database__.escapeChar()
		parentClassName = self.__class__.__bases__[0].__name__
		if(parentClassName == "Record" or parentClassName.startswith('__')):
			self.tableName__ = TableName(self.__class__.__name__)
		else:
			self.tableName__ = TableName(f"{quoteChar}{parentClassName}{quoteChar}")
		self.alias = Alias(f"{quoteChar}{self.__class__.__name__}{quoteChar}")
	#--------------------------------------#
	def __table(self):
		quoteChar = '' #self.database__.escapeChar()
		return f"{quoteChar}{self.tableName__.value()}{quoteChar}"
	#--------------------------------------#
	def __repr__(self):
		items = list(self.data.items())[:5]  # Show first 5 fields
		fields = ', '.join(f'{k}={v!r}' for k, v in items)
		if len(self.data) > 5:
			fields += ', ...'
		return f"<{self.__class__.__name__} {fields}>"
	#--------------------------------------#	
	def id(self): return self.query__.result.lastrowid
	#--------------------------------------#
	def rowsCount(self): return self.query__.result.count
	#--------------------------------------#
	# def getField(self, fieldName): return self.__dict__[fieldName] #get field without invoke __getattr__
	# def setField(self, fieldName, fieldValue): self.__dict__[fieldName]=fieldValue #set field without invoke __setattr__
	def getField(self, fieldName): return self.data[fieldName] #get field without invoke __getattr__
	def setField(self, fieldName, fieldValue): self.data[fieldName]=fieldValue #set field without invoke __setattr__
	#--------------------------------------#
	def filter(self, *args, **kwargs): return self.filter_.filter(*args, **kwargs)
	#--------------------------------------#
	def in_subquery(self, **kwargs):
		self.filter_.in_subquery(**kwargs)
		return self
	def exists(self, **kwargs):
		self.filter_.exists(**kwargs)
		return self
	def not_exists(self, **kwargs):
		self.filter_.not_exists(**kwargs)
		return self
	def in_(self, **kwargs):
		self.filter_.in_(**kwargs)
		return self
	def not_in(self, **kwargs):
		self.filter_.not_in(**kwargs)
		return self
	def like(self, **kwargs):
		self.filter_.like(**kwargs)
		return self
	def is_null(self, **kwargs):
		self.filter_.is_null(**kwargs)
		return self
	def is_not_null(self, **kwargs):
		self.filter_.is_not_null(**kwargs)
		return self
	def between(self, **kwargs):
		self.filter_.between(**kwargs)
		return self	
	def gt(self, **kwargs):
		self.filter_.gt(**kwargs)
		return self
	def ge(self, **kwargs):
		self.filter_.ge(**kwargs)
		return self
	def lt(self, **kwargs):
		self.filter_.lt(**kwargs)
		return self
	def le(self, **kwargs):
		self.filter_.le(**kwargs)
		return self
	#--------------------------------------#
	def set_(self, **kwargs):
		for field, value in kwargs.items():
			setattr(self.set, field, value)
		return self
	#--------------------------------------#
	#def __str__(self): pass
	#--------------------------------------#
	def __iter__(self):
		self.__iterationIndex = Dummy(0)
		self.__iterationBound = Dummy(len(self.recordset.iterate()))
		return self
	#--------------------------------------#
	def __next__(self): #python 3 compatibility
		if(self.__iterationIndex.value < self.__iterationBound.value):
			currentItem = self.recordset.iterate()[self.__iterationIndex.value]
			self.__iterationIndex.value += 1
			return currentItem
		else:
			del(self.__iterationIndex) # to prevent using them as database's column
			del(self.__iterationBound) # to prevent using them as database's column
			raise StopIteration
	#--------------------------------------#
	def next(self): return self.__next__() #python 2 compatibility
	#--------------------------------------#
	def insert(self): self.database__.insert(record=self)
	# def read(self, selected="*", group_by='', order_by='', limit=''): self.database__.read(Database.read, record=self, selected=selected, group_by=group_by, order_by=order_by, limit=limit)
	def read(self, selected="*", group_by='', order_by='', limit='', **kwargs): return self.filter_.read(selected, group_by, order_by, limit, **kwargs)
	def update(self): self.database__.update(Database.update, record=self)
	def delete(self): self.database__.delete(Database.delete, record=self)
	def all(self): self.database__.all(record=self)
	def upsert(self, onColumns): self.database__.upsert(record=self, onColumns=onColumns)
	def commit(self): self.database__.commit()
	#--------------------------------------#
	def join(self, table, fields): self.joins__[table.alias.value()] = Join(table, fields)
	#--------------------------------------#
	def rightJoin(self, table, fields): self.joins__[table.alias.value()] = Join(table, fields, ' RIGHT JOIN ')
	#--------------------------------------#
	def leftJoin(self, table, fields): self.joins__[table.alias.value()] = Join(table, fields, ' LEFT JOIN ')
	#--------------------------------------#
	def toDict(self): return self.data
	#--------------------------------------#
	def toList(self): return list(self.toDict().values())
	#--------------------------------------#
	def limit(self, pageNumber=1, recordsCount=1): return self.database__.paginate(pageNumber, recordsCount)
	#--------------------------------------#
#================================================================================#
class Recordset:
	def __init__(self):
		self.__records = [] #mapped objects from records
		self.rowsCount = 0
		self.data = [] # extended in ORM
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
	def update(self, onColumns=None):
		if(self.firstRecord()):  self.firstRecord().database__.updateMany(self.firstRecord(), onColumns=onColumns)
	def delete(self, onColumns=None):
		if(self.firstRecord()):  self.firstRecord().database__.deleteMany(self.firstRecord(), onColumns=onColumns)
	def upsert(self, onColumns=None):
		if(self.firstRecord()):  self.firstRecord().database__.upsertMany(self.firstRecord(), onColumns=onColumns)
	def commit(self):
		if(self.firstRecord()):  self.firstRecord().database__.commit()
	#--------------------------------------#
	def toLists(self):
		data = []
		for record in self.iterate():
			data.append(record.toList())
		return data
	#--------------------------------------#
	def toDicts(self):
		return self.data
	#--------------------------------------#
#================================================================================#