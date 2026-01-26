#!/usr/bin/php

<?php
header("Content-Type:text/plain");
#header("Content-Type:text/html");

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
function println($string){echo($string . "\n");}
#================================================================================#
class Query{
	public function __construct(){
		$this->statement	= Null;
		$this->result		= Null;
	}
}
#================================================================================#
class Result{
	public function __construct($columns=Null, $rows=Null, $count=0, $rowcount=0, $lastrowid=0){
		$this->columns	= $columns;
		$this->rows		= $rows;
		$this->count	= $count;
		$this->rowcount	= $rowcount;
		$this->lastrowid = $lastrowid;
	}
}
#================================================================================#
class Recordset{
	private $__records;
	public function __construct(){
		$this->__records = []; #mapped objects from records
	}
	public function empty(){ $this->__records = []; }
	public function add($record){ array_push($this->__records, $record); }
	public function iterate(){ return $this->__records; }
}
#================================================================================#
class Database{
	private $__database;
	private $__username;
	private $__password;
	private $__host;
	private $__connection;
	private $__cursor;
	public function __construct($database=Null, $username=Null, $password=Null, $host=Null){
		$this->__database	= $database;
		$this->__username	= $username;
		$this->__password	= $password;
		$this->__host		= $host;
		$this->__connection	= Null;
		$this->__cursor		= Null;
		$this->connect();
	}
	#--------------------------------------#
	public function connect(){
		if($this->__database){
			if($this->__username){
				if($this->__password){
					if($this->__host){
						$this->__connection = new PDO("mysql:host=$this->__host;dbname=$this->__database", $this->__username, $this->__password);
					}else{
						
					}
				}
			}else{
				$this->__connection = new PDO($this->__database);
			}
		}
		$this->cursor();
	}
	public function cursor(){ $this->__cursor = $this->__connection;}
	public function beginTransaction(){ $this->__connection->beginTransaction(); }
	public function commit(){ $this->__connection->commit(); }
	public function rollback(){ $this->__connection->rollback(); }
	public function close(){ $this->__connection->close(); }
	#--------------------------------------#
	public function execute($query){
		if($query->statement != Null){
			#println($query->statement);
			$q = $this->__cursor->query($query->statement);
			$rows = Null;
			$count = Null;
			if(strtolower(substr($query->statement, 0, 6)) == "select"){
				$rows = $q->fetchAll(PDO::FETCH_ASSOC);
				$count = count($rows);
			}
			$columns = [];
			
			$query->result = new Result($columns, $rows, $count, $rowcount);
			return $query;
		}
	#--------------------------------------#
	}
}
#================================================================================#
class ObjectRelationalMapper{
	public function __construct(){}
	#--------------------------------------#
	public function map($query, $passedObject){
		$object = $passedObject;
		if($query->result->rows != Null){
			foreach($query->result->rows as $row){
				foreach($row as $column => $fieldValue){
					# str() don't use # to map Null value to None field correctly. 
					$object->{$column} = $fieldValue;
				}
				array_push($passedObject->mappedObjectsFromRecords, $object);
				$object = new Record();
			}
		}
	}
}
#================================================================================#
class State{
	public function __construct(){ $this->current = Null; }
}
#================================================================================#
class Record{
	public static $database = Null;
	private static $orm;
	# select, update and delete
	private static $fieldValueTemplate;
	# insert
	private static $field;
	private static $value;
	private static $fieldsValuesTemplate;
	# ------
	private static $selectStatementTemplate;
	private static $deleteStatementTemplate;
	private static $insertStatementTemplate;
	private static $updateStatementTemplate;
	
	#private $position;
	public $mappedObjectsFromRecords;
	private $__state;
	private $__query;
	#--------------------------------------#
	public function __construct($statement=Null){ #kwargs
		Record::$orm							= new ObjectRelationalMapper();
		# select, update and delete
		Record::$fieldValueTemplate				= new Template('${field}=${value}${separator}');
		# insert
		Record::$field							= new Template('${field}, ');
		Record::$value							= new Template('${value}, ');
		Record::$fieldsValuesTemplate			= new Template('(${fields}) VALUES (${values})');
		# ------
		Record::$selectStatementTemplate		= new Template('SELECT * FROM ${table} WHERE ${fieldsValues}');
		Record::$deleteStatementTemplate		= new Template('DELETE FROM ${table} WHERE ${fieldsValues}');
		Record::$insertStatementTemplate		= new Template('INSERT INTO ${table}${fieldsValues}');
		Record::$updateStatementTemplate		= new Template('UPDATE ${table} SET ${fieldsValues} WHERE ${_fieldsValues_}');

		#$this->position = 0;
		$this->mappedObjectsFromRecords = [];
		$this->__state = new State();
		#if(kwargs is not None):
		#	for key, value in kwargs.items():
		#		setattr(self, key, value)
		$this->__query = new Query(); # must be declared before self.queryObject(statement)
		if($statement != Null){
			$this->__query->statement = $statement;
			Record::$database->execute($this->__query);
			Record::$orm->map($this->__query, $this);
		}
	}
	#--------------------------------------#
	public function recordset(){ return $this->mappedObjectsFromRecords; } #in PHP instead of #implements Iterator|IteratorAggregate
	#--------------------------------------#
	public function table(){ return get_class($this); }
	#--------------------------------------#
	public function fieldsNames(){
		$fieldsNames = [];
		$fieldsEqual = '';
		$fields = '';
		foreach($this as $attribute => $value){ #for a in dir(r): println(a)
			if(in_array(gettype($value) , [string, integer], TRUE)){ # any other type will be execluded Class type, None type and others ...
				#if($value != 'Null'){ $value = "'" . (string)$value . "'"; }
				array_push($fieldsNames, $attribute);
				$fieldsEqual .= $attribute . '=?, ';
				$fields .= $attribute . ', ';
			}
		}
		println($fieldsEqual);
		println($fields);
		return $fieldsNames;
	}
	#--------------------------------------#
	public function filedsValues($filedsNames){
		$fieldsValues = [];
		foreach($fieldsNames as $fieldName){ array_push($fieldsValues, $this[$fieldName]); }
		return $filedsValues;
	}
	#--------------------------------------#
	public function fieldsEqualValues($separator=' AND ', $fieldsValues = ''){
		$separatorLength = strlen($separator);
		foreach($this as $attribute => $value){ #for a in dir(r): println(a)
			if(in_array(gettype($value) , [string, integer], TRUE)){ # any other type will be execluded Class type, None type and others ...
				if($value != 'Null'){ $value = "'" . (string)$value . "'"; }
				$fieldsValues .= Record::$fieldValueTemplate->substitute(['field' => $attribute, 'value' => $value, 'separator' => $separator]);
			}
		}
		if($fieldsValues != Null){ return substr($fieldsValues, 0, -$separatorLength); }
		else{ return Null; }
	}
	#--------------------------------------#
	public function fieldsThenValues($fields='', $values=''){
		foreach($this as $attribute => $value){ #for a in dir(r): println(a)
			if(in_array(gettype($value) , [string, integer], TRUE)){ # any other type will be execluded Class type, None type and others ...
				if($value != 'Null'){ $value = "'" . (string)$value . "'"; }
				$fields .= Record::$field->substitute(['field' => $attribute]);
				$values .= Record::$value->substitute(['value' => $value]);
			}
		}
		$fields = substr($fields, 0, -2);
		$values = substr($values, 0, -2);
		$fieldsValues = Record::$fieldsValuesTemplate->substitute(['fields' => $fields, 'values' => $values]);
		if($fieldsValues != Null){ return $fieldsValues; }
		else{ return Null; }
	}
	#--------------------------------------#
	private function __crd($template, $fieldsValues, $_fieldsValues_=Null){
		if($fieldsValues != Null){
			$this->__query->statement = $template->substitute(['table' => $this->table(), 'fieldsValues' => $fieldsValues, '_filedsValues' => $_fieldsValues_]);
		}
		$this->__state->current = Null;
		Record::$database->execute($this->__query);
		Record::$orm->map($this->__query, $this);
	}
	#--------------------------------------#
	public function startUpdate(){ $this->__state->current = $this->fieldsEqualValues(); }
	#--------------------------------------#
	public function insert(){ $this->__crd(Record::$insertStatementTemplate, $this->fieldsThenValues()); }
	public function read(){	$this->__crd(Record::$selectStatementTemplate, $this->fieldsEqualValues()); }
	public function delete(){ $this->__crd(Record::$deleteStatementTemplate, $this->fieldsEqualValues()); }
	public function update(){
		if($this->__state->current != Null){
			$this->__crd(Record::$updateStatementTemplate, $this->fieldsEqualValues(', '), $this->__state->current);
		}else{
			println("The update doesn't start, no current state !");
		}			
	}
	#--------------------------------------#
}
#================================================================================#
?>