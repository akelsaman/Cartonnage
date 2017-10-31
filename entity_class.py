import sqlite3
from string import Template

attributeTemplate	= Template('''self._${attributeName} = Field(index=0, name='[${attributeName}]')\n\t\t''')
fieldTemplate		= Template('''self._${attributeName}, ''')

getterTemplate		= Template('''
	@property
	def ${attributeName}(self): return self._${attributeName}.value''')

setterTemplate		= Template('''
	@${attributeName}.setter
	def ${attributeName}(self, ${attributeName}): self._${attributeName}.value = ${attributeName}''')

classTemplate = Template('''
class ${tableName}(Record):
	def __init__(self, pk=None, name=None, index=None, verbose=0):
		self.__ttable = '[${tableName}]'
		${attributes}
		self.__fields = [${fields}]
		Record.__init__(self, pk, table = self.__ttable, name=name, index=index, fields=self.__fields, verbose=verbose)
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
			self.attributes += attributeTemplate.substitute({"attributeName":attributeName})
			self.fields		+= fieldTemplate.substitute({"attributeName":attributeName})
			self.getters	+= getterTemplate.substitute({"attributeName":attributeName})
			self.setters	+= setterTemplate.substitute({"attributeName":attributeName})
		self.classCode = classTemplate.substitute({"tableName":self.tableName, "attributes":self.attributes[:-3], "fields":self.fields[:-2], "getters":self.getters, "setters": self.setters})
		with open(self.tableName + '.py', 'w') as f:
			f.write(self.classCode)
		f.close()
		print(self.classCode)
		
_tables_columns = entity_class(tableName="_tables_columns", attributesNames=["_table_pk", "_column"])
_tables_columns.write()
