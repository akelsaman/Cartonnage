<?php
header("Content-Type:text/plain");
#header("Content-Type:text/html");

#$databaseFile = 'database/thehardlock.db';
$databaseFile = 'sqlite:database/thehardlock.db';
#================================================================================#
class Template{
	private $__templateString;
	private $__string;
	public function __construct($string){
		$this->__templateString = $string;
	}
	public function substitute($keywords){
		$this->__string = $this->__templateString;
		foreach($keywords as $key => $value){
			$key = '${' . $key . '}';
			$this->__string = str_replace($key, $value, $this->__string);
		}
		return $this->__string;
	}
}
#================================================================================#
/*
class Database{
	private $__database;
	private $__connection;
	private $__cursor;
	public function __construct($database){
		$this->__database	= $database;
		$this->__connection	= Null;
		$this->__cursor		= Null;
		$this->connectionCursor();
	}
	#--------------------------------------#
	#no cursor in php like python.
	#SQLite3 constructor returns the connection to the database and the cursor also.
	#so to only conform with the python version of this layer we keep two private attribute for connection and cursor.
	#the private attibute connection and cursor are the same memeory address referes to the instance of the SQLite3.
	public function connectionCursor(){
		$this->__connection	= new SQLite3($this->__database);
		$this->__cursor		= $this->__connection; 
	}
	public function beginTransaction(){$this->__cursor->exec('BEGIN');} #no begin transaction in the SQLite3 for PHP
	public function commit(){$this->__cursor->exec('COMMIT');} #no commit in the SQLite3 for PHP
	public function close(){$this->__connection->close();}
	#--------------------------------------#
	#unlike pyhton, in php execute() returns boolean so it is used for insert, update and delete.
	#query() is used for select.
	public function execute($statement){
		$record = Null;
		$this->beginTransaction();
		$query = $this->__cursor->exec($statement);
		$this->commit();
	}
	#--------------------------------------#
	#unlike pyhton, in php execute() returns boolean so it is used for insert, update and delete.
	#query() is used for select.
	public function query($statement){
		$record = Null;
		$this->beginTransaction();
		$query = $this->__cursor->query($statement);
		$this->commit();
		$row = $query->fetchArray(SQLITE3_BOTH); #SQLITE3_NUM#SQLITE3_ASSOC
		$record = $row;
		#--------------------------------------#
		#while ($row = $query->fetchArray(SQLITE3_BOTH)) { #SQLITE3_NUM#SQLITE3_ASSOC
		#	#var_dump($row);
		#	#echo("\n".' '.$row[0]);
		#	echo("\n".' '.$row['_Schema']);
		#}
		#--------------------------------------#
		return $record;
	}
	#--------------------------------------#
	public function prepareExecute($statement){
		$record = Null;
		$this->beginTransaction();
		$statement = $this->__cursor->prepare($statement);
		#replace placeholder with values, can be commented if no place holder
		#bindParam is used with assigned variable yet.bindValue is used with existing value only.
		#$statement->bindValue(':id', 1, SQLITE3_INTEGER);
		$row = $statement->execute();
		$this->commit();
		#fetchArray is to be used only by 'SELECT' statements.
		#$row = $query->fetchArray(SQLITE3_BOTH); #SQLITE3_NUM#SQLITE3_ASSOC
		$record = $row;
		return $record;
	}
	#--------------------------------------#
	public function querySingle($statement){
		#to be used with 'SELECT' statement only
		$record = Null;
		$this->beginTransaction();
		#returns first column of first result's row, if no result returns Null
		#$row = $this->__cursor->querySingle($statement); #entire_row=false]
		#returns first result's row, if no results returns empty array.
		$row = $this->__cursor->querySingle($statement, $entire_row=true);
		$this->commit();
		$record = $row;
		return $record;
	}
	#--------------------------------------#
	public function select($statement){
		$record = $this->query($statement);
		return $record;
	}
	#--------------------------------------#
	public function insert($statement){
		$this->execute($statement);
		return $this->__cursor->lastInsertRowID();
	}
	#--------------------------------------#
	public function update($statement){
		$this->execute($statement);
		return $this->__cursor->changes();
	}
	#--------------------------------------#
	public function delete($statement){
		$rowCount = $this->execute($statement);
		return $this->__cursor->changes();
	}
	#--------------------------------------#
}
*/
#================================================================================#
#https://code.tutsplus.com/tutorials/why-you-should-be-using-phps-pdo-for-database-access--net-12059
class Database{
	private $__database;
	private $__connection;
	private $__cursor;
	public function __construct($database){
		$this->__database	= $database;
		$this->__connection	= Null;
		$this->__cursor		= Null;
		$this->connectionCursor();
	}
	#--------------------------------------#
	#no cursor in php like python.
	#PDO constructor returns the connection to the database and the cursor also.
	#so to only conform with the python version of this layer we keep two private attribute for connection and cursor.
	#the private attibute connection and cursor are the same memeory address referes to the instance of the SQLite3.
	public function connectionCursor(){
		$this->__connection = new PDO($this->__database);
		$this->__cursor		= $this->__connection; # no cursor in php, the cursor returns by connection directly
	}
	public function beginTransaction(){$this->__connection->beginTransaction();}
	public function commit(){$this->__connection->commit();}
	public function close(){$this->__connection = Null;}
	#--------------------------------------#
	public function execute($statement){
		$record = Null;
		$this->beginTransaction();
		# unlike of the exec() method of sqlite3 driver.
		#the exec() method of pdo driver returns the inserted/updated/deleted rows
		$row = $this->__cursor->exec($statement);
		$this->commit();
		$record = $row;
		return $record;
	}
	#--------------------------------------#
	#PDO::FETCH_ASSOC: returns an array indexed by column name.
	#PDO::FETCH_BOTH (default): returns an array indexed by both column name and number.
	#PDO::FETCH_BOUND: Assigns the values of your columns to the variables set with the ->bindColumn() method.
	#PDO::FETCH_CLASS: Assigns the values of your columns to properties of the named class. It will create the properties if matching properties do not exist.
	#PDO::FETCH_INTO: Updates an existing instance of the named class.
	#PDO::FETCH_LAZY: Combines PDO::FETCH_BOTH/PDO::FETCH_OBJ, creating the object variable names as they are used.
	#PDO::FETCH_NUM: returns an array indexed by column number.
	#PDO::FETCH_OBJ.
	public function query($statement){
		$record = Null;
		$this->beginTransaction();
		$query = $this->__cursor->query($statement);
		$this->commit();
		$row = $query->fetch();
		$record = $row;
		return $record;
	}
	#--------------------------------------#
	public function prepareExecute($statement){
		$statement = $this->__cursor->prepare($statement);
		#$statement->bindValue(':id', 1, SQLITE3_INTEGER);
		$row = $statement->execute(); # returns 0/1 true/false
		#$rowCount = $statement->rowCount(); #the rowCount() is method of the prepared statement
		$record = $row;
		return $record;
	}
	#--------------------------------------#
	public function select($statement){
		$record = $this->query($statement);
		return $record;
	}
	#--------------------------------------#
	public function insert($statement){
		$this->execute($statement);
		return $this->__cursor->lastInsertID(); #the lastInsertID() is method of the connection/cursor.
	}
	#--------------------------------------#
	public function update($statement){
		return $this->execute($statement);
	}
	#--------------------------------------#
	public function delete($statement){
		return $this->execute($statement);
	}
	#--------------------------------------#
}
#================================================================================#
$databaseInstance = new Database($databaseFile);
#================================================================================#
class Field{
	private $__name;
	private $__foreignKey;
	private $__value;
	private $__oldValue;
	#--------------------------------------#
	public function __construct($name=Null, $foreignKey=Null){
		$this->__name        = $name;
		$this->__foreignKey  = $foreignKey;

		if($this->__foreignKey){$this->__foreignKey->field($this);}
	}
	#--------------------------------------#
	public function valueGet(){
		if($this->__foreignKey){
			return $this->__foreignKey->referenceClassObjectInstance();
		} else {
			return $this->__value;
		}
	}
	public function _value_(){return $this->__value;}
	public function nameGet(){return $this->__name;}
	#--------------------------------------#
	public function valueSet($value){$this->__value=$value;return $this;}
	#--------------------------------------#
}
#================================================================================#
class PrimaryKey{
	private static $fieldValueTemplateString = '${table}.${field}=\'${value}\' AND ';
	private static $fieldValueTemplate;

	private $__table;
	private $__fields;
	private $__sql;
	#--------------------------------------#
	public function __construct($table){
		$this->fieldValueTemplate = new Template(PrimaryKey::$fieldValueTemplateString);

		$this->__table	= $table;
		$this->__fields	= [];
		$this->__sql	= Null;
	}
	#--------------------------------------#
	public function fieldsGet(){ return $this->__fields; }
	#--------------------------------------#
	public function field($field){
		#$this->__fields->append($field);
		array_push($this->__fields, $field);
		return $this;
	}
	#--------------------------------------#
	public function sqlGet(){
		$this->__sql = '';
		foreach($this->__fields as $field){
			$this->__sql .= $this->fieldValueTemplate->substitute(['table' => $this->__table, 'field' => $field->nameGet(), 'value' => $field->_value_()]);
		}
		return substr($this->__sql, 0, -5);  # without " AND "
	}
	#--------------------------------------#
}
#================================================================================#
class ForeignKey{
	private $__reference;
	private $__fields;
	private $__referenceClassObjectInstance;

	public function __construct($reference){
		$this->__reference						= $reference;
		$this->__fields							= [];
		$this->__referenceClassObjectInstance	= Null;
	}
	#--------------------------------------#
	public function field($field){
		#$this->__fields.append($field);
		array_push($this->__fields, $field);
		return $this;
	}
	#--------------------------------------#
	public function referenceClassObjectInstance(){
		if($this->__referenceClassObjectInstance){ return $this->__referenceClassObjectInstance; }
		else{
			$this->__referenceClassObjectInstance = new $this->__reference();
			#var_dump($this->__referenceClassObjectInstance); #to dump the context of the class object instance for debugging.
			#sizeof() is alias for count()
			$primaryKeyFieldsCount = count($this->__referenceClassObjectInstance->primaryKey->fieldsGet());
			for($i =0; $i < $primaryKeyFieldsCount; $i++){
				$primaryKeyField = $this->__referenceClassObjectInstance->primaryKey->fieldsGet()[$i];
				$foreignKeyField = $this->__fields[$i];
				$primaryKeyField->valueSet($foreignKeyField->_value_());
			}
			$this->__referenceClassObjectInstance->read();
			return $this->__referenceClassObjectInstance;
		}
	}
	#--------------------------------------#
	public function instance(){
		return $this->referenceClassObjectInstance();
	#--------------------------------------#
	}
}
#================================================================================#
class Record{
	private static $selectStatementTemplate;
	private static $insertStatementTemplate;
	private static $updateStatementTemplate;
	private static $deleteStatementTemplate;
	
	private static $fieldValueTemplate;
	private static $instanceStringLineTemplate;
	private static $instanceStringTemplate;
	private static $recordNotExistTemplate;

	private static $readHeader="
#--------------------------------------#
#                 Read                 #
#--------------------------------------#
";

	private static $insertHeader="
#--------------------------------------#
#                Insert                #
#--------------------------------------#
";

	private static $updateHeader="
#--------------------------------------#
#                Update                #
#--------------------------------------#
";

	private static $deleteHeader="
#--------------------------------------#
#                Delete                #
#--------------------------------------#
";

	private static $__database;

	private $__table;
	private $__fields;
	private $__new;
	private $__verbose;
	public $primaryKey;

	public function __construct($table=None, $fields=[], $verbose=0){
		#print("==================== ====================")
		#print($this->__class__->__name__)
		#arrange of attributes is important
		#cannot declare $this->__fields before $this->__pk
		#cannot use $this->_pk to call read() before $this->
		Record::$__database	= $GLOBALS['databaseInstance'];
		
		# when to use self::, static:: or Record:: ?
		#https://stackoverflow.com/questions/151969/when-to-use-self-over-this
		# $this is used for non-static members.
		# self::, static:: or Record:: is used for static members.

		Record::$selectStatementTemplate = new Template('SELECT * FROM ${table} WHERE ${primaryKey};');
		Record::$insertStatementTemplate = new Template('INSERT INTO ${table}(${fields}) VALUES (${values});');
		Record::$updateStatementTemplate = new Template('UPDATE ${table} SET ${fieldsValues} WHERE ${primaryKey};');
		Record::$deleteStatementTemplate = new Template('DELETE FROM ${table} WHERE ${primaryKey};');
		
		Record::$fieldValueTemplate			= new Template('${field}=\'${value}\', ');
		Record::$instanceStringLineTemplate	= new Template('${table}->${field}: ${value}' . "\n");
		Record::$instanceStringTemplate		= new Template('Record status: ${status}' . "\n" . '${instanceStringLines}');
		Record::$recordNotExistTemplate		= new Template('Record ${pk} is not exist');

		$this->__table			= $table;
		$this->__fields			= $fields;
		$this->__new			= 1;
		$this->__verbose		= $verbose;
		$this->primaryKey		= new PrimaryKey($this->__table);

		#print($this->__dict__) #python
	}
	#--------------------------------------#
	public function valueGet(){ return $this; }
	public function fieldsGet(){ return $this->__fields; }
	public function newGet(){
		#return $this->__new
		if($this->__new){ return 'New'; }
		else{ return 'Exist'; }
	}
	public function verboseGet(){ return $this->__verbose; }
	#--------------------------------------#
	public function verboseSet($verbose){ $this->__verbose = $verbos; }
	#--------------------------------------#
	public function read($verbose=0){
		$statement = Record::$selectStatementTemplate->substitute(['table' => $this->__table, 'primaryKey' => $this->primaryKey->sqlGet()]);
		#echo($statement);
		$record = Record::$__database->select($statement);
		
		if($record){
			$this->__new = 0;
			$columnIndex = 0;
			foreach($this->__fields as $field){
				$field->valueSet($record[$columnIndex]);
				$columnIndex+=1;
			}
		}
		
		if($this->verbose){	$this->print(Record::$readHeader); }
		if($verbose){		$this->print(Record::$readHeader); }
	}
	#--------------------------------------#
	public function save($verbose=0){
		if($this->__new){ $this->__insert($verbose); }
		else{ $this->__update($verbose); }
	}
	#--------------------------------------#
	public function __insert($verbose=0){
		$fields	= '';
		$values	= '';
		foreach($this->__fields as $field){
			# can't use if($field->value)
			# $field->value may contains integer 0
			# if(Null) = if(0) # field will be excluded in this way
			if($field->_value_() != Null){
				$fields .= $field->nameGet() . ', ';
				$values	.= "'" . (string)$field->_value_() . "', ";
			}
		}
		$fields	= substr($fields, 0 , -2); # without comma and space
		$values	= substr($values, 0 , -2); # without comma and space
		
		$lastrowid = Null; # prevent-> UnboundLocalError: local variable '$lastrowid' referenced before assignment
		$statement = Record::$insertStatementTemplate->substitute(['table' => $this->__table, 'fields' => $fields, 'values' => $values]);
		#echo($statement);
				
		if($fields){
			if($values){ $lastrowid = Record::$__database->insert($statement); echo($lastrowid);}
		}
		
		if($lastrowid){
			# if user doesn't define pk to be generated update the instance with it after insertion
			$this->_pkSet($lastrowid);
			# $this->___pk->value = $lastrowid
			if($this->verbose){	$this->print(Record::$insertHeader); }
			if($verbose){		$this->print(Record::$insertHeader); }
		}
	}
	#--------------------------------------#
	public function __update($verbose=0){
		$fieldsValues = '';
		foreach($this->__fields as $field){
			# can't use if($field->value)
			# $field->value may contains integer 0
			# if(Null) = if(0) # field will be excluded in this way
			if($field->_value_() != Null){
				$fieldsValues .= Record::$fieldValueTemplate->substitute(['field' => $field->nameGet(), 'value' => (string)$field->_value_()]);
			}
		}
		$fieldsValues = substr($fieldsValues, 0 , -2);
		
		$rowcount=Null; # prevent -> UnboundLocalError: local variable 'rowcount' referenced before assignment
		$statement	= Record::$updateStatementTemplate->substitute(['table' => $this->__table, 'fieldsValues' => $fieldsValues, 'primaryKey' => $this->primaryKey->sqlGet()]);
		#echo($statement);
		$rowcount	= Record::$__database->update($statement);
		
		if($rowcount){
			if($this->verbose){	$this->print(Record::$updateHeader); }
			if($verbose){		$this->print(Record::$updateHeader); }
		}
	}
	#--------------------------------------#
	public function delete($verbose=0){
		if($this->__new){
			print($this->recordNotExistTemplate->substitute(['pk' => $this->_pk]));
		}
		else{			
			$rowcount=Null;  # prevent -> UnboundLocalError: local variable 'rowcount' referenced before assignment
			$statement = Record::$deleteStatementTemplate->substitute(['table' => $this->__table, 'primaryKey' => $this->primaryKey->sql()]);
			#echo($statement);
			$rowcount = Record::$__database->delete($statement);
			
			if($rowcount){
				if($this->verbose){	$this->print(Record::$deleteHeader); }
				if($verbose){		$this->print(Record::$deleteHeader); }
			}
		}
	}
	#--------------------------------------#
	public function print($header=Null){
		if($header){}
		else{$header=Record::$readHeader;}
		
		$instanceStringLines = '';
		foreach($this->__fields as $field){
			$instanceStringLines .= Record::$instanceStringLineTemplate->substitute(['table' => $this->__table, 'field' => $field->nameGet(), 'value' => (string)$field->_value_()]);
		}
		$instanceString = Record::$instanceStringTemplate->substitute(['status' => $this->newGet(), 'instanceStringLines' => $instanceStringLines]);
		echo($header);
		echo($instanceString);
		return $instanceString;
	}
	#--------------------------------------#
}
#================================================================================#
/*
#$e = Field;
#$f = new $e($name="AKE");
$f = new Field($name="AKE");
$f->valueSet("Ahmed Kamal ELSaman")->valueSet("Adel ELSayed");
echo($f->nameGet());
echo("\n");
echo($f->valueGet());


$d = new Database($databaseFile);
$record = $d->select("SELECT * FROM [_Schemas];");
#returned records drom sqlite3 driver or PDO driver using fetch()
foreach($record as $field){echo(', ' . $field);}

#returned records from pdo driver without fetch()
#foreach($record as $record){
#	foreach($record as $field){echo(', ' . $field);}
#}

$record = $d->insert("INSERT INTO [_Schemas]([_Schema]) VALUES ('2017-12-08');");
echo("\n");
echo($record);

$record = $d->insert("INSERT INTO [_SchemasDates]([_Schema], [_Date]) VALUES ('2017-12-08', '2017-12-08');");
echo("\n");
echo($record);

$record = $d->insert("INSERT INTO [_SchemasDates]([_Schema], [_Date]) VALUES ('2017-12-08', '2017-12-09');");
echo("\n");
echo($record);

$record = $d->delete("DELETE FROM [_SchemasDates] WHERE [_SchemasDates].[_Schema] >= '2017-12-08';");
echo("\n");
echo($record);

$record = $d->delete("DELETE FROM [_Schemas] WHERE [_Schema] >= '2017-12-08';");
echo("\n");
echo($record);
*/
?>