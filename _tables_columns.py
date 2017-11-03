
class _tables_columns(Record):
	def __init__(self, pk=None, name=None, index=None, verbose=0):
		self.__ttable = '[_tables_columns]'
		self.__table_pk = Field(index=0, name='[_table_pk]')
		self.__column = Field(index=0, name='[_column]')
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
