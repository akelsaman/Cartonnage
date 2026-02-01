from queue import Queue, Empty
from threading import Lock
from contextlib import contextmanager
import time

# from ake_cartonnage import *
from cartonnage import * # installed by pip install cartonnage

import oracledb
import os
from dotenv import load_dotenv

#================================================================================#
# DATABASE CONNECTION CONFIGURATION
# Replace these values with your actual database credentials
#================================================================================#
# SQLite Configuration
class AKESQLiteConfig:
	DATABASE_PATH = 'hr.db'

# Oracle Configuration
class AKEOracleConfig:
	USER = ''
	PASSWORD = ''
	DSN = ''
	CLIENT_LIB_DIR = './instantclient_23_3'

# MySQL Configuration
class AKEMySQLConfig:
	HOST = ''
	PORT = 3306
	USER = ''
	PASSWORD = ''
	DATABASE = ''
	SSL_CA = ''
	SSL_VERIFY_CERT = True

# PostgreSQL Configuration
class PostgresConfig:
	HOST = ''
	PORT = 5432
	USER = ''
	PASSWORD = ''
	DATABASE = ''
	SSLMODE = ''
	DSN = f'postgres://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}?sslmode={SSLMODE}'

# Azure SQL / Microsoft SQL Server Configuration
class AKEAzureConfig:
	SERVER = ''
	DATABASE = ''
	USERNAME = ''
	PASSWORD = ''
	DRIVER = '{ODBC Driver 18 for SQL Server}'
	ENCRYPT = 'yes'
	TRUST_SERVER_CERTIFICATE = 'no'

#================================================================================#
class ConnectionPool:
	"""
	Universal connection pool that works with SQLite3, Oracle, MySQL, Postgres, and Azure/pyodbc.

	Usage:
		# SQLite
		pool = ConnectionPool(
			creator=lambda: sqlite3.connect('hr.db', check_same_thread=False),
			pool_size=5
		)

		# With context manager
		with pool.connection() as conn:
			cursor = conn.cursor()
			cursor.execute("SELECT * FROM users")

		# Manual acquire/release
		conn = pool.acquire()
		try:
			# use connection
		finally:
			pool.release(conn)
	"""

	def __init__(self, creator, pool_size=5, max_overflow=0, timeout=30,
				 recycle=3600, pre_ping=True, reset_on_return=True):
		"""
		Args:
			creator: Callable that returns a new database connection
			pool_size: Number of connections to maintain in the pool
			max_overflow: Max connections above pool_size (0 = no overflow)
			timeout: Seconds to wait for available connection
			recycle: Seconds before connection is recycled (0 = never)
			pre_ping: Test connection before returning from pool
			reset_on_return: Rollback uncommitted transactions on return
		"""
		self._creator = creator
		self._pool_size = pool_size
		self._max_overflow = max_overflow
		self._timeout = timeout
		self._recycle = recycle
		self._pre_ping = pre_ping
		self._reset_on_return = reset_on_return

		self._pool = Queue(maxsize=pool_size)
		self._overflow_count = 0
		self._lock = Lock()
		self._connection_times = {}  # Track creation time for recycling

		# Pre-populate pool
		for _ in range(pool_size):
			conn = self._create_connection()
			self._pool.put(conn)

	def _create_connection(self):
		"""Create a new connection and track its creation time."""
		conn = self._creator()
		self._connection_times[id(conn)] = time.time()
		return conn

	def _is_connection_stale(self, conn):
		"""Check if connection should be recycled based on age."""
		if self._recycle <= 0:
			return False
		created_at = self._connection_times.get(id(conn), 0)
		return (time.time() - created_at) > self._recycle

	def _validate_connection(self, conn):
		"""Test if connection is still alive."""
		if not self._pre_ping:
			return True
		try:
			cursor = conn.cursor()
			cursor.execute("SELECT 1")
			cursor.fetchone()
			cursor.close()
			return True
		except Exception:
			return False

	def _close_connection(self, conn):
		"""Safely close a connection."""
		try:
			del self._connection_times[id(conn)]
			conn.close()
		except Exception:
			pass

	def _reset_connection(self, conn):
		"""Reset connection state (rollback uncommitted transactions)."""
		if not self._reset_on_return:
			return
		try:
			conn.rollback()
		except Exception:
			pass

	def acquire(self):
		"""
		Get a connection from the pool.

		Returns:
			Database connection

		Raises:
			TimeoutError: If no connection available within timeout
		"""
		# Try to get from pool
		try:
			conn = self._pool.get(timeout=self._timeout)

			# Check if connection is stale (needs recycling)
			if self._is_connection_stale(conn):
				self._close_connection(conn)
				conn = self._create_connection()

			# Validate connection is alive
			elif not self._validate_connection(conn):
				self._close_connection(conn)
				conn = self._create_connection()

			return conn

		except Empty:
			# Pool exhausted, try overflow
			with self._lock:
				if self._overflow_count < self._max_overflow:
					self._overflow_count += 1
					return self._create_connection()

			raise TimeoutError(f"Connection pool exhausted (size={self._pool_size}, overflow={self._max_overflow})")

	def release(self, conn):
		"""Return a connection to the pool."""
		if conn is None:
			return

		# Reset connection state
		self._reset_connection(conn)

		# Try to return to pool
		try:
			self._pool.put_nowait(conn)
		except:
			# Pool is full (overflow connection), close it
			with self._lock:
				self._overflow_count = max(0, self._overflow_count - 1)
			self._close_connection(conn)

	def get(self):
		"""Alias for acquire()."""
		return self.acquire()

	def put(self, conn):
		"""Alias for release()."""
		self.release(conn)

	@contextmanager
	def connection(self):
		"""Context manager for automatic acquire/release."""
		conn = self.acquire()
		try:
			yield conn
		finally:
			self.release(conn)

	def close_all(self):
		"""Close all connections in the pool."""
		while True:
			try:
				conn = self._pool.get_nowait()
				self._close_connection(conn)
			except Empty:
				break

	def size(self):
		"""Return current number of connections in pool."""
		return self._pool.qsize()

	def status(self):
		"""Return pool status information."""
		return {
			'pool_size': self._pool_size,
			'available': self._pool.qsize(),
			'overflow': self._overflow_count,
			'max_overflow': self._max_overflow
		}
#================================================================================#
# Native Pool Factory Functions
#================================================================================#
def create_oracle_native_pool(user, password, dsn, lib_dir=None,
							  min_connections=2, max_connections=10,
							  increment=1, **kwargs):
	"""
	Create a native Oracle connection pool using oracledb.create_pool().

	Args:
		user: Database username
		password: Database password
		dsn: Data source name (host:port/service)
		lib_dir: Path to Oracle Instant Client (optional)
		min_connections: Minimum connections to maintain
		max_connections: Maximum connections allowed
		increment: Number of connections to add when pool needs to grow
		**kwargs: Additional oracledb.create_pool arguments

	Usage:
		pool = create_oracle_native_pool(
			user="admin",
			password="secret",
			dsn="localhost:1521/XEPDB1",
			lib_dir="./instantclient_23_3"
		)
		conn = pool.acquire()
		# ... use connection ...
		pool.release(conn)

		# Or with context manager:
		with pool.acquire() as conn:
			cursor = conn.cursor()
			cursor.execute("SELECT * FROM users")
	"""
	import oracledb
	if lib_dir:
		oracledb.init_oracle_client(lib_dir=lib_dir)

	return oracledb.create_pool(
		user=user,
		password=password,
		dsn=dsn,
		min=min_connections,
		max=max_connections,
		increment=increment,
		**kwargs
	)
#--------------------------------------#
def create_mysql_native_pool(host, port, user, password, database,
							 pool_name="mypool", pool_size=5,
							 ssl_ca=None, ssl_verify_cert=False, **kwargs):
	"""
	Create a native MySQL connection pool using mysql.connector.pooling.

	Args:
		host: Database host
		port: Database port
		user: Database username
		password: Database password
		database: Database name
		pool_name: Name for the connection pool
		pool_size: Number of connections in pool (1-32)
		ssl_ca: Path to SSL CA certificate (optional)
		ssl_verify_cert: Verify SSL certificate
		**kwargs: Additional mysql.connector arguments

	Usage:
		pool = create_mysql_native_pool(
			host="localhost",
			port=3306,
			user="root",
			password="secret",
			database="mydb"
		)
		conn = pool.get_connection()
		# ... use connection ...
		conn.close()  # Returns to pool
	"""
	from mysql.connector import pooling

	config = {
		'host': host,
		'port': port,
		'user': user,
		'password': password,
		'database': database,
		'pool_name': pool_name,
		'pool_size': pool_size,
		**kwargs
	}
	if ssl_ca:
		config['ssl_ca'] = ssl_ca
		config['ssl_verify_cert'] = ssl_verify_cert

	return pooling.MySQLConnectionPool(**config)
#--------------------------------------#
def create_postgres_native_pool(dsn=None, host=None, port=None, user=None,
								password=None, database=None, sslmode=None,
								min_connections=2, max_connections=10, **kwargs):
	"""
	Create a native PostgreSQL connection pool using psycopg2.pool.ThreadedConnectionPool.

	Args:
		dsn: Connection string (alternative to individual params)
		host: Database host
		port: Database port
		user: Database username
		password: Database password
		database: Database name
		sslmode: SSL mode (disable, allow, prefer, require, verify-ca, verify-full)
		min_connections: Minimum connections to maintain
		max_connections: Maximum connections allowed
		**kwargs: Additional psycopg2 connection arguments

	Usage:
		pool = create_postgres_native_pool(
			dsn="postgres://user:pass@host:5432/db?sslmode=require"
		)
		conn = pool.getconn()
		# ... use connection ...
		pool.putconn(conn)
	"""
	from psycopg2 import pool as pg_pool

	if dsn:
		return pg_pool.ThreadedConnectionPool(
			minconn=min_connections,
			maxconn=max_connections,
			dsn=dsn,
			**kwargs
		)
	else:
		config = {}
		if host: config['host'] = host
		if port: config['port'] = port
		if user: config['user'] = user
		if password: config['password'] = password
		if database: config['database'] = database
		if sslmode: config['sslmode'] = sslmode
		config.update(kwargs)

		return pg_pool.ThreadedConnectionPool(
			minconn=min_connections,
			maxconn=max_connections,
			**config
		)
#================================================================================#
# Generic Pool Factory Functions (using custom ConnectionPool)
#================================================================================#
def create_sqlite_pool(database_path, pool_size=5, **kwargs):
	"""
	Create a connection pool for SQLite.

	Args:
		database_path: Path to SQLite database file
		pool_size: Number of connections in pool
		**kwargs: Additional ConnectionPool arguments

	Usage:
		pool = create_sqlite_pool('hr.db', pool_size=5)
		conn = pool.acquire()
		sqlite3Database = SQLite(conn)
		sqlite3Database._pool = pool
		Record.database__ = sqlite3Database
	"""
	import sqlite3
	# Python 3.12+: use autocommit=False for proper transaction control
	return ConnectionPool(
		creator=lambda: sqlite3.connect(database_path, check_same_thread=False, autocommit=False),
		pool_size=pool_size,
		**kwargs
	)
#--------------------------------------#
def create_oracle_pool(user, password, dsn, lib_dir=None, pool_size=5, **kwargs):
	"""
	Create a connection pool for Oracle.

	Args:
		user: Database username
		password: Database password
		dsn: Data source name (host:port/service)
		lib_dir: Path to Oracle Instant Client (optional)
		pool_size: Number of connections in pool
		**kwargs: Additional ConnectionPool arguments

	Usage:
		pool = create_oracle_pool(
			user="admin",
			password="secret",
			dsn="localhost:1521/XEPDB1",
			lib_dir="./instantclient_23_3"
		)
		conn = pool.acquire()
		oracleDatabase = Oracle(conn)
		oracleDatabase._pool = pool
		Record.database__ = oracleDatabase
	"""
	import oracledb
	if lib_dir:
		oracledb.init_oracle_client(lib_dir=lib_dir)

	def creator():
		return oracledb.connect(user=user, password=password, dsn=dsn)

	return ConnectionPool(
		creator=creator,
		pool_size=pool_size,
		**kwargs
	)
#--------------------------------------#
def create_mysql_pool(host, port, user, password, database,
					  ssl_ca=None, ssl_verify_cert=False, pool_size=5, **kwargs):
	"""
	Create a connection pool for MySQL.

	Args:
		host: Database host
		port: Database port
		user: Database username
		password: Database password
		database: Database name
		ssl_ca: Path to SSL CA certificate (optional)
		ssl_verify_cert: Verify SSL certificate
		pool_size: Number of connections in pool
		**kwargs: Additional ConnectionPool arguments

	Usage:
		pool = create_mysql_pool(
			host="localhost",
			port=3306,
			user="root",
			password="secret",
			database="mydb"
		)
		conn = pool.acquire()
		mysqlDatabase = MySQL(conn)
		mysqlDatabase._pool = pool
		Record.database__ = mysqlDatabase
	"""
	import mysql.connector

	def creator():
		config = {
			'host': host,
			'port': port,
			'user': user,
			'password': password,
			'database': database,
		}
		if ssl_ca:
			config['ssl_ca'] = ssl_ca
			config['ssl_verify_cert'] = ssl_verify_cert
		return mysql.connector.connect(**config)

	return ConnectionPool(
		creator=creator,
		pool_size=pool_size,
		**kwargs
	)
#--------------------------------------#
def create_postgres_pool(dsn=None, host=None, port=None, user=None,
						 password=None, database=None, sslmode=None,
						 pool_size=5, **kwargs):
	"""
	Create a connection pool for PostgreSQL.

	Args:
		dsn: Connection string (alternative to individual params)
		host: Database host
		port: Database port
		user: Database username
		password: Database password
		database: Database name
		sslmode: SSL mode (disable, allow, prefer, require, verify-ca, verify-full)
		pool_size: Number of connections in pool
		**kwargs: Additional ConnectionPool arguments

	Usage:
		# Using DSN
		pool = create_postgres_pool(
			dsn="postgres://user:pass@host:5432/db?sslmode=require"
		)

		# Using individual parameters
		pool = create_postgres_pool(
			host="localhost",
			port=5432,
			user="postgres",
			password="secret",
			database="mydb"
		)
		conn = pool.acquire()
		postgresDatabase = Postgres(conn)
		postgresDatabase._pool = pool
		Record.database__ = postgresDatabase
	"""
	import psycopg2

	def creator():
		if dsn:
			return psycopg2.connect(dsn)
		else:
			config = {}
			if host: config['host'] = host
			if port: config['port'] = port
			if user: config['user'] = user
			if password: config['password'] = password
			if database: config['database'] = database
			if sslmode: config['sslmode'] = sslmode
			return psycopg2.connect(**config)

	return ConnectionPool(
		creator=creator,
		pool_size=pool_size,
		**kwargs
	)
#--------------------------------------#
def create_azure_pool(server, database, username, password,
					  driver='{ODBC Driver 18 for SQL Server}',
					  encrypt='yes', trust_server_certificate='no',
					  pool_size=5, **kwargs):
	"""
	Create a connection pool for Azure SQL / Microsoft SQL Server.

	Args:
		server: Server address (e.g., 'myserver.database.windows.net')
		database: Database name
		username: Database username
		password: Database password
		driver: ODBC driver name
		encrypt: Enable encryption ('yes' or 'no')
		trust_server_certificate: Trust server certificate ('yes' or 'no')
		pool_size: Number of connections in pool
		**kwargs: Additional ConnectionPool arguments

	Usage:
		pool = create_azure_pool(
			server="myserver.database.windows.net",
			database="mydb",
			username="admin",
			password="secret"
		)
		conn = pool.acquire()
		azureDatabase = MicrosoftSQL(conn)
		azureDatabase._pool = pool
		Record.database__ = azureDatabase
	"""
	import pyodbc

	connection_string = (
		f'DRIVER={driver};'
		f'SERVER={server};'
		f'DATABASE={database};'
		f'UID={username};'
		f'PWD={password};'
		f'Encrypt={encrypt};'
		f'TrustServerCertificate={trust_server_certificate};'
	)

	return ConnectionPool(
		creator=lambda: pyodbc.connect(connection_string),
		pool_size=pool_size,
		**kwargs
	)
#================================================================================#
# ----- WITHOUT CONNECTION POOL -----
#================================================================================#
def initSQLite3Env():
	import sqlite3
	# Python 3.12+: use autocommit=False for proper transaction control
	# isolation_level='DEFERRED' is deprecated and doesn't work correctly in Python 3.12+
	sqlite3Connection = sqlite3.connect(AKESQLiteConfig.DATABASE_PATH, check_same_thread=True, autocommit=False)
	sqlite3Database = SQLite(sqlite3Connection)
	Record.database__ = database = sqlite3Database
# -----
def initOracleEnv():
	oracledb.init_oracle_client(lib_dir=AKEOracleConfig.CLIENT_LIB_DIR)

	load_dotenv()
	oracleConnection = oracledb.connect(
		user=AKEOracleConfig.USER,
		password=AKEOracleConfig.PASSWORD,
		dsn=AKEOracleConfig.DSN
	)
	oracleDatabase = Oracle(oracleConnection)
	Record.database__ = database = oracleDatabase
# -----
# pip3 install mysql-connector-python
def initMySQLEnv():
	import mysql.connector

	mysqlConnection = mysql.connector.connect(
		host=AKEMySQLConfig.HOST,
		port=AKEMySQLConfig.PORT,
		user=AKEMySQLConfig.USER,
		password=AKEMySQLConfig.PASSWORD,
		database=AKEMySQLConfig.DATABASE,
		ssl_verify_cert=AKEMySQLConfig.SSL_VERIFY_CERT,
		ssl_ca=AKEMySQLConfig.SSL_CA
	)
	mysqlDatabase = MySQL(mysqlConnection)
	Record.database__ = database = mysqlDatabase
# -----
# python3 -m pip install psycopg2-binary
def initPostgresEnv():
	import psycopg2

	postgresConnection = psycopg2.connect(PostgresConfig.DSN)
	postgresDatabase = Postgres(postgresConnection)
	Record.database__ = database = postgresDatabase
# -----
# https://learn.microsoft.com/en-us/azure/azure-sql/database/free-offer?view=azuresql&source=docs
# https://aka.ms/azuresqlhub

# pip3 install pyodbc
# brew install microsoft/mssql-release/msodbcsql18
def initAzureSQLEnv():
	import pyodbc

	connection_string = (
		f'DRIVER={AKEAzureConfig.DRIVER};'
		f'SERVER={AKEAzureConfig.SERVER};'
		f'DATABASE={AKEAzureConfig.DATABASE};'
		f'UID={AKEAzureConfig.USERNAME};'
		f'PWD={AKEAzureConfig.PASSWORD};'
		f'Encrypt={AKEAzureConfig.ENCRYPT};'
		f'TrustServerCertificate={AKEAzureConfig.TRUST_SERVER_CERTIFICATE};'
	)

	azureConnection = pyodbc.connect(connection_string)
	azureDatabase = MicrosoftSQL(azureConnection)
	Record.database__ = database = azureDatabase

#================================================================================#
# ----- WITH CONNECTION POOL (recommended for production) -----
#================================================================================#
def initSQLite3PoolEnv():
	"""
	Initialize SQLite with connection pooling.
	Pool settings: 5 connections, 1 hour recycle, health check enabled.
	"""
	pool = create_sqlite_pool(
		database_path=AKESQLiteConfig.DATABASE_PATH,
		pool_size=5,
		recycle=3600,
		pre_ping=True
	)
	conn = pool.acquire()
	sqlite3Database = SQLite(conn)
	sqlite3Database._pool = pool
	Record.database__ = sqlite3Database
	print(f"SQLite pool initialized: {pool.status()}")
# -----
def initOraclePoolEnv():
	"""
	Initialize Oracle with connection pooling.
	Pool settings: 5 connections, 1 hour recycle, health check enabled.
	"""
	pool = create_oracle_pool(
		user=AKEOracleConfig.USER,
		password=AKEOracleConfig.PASSWORD,
		dsn=AKEOracleConfig.DSN,
		lib_dir=AKEOracleConfig.CLIENT_LIB_DIR,
		pool_size=5,
		recycle=3600,
		pre_ping=True
	)
	conn = pool.acquire()
	oracleDatabase = Oracle(conn)
	oracleDatabase._pool = pool
	Record.database__ = oracleDatabase
	print(f"Oracle pool initialized: {pool.status()}")
# -----
def initMySQLPoolEnv():
	"""
	Initialize MySQL with connection pooling.
	Pool settings: 5 connections, 1 hour recycle, health check enabled.
	"""
	pool = create_mysql_pool(
		host=AKEMySQLConfig.HOST,
		port=AKEMySQLConfig.PORT,
		user=AKEMySQLConfig.USER,
		password=AKEMySQLConfig.PASSWORD,
		database=AKEMySQLConfig.DATABASE,
		ssl_ca=AKEMySQLConfig.SSL_CA,
		ssl_verify_cert=AKEMySQLConfig.SSL_VERIFY_CERT,
		pool_size=5,
		recycle=3600,
		pre_ping=True
	)
	conn = pool.acquire()
	mysqlDatabase = MySQL(conn)
	mysqlDatabase._pool = pool
	Record.database__ = mysqlDatabase
	print(f"MySQL pool initialized: {pool.status()}")
# -----
def initPostgresPoolEnv():
	"""
	Initialize PostgreSQL with connection pooling.
	Pool settings: 5 connections, 1 hour recycle, health check enabled.
	"""
	pool = create_postgres_pool(
		dsn=PostgresConfig.DSN,
		pool_size=5,
		recycle=3600,
		pre_ping=True
	)
	conn = pool.acquire()
	postgresDatabase = Postgres(conn)
	postgresDatabase._pool = pool
	Record.database__ = postgresDatabase
	print(f"Postgres pool initialized: {pool.status()}")
# -----
def initAzureSQLPoolEnv():
	"""
	Initialize Azure SQL with connection pooling.
	Pool settings: 5 connections, 1 hour recycle, health check enabled.
	"""
	pool = create_azure_pool(
		server=AKEAzureConfig.SERVER,
		database=AKEAzureConfig.DATABASE,
		username=AKEAzureConfig.USERNAME,
		password=AKEAzureConfig.PASSWORD,
		pool_size=5,
		recycle=3600,
		pre_ping=True
	)
	conn = pool.acquire()
	azureDatabase = MicrosoftSQL(conn)
	azureDatabase._pool = pool
	Record.database__ = azureDatabase
	print(f"Azure SQL pool initialized: {pool.status()}")
#================================================================================#
# ----- WITH NATIVE CONNECTION POOL (recommended for high concurrency) -----
#================================================================================#
def initOracleNativePoolEnv():
	"""
	Initialize Oracle with native connection pooling (oracledb.create_pool).
	More efficient than generic pool for high-concurrency scenarios.
	"""
	pool = create_oracle_native_pool(
		user=AKEOracleConfig.USER,
		password=AKEOracleConfig.PASSWORD,
		dsn=AKEOracleConfig.DSN,
		lib_dir=AKEOracleConfig.CLIENT_LIB_DIR,
		min_connections=2,
		max_connections=10
	)
	conn = pool.acquire()
	oracleDatabase = Oracle(conn)
	oracleDatabase._pool = pool
	Record.database__ = oracleDatabase
	print(f"Oracle native pool initialized: min={pool.min}, max={pool.max}, opened={pool.opened}")
# -----
def initMySQLNativePoolEnv():
	"""
	Initialize MySQL with native connection pooling (mysql.connector.pooling).
	"""
	pool = create_mysql_native_pool(
		host=AKEMySQLConfig.HOST,
		port=AKEMySQLConfig.PORT,
		user=AKEMySQLConfig.USER,
		password=AKEMySQLConfig.PASSWORD,
		database=AKEMySQLConfig.DATABASE,
		ssl_ca=AKEMySQLConfig.SSL_CA,
		ssl_verify_cert=AKEMySQLConfig.SSL_VERIFY_CERT,
		pool_name="mysql_native_pool",
		pool_size=5
	)
	conn = pool.get_connection()
	mysqlDatabase = MySQL(conn)
	mysqlDatabase._pool = pool
	Record.database__ = mysqlDatabase
	print(f"MySQL native pool initialized: name={pool.pool_name}, size={pool.pool_size}")
# -----
def initPostgresNativePoolEnv():
	"""
	Initialize PostgreSQL with native connection pooling (psycopg2.pool.ThreadedConnectionPool).
	Thread-safe pool for concurrent access.
	"""
	pool = create_postgres_native_pool(
		dsn=PostgresConfig.DSN,
		min_connections=2,
		max_connections=10
	)
	conn = pool.getconn()
	postgresDatabase = Postgres(conn)
	postgresDatabase._pool = pool
	Record.database__ = postgresDatabase
	print(f"Postgres native pool initialized")
#=================================================================================#