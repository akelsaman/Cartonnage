#!/usr/local/bin/python3

#================================================================================#
# if error appears while execute database statement, uncomment print(statement)
# in the realted method (read/insert/update/delete)
#
# to debug class instance, print the dictionary of the attributes
# print(field.__dict__)
#
# the self reference condition method to be passed parameter.
# make the primay key is choosable from the columns and can be composite.
# what is the difference between [.value] [._value_] [.__value] and where are they used ?
# 
# revise the commented lines

import sqlite3
from string import Template

databaseFile = 'thehardlock.db'
#================================================================================#
class debugTracer:
	attributeTemplate	= Template('''	@>>> ${value}''')
	ifTemplate			= Template('''	@>>> ${value1} == ${value2}''')
	codeTemplate		= Template('''\n${indentation}${codeStatement}''')
	#--------------------------------------#
	class defDebugTracer:
		def __init__(self, debugTracer):
			self.debugTracer = debugTracer
		def start(self):
			self.debugTracer.increaseIndentationTabsCount()
			return self.debugTracer
		def end(self):
			self.debugTracer.decreaseIndentationTabsCount()
			return self.debugTracer
	#--------------------------------------#
	def __init__(self):
		self.__context = ''
		self.__indentationTabsCount = 0
		self.__indentation = ''
		self.defDebugTracerObjectInstance = self.defDebugTracer(self)
	#--------------------------------------#
	@property
	def context(self): return self.__context
	@property
	def indentation(self): return self.__indentation
	@property
	def def_(self): return self.defDebugTracerObjectInstance
	#--------------------------------------#
	@context.setter
	def context(self, context): self.__context += context
	#--------------------------------------#
	def __indentationTabs(self):
		self.__indentation = ''
		for i in range(0, self.__indentationTabsCount): self.__indentation += '\t'
		
	def increaseIndentationTabsCount(self):
		self.__indentationTabsCount += 1
		self.__indentationTabs()
		
	def decreaseIndentationTabsCount(self):
		self.__indentationTabsCount -= 1
		self.__indentationTabs()
		
	def print(self):
		print(self.__context)
		
	def save(self, fileName):
		with open(fileName, 'w') as f:
			f.write(self.context)
		f.close()
	#--------------------------------------#
	def if_(self, value1, value2):
		self.context = debugTracer.ifTemplate.substitute({'indentation': self.__indentation, 'value1': value1, 'value2': value2})
		return self
	def code(self, codeStatement, value=None):
		self.context = debugTracer.codeTemplate.substitute({'indentation': self.__indentation, 'codeStatement': codeStatement})
		if(value):
			self.context = debugTracer.attributeTemplate.substitute({'indentation': self.__indentation, 'value': value})
		return self
#================================================================================#
debug_tracer = debugTracer()
#================================================================================#
class Database:
	def __init__(self, database):
		self.__database				= database
		self.__connection			= None
		self.__cursor				= None
		cursor = self.connectionCursor()
	#--------------------------------------#
	def connectionCursor(self):
		self.__connection	= sqlite3.connect(self.__database)
		self.__cursor		= self.__connection.cursor()
	def commit(self): self.__connection.commit()
	def close(self): self.__connection.close()
	def execute(self, statement):
		record = None
		for row in self.__cursor.execute(statement): record = row
		self.commit()
		return record
	#--------------------------------------#
	def select(self, statement):
		record = self.execute(statement)
		return record
	#--------------------------------------#
	def insert(self, statement):
		self.execute(statement)
		return self.__cursor.lastrowid
	#--------------------------------------#
	def update(self, statement):
		self.execute(statement)
		return self.__cursor.rowcount
	#--------------------------------------#
	def delete(self, statement):
		self.execute(statement)
		return self.__cursor.rowcount
	#--------------------------------------#		
#================================================================================#
databaseInstance = Database(databaseFile)
#================================================================================#
class Field:
	def __init__(self, name=None, foreignKey=None):
		self.__name					= name
		self.__foreignKey			= foreignKey
		self.__value				= None
		self.__oldValue				= None

		if(self.__foreignKey): self.__foreignKey.field(self) # add the field to the foreign key
	#--------------------------------------#
	@property
	def value(self):
		if(self.__foreignKey):
			return self.__foreignKey.referenceClassObjectInstance()
		else:
			return self.__value
	@property
	def _value_(self): return self.__value
	@property
	def name(self): return self.__name
	#--------------------------------------#
	@value.setter
	def value(self, value): self.__value = value
	#--------------------------------------#	
#================================================================================#
class PrimaryKey:
	fieldValueTemplate	= Template('''${table}.${field}='${value}' AND ''')
	#--------------------------------------#
	def __init__(self, table):
		self.__table	= table
		self.__fields	= []
		self.__sql		= None
	#--------------------------------------#
	@property
	def fields(self): return self.__fields
	#--------------------------------------#
	def field(self, field):
		self.__fields.append(field)
		return self
	#--------------------------------------#
	def sql(self):
		self.__sql = ''
		for field in self.__fields:
			self.__sql += PrimaryKey.fieldValueTemplate.substitute({'table': self.__table, 'field': field.name, 'value': field._value_})
		return self.__sql[:-5]  # without " AND "
	#--------------------------------------#
#================================================================================#
class ForeignKey:
	def __init__(self, reference):
		self.__reference					= reference
		self.__fields						= []
		self.__referenceClassObjectInstance	= None
	#--------------------------------------#
	def field(self, field):
		self.__fields.append(field)
		return self
	#--------------------------------------#
	def referenceClassObjectInstance(self):
		if(self.__referenceClassObjectInstance): return self.__referenceClassObjectInstance
		else:
			self.__referenceClassObjectInstance = self.__reference()
			primaryKeyFieldsCount = len(self.__referenceClassObjectInstance.primaryKey.fields)
			for i in range(0, primaryKeyFieldsCount):
				primaryKeyField = self.__referenceClassObjectInstance.primaryKey.fields[i]
				foreignKeyField = self.__fields[i]
				primaryKeyField.value = foreignKeyField._value_
			self.__referenceClassObjectInstance.read()
			return self.__referenceClassObjectInstance
	#--------------------------------------#
	def instance(self):
			return self.referenceClassObjectInstance()
	#--------------------------------------#
#================================================================================#
class Record:
	selectStatementTemplate		= Template('''SELECT * FROM ${table} WHERE ${primaryKey};''')
	insertStatementTemplate		= Template('''INSERT INTO ${table}(${fields}) VALUES (${values});''')
	updateStatementTemplate		= Template('''UPDATE ${table} SET ${fieldsValues} WHERE ${primaryKey};''')
	deleteStatementTemplate		= Template('''DELETE FROM ${table} WHERE ${primaryKey};''')

	fieldValueTemplate			= Template('''${field}='${value}', ''')
	instanceStringLineTemplate	= Template('''${table}.${field}: ${value}\n''')
	instanceStringTemplate		= Template('''Record status: ${status}\n${instanceStringLines}''')
	recordNotExistTemplate		= Template('''Record ${pk} is not exist''')

	readHeader='''
	#--------------------------------------#
	#                 Read                 #
	#--------------------------------------#
	'''

	insertHeader='''
	#--------------------------------------#
	#                Insert                #
	#--------------------------------------#
	'''

	updateHeader='''
	#--------------------------------------#
	#                Update                #
	#--------------------------------------#
	'''

	deleteHeader='''
	#--------------------------------------#
	#                Delete                #
	#--------------------------------------#
	'''
	
	def __init__(self, table=None, fields=[], verbose=0):
		#print("==================== ====================")
		#print(self.__class__.__name__)
		#arrange of attributes is important
		#cannot declare self.__fields before self.__pk
		#cannot use self._pk to call read() before self.__fields
		self.__database			= databaseInstance
			
		self.__table			= table
		self.__fields			= fields
		self.__new				= 1
		self.__verbose			= verbose
		self.primaryKey			= PrimaryKey(self.__table)

		#print(self.__dict__)
	#--------------------------------------#
	@property
	def value(self): return self
	@property
	def fields(self): return self.__fields
	@property
	def new(self): #return self.__new
		if(self.__new):	return 'New'
		else:			return 'Exist'
	@property
	def verbose(self): return self.__verbose
	#--------------------------------------#
	@verbose.setter
	def verbose(self, verbose): self.__verbose = verbose
	#--------------------------------------#
	def read(self, verbose=0):
		statement = Record.selectStatementTemplate.substitute({'table': self.__table, 'primaryKey': self.primaryKey.sql()})
		#print(statement)
		record = self.__database.select(statement)
		
		if(record):
			self.__new = 0
			columnIndex = 0
			for field in self.__fields:
				field.value = record[columnIndex]
				columnIndex+=1
				
		if(self.verbose):	self.print(Record.readHeader)
		if(verbose):		self.print(Record.readHeader)
	#--------------------------------------#
	def save(self, verbose=0):
		if(self.__new):	self.__insert(verbose)
		else:			self.__update(verbose)
	#--------------------------------------#
	def __insert(self, verbose=0):
		fields	= ''
		values	= ''
		for field in self.__fields:
			# can't use if(field.value):
			# field.value may contains integer 0
			# if(None) = if(0) # field will be excluded in this way
			if(field._value_ is not None):
				fields += field.name + ', '
				values	+= "'" + str(field._value_) + "', "
		fields	= fields[:-2] # without comma and space
		values	= values[:-2] # without comma and space
		
		lastrowid = None # prevent-> UnboundLocalError: local variable 'lastrowid' referenced before assignment
		statement = Record.insertStatementTemplate.substitute({'table': self.__table, 'fields': fields, 'values': values})
		#print(statement)
				
		if(fields):
			if(values): lastrowid = self.__database.insert(statement)
		
		if(lastrowid):
			# if user doesn't define pk to be generated update the instance with it after insertion
			self._pk = lastrowid
			# self.___pk.value = lastrowid
			if(self.verbose):	self.print(Record.insertHeader)
			if(verbose):		self.print(Record.insertHeader)
	#--------------------------------------#
	def __update(self, verbose=0):
		fieldsValues = ''
		for field in self.__fields:
			# can't use if(field.value):
			# field.value may contains integer 0
			# if(None) = if(0) # field will be excluded in this way
			if(field._value_ is not None):
				fieldsValues += Record.fieldValueTemplate.substitute({'field': field.name, 'value': str(field._value_)})
		fieldsValues = fieldsValues[:-2]
		
		rowcount=None # prevent -> UnboundLocalError: local variable 'rowcount' referenced before assignment
		statement	= Record.updateStatementTemplate.substitute({'table': self.__table, 'fieldsValues': fieldsValues, 'primaryKey': self.primaryKey.sql()})
		#print(statement)
		rowcount	= self.__database.update(statement)
		
		if(rowcount):
			if(self.verbose):	self.print(Record.updateHeader)
			if(verbose):		self.print(Record.updateHeader)
	#--------------------------------------#
	def delete(self, verbose=0):
		if(self.__new):
			print(Record.recordNotExistTemplate.substitute({'pk': self._pk}))
		else:			
			rowcount=None  # prevent -> UnboundLocalError: local variable 'rowcount' referenced before assignment
			statement = Record.deleteStatementTemplate.substitute({'table': self.__table, 'primaryKey': self.primaryKey.sql()})
			#print(statement)
			rowcount = self.__database.delete(statement)
			
			if(rowcount):
				if(self.verbose):	self.print(Record.deleteHeader)
				if(verbose):		self.print(Record.deleteHeader)
	#--------------------------------------#
	def print(self, header=readHeader):
		instanceStringLines = ''
		for field in self.__fields:
			instanceStringLines += Record.instanceStringLineTemplate.substitute({'table': self.__table, 'field': field.name, 'value': str(field._value_)})
		instanceString = Record.instanceStringTemplate.substitute({'status': self.new, 'instanceStringLines': instanceStringLines})
		print(header)
		print(instanceString)
		return instanceString
	#--------------------------------------#
#================================================================================#
class _values_lists(Record):
	__table = '[_values_lists]' #it's a good practice to make it read only but no oop way in python
	def __init__(self, pk=None, selfReference=1, verbose=0):
		self.___pk		= Field(name='[_pk]')
		self.___value	= Field(name='[_value]')
		self.___list_pk	= Field(name='[_list_pk]', foreignKey=ForeignKey(reference=_values_lists))
		
		self.__fields	= [self.___pk, self.___value, self.___list_pk]
		Record.__init__(self, table = self.__table, fields=self.__fields, verbose=verbose)

		# assign values to attributes after calling supper/parent class
		# constructor of the child class to be created to make sure all the
		# super's/parent's class and child class's attributes and methods are
		# comined to constitute/form the class.

		self.primaryKey.field(self.___pk)
		self._pk		= pk
	#--------------------------------------#
	#no setter without property(getter)
	#property (getter) declaration must preceed setter declaration
	#to override parent private attribute use the name of the property instead
	#self._pk instead self.___pk
	#Record.value = value # to modify static attribute
	@property
	def table(self): return self.__table
	@property
	def _pk(self): return self.___pk.value
	@property
	def _value(self): return self.___value.value
	@property
	def _list_pk(self): return self.___list_pk.value
	#--------------------------------------#
	@_pk.setter
	def _pk(self, _pk): self.___pk.value = _pk
	@_value.setter
	def _value(self, _value): self.___value.value = _value
	@_list_pk.setter
	def _list_pk(self, _list_pk): self.___list_pk.value = _list_pk
	#--------------------------------------#
#================================================================================#
class _tables(Record):
	__table = '[_tables]' #it's a good practice to make it read only but no oop way in python
	def __init__(self, pk=None, verbose=0):
		self.___pk		= Field(name='[_pk]')
		self.___table	= Field(name='[_table]')

		self.__fields	= [self.___pk, self.___table]
		Record.__init__(self, table = self.__table, fields=self.__fields, verbose=verbose)

		self.primaryKey.field(self.___pk)
		self._pk		= pk
	#--------------------------------------#
	@property
	def table(self): return self.__table
	@property
	def _pk(self): return self.___pk.value
	@property
	def _table(self): return self.___table.value
	#--------------------------------------#
	@_pk.setter
	def _pk(self, _pk): self.___pk.value = _pk
	@_table.setter
	def _table(self, _table): self.___table.value = _table
	#--------------------------------------#
#================================================================================#
class _tables_columns(Record):
	__table = '[_tables_columns]' #it's a good practice to make it read only but no oop way in python
	def __init__(self, pk=None, verbose=0):
		self.___pk			= Field(name='[_pk]')
		self.___table_pk	= Field(name='[_table_pk]', foreignKey=ForeignKey(reference=_tables))
		self.___column		= Field(name='[_column]')

		self.__fields		= [self.___pk, self.___table_pk, self.___column]
		Record.__init__(self, table = self.__table, fields=self.__fields, verbose=verbose)

		self.primaryKey.field(self.___pk)
		self._pk			= pk
	#--------------------------------------#
	@property
	def table(self): return self.__table
	@property
	def _pk(self): return self.___pk.value
	@property
	def _table_pk(self): return self.___table_pk.value
	@property
	def _column(self): return self.___column.value
	#--------------------------------------#
	@_pk.setter
	def _pk(self, _pk): self.___pk.value = _pk
	@_table_pk.setter
	def _table_pk(self, _table_pk): self.___table_pk.value = _table_pk
	@_column.setter
	def _column(self, _column): self.___column.value = _column
#================================================================================#

#================================================================================#