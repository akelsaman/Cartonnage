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
		$this->values		= [];
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
	public function __construct(){ $this->__records = []; }
	public function emptyy(){ $this->__records = []; }
	public function add($recordObject){ array_push($this->__records, $recordObject); }
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
						$this->__connection->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
						$this->cursor();
					}else{
						
					}
				}
			}else{
				$this->__connection = new PDO($this->__database);
				$this->cursor();
			}
		}
	}
	public function cursor(){ $this->__cursor = $this->__connection;}
	public function beginTransaction(){ $this->__connection->beginTransaction(); }
	public function commit(){ $this->__connection->commit(); }
	public function rollback(){ $this->__connection->rollback(); }
	public function close(){ $this->__connection->close(); }
	#--------------------------------------#
	public function executeStatement($query){
		if($query->statement){
			#println($query->statement);
			#var_dump($query->values);
			$q = $this->__cursor->prepare($query->statement);
			$q->execute($query->values);
			$rows = Null;
			$count = Null;
			if(strtolower(substr($query->statement, 0, 6)) == "select"){
				$rows = $q->fetchAll(PDO::FETCH_ASSOC);
				$count = count($rows);
			}
			$columns = [];
			
			$query->result = new Result($columns, $rows, $count);
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
		if($query->result->rows){
			foreach($query->result->rows as $row){
				foreach($row as $column => $fieldValue){
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
	public function __construct(){ 
		$this->currentStatement = Null;
		$this->currentValues = Null;
	}
}
#================================================================================#
class PrepareStatement{
	private $__fieldsNames;
	private $__fieldsEqualPlaceholdersComma;
	private $__fieldsEqualPlaceholdersAnd;
	private $__fields;
	private $__valuesPlaceholders;
	private $__recordObject;

	public function __construct($recordObject){
		$this->__fieldsNames = [];
		$this->__fieldsEqualPlaceholdersComma = '';
		$this->__fieldsEqualPlaceholdersAnd = '';
		$this->__fields = '';
		$this->__valuesPlaceholders = '';
		$this->__recordObject = $recordObject;
		$this->prepare();
	}

	public function fieldsNames(){ return $this->__fieldsNames; }
	public function fields(){ return $this->__fields; }
	public function valuesPlaceholders(){ return $this->__valuesPlaceholders; }
	public function fieldsEqualPlaceholdersComma(){ return substr($this->__fieldsEqualPlaceholdersComma, 0, -2); }
	public function fieldsEqualPlaceholdersAnd(){ return substr($this->__fieldsEqualPlaceholdersAnd, 0, -5); }
	public function fieldsThenPlaceholders(){ return '(' . substr($this->__fields, 0, -2) . ') VALUES (' . substr($this->__valuesPlaceholders, 0, -2) . ')'; }

	public function __add($field){
		array_push($this->__fieldsNames, $field);
		$this->__fieldsEqualPlaceholdersComma .= $field . '=?, ';
		$this->__fieldsEqualPlaceholdersAnd .= $field . '=? AND ';
		$this->__fields .= $field . ', ';
		$this->__valuesPlaceholders .= '?, ';
	}

	public function prepare(){
		foreach($this->__recordObject as $attribute => $value){
			#working in php 7 not php 5 #if(in_array(gettype($value) , [string, integer], TRUE)){
			if(in_array(gettype($value) , ['string', 'integer'], TRUE)){
				$this->__add($attribute);
			}
		}
		return $this;
	}
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
	private static $selectPreparedStatementTemplate;
	private static $deletePreparedStatementTemplate;
	private static $insertPreparedStatementTemplate;
	private static $updatePreparedStatementTemplate;
	
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
		Record::$selectPreparedStatementTemplate	= new Template('SELECT * FROM ${table} WHERE ${fieldsWithPlaceHolders}');
		Record::$deletePreparedStatementTemplate	= new Template('DELETE FROM ${table} WHERE ${fieldsWithPlaceHolders}');
		Record::$insertPreparedStatementTemplate	= new Template('INSERT INTO ${table}${fieldsWithPlaceHolders}');
		Record::$updatePreparedStatementTemplate	= new Template('UPDATE ${table} SET ${fieldsWithPlaceHolders} WHERE ${_fieldsWithPlaceHolders_}');

		#$this->position = 0;
		$this->mappedObjectsFromRecords = [];
		$this->__state = new State();
		#if(kwargs):
		#	for key, value in kwargs.items():
		#		setattr(self, key, value)
		$this->__query = new Query(); # must be declared before self.queryObject(statement)
		if($statement){
			$this->__query->statement = $statement;
			$this::$database->executeStatement($this->__query);
			Record::$orm->map($this->__query, $this);
		}
	}
	#--------------------------------------#
	public function recordset(){ return $this->mappedObjectsFromRecords; } #in PHP instead of #implements Iterator|IteratorAggregate
	#--------------------------------------#
	public function table(){ return get_class($this); }
	#--------------------------------------#
	public function prepareValues($fieldsNames=Null){
		$values = [];
		if($fieldsNames == Null){ $fieldsNames = (new PrepareStatement($this))->fieldsNames(); }
		if($fieldsNames){
			foreach($fieldsNames as $field){
				array_push($values, $this->$field);
			}
		}
		return $values;
	}
	#--------------------------------------#
	public function __crud($template, $fieldsWithPlaceHolders, $_fieldsWithPlaceHolders_=Null){
		if($fieldsWithPlaceHolders){
			$this->__query->statement = $template->substitute(['table' => $this->table(), 'fieldsWithPlaceHolders' => $fieldsWithPlaceHolders, '_fieldsWithPlaceHolders_' => $_fieldsWithPlaceHolders_]);
			$this->__query->values = $this->prepareValues();
			if($this->__state->currentValues){ $this->__query->values = array_merge($this->__query->values, $this->__state->currentValues); }
			$this->__state->currentStatement = Null;
			$this->__state->currentValues = Null;
			$this::$database->executeStatement($this->__query);
			Record::$orm->map($this->__query, $this);
		}
	}
	#--------------------------------------#
	public function insert(){ $this->__crud(Record::$insertPreparedStatementTemplate, (new PrepareStatement($this))->fieldsThenPlaceholders()); }
	public function read(){	$this->__crud(Record::$selectPreparedStatementTemplate, (new PrepareStatement($this))->fieldsEqualPlaceholdersAnd()); }
	public function delete(){ $this->__crud(Record::$deletePreparedStatementTemplate, (new PrepareStatement($this))->fieldsEqualPlaceholdersAnd()); }
	public function update(){
		if($this->__state->currentStatement){
			$this->__crud(Record::$updatePreparedStatementTemplate, (new PrepareStatement($this))->fieldsEqualPlaceholdersComma(), $this->__state->currentStatement);
		}else{
			println("The update doesn't start, no current state !");
		}
	}
	#--------------------------------------#
	public function startUpdate(){
		$this->__state->currentStatement = (new PrepareStatement($this))->fieldsEqualPlaceholdersAnd();
		$this->__state->currentValues = $this->prepareValues();
	}
	#--------------------------------------#
}
#================================================================================#
?>