#!/usr/bin/python

#version: 202601192302

# free Record from all other instances
# batch size
#================================================================================#
from string import Template #used for secure id
from datetime import datetime
import re #used for secure id
#================================================================================#
#python2 has two classes represent strings (str) and (unicode)
#python3 has only one class represents string (str) and has no (unicode) class
#the following code is for python3 and python2 compatibility-back
#type(value) in [str,] only will ignore unicode attributes/values if not casting
# using str() explicity when assigning object.attribute = value of unicode()
try:
	a = unicode()
except Exception as e:
	unicode = str

NoneType = type(None)
#================================================================================#
def createTableClass(tableName, base=(object, ), attributesDictionary={}):
	return type(str(tableName), base, attributesDictionary) #str() to prevent any error from missed type casting/conversion
#================================================================================#
class Field:
	def __init__(self, cls, name, value):
		self.cls = cls
		self.name = name
		self.value = value
		self.placeholder = '?'

	def _field_name(self):
		return f"{self.cls.__name__}.{self.name}"

	def _resolve_value(self, value):
		"""Returns (sql_value, parameters)"""
		if type(value) == Field:
			return (f"{value.cls.__name__}.{value.name}", [])
		elif isinstance(value, Exp):
			return (value.value, value.parameters)
		else:
			return (self.placeholder, [value])

	def __eq__(self, value):
		sql_val, params = self._resolve_value(value)
		return Exp(f"{self._field_name()} = {sql_val}", params)
	def __ne__(self, value):
		sql_val, params = self._resolve_value(value)
		return Exp(f"{self._field_name()} <> {sql_val}", params)
	def __gt__(self, value):
		sql_val, params = self._resolve_value(value)
		return Exp(f"{self._field_name()} > {sql_val}", params)
	def __ge__(self, value):
		sql_val, params = self._resolve_value(value)
		return Exp(f"{self._field_name()} >= {sql_val}", params)
	def __lt__(self, value):
		sql_val, params = self._resolve_value(value)
		return Exp(f"{self._field_name()} < {sql_val}", params)
	def __le__(self, value):
		sql_val, params = self._resolve_value(value)
		return Exp(f"{self._field_name()} <= {sql_val}", params)
	def __add__(self, value):
		sql_val, params = self._resolve_value(value)
		return Exp(f"{self._field_name()} + {sql_val}", params)
	def __sub__(self, value):
		sql_val, params = self._resolve_value(value)
		return Exp(f"{self._field_name()} - {sql_val}", params)
	def __mul__(self, value):
		sql_val, params = self._resolve_value(value)
		return Exp(f"{self._field_name()} * {sql_val}", params)
	def __truediv__(self, value):
		sql_val, params = self._resolve_value(value)
		return Exp(f"{self._field_name()} / {sql_val}", params)

	# SQL-specific methods
	def is_null(self):
		return Exp(f"{self._field_name()} IS NULL", [])
	def is_not_null(self):
		return Exp(f"{self._field_name()} IS NOT NULL", [])
	def like(self, pattern):
		return Exp(f"{self._field_name()} LIKE {self.placeholder}", [pattern])
	def in_(self, values):
		placeholders = ', '.join([self.placeholder] * len(values))
		return Exp(f"{self._field_name()} IN ({placeholders})", list(values))
	def not_in(self, values):
		placeholders = ', '.join([self.placeholder] * len(values))
		return Exp(f"{self._field_name()} NOT IN ({placeholders})", list(values))
	def between(self, low, high):
		return Exp(f"{self._field_name()} BETWEEN {self.placeholder} AND {self.placeholder}", [low, high])

	# Subquery methods - take a Record instance and generate SQL
	def in_subquery(self, record, selected="*"):
		"""field IN (SELECT ... FROM ...)"""
		query = Database.crud(operation=Database.read, record=record, mode='filter_', selected=selected, group_by='', limit='')
		return Exp(f"{self._field_name()} IN (\n{query.statement}\n)", query.parameters)

	def not_in_subquery(self, record, selected="*"):
		"""field NOT IN (SELECT ... FROM ...)"""
		query = Database.crud(operation=Database.read, record=record, mode='filter_', selected=selected, group_by='', limit='')
		return Exp(f"{self._field_name()} NOT IN (\n{query.statement}\n)", query.parameters)

	@staticmethod
	def exists(record, selected="1"):
		"""EXISTS (SELECT ... FROM ... WHERE ...)"""
		query = Database.crud(operation=Database.read, record=record, mode='filter_', selected=selected, group_by='', limit='')
		return Exp(f"EXISTS (\n{query.statement}\n)", query.parameters)

	@staticmethod
	def not_exists(record, selected="1"):
		"""NOT EXISTS (SELECT ... FROM ... WHERE ...)"""
		query = Database.crud(operation=Database.read, record=record, mode='filter_', selected=selected, group_by='', limit='')
		return Exp(f"NOT EXISTS (\n{query.statement}\n)", query.parameters)
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
class UserID(SpecialValue):
	def __init__(self, value=None):
		self.user_id = value
#--------------------------------------#
class Expression(SpecialValue):
	def __init__(self, value):
		self.__value = value
		SpecialValue.__init__(self, self.__value)
	def placeholder(self, placeholder): return self.__value
	def fltr(self, field, placeholder): return f"{field} = {self.__value}"  # Add this
	def parametersAppend(self, parameters): pass  # Add this - no params to append
	def __str__(self): return self.__value
	def __repr__(self): return self.__value
	def __and__(self, other): return Expression(f"({self.value()} AND {other.value()})")
	def __or__(self, other): return Expression(f"({self.value()} OR {other.value()})")
#--------------------------------------#
class Exp():
	def __init__(self, value, parameters):
		self.value = value
		self.parameters = parameters
	def fltr(self, field, placeholder): return self.value
	def parametersAppend(self, parameters): parameters.extend(self.parameters)
	def __str__(self): return self.value
	def __repr__(self): return self.value
	def __and__(self, other): return Exp(f"({self.value} AND {other.value})", self.parameters + other.parameters)
	def __or__(self, other): return Exp(f"({self.value} OR {other.value})", self.parameters + other.parameters)
# #--------------------------------------#
class SubQuery(SpecialValue):
	def __init__(self, value):
		self.__value = value
		SpecialValue.__init__(self, self.__value)
	def operator(self): return ""
	def fltr(self, field, placeholder): 
		self.query = Database.crud(operation=Database.read, record=self.value(), mode='filter_', selected="employee_id", group_by='', limit='')
		return f"{field} IN (\n{self.query.statement}\n) "
	def parametersAppend(self, parameters): parameters.extend(self.query.parameters)
#--------------------
class EXISTS(SpecialValue):
	def __init__(self, value):
		self.__value = value
		SpecialValue.__init__(self, self.__value)
	def operator(self): return ""
	def fltr(self, field, placeholder): 
		self.query = Database.crud(operation=Database.read, record=self.value(), mode='filter_', selected="employee_id", group_by='', limit='')
		return f"EXISTS (\n{self.query.statement}\n) "
	def parametersAppend(self, parameters): parameters.extend(self.query.parameters)
#--------------------
class NOTEXISTS(SpecialValue):
	def __init__(self, value):
		self.__value = value
		SpecialValue.__init__(self, self.__value)
	def operator(self): return ""
	def fltr(self, field, placeholder): 
		self.query = Database.crud(operation=Database.read, record=self.value(), mode='filter_', selected="employee_id", group_by='', limit='')
		return f"NOT EXISTS (\n{self.query.statement}\n) "
	def parametersAppend(self, parameters): parameters.extend(self.query.parameters)
#--------------------
class LIKE(SpecialValue):
	def __init__(self, value):
		self.__value = value.replace("*","%")
		SpecialValue.__init__(self, self.__value)
	def operator(self): return " LIKE "
	def fltr(self, field, placeholder): return f"{field} LIKE {placeholder}"
	def parametersAppend(self, parameters): parameters.append(self.value())
#--------------------
class IN(SpecialValue):
	def operator(self): return " IN "
	def placeholder(self, placeholder): 
		__placeholder = ','.join([placeholder]*len(self._SpecialValue__value))
		return f"({__placeholder})"
	def fltr(self, field, placeholder): return f"{field} IN {self.placeholder(placeholder)}"
	def parametersAppend(self, parameters): parameters.extend(self.value())
#--------------------
class NOT_IN(SpecialValue):
	def operator(self): return " NOT IN "
	def placeholder(self, placeholder):
		__placeholder = ','.join([placeholder]*len(self._SpecialValue__value))
		return f"({__placeholder})"
	def fltr(self, field, placeholder): return f"{field} NOT IN {self.placeholder(placeholder)}"
	def parametersAppend(self, parameters): parameters.extend(self.value())
#--------------------
class BETWEEN(SpecialValue):
	def __init__(self, minValue, maxValue):
		self.__minValue = minValue
		self.__maxValue = maxValue

	def value(self): return [self.__minValue, self.__maxValue]
	def operator(self): return " BETWEEN "
	def placeholder(self, placeholder): return placeholder + " AND " + placeholder
	def fltr(self, field, placeholder): return f"{field} BETWEEN {self.placeholder(placeholder)}"
	def parametersAppend(self, parameters): parameters.extend(self.value())
#--------------------
class gt(SpecialValue):
	def operator(self): return " > "
	def fltr(self, field, placeholder): return f"{field} > {placeholder}"
	def parametersAppend(self, parameters): parameters.append(self.value())
#--------------------
class ge(SpecialValue):
	def operator(self): return " >= "
	def fltr(self, field, placeholder): return f"{field} >= {placeholder}"
	def parametersAppend(self, parameters): parameters.append(self.value())
#--------------------
class lt(SpecialValue):
	def operator(self): return " < "
	def fltr(self, field, placeholder): return f"{field} < {placeholder}"
	def parametersAppend(self, parameters): parameters.append(self.value())
#--------------------
class le(SpecialValue):
	def operator(self): return " <= "
	def fltr(self, field, placeholder): return f"{field} <= {placeholder}"
	def parametersAppend(self, parameters): parameters.append(self.value())
#--------------------
class NULL(SpecialValue, dict): #to make it json serializable using jsonifiy
	def operator(self, operation=2):
		if(operation==Database.update):
			return "="
		else:
			return " IS "
	def placeholder(self, placeholder): return "NULL"
	def __str__(self): return "NULL"
	def __repr__(self): return "NULL"
	def __eq__(self, other): return "NULL"==other
	def fltr(self, field, placeholder): return f"{field} IS NULL"
	def parametersAppend(self, parameters): return parameters
#--------------------
class NOT_NULL(SpecialValue):
	def __init__(self):
		self.__value = "NOT NULL"
		SpecialValue.__init__(self, self.__value)
	def operator(self): return " IS "
	def placeholder(self, placeholder): return "NOT NULL"
	def __str__(self): return "NOT NULL"
	def __repr__(self): return "NOT NULL"
	def __eq__(self, other): return "NOT NULL"==other
	def fltr(self, field, placeholder): return f"{field} IS NOT NULL"
	def parametersAppend(self, parameters): return parameters
# #--------------------
class Join():
	def __init__(self, object, fields, type=' INNER JOIN ', value=None):
		self.type = type
		self.object = object
		self.fields = fields
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
				statement += f"{field}={value.placeholder(None)}, "  # Expression directly
			else:
				statement += f"{field}={self.parent.database__.placeholder()}, "
		return statement[:-2]
	
	def parameters(self, fieldsNames=None):
		fields = fieldsNames if(fieldsNames) else list(self.new.keys())
		parameters = []
		for field in fields:
			value = self.new[field]
			if not isinstance(value, Expression):  # Skip expressions
				parameters.append(value) # 			if type(value) != Expression:
		return parameters

	def __setattr__(self, name, value):
		# if(name=="custom"): self.__dict__["custom"] = value
		if(type(value) in [NoneType, str, int, float, datetime, unicode] or isinstance(value, Expression)):
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
			if(type(value) in [str, int, float, datetime, unicode]):
				fields.append(field)
		return fields
	#--------------------------------------#
	@staticmethod
	def where(record):
		#getStatement always used to collect exact values not filters so no "NOT NULL", "LIKE", ... but only [str, unicode, int, float, and datetime] values.
		statement = ''
		fields = Values.fields(record)
		for field in fields:
			value = record.getField(field)
			placeholder = record.database__.placeholder()
			statement += f"{record.alias.value()}.{field} = {placeholder} AND "
		return statement[:-5]
	#--------------------------------------#
	@staticmethod
	def parameters(record, fieldsNames=None):
		#getStatement always used to collect exact values not filters so no "NOT NULL", "LIKE", ... but only [str, unicode, int, float, and datetime] values.
		fields = fieldsNames if (fieldsNames) else Values.fields(record)
		parameters = []
		for field in fields:
			value = record.getField(field)
			parameters.append(value)
		return parameters
	#--------------------------------------#
#================================================================================#
class Filter:
	def __init__(self, parent):
		self.__dict__['parent'] = parent
		self.empty()

	def empty(self):
		self.__where = ''
		self.__parameters = []
	
	def filter(self, **kwargs):
		for field, value in kwargs.items():
			self.addCondition(field, value)
		return self
	def read(self, selected="*", group_by='', limit=''): self.parent.database__.read(operation=Database.read,  record=self.parent, mode='filter_', selected=selected, group_by=group_by, limit=limit)
	def delete(self): self.parent.database__.delete(operation=Database.delete, record=self.parent, mode='filter_')
	def update(self): self.parent.database__.update(operation=Database.update, record=self.parent, mode='filter_')

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
	
	def addCondition(self, field, value):
		placeholder = self.parent.database__.placeholder()
		field = f"{self.parent.alias.value()}.{field}"
		if(type(value) in [str, unicode, int, float, datetime]):
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
		where = self.parent.values.where(self.parent)
		where = f"{where} AND " if (where) else ""
		# Return combined where without modifying self.__where
		combined_where = where + self.__where
		# print(">>>>>>>>>>>>>>>>>>>>", combined_where)
		return combined_where[:-5]
	
	#This 'Filter.parameters' function follow the same signature/interface of 'Values.parameters' function design pattern
	#Both are used interchangeably in 'Database.__crud' function
	def parameters(self, record=None):
		parameters = []
		parameters = self.parent.values.parameters(self.parent)
		# Return combined parameters without modifying self.__parameters
		# print(">>>>>>>>>>>>>>>>>>>>", parameters + self.__parameters)
		return parameters + self.__parameters
	#--------------------------------------#
	# def SubQuery(self, **kwargs):
	# 	for field, value in kwargs.items():
	# 		self.filter(_=Field(self.parent.__class__, field, None).in_subquery(value))
	# 	return self
	# def EXISTS(self, **kwargs):
	# 	for field, value in kwargs.items():
	# 		self.filter(_=Field.exists(value))
	# 	return self
	# def NOT_EXISTS(self, **kwargs):
	# 	for field, value in kwargs.items():
	# 		self.filter(_=Field.not_exists(value))
	# 	return self
	# def IN(self, **kwargs):
	# 	for field, value in kwargs.items():
	# 		self.filter(_=Field(self.parent.__class__, field, None).in_(value))
	# 	return self
	# def NOT_IN(self, **kwargs):
	# 	for field, value in kwargs.items():
	# 		self.filter(_=Field(self.parent.__class__, field, None).not_in(value))
	# 	return self
	# def LIKE(self, **kwargs):
	# 	for field, value in kwargs.items():
	# 		self.filter(_=Field(self.parent.__class__, field, None).like(value))
	# 	return self
	# def NULL(self, **kwargs):
	# 	for field, value in kwargs.items():
	# 		self.filter(_=Field(self.parent.__class__, field, value).is_null())
	# 	return self
	# def NOT_NULL(self, **kwargs):
	# 	for field, value in kwargs.items():
	# 		self.filter(_=Field(self.parent.__class__, field, None).is_not_null())
	# 	return self
	# def BETWEEN(self, **kwargs):
	# 	for field, value in kwargs.items():
	# 		self.filter(_=Field(self.parent.__class__, field, None).between(value[0], value[1]))
	# 	return self
	# def gt(self, **kwargs):
	# 	for field, value in kwargs.items():
	# 		self.filter(_=Field(self.parent.__class__, field, None) > value)
	# 	return self
	# def ge(self, **kwargs):
	# 	for field, value in kwargs.items():
	# 		self.filter(_=Field(self.parent.__class__, field, None) >= value)
	# 	return self
	# def lt(self, **kwargs):
	# 	for field, value in kwargs.items():
	# 		self.filter(_=Field(self.parent.__class__, field, None) < value)
	# 	return self
	# def le(self, **kwargs):
	# 	for field, value in kwargs.items():
	# 		self.filter(_=Field(self.parent.__class__, field, None) <= value)
	# 	return self
	#--------------------------------------#
	def SubQuery(self, **kwargs):
		for field, value in kwargs.items():
			self.addCondition(field, SubQuery(value))
		return self
	def EXISTS(self, **kwargs):
		for field, value in kwargs.items():
			self.addCondition(field, EXISTS(value))
		return self
	def NOT_EXISTS(self, **kwargs):
		for field, value in kwargs.items():
			self.addCondition(field, NOT_EXISTS(value))
		return self
	def IN(self, **kwargs):
		for field, value in kwargs.items():
			self.addCondition(field, IN(value))
		return self
	def NOT_IN(self, **kwargs):
		for field, value in kwargs.items():
			self.addCondition(field, NOT_IN(value))
		return self
	def LIKE(self, **kwargs):
		for field, value in kwargs.items():
			self.addCondition(field, LIKE(value))
		return self
	def NULL(self, **kwargs):
		for field, value in kwargs.items():
			self.addCondition(field, NULL())
		return self
	def NOT_NULL(self, **kwargs):
		for field, value in kwargs.items():
			self.addCondition(field, NOT_NULL())
		return self
	def BETWEEN(self, **kwargs):
		for field, value in kwargs.items():
			self.addCondition(field, BETWEEN(value[0], value[1]))
		return self	
	def gt(self, **kwargs):
		for field, value in kwargs.items():
			self.addCondition(field, gt(value))
		return self
	def ge(self, **kwargs):
		for field, value in kwargs.items():
			self.addCondition(field, ge(value))
		return self
	def lt(self, **kwargs):
		for field, value in kwargs.items():
			self.addCondition(field, lt(value))
		return self
	def le(self, **kwargs):
		for field, value in kwargs.items():
			self.addCondition(field, le(value))
		return self
	#--------------------------------------#
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
	def joining(record, mode):
		joiners = Joiners()
		quoteChar = '' #cls.escapeChar()
		for key, join in record.joins__.items():
			#" INNER JOIN Persons pp ON "
			main_join = f"{join.type}{join.object.table__()} {join.object.alias.value()} ON "
			for foreign_key, primary_key in join.fields.items():
				#"	cc.fk=pp.pk AND "
				main_join += f"\n\t{record.alias.value()}.{quoteChar}{foreign_key}{quoteChar}={join.object.alias.value()}.{quoteChar}{primary_key}{quoteChar} AND "
			main_join = "\n" + main_join[:-5]
			joiners.joinClause += main_join
			#--------------------
			statement = join.object.getMode(mode).where(join.object)
			if(statement): joiners.preparedStatement += f" AND {statement}"
			joiners.parameters.extend(join.object.getMode(mode).parameters(join.object))
			#--------------------
			child_joiners = Database.joining(join.object, mode)
			joiners.joinClause += child_joiners.joinClause
			joiners.preparedStatement += child_joiners.preparedStatement
			joiners.parameters.extend(child_joiners.parameters)

		return joiners
	#--------------------------------------#
	@staticmethod
	def secure(record):
		__db__ = record.database__
		queryStatement = record.query__.statement

		#aa = re.search('{([a-zA-Z0-9_]+)}', query, re.IGNORECASE)
		#if (aa): print(a.groups(1))
		tablesNames = re.findall(r"\${([a-zA-Z0-9_]+)}", queryStatement)

		tables_names_placeholders = ', '.join('?'*len(tablesNames))
		
		loadViews = f"""SELECT V.view, V.table_name, V.crud_statement
		FROM Policys_Views_Authoritys PVA
		INNER JOIN Users_Policys UP ON PVA.policy_fk = UP.policy_fk
		INNER JOIN Views V ON PVA.view_fk = V.pk
		WHERE UP.user_fk = ?
			AND V.table_name IN ({tables_names_placeholders})"""

		#https://forums.mysql.com/read.php?100,630131,630158#msg-630158
		secureViewsStatement = {}
		if(tables_names_placeholders):
			
			class Views(Record): pass
			views = Views()
			# views.recordset = Recordset()
			views.query__ = Query()
			views.query__.operation = Database.read
			views.query__.parent = views
			views.query__.statement = loadViews

			# mysql.connector.errors.InterfaceError
			# InterfaceError: No result set to fetch from.
			# No parameters were provided with the prepared statement
			# "views.query__.parameters" was written by mistake "views.parameters"

			views.query__.parameters = [record.secure__.user_id] + tablesNames
			__db__.executeStatement(views.query__)
			# Database.orm.map(views) #orm moved inside executeStatement method

			#print(views.recordset.count())
			for view in views:
				#print(view.columns)
					secureViewsStatement[str(view.table_name)] = f'({str(view.crud_statement)} \n)'
			for tableName in tablesNames:
				if(tableName not in secureViewsStatement):
					secureViewsStatement[tableName] = f"{__db__.escapeChar()}{tableName}{__db__.escapeChar()}"

			#print(secureViewsStatement)

			queryStatementTemplate = Template(queryStatement)
			secureQuerySatement = queryStatementTemplate.safe_substitute(secureViewsStatement)
			secureQuerySatement = secureQuerySatement.replace("$|user.pk|", str(record.secure__.user_id))
			record.query__.statement = secureQuerySatement
			#return secureQuery
	#--------------------------------------#
	def executeStatement(self, query):
		if(query.statement):
			print(f"<s|{'-'*3}")
			print(" > Execute statement: ", query.statement)
			print(" > Execute parameters: ", query.parameters)
			print(f"{'-'*3}|e>")
			#
			self.__cursor.execute(query.statement, tuple(query.parameters))
			self.operationsCount +=1
			#
			count=0
			columns = []

			if(query.operation in [Database.all, Database.read]):
				# for index, column in enumerate(self.__cursor.description): columns.append(column[0].lower())
				columns = [column[0].lower() for column in self.__cursor.description] #lower() to low column names
				query.result.columns = columns
				
				parent = query.parent
				parent.recordset = Recordset()
				while True:
					fetchedRows = [dict(zip(columns, row)) for row in self.__cursor.fetchmany(10000)]
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
		print(f"<s|{'-'*3}")
		print(" > Execute statement: ", query.statement)
		print(" > Execute parameters: ", query.parameters)
		print(f"{'-'*3}|e>")
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
	@staticmethod
	def crud(operation, record, mode, selected="*", group_by='', limit=''):
		current = []
		where = record.getMode(mode).where(record)
		parameters = record.getMode(mode).parameters(record)
		joiners = Database.joining(record, mode)
		joinsCriteria = joiners.preparedStatement
		#----- #ordered by occurance propability for single record
		if(operation==Database.read):
			statement = f"SELECT {selected} FROM {record.table__()} {record.alias.value()} {joiners.joinClause} \nWHERE {where if (where) else '1=1'} {joinsCriteria} \n{group_by} {limit}"
		#-----
		elif(operation==Database.insert):
			fieldsValuesClause = f"({', '.join(record.values.fields(record))}) VALUES ({', '.join([record.database__.placeholder() for i in range(0, len(record.values.fields(record)))])})"
			statement = f"INSERT INTO {record.table__()} {fieldsValuesClause}"
		#-----
		elif(operation==Database.update):
			current = parameters
			setFields = record.set.setFields()
			parameters = record.set.parameters()
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
		record.query__.parameters = parameters
		record.query__.parameters.extend(current) #state.parameters must be reset to empty list [] not None for this operation to work correctly
		record.query__.parameters.extend(joiners.parameters)
		if(record.secure__.user_id): Database.secure(record)
		record.query__.operation = operation
		return record.query__
	#--------------------------------------#
	def __crudMany(self, operation, record, selected="*", group_by='', limit=''):
		joiners = Database.joining(record, 'values')
		joinsCriteria = joiners.preparedStatement
		#
		where = record.values.where(record)
		#----- #ordered by occurance propability for single record
		if(operation==Database.insert):
			fieldsValuesClause = f"({', '.join(record.values.fields(record))}) VALUES ({', '.join([self.database__.placeholder() for i in range(0, len(record.values.fields(record)))])})"
			statement = f"INSERT INTO {record.table__()} {fieldsValuesClause}"
		#-----
		elif(operation==Database.update):
			setFields = record.set.setFields()
			statement = f"UPDATE {record.table__()} SET {setFields} {joiners.joinClause} \nWHERE {where} {joinsCriteria}" #no 1=1 to prevent "update all" by mistake if user forget to set filters
		#-----
		elif(operation==Database.delete):
			statement = f"DELETE FROM {record.table__()} {joiners.joinClause} \nWHERE {where} {joinsCriteria}" #no 1=1 to prevent "delete all" by mistake if user forget to set values
		#-----
		fieldsNames = list(record.values.fields(record))
		query = Query() # as 
		query.statement = statement
		for r in record.recordset.iterate():
			params = r.set.parameters() + r.values.parameters(r, fieldsNames=fieldsNames) #no problem withr.set.parameters() as it's emptied after sucessful update
			query.parameters.append(tuple(params))
		#if(record.secure__.user_id): self.secure(record) #not implemented for many (insert and update)
		query.operation = operation
		record.recordset.rowsCount = self.executeMany(query)
	#--------------------------------------#
	def all(self, record, mode): self.executeStatement(self.crud(operation=Database.all, record=record, mode=mode))
	def insert(self, record, mode): self.executeStatement(self.crud(operation=Database.insert, record=record, mode=mode))
	def read(self, operation, record, mode, selected="*", group_by='', limit=''): self.executeStatement(self.crud(operation=operation, record=record, mode=mode, selected=selected, group_by=group_by, limit=limit))
	def delete(self, operation, record, mode): self.executeStatement(self.crud(operation=operation, record=record, mode=mode))
	def update(self, operation, record, mode):
		self.executeStatement(self.crud(operation=operation, record=record, mode=mode))
		for field, value in record.set.new.items():
			record.setField(field, value)
			record.set.empty()
	#--------------------------------------#
	def insertMany(self, record): self.__crudMany(operation=Database.insert, record=record)
	def deleteMany(self, record): self.__crudMany(operation=Database.delete, record=record)
	def updateMany(self, record): 
		self.__crudMany(operation=Database.update, record=record)
		for r in record.recordset.iterate():
			for field, value in r.set.new.items():
				r.setField(field, value)
				r.set.empty()
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
	def getCopyInstance(self, record, base=(object, ), attributesDictionary={}):
		if(base):
			Copy = createTableClass(record.__class__.__name__, base, attributesDictionary)
			copy = Copy()
		else:
			copy = record.__class__() #object = Record() #bug
		
		for attributeName, attributeValue in record.__dict__.items(): #for a in dir(r): println(a)
			# any other type will be execluded Class type, None type and others ...
			if(type(attributeValue) in [NoneType, str, unicode, int, float, datetime]):
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
	def __init__(self, connection):
		Database.__init__(self)
		self._Database__connection = connection
		self.cursor()
		
	@staticmethod
	def limit(offset=0, recordsCount=1):
		return f"LIMIT {offset}, {recordsCount}"
#================================================================================#
class Oracle(Database):
	def __init__(self, connection):
		Database.__init__(self)
		self._Database__connection = connection
		self.cursor()
		self._Database__placeholder = ':1' #1 #start of numeric
		self._Database__escapeChar = "'"

	@staticmethod
	def limit(offset=0, recordsCount=1):
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
	def limit(offset=0, recordsCount=1):
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
	def limit(offset=0, recordsCount=1):
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
			self._Database__connection = pyodbc.connect(Driver='{ODBC Driver 17 for SQL Server}', database=self._Database__database, user=self._Database__username, password=self._Database__password, host=self._Database__host)
			#self._Database__connection = pyodbc.connect('Driver={ODBC Driver 17 for SQL Server};Server=tcp:example.database.windows.net,1433;Database=example_db;;;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;')
			self.cursor()
#================================================================================#
class RecordMeta(type):
	def __getattr__(cls, field):
		# Don't cache Field on class - return new Field each time
		# This prevents Field objects from shadowing instance data attributes
		return Field(cls, field, None)
#================================================================================#
class Record(metaclass=RecordMeta):
	database__	= None
	representer__ = Representer()
	tableName__ = TableName()
	#--------------------------------------#
	def __init__(self, statement=None, parameters=None, alias=None, secure_by_user_id=None, **kwargs):
		self.values = Database.values
		self.set = Set(self)
		self.filter_ = Filter(self)
		# self.recordset = Recordset()
		self.columns = [] #use only after reading data from database #because it's loaded only from the query's result
		self.joins__ = {}
		self.secure__ = UserID(secure_by_user_id)
		self.data = {}
		
		self.setupTableNameAndAlias()
		# self.alias = Alias(f"{quoteChar}{self.__class__.__name__}{quoteChar}")

		if(self.secure__.user_id):
			self.table__ = self.__tableSecure
		else:
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
			if(self.secure__.user_id): self.database__.secure(self)
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
			except:
				return None

	def __setattr__(self, name, value):
		# if(name=="custom"): self.__dict__["custom"] = value
		if(type(value) in [str, int, float, datetime, unicode]):
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
	def __tableSecure(self):
		quoteChar = '' #self.database__.escapeChar()
		return f"{quoteChar}${{{self.tableName__.value()}}}{quoteChar}"
	#--------------------------------------#
	def id(self): return self.query__.result.lastrowid
	#--------------------------------------#
	def rowsCount(self): return self.query__.result.count
	#--------------------------------------#
	def getMode(self, mode): return self.__dict__[mode]
	#--------------------------------------#
	# def getField(self, fieldName): return self.__dict__[fieldName] #get field without invoke __getattr__
	# def setField(self, fieldName, fieldValue): self.__dict__[fieldName]=fieldValue #set field without invoke __setattr__
	def getField(self, fieldName): return self.data[fieldName] #get field without invoke __getattr__
	def setField(self, fieldName, fieldValue): self.data[fieldName]=fieldValue #set field without invoke __setattr__
	#--------------------------------------#
	def filter(self, **kwargs): return self.filter_.filter(**kwargs)
	#--------------------------------------#
	def SubQuery(self, **kwargs):
		self.filter_.SubQuery(**kwargs)
		return self
	def EXISTS(self, **kwargs):
		self.filter_.EXISTS(**kwargs)
		return self
	def NOT_EXISTS(self, **kwargs):
		self.filter_.NOT_EXISTS(**kwargs)
		return self
	def IN(self, **kwargs):
		self.filter_.IN(**kwargs)
		return self
	def NOT_IN(self, **kwargs):
		self.filter_.NOT_IN(**kwargs)
		return self
	def LIKE(self, **kwargs):
		self.filter_.LIKE(**kwargs)
		return self
	def NULL(self, **kwargs):
		self.filter_.NULL(**kwargs)
		return self
	def NOT_NULL(self, **kwargs):
		self.filter_.NOT_NULL(**kwargs)
		return self
	def BETWEEN(self, **kwargs):
		self.filter_.BETWEEN(**kwargs)
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
	def insert(self): self.database__.insert(record=self, mode='values')
	def read(self, selected="*", group_by='', limit=''): self.database__.read(Database.read, record=self, mode='values', selected=selected, group_by=group_by, limit=limit)
	def update(self): self.database__.update(Database.update, record=self, mode='values')
	def delete(self): self.database__.delete(Database.delete, record=self, mode='values')
	def all(self): self.database__.all(record=self, mode='values')
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
	def getCopyInstance(self, base=(object, ), attributesDictionary={}):
		return self.database__.getCopyInstance(self, base, attributesDictionary={})
	#--------------------------------------#
	def to_xml(self): return self.representer__.xml(self)
	def searchURL(self, url): return self.representer__.search(self, url)
	def importSearchCriteria(self, searchCriteria): return self.representer__.importSearchCriteria(self, searchCriteria)
	def search(self, searchCriteria, selected="*", group_by='', limit=''):
		self.importSearchCriteria(searchCriteria)
		self.read(selected, group_by, limit)
	def limit(self, pageNumber=1, recordsCount=1): return self.database__.paginate(pageNumber, recordsCount)
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
	def update(self):
		if(self.firstRecord()):  self.firstRecord().database__.updateMany(self.firstRecord())
	def delete(self):
		if(self.firstRecord()):  self.firstRecord().database__.deleteMany(self.firstRecord())
	def commit(self):
		if(self.firstRecord()):  self.firstRecord().database__.commit()
	#--------------------------------------#
	def toList(self):
		data = []
		for record in self.iterate():
			data.append(record.toList())
		return data
	#--------------------------------------#
	def toDict(self):
		data = {}
		id = 0
		for record in self.iterate():
			data[id] = record.toDict()
			id += 1
		return data
	#--------------------------------------#
	def toListOfDict(self):
		return self.data
	#--------------------------------------#
	def to_json(self):
		recordsetJSONList = []
		for record in self.iterate():
			recordsetJSONList.append(record.to_json())
		return recordsetJSONList
#================================================================================#
class Collection(list): pass
#================================================================================#
class Manipolatore:
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
		else: return NULL()
	#--------------------
#================================================================================#