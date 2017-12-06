#!/usr/local/bin/python3

import sqlite3
from string import Template

attributeTemplate	= Template('''self.__${attributeName} = Field(name='[${attributeName}]')\n\t\t''')
fieldTemplate		= Template('''self.__${attributeName}, ''')

getterTemplate		= Template('''
	@property
	def ${attributeName}(self): return self.__${attributeName}.value''')

setterTemplate		= Template('''
	@${attributeName}.setter
	def ${attributeName}(self, ${attributeName}): self.__${attributeName}.value = ${attributeName}''')

classTemplate = Template('''
class ${tableName}(Record):
	table='[${tableName}]'
	def __init__(self, pk=None, verbose=0):
		${attributes}
		self.__fields = [${fields}]
		Record.__init__(self, table = self.table, fields=self.__fields, verbose=verbose)
	#--------------------------------------#
	${getters}
	#--------------------------------------#
	${setters}
''')

class entity_class:
	def __init__(self, tableName=None, attributesNames=[]):
		self.tableName			= tableName
		self.attributesNames	= attributesNames
		self.attributes			= ''
		self.fields				= ''
		self.constructor		= None
		self.getters			= ''
		self.setters			= ''
		self.classCode			= None
	
	def write(self):
		for attributeName in self.attributesNames:
			self.attributes += attributeTemplate.substitute({'attributeName':attributeName})
			self.fields		+= fieldTemplate.substitute({'attributeName':attributeName})
			self.getters	+= getterTemplate.substitute({'attributeName':attributeName})
			self.setters	+= setterTemplate.substitute({'attributeName':attributeName})
		self.classCode = classTemplate.substitute({'tableName':self.tableName, 'attributes':self.attributes[:-3], 'fields':self.fields[:-2], 'getters':self.getters, 'setters': self.setters})
		with open(self.tableName + '.py', 'w') as f:
			f.write(self.classCode)
		f.close()
		print(self.classCode)
		
_tables_columns = entity_class(tableName='_Bookings', attributesNames=['_PK', '_BookingNumber', '_Room', '_Schema', '_Date', '_Time', '_Customer', '_Mobile', '_MembersCount', '_PaymentAmount', '_PaymentDiscount', '_Payment_Type', '_PaymentReceived', '_PaymentRefunded', '_Pass', '_TimeTaken', '_Cancelled'])
_tables_columns.write()