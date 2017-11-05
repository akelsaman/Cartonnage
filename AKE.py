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

databaseFile = 'queueing_system.db'
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
	def __init__(self, value=None, name=None, index=None):
		debug_tracer.code('''class Field:''').code('''def __init__(self, value=None, name=None, index=None):''').def_.start()
		debug_tracer.code('''self.__value	= value''', value).code('''self.__nname	= name''', name).\
			code('''self.__oldValue	= None''', None).code('''self.__index	= index''', index)
		self.__value	= value
		self.__nname	= name
		self.__oldValue	= None
		self.__index	= index
		debug_tracer.def_.end()
	#--------------------------------------#
	@property
	def name(self): return self.__nname
	@property
	def value(self): return self.__value
	@property
	def _value_(self): return self.__value
	@property
	def index(self): return self.__index
	#--------------------------------------#
	#@name.setter
	#def name(self, name): self.__nname = name
	@value.setter
	def value(self, value):
		debug_tracer.code('''class Field:''').code('''def value(self, value):''').def_.start()
		debug_tracer.code('''self.__value = value''', value)
		self.__value = value
		debug_tracer.def_.end()
	#@index.setter
	#def index(self, index): self.__index = index
	#--------------------------------------#
	#@name.deleter
	#def name(self): del self.__nname
	#@value.deleter
	#def value(self): del self.__value
	#@index.deleter
	#def index(self): del self.__index
	#--------------------------------------#
	
#================================================================================#
class Record:
	selectStatementTemplate		= Template('''SELECT * FROM ${table} WHERE ${table}.[_pk]='${pk}';''')
	insertStatementTemplate		= Template('''INSERT INTO ${table}(${fields}) VALUES (${values});''')
	updateStatementTemplate		= Template('''UPDATE ${table} SET ${fieldsValues} WHERE ${table}.[_pk]='${pk}';''')
	deleteStatementTemplate		= Template('''DELETE FROM ${table} WHERE ${table}.[_pk]='${pk}';''')

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
	
	def __init__(self, pk=None, table=None, name=None, index=None, fields=[], verbose=0):
		debug_tracer.code('''class Record:''').code('''def __init__(self, pk=None, table=None, name=None, index=None, fields=[], verbose=0):''').def_.start()
		#print("==================== ====================")
		#print(self.__class__.__name__)
		#arrange of attributes is important
		#cannot declare self.__fields before self.__pk
		#cannot use self._pk to call read() before self.__fields
		self.__database			= databaseInstance
		
		debug_tracer.code('''self.__ttable = table''', table).code('''self.__pk	= Field(value=None, index=0, name='[_pk]')''').\
			code('''self.__nname = name''', name).code('''self.__index = index''', index).\
			code('''self.__new = 1''', 1).code('''self.__verbose = verbose''', verbose)
			
		self.__ttable			= table
		self.__pk				= Field(value=None, index=0, name='[_pk]')
		self.__fields			= [self.__pk] + fields
		debug_tracer.code('''self.__fields = [self.__pk] + fields''', self.__fields)
		self.__nname			= name
		self.__index			= index
		self.__new				= 1
		self.__verbose			= verbose
		
		debug_tracer.code('''self._pk = pk''', pk)
		self._pk				= pk # to call read()
		#print(self.__dict__)
		debug_tracer.def_.end()
	#--------------------------------------#
	@property
	def _pk(self): return self.__pk.value
	@property
	def name(self): return self.__nname
	@property
	def value(self): return self
	@property
	def _value_(self): return self._pk
	@property
	def index(self): return self.__index
	@property
	def fields(self): return self.__fields
	@property
	def new(self): #return self.__new
		if(self.__new): return 'New'
		else: return 'Exist'
	@property
	def verbose(self): return self.__verbose
	#--------------------------------------#
	@_pk.setter
	def _pk(self, _pk):
		debug_tracer.code('''class Record:''').code('''def _pk(self, _pk):''').def_.start()
		#if(isinstance(_pk, int)):
		debug_tracer.code('''if(_pk is not None):''')
		if(_pk is not None):
			debug_tracer.code('''self.__pk.value = _pk''', _pk)
			self.__pk.value = _pk
			debug_tracer.code('''self.read()''')
			self.read()
		debug_tracer.def_.end()
	@value.setter
	def value(self, value):
		debug_tracer.code('''class Record:''').code('''def value(self, value):''').def_.start()
		debug_tracer.code('''self._pk = value''', value)
		self._pk = value
		debug_tracer.def_.end()
	@verbose.setter
	def verbose(self, verbose): self.__verbose = verbose
	#--------------------------------------#
	def read(self, verbose=0):
		debug_tracer.code('''class Record:''').code('''	def read(self, verbose=0):''').def_.start()
		
		statement = Record.selectStatementTemplate.substitute({'table': self.__ttable, 'pk': str(self._pk)})
		#print(statement)
		record = self.__database.select(statement)
		
		if(record):
			debug_tracer.code('''if(record):''', record).code('''self.__new = 0''', 0)
			self.__new = 0
			
			debug_tracer.code('''for field in self.__fields:''')
			for field in self.__fields:
				debug_tracer.code('''field.value = record[field.index]''', record[field.index])
				field.value = record[field.index]
				
		if(self.verbose):	self.print(readHeader)
		if(verbose):		self.print(readHeader)
		debug_tracer.def_.end()
	#--------------------------------------#
	def save(self, verbose=0):
		if(self.__new):
			self.__insert(verbose)
		else:
			self.__update(verbose)
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
				print(field._value_)
		fields	= fields[:-2] # without comma and space
		values	= values[:-2] # without comma and space
		
		lastrowid = None # prevent-> UnboundLocalError: local variable 'lastrowid' referenced before assignment
		statement = Record.insertStatementTemplate.substitute({'table': self.__ttable, 'fields': fields, 'values': values})
		#print(statement)
				
		if(fields):
			if(values):
				lastrowid = self.__database.insert(statement)
		
		if(lastrowid):
			# if user doesn't define pk to be generated update the instance with it after insertion
			self._pk = lastrowid
			#self.__pk.value = lastrowid
			if(self.verbose):	self.print(insertHeader)
			if(verbose):		self.print(insertHeader)
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
		statement	= Record.updateStatementTemplate.substitute({'table': self.__ttable, 'fieldsValues': fieldsValues, 'pk': self._pk})
		#print(statement)
		rowcount	= self.__database.update(statement)
		
		if(rowcount):
			if(self.verbose):	self.print(updateHeader)
			if(verbose):		self.print(updateHeader)
	#--------------------------------------#
	def delete(self, verbose=0):
		if(self.__new):
			print(Record.recordNotExistTemplate.substitute({'pk': self._pk}))
		else:			
			rowcount=None  # prevent -> UnboundLocalError: local variable 'rowcount' referenced before assignment
			statement = Record.deleteStatementTemplate.substitute({'table': self.__ttable, 'pk': self._pk})
			#print(statement)
			rowcount = self.__database.delete(statement)
			
			if(rowcount):
				if(self.verbose):	self.print(deleteHeader)
				if(verbose):		self.print(deleteHeader)
	#--------------------------------------#
	def print(self, header=readHeader):
		instanceStringLines = ''
		for field in self.__fields:
			instanceStringLines += Record.instanceStringLineTemplate.substitute({'table': self.__ttable, 'field': field.name, 'value': str(field.value)})
		instanceString = Record.instanceStringTemplate.substitute({'status': self.new, 'instanceStringLines': instanceStringLines})
		print(header)
		print(instanceString)
		return instanceString
#================================================================================#
class _values_lists(Record):
	def __init__(self, pk=None, name=None, index=None, selfReference=1, verbose=0):
		debug_tracer.code('''class _values_lists:''').code('''def __init__(self, pk=None, name=None, index=None, selfReference=1, verbose=0):''').def_.start()
		self.__ttable	= '[_values_lists]'
		self.__value	= Field(index=1, name='[_value]')
		self.__list_pk	= Field(index=2, name='[_list_pk]')
		
		self.__fields	= [self.__value, self.__list_pk]
		Record.__init__(self, pk, table = self.__ttable, name=name, index=index, fields=self.__fields, verbose=verbose)
		
		if(pk): 
			debug_tracer.code('''self.selfReference(pk)''', pk)
			self.selfReference(pk)
		debug_tracer.def_.end()
	#--------------------------------------#
	#no setter without property(getter)
	#property (getter) declaration must preceed setter declaration
	#to override parent private attribute use the name of the property instead
	#self._pk instead self.__pk
	
	@property
	def value(self): return self
	
	@property
	def _value(self): return self.__value.value
	@property
	def _list_pk(self): return self.__list_pk.value
	#--------------------------------------#
	#no setter without property(getter)
	#property (getter) declaration must preceed setter declaration
	#to override parent private attribute use the name of the property instead
	#self._pk instead self.__pk
	#Record.value = value
	
	@value.setter
	def value(self, value):
		debug_tracer.code('''class _values_lists:''').code('''def value(self, value):''').def_.start()
		debug_tracer.code('''self._pk = value''', value)
		self._pk = value
		debug_tracer.code('''self.selfReference(value)''', value)
		self.selfReference(value)
		debug_tracer.def_.end()
		
	@_value.setter
	def _value(self, _value):
		debug_tracer.code('''class _values_lists:''').code('''def value(self, _value):''').def_.start()
		debug_tracer.code('''self.__value.value = _value''', _value)
		self.__value.value = _value
		debug_tracer.def_.end()
		
	@_list_pk.setter
	def _list_pk(self, _list_pk): self.__list_pk.value = _list_pk
	#--------------------------------------#
	def selfReference(self, value):
		debug_tracer.code('''class _values_lists:''').code('''def selfReference(self, value):''').def_.start()
		if(isinstance(value, int)):
			if(value>=0):
				_values_lists_instance	= _values_lists(self._list_pk, index=2, name='[_list_pk]')
				sameRecord = 0
				debug_tracer.code('''for i in range(0, len(_values_lists_instance.fields)):''')
				for i in range(0, len(_values_lists_instance.fields)):
					debug_tracer.code('''if(_values_lists_instance.fields[i].value==self.fields[i].value): sameRecord = 1''').\
						if_(_values_lists_instance.fields[i].value, self.fields[i].value)
					if(_values_lists_instance.fields[i].value==self.fields[i].value): sameRecord = 1
				if(sameRecord):
					pass
				else:
					self.__list_pk = _values_lists_instance
		debug_tracer.def_.end()
#================================================================================#
class _tables(Record):
	def __init__(self, pk=None, name=None, index=None, verbose=0):
		self.__ttable = '[_tables]'
		self.__table = Field(index=1, name='[_table]')
		self.__fields = [self.__table]
		Record.__init__(self, pk, table = self.__ttable, name=name, index=index, fields=self.__fields, verbose=verbose)
	#--------------------------------------#
	@property
	def _table(self): return self.__table.value
	#--------------------------------------#
	@_table.setter
	def _table(self, _table): self.__table.value = _table
#================================================================================#
class _tables_columns(Record):
	def __init__(self, pk=None, name=None, index=None, verbose=0):
		self.__ttable = '[_tables_columns]'
		self.__table_pk = _tables(index=1, name='[_table_pk]')
		self.__column = Field(index=2, name='[_column]')
		self.__fields = [self.__table_pk, self.__column]
		Record.__init__(self, pk, table = self.__ttable, name=name, index=index, fields=self.__fields, verbose=verbose)
	#--------------------------------------#
	@property
	def _table_pk(self): return self.__table_pk.value
	@property
	def _column(self): return self.__column.value
	#--------------------------------------#
	@_table_pk.setter
	def _table_pk(self, _table_pk): self.__table_pk.value = _table_pk
	@_column.setter
	def _column(self, _column): self.__column.value = _column
#================================================================================#

#================================================================================#