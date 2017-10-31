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
