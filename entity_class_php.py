#!/usr/local/bin/python3

import sqlite3
from string import Template

attributesDeclarationsTemplate	= Template('''private $$__${attributeName};\n\t''')
attributeAssignmentsTemplate	= Template('''$$this->__${attributeName} = new Field($$name='[${attributeName}]');\n\t\t''')
fieldTemplate		= Template('''$$this->__${attributeName}, ''')

getterTemplate		= Template('''
	public function ${attributeName}Get(){ return $$this->__${attributeName}->valueGet(); }''')

setterTemplate		= Template('''
	public function ${attributeName}Set($$${attributeName}){ $$this->__${attributeName}->valueSet($$${attributeName}); }''')

classTemplate = Template('''
<?php
class ${tableName} Extends Record{
	private static $$__table='[${tableName}]';
	private $$__fields;

	${attributesDeclarations}
	public function __construct($$pk=Null, $$verbose=0){
		${attributesAssignments}

		$$this->__fields = [${fields}];
		Record::__construct($$table = ${tableName}::$$__table, $$fields=$$this->__fields, $$verbose=$$verbose);
	}
	#--------------------------------------#
	${getters}
	#--------------------------------------#
	${setters}
}
?>
''')

class entity_class:
	def __init__(self, tableName=None, attributesNames=[]):
		self.tableName				= tableName
		self.attributesNames		= attributesNames
		self.attributesDeclarations	= ''
		self.attributesAssignments	= ''
		self.fields					= ''
		self.constructor			= None
		self.getters				= ''
		self.setters				= ''
		self.classCode				= None
	
	def write(self):
		for attributeName in self.attributesNames:
			self.attributesDeclarations += attributesDeclarationsTemplate.substitute({'attributeName':attributeName})
			self.attributesAssignments	+= attributeAssignmentsTemplate.substitute({'attributeName':attributeName})
			self.fields					+= fieldTemplate.substitute({'attributeName':attributeName})
			self.getters				+= getterTemplate.substitute({'attributeName':attributeName})
			self.setters				+= setterTemplate.substitute({'attributeName':attributeName})
		self.classCode = classTemplate.substitute({'tableName':self.tableName, 'attributesAssignments':self.attributesAssignments[:-3], 'attributesDeclarations':self.attributesDeclarations, 'fields':self.fields[:-2], 'getters':self.getters, 'setters': self.setters})
		with open(self.tableName + '.php', 'w') as f:
			f.write(self.classCode)
		f.close()
		print(self.classCode)
		
#_tables_columns = entity_class(tableName='_Bookings', attributesNames=['_PK', '_BookingNumber', '_Room', '_Schema', '_Date', '_Time', '_Customer', '_Mobile', '_MembersCount', '_PaymentAmount', '_PaymentDiscount', '_PaymentType', '_PaymentReceived', '_PaymentRefunded', '_Pass', '_TimeTaken', '_Cancelled'])
#_tables_columns.write()

#_tables_columns = entity_class(tableName='_SchemasDates', attributesNames=['_Schema', '_Date'])
#_tables_columns.write()

_tables_columns = entity_class(tableName='_SchemasTimes', attributesNames=['_Schema', '_Time'])
_tables_columns.write()