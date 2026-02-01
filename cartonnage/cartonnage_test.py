#!/usr/bin/python3
# from cartonnage import *
from ake_cartonnage import *

from decimal import Decimal
from datetime import date

import time
start = time.time()


#================================================================================#
from ake_connections import *
initSQLite3Env()
# initOracleEnv()
# initMySQLEnv()
# initPostgresEnv()
# initAzureSQLEnv()

# ----- Pooled versions (recommended) -----
# initSQLite3PoolEnv()
# initOraclePoolEnv()
# initMySQLPoolEnv()
# initPostgresPoolEnv()
# initAzureSQLPoolEnv()

# initOracleNativePoolEnv()
# initMySQLNativePoolEnv()
# initPostgresNativePoolEnv()

placeholder = Record.database__.placeholder()
#================================================================================#
class __Record(Record): pass

class Regions(Record): pass
class Countries(Record): pass
class Departments(Record): pass
class Jobs(Record): pass
class Job_History(Record): pass
class Locations(Record): pass
class Employees(Record): pass
class Dependents(__Record): pass

class RegionsAlias(Regions): pass
class CountriesAlias(Countries): pass
class DepartmentsAlias(Departments): pass
class JobsAlias(Jobs): pass
class Job_HistoryAlias(Job_History): pass
class LocationsAlias(Locations): pass
class EmployeesAlias(Employees): pass
class DependentsAlias(Dependents): pass

class Managers(Employees): pass

class EXCLUDED(Record): pass # used for upsert
class S(Record): pass # used for upsert
class T(Record): pass # used for upsert

employeeManagerRelation = (Employees.manager_id == Managers.employee_id)
#==============================================================================#
try:
	emp = (
		Employees()
		.where(Employees.first_name == 'Steve')
		.value(employee_id=1000, first_name='Ahmed', last_name='ELSamman')
		.insert()
	)
except Exception as e:
	# will raise and exception because you added where to an insert statement
	print(e)
	
recordset = Recordset.fromDicts(Employees,
	[
		{'employee_id': 5, 'first_name': "Mickey", 'last_name': "Mouse"},
		{'employee_id': 6, 'first_name': "Donald", 'last_name': "Duck"}
	]
)

assert recordset.data == [{'employee_id': 5, 'first_name': 'Mickey', 'last_name': 'Mouse'}, {'employee_id': 6, 'first_name': 'Donald', 'last_name': 'Duck'}], recordset.toDicts()

session = Session(Record.database__)
session.set(recordset.insert_())
recordset.set(phone_number='+201011223344')
session.set(recordset.update_())
session.commit()
insertedEmployeesAfterUpdate = (
	Employees().where(Employees.employee_id.in_([5,6])).select(selected="employee_id, first_name, last_name, phone_number")
)
assert insertedEmployeesAfterUpdate.recordset.data == [{'employee_id': 5, 'first_name': 'Mickey', 'last_name': 'Mouse', 'phone_number': '+201011223344'}, {'employee_id': 6, 'first_name': 'Donald', 'last_name': 'Duck', 'phone_number': '+201011223344'}], insertedEmployeesAfterUpdate.recordset.data
session.set(recordset.delete_(onColumns=["employee_id"]))
session.commit()

#==============================================================================#
# 1. Non-Recursive CTE (all databases)
# WITH sales_summary AS (
#     SELECT region, SUM(amount) as total
#     FROM sales
#     GROUP BY region
# )
# SELECT * FROM sales_summary;
# 5. Multiple CTEs (all databases)
# WITH 
#     cte1 AS (SELECT ...),
#     cte2 AS (SELECT ... FROM cte1)
# SELECT * FROM cte2;

## PostgreSQL/MySQL/SQLite
# cte = """
# WITH RECURSIVE Hierarchy AS (
#     SELECT /*+ MATERIALIZE */ employee_id, manager_id, first_name FROM Employees WHERE manager_id IS NULL
#     UNION ALL
#     SELECT C.employee_id, C.manager_id, C.first_name FROM Employees C INNER JOIN Hierarchy Hierarchy ON C.manager_id = Hierarchy.employee_id
# )
# SELECT * FROM Hierarchy
# """

# cte = """
# WITH RECURSIVE Hierarchy AS (
#     -- Anchor 1: top-level managers (no manager)
#     SELECT employee_id, manager_id, first_name, CAST('ROOT' AS CHAR(20)) as type FROM Employees WHERE manager_id IS NULL
#     UNION ALL
#     -- Anchor 2: specific department heads
#     SELECT employee_id, manager_id, first_name, CAST('DEPT_HEAD' AS CHAR(20)) as type FROM Employees WHERE employee_id IN (108, 114, 120)
#     UNION ALL
#     -- Recursive: their subordinates
#     SELECT C.employee_id, C.manager_id, C.first_name, CAST('SUBORDINATE' AS CHAR(20)) FROM Employees C INNER JOIN Hierarchy Hierarchy ON C.manager_id = Hierarchy.employee_id
# )
# SELECT * FROM Hierarchy
# """

### Oracle
# cte = """
# WITH Hierarchy (employee_id, manager_id, first_name) AS (
#     SELECT employee_id, manager_id, first_name FROM Employees P WHERE P.manager_id IS NULL
#     UNION ALL
#     SELECT c.employee_id, c.manager_id, c.first_name FROM Employees C INNER JOIN Hierarchy Hierarchy ON C.manager_id = Hierarchy.employee_id
# )
# SELECT * FROM Hierarchy
# """

### Recursive CTE - MSSQL (no RECURSIVE keyword)
# cte = """
# WITH Hierarchy AS (
#     SELECT employee_id, manager_id, first_name FROM Employees P WHERE P.manager_id IS NULL
#     UNION ALL
#     SELECT c.employee_id, c.manager_id, c.first_name FROM Employees C INNER JOIN Hierarchy Hierarchy ON C.manager_id = Hierarchy.employee_id
# )
# SELECT * FROM hierarchy
# OPTION (MAXRECURSION 100);
# """

# ee1 = CTE(p_select.statement, p_select.parameters)
# ee2 = CTE(c_select.statement, c_select.parameters)

# ================================================================================
# Recursive depth column
# Lateral
# Transaction savepoints	SAVEPOINT/ROLLBACK TO support	Low
# =============== SELECT, INSERT, UPDATE, and DELETE Record WithCTE ===============
class Hierarchy(Record): pass # for recursive CTE
class P(Employees): pass
class C(Employees): pass
class ExecutivesDepartment(Departments): pass
class AdministrationJobs(Jobs): pass

hierarchy = Hierarchy() # used as subquery ... IN (SELECT * FROM Hierarchy) # Hierarchy is Recursive CTE

# Oracle: use hints after SELECT
# 'MySQL': Not support 'Default Behavior'
# 'MicrosoftSQL': Not supported directly, Uses temp tables instead.

#  ['Oracle', 'MySQL', 'MicrosoftSQL']:
cte1 = (
	P()
	.where(P.manager_id.is_null())
	.cte(selected='/*+ INLINE */ employee_id, manager_id, first_name', materialization=None)
)
cte2 = (
	C()
	.join(Hierarchy, (C.manager_id == Hierarchy.employee_id))
	.where(C.first_name == 'Neena')
	.cte(selected='/*+ MATERIALIZE */ C.employee_id, C.manager_id, C.first_name', materialization=None)
)
cte3 = (
	ExecutivesDepartment()
	.where(ExecutivesDepartment.department_name == 'Executive')
	.cte(selected='/*+ INLINE */ ExecutivesDepartment.*', materialization=None)
)
cte4 = (
	AdministrationJobs()
	.where(AdministrationJobs.job_title.like('Administration%'))
	.cte(selected='/*+ MATERIALIZE */ AdministrationJobs.*', materialization=None)
)

if Record.database__.name in ['SQLite3', 'Postgres']:
	cte1.materialization=False
	cte2.materialization=True
	cte3.materialization=False
	cte4.materialization=True


# ^ union: recursive_cte = (cte1 ^ cte2)
# Recursive CTE wit UINION only supported by: SQLite3, MySQL, Postgres.
recursive_cte = (cte1 + cte2)
recursive_cte.alias = "Hierarchy" # you have to set alias for Recursive CTE

# columnsAliases used for Oracle only but they are accepted syntax if you didn't remove it from the test for SQLite3, MySQL, Postgres, and MicrosoftSQL.
recursive_cte.columnsAliases = "employee_id, manager_id, first_name"

# ee.materialization(True) # Error: materialization with recursive

# RECURSIVE: Required for MySQL and Postgres. Optional for SQLite3.
# RECURSIVE: are not used by Oracle and MicrosoftSQL.
if Record.database__.name in ['Oracle', 'MicrosoftSQL']:
	with_cte = WithCTE((cte3 >> cte4 >> recursive_cte), recursive=False)
elif Record.database__.name in ['Postgres']:
	"""
	CYCLE Detection (PostgreSQL 14+): CYCLE employee_id SET is_cycle USING path
	SEARCH Clause (PostgreSQL 14+): SEARCH DEPTH FIRST BY employee_id SET ordercol
	"""
	# with_cte = WithCTE((cte3 >> cte4 >> recursive_cte), recursive=True, options='CYCLE employee_id SET is_cycle USING path')
	with_cte = WithCTE((cte3 >> cte4 >> recursive_cte), recursive=True, options='SEARCH DEPTH FIRST BY employee_id SET ordercol')
else:# ['SQLite3', 'MySQL']
	with_cte = WithCTE((cte3 >> cte4 >> recursive_cte), recursive=True)

sql_query = f"{with_cte.value} SELECT * FROM Hierarchy" # build on top of generated WITH CTE
print(sql_query)

print("Raw SQL:")
# Run SELECT WITH CTE as raw/plain SQL
rec = Record(statement=sql_query, parameters=with_cte.parameters, operation=Database.select)
for r in rec:
	print(r.data)

print("Cartonnage:")

if(Record.database__.name not in ['Oracle']):
	emp = (
		Employees()
		.with_cte(with_cte)
		.where(Employees.employee_id.in_subquery(hierarchy, selected='employee_id'))
		.set(salary = 2000)
		.update()
	)

	# sqlite3 returns -1 for complex operations not the real affected rows count
	if(Record.database__.name in ['SQLite3']):
		assert emp.rowsCount() == -1, emp.rowsCount()
	else:
		assert emp.rowsCount() == 2, emp.rowsCount()

	print(f"{'-'*80}")
	print(emp.query__.statement)
	print(emp.query__.parameters)

emp = (
	Employees()
	.with_cte(with_cte)
	.join(Hierarchy, (Employees.employee_id == Hierarchy.employee_id))
	.join(ExecutivesDepartment, (Employees.department_id == ExecutivesDepartment.department_id))
	.join(AdministrationJobs, (Employees.job_id == AdministrationJobs.job_id))
)
if Record.database__.name in ['MicrosoftSQL']:
	# MSSQL MAXRECURSION Option: OPTION (MAXRECURSION 100)
	emp.select(option='OPTION (MAXRECURSION 100)')
else:
	emp.select()

for r in emp:
	print(r.data)

print(f"{'-'*80}")
print(emp.query__.statement)
print(emp.query__.parameters)

if(Record.database__.name not in ['Oracle']):
	emp = (
		Employees()
		.with_cte(with_cte)
		.where(Employees.employee_id.in_subquery(hierarchy, selected='employee_id'))
		.delete()
	)

	# sqlite3 returns -1 for complex operations not the real affected rows count
	if(Record.database__.name in ['SQLite3']):
		assert emp.rowsCount() == -1, emp.rowsCount()
	else:
		assert emp.rowsCount() == 2, emp.rowsCount()

	print(f"{'-'*80}")
	print(emp.query__.statement)
	print(emp.query__.parameters)

# print("After delete - checking if in transaction:")
# print(f"autocommit: {emp.database__._Database__connection.autocommit if hasattr(emp.database__._Database__connection, 'autocommit') else 'N/A'}")
Record.database__.rollback()  # Force rollback
# =============================== Recordset WithCTE ===============================
employees = Recordset()
emp1 = (
	Employees()
	.value(employee_id = 100)
	.select()
).set(last_name='Ahmed')
emp2 = (
	Employees()
	.value(employee_id = 101)
	.select()
).set(last_name='kamal')

employees.add(emp1, emp2)

if not (Record.database__.name == "Oracle"):
	# add with_cte and filters to Recordset through it's first Record instance
	emp1.with_cte(with_cte).where(Employees.employee_id.in_subquery(hierarchy, selected='employee_id'))
	# use onColumns if you are not sure all columns are null free
	employees.update(onColumns=["employee_id"])

	# Insert, Update, and Delete with Recursive CTE is not tracked on SQLite3 and MicrosoftSQL
	if(Record.database__.name in ["SQLite3", "MicrosoftSQL"]):
		assert employees.rowsCount() == -1, employees.rowsCount
	else:
		assert employees.rowsCount() == 2, employees.rowsCount

	# This will delete only 100, But 101 will not be deleted ? why because database will evaluate CTE after each deletion !
	# after deleteing 100 which is the only parent with manager_id=null will be no parent qualified with manager_id=null
	# so when no parent then no childs ! so 101 will not available with the second iteration to be deleted.
	employees.delete(onColumns=["employee_id"])


	if(Record.database__.name in ["SQLite3", "MicrosoftSQL"]):
		assert employees.rowsCount() == -1, employees.rowsCount
	else:
		assert employees.rowsCount() == 1, employees.rowsCount

	availableEmployeesAfterDeletion = (
		Employees()
		.where(Employees.employee_id.in_([100,101]))
		.select(selected="employee_id")
	)
	availableEmployees = [{'employee_id': 101}]
	assert availableEmployeesAfterDeletion.recordset.data == availableEmployees, availableEmployeesAfterDeletion.recordset.data

	# now I will delete 101 to test Recordset insertion WithCTE
	# use onColumns if you are not sure all columns are null free
	availableEmployeesAfterDeletion.delete()

# Record.database__._Database__cursor.execute("SELECT employee_id FROM Employees WHERE employee_id IN (100, 101)")
# print("RAW CHECK:", Record.database__._Database__cursor.fetchall())

if (Record.database__.name not in ["Oracle", "MySQL"]):

	employees.insert()

	if(Record.database__.name in ["SQLite3", "MicrosoftSQL"]):
		assert employees.rowsCount() == -1, employees.rowsCount
	else:
		assert employees.rowsCount() == 2, employees.rowsCount

Record.database__.rollback()  # Force rollback
#==============================================================================#
print("---------------------------------------00---------------------------------------")
#==============================================================================#
jobSubQuery = (Jobs().where(Jobs.job_title.in_(['Programmer', 'Purchasing Clerk'])))
departmentExistsQuery = (
	Departments().where(
		(Employees.department_id == Departments.department_id) &
		Departments.department_name.in_(['IT', 'Purchasing'])
	)
)

EmployeesConditions = (
	(Employees.employee_id.in_([115, 103])) &
	(Employees.last_name.in_(['Khoo', 'Hunold'])) &
	(Employees.department_id.not_in([12])) &
	(Employees.commission_pct.is_null()) &
	(Employees.phone_number.is_not_null()) &
	(Employees.email.like('alexander%')) &
	(Employees.employee_id.between(103, 116)) &
	(Employees.employee_id > 102) &
	(Employees.employee_id >= 103) &
	(Employees.employee_id <= 115) &
	(Employees.employee_id < 116) &
	(Employees.hire_date.between(datetime.strptime('1990-01-02', '%Y-%m-%d'), datetime.strptime('1995-05-18', '%Y-%m-%d'))) &
	(Employees.hire_date > datetime.strptime('1990-01-02', '%Y-%m-%d')) &
	(Employees.hire_date >= datetime.strptime('1990-01-02', '%Y-%m-%d')) &
	(Employees.hire_date <= datetime.strptime('1995-05-18', '%Y-%m-%d')) &
	(Employees.hire_date < datetime.strptime('1995-05-19', '%Y-%m-%d')) &
	(Employees.job_id.in_subquery(jobSubQuery, selected="job_id")) &
	(Employees._.exists(departmentExistsQuery))
)

employee = (
	Employees().join(Managers, employeeManagerRelation)
	.join(Jobs, (Employees.job_id == Jobs.job_id))
	.join(Departments, (Employees.department_id == Departments.department_id))
	.join(Locations, (Departments.location_id == Locations.location_id))
	.join(Countries, (Locations.country_id == Countries.country_id))
	.join(Regions, (Countries.region_id == Regions.region_id))

	.where(Jobs.job_title.in_(['Programmer', 'Purchasing Clerk']))
	.where(Departments.department_name.in_(['IT', 'Purchasing']))

	.where(EmployeesConditions | EmployeesConditions).where(EmployeesConditions & EmployeesConditions)
	
	.in_(employee_id = [115, 103], last_name = ['Khoo', 'Hunold'])
	.not_in(department_id = [12])
	.is_null(commission_pct = None)
	.is_not_null(phone_number = None)
	.like(email = 'alexander%')
	.gt(employee_id = 102)
	.ge(employee_id = 103)
	.le(employee_id = 115)
	.lt(employee_id = 116)
	.between(employee_id = (103, 116))
	.between(hire_date = (datetime.strptime('1990-01-02', '%Y-%m-%d'), datetime.strptime('1995-05-18', '%Y-%m-%d')))
	.gt(hire_date = datetime.strptime('1990-01-01', '%Y-%m-%d'))
	.ge(hire_date = datetime.strptime('1990-01-02', '%Y-%m-%d'))
	.le(hire_date = datetime.strptime('1995-05-18', '%Y-%m-%d'))
	.lt(hire_date = datetime.strptime('1995-05-19', '%Y-%m-%d'))
	.in_subquery(job_id = jobSubQuery, selected="job_id")
	.exists(_=departmentExistsQuery)

	.filter_.where(EmployeesConditions | EmployeesConditions).where(EmployeesConditions & EmployeesConditions)

	.filter_.in_(employee_id = [115, 103], last_name = ['Khoo', 'Hunold'])
	.not_in(department_id = [12])
	.is_null(commission_pct = None)
	.is_not_null(phone_number = None)
	.like(email = 'alexander%')
	.between(employee_id = (103, 116))
	.gt(employee_id = 102)
	.ge(employee_id = 103)
	.le(employee_id = 115)
	.lt(employee_id = 116)
	.between(hire_date = (datetime.strptime('1990-01-02', '%Y-%m-%d'), datetime.strptime('1995-05-18', '%Y-%m-%d')))
	.gt(hire_date = datetime.strptime('1990-01-01', '%Y-%m-%d'))
	.ge(hire_date = datetime.strptime('1990-01-02', '%Y-%m-%d'))
	.le(hire_date = datetime.strptime('1995-05-18', '%Y-%m-%d'))
	.lt(hire_date = datetime.strptime('1995-05-19', '%Y-%m-%d'))
	.in_subquery(job_id = jobSubQuery, selected="job_id")
	.exists(_=departmentExistsQuery)
)



employee.value(first_name='Alex') # set the first_name field/column exact value to search by.
employee.value(first_name='Alexander') # override first_name field/column exact value to search by.

# '%Y-%m-%d %H:%M:%S'

employee.select(selected='Employees.*, Jobs.*, Departments.*, Locations.*, Countries.*, Regions.*, Managers.employee_id AS "manager_employee_id"', order_by="Employees.employee_id", limit=employee.limit(1,2)) # page_number, records_per_page

for emp in employee.recordset.iterate():
	# oracle # 'hire_date': datetime(1994, 6, 7, 0, 0)
	# mysql | postgres | microsoft azure/sql # 'hire_date': date(1994, 6, 7)
	# microsoft azure/sql # 'salary': Decimal('8300.00')
	emp.hire_date = str(emp.hire_date)[:10] # convert datetime to str # emp.hire_date.strftime('%Y-%m-%d')
	emp.salary = float(emp.salary)
	emp.min_salary = float(emp.min_salary)
	emp.max_salary = float(emp.max_salary)

assert employee.columns == ['employee_id', 'first_name', 'last_name', 'email', 'phone_number', 'hire_date', 'job_id', 'salary', 'commission_pct', 'manager_id', 'department_id', 'job_id', 'job_title', 'min_salary', 'max_salary', 'department_id', 'department_name', 'manager_id', 'location_id', 'location_id', 'street_address', 'postal_code', 'city', 'state_province', 'country_id', 'country_id', 'country_name', 'region_id', 'region_id', 'region_name', 'manager_employee_id']
assert employee.recordset.data == [{'employee_id': 103, 'first_name': 'Alexander', 'last_name': 'Hunold', 'email': 'alexander.hunold@sqltutorial.org', 'phone_number': '590.423.4567', 'hire_date': '1990-01-03', 'job_id': 9, 'salary': 9000, 'commission_pct': None, 'manager_id': None, 'department_id': 6, 'job_title': 'Programmer', 'min_salary': 4000, 'max_salary': 10000, 'department_name': 'IT', 'location_id': 1400, 'street_address': '2014 Jabberwocky Rd', 'postal_code': '26192', 'city': 'Southlake', 'state_province': 'Texas', 'country_id': 'US', 'country_name': 'United States of America', 'region_id': 2, 'region_name': 'Americas', 'manager_employee_id': 102}, {'employee_id': 115, 'first_name': 'Alexander', 'last_name': 'Khoo', 'email': 'alexander.khoo@sqltutorial.org', 'phone_number': '515.127.4562', 'hire_date': '1995-05-18', 'job_id': 13, 'salary': 3100, 'commission_pct': None, 'manager_id': None, 'department_id': 3, 'job_title': 'Purchasing Clerk', 'min_salary': 2500, 'max_salary': 5500, 'department_name': 'Purchasing', 'location_id': 1700, 'street_address': '2004 Charade Rd', 'postal_code': '98199', 'city': 'Seattle', 'state_province': 'Washington', 'country_id': 'US', 'country_name': 'United States of America', 'region_id': 2, 'region_name': 'Americas', 'manager_employee_id': 114}]
assert employee.recordset.toLists() == [[103, 'Alexander', 'Hunold', 'alexander.hunold@sqltutorial.org', '590.423.4567', '1990-01-03', 9, 9000, None, None, 6, 'Programmer', 4000, 10000, 'IT', 1400, '2014 Jabberwocky Rd', '26192', 'Southlake', 'Texas', 'US', 'United States of America', 2, 'Americas', 102], [115, 'Alexander', 'Khoo', 'alexander.khoo@sqltutorial.org', '515.127.4562', '1995-05-18', 13, 3100, None, None, 3, 'Purchasing Clerk', 2500, 5500, 'Purchasing', 1700, '2004 Charade Rd', '98199', 'Seattle', 'Washington', 'US', 'United States of America', 2, 'Americas', 114]]
assert employee.recordset.toDicts() == employee.recordset.data
assert employee.recordset.columns() == employee.columns
assert employee.rowsCount() == 2
#==============================================================================#
print("---------------------------------------01---------------------------------------")
#==============================================================================#
# read section 00 in sql_cartonnage_test.py and write a test scenatio for each feature included in this section:
# Expressive filtering:
# Join two tables
# Join Same table
# like()
# is_null()
# is_not_null()
# in_
# not_in
# between
# gt
# ge
# le
# lt
# filter using multiple kwargs
# & | expressions
# & | filters

# filter using Record.field = exact value
employee = Employees().value(employee_id=100).select()
employee.hire_date = str(employee.hire_date)[:10] # convert datetime to str
employee.salary = float(employee.salary)
assert employee.data == {'employee_id': 100, 'first_name': 'Steven', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': '1987-06-17', 'job_id': 4, 'salary': 24000, 'commission_pct': None, 'manager_id': None, 'department_id': 9}

# filter using Record.where(expression)
employee = (Employees().where(Employees.employee_id == 100).select())
employee.hire_date = str(employee.hire_date)[:10] # convert datetime to str
employee.salary = float(employee.salary)
assert employee.data == {'employee_id': 100, 'first_name': 'Steven', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': '1987-06-17', 'job_id': 4, 'salary': 24000, 'commission_pct': None, 'manager_id': None, 'department_id': 9}

# join two tables
employee = (
	Employees()
	.join(Dependents, (Employees.employee_id == Dependents.employee_id))
	.where(Dependents.first_name == "Jennifer")
	.select(selected="Employees.*")
)
employee.hire_date = str(employee.hire_date)[:10] # convert datetime to str
employee.salary = float(employee.salary)
assert employee.data == {'employee_id': 100, 'first_name': 'Steven', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': '1987-06-17', 'job_id': 4, 'salary': 24000, 'commission_pct': None, 'manager_id': None, 'department_id': 9}

# join same table
employee = (
	Employees()
	.join(Managers, (Employees.manager_id == Managers.employee_id))
	.where(Managers.first_name == 'Lex')
	.select(selected='Employees.*, Managers.employee_id AS "manager_employee_id", Managers.email AS "manager_email"') # selected columns
)
employee.hire_date = str(employee.hire_date)[:10] # convert datetime to str
employee.salary = float(employee.salary)
assert employee.data == {'employee_id': 103, 'first_name': 'Alexander', 'last_name': 'Hunold', 'email': 'alexander.hunold@sqltutorial.org', 'phone_number': '590.423.4567', 'hire_date': '1990-01-03', 'job_id': 9, 'salary': 9000, 'commission_pct': None, 'manager_id': 102, 'department_id': 6, 'manager_employee_id': 102, 'manager_email': 'lex.de haan@sqltutorial.org'}

# filter using like() # use two diffent filteration methods
employee = (
	Employees()
	.like(first_name = 'Stev%') # calls internally Record.filter_.like()
	.where(Employees.first_name.like('Stev%')) # calls internally Record.filter_.like()
	.select()
)
employee.hire_date = str(employee.hire_date)[:10] # convert datetime to str
employee.salary = float(employee.salary)
assert employee.data == {'employee_id': 100, 'first_name': 'Steven', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': '1987-06-17', 'job_id': 4, 'salary': 24000, 'commission_pct': None, 'manager_id': None, 'department_id': 9}

# filter using is_null() # use two diffent filteration methods
employee = (
	Employees()
	.is_null(manager_id = None) # calls internally Record.filter_.is_null()
	.where(Employees.manager_id.is_null()) # calls internally Record.filter_.where()
	.select()
)
employee.hire_date = str(employee.hire_date)[:10] # convert datetime to str
employee.salary = float(employee.salary)
assert employee.data == {'employee_id': 100, 'first_name': 'Steven', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': '1987-06-17', 'job_id': 4, 'salary': 24000, 'commission_pct': None, 'manager_id': None, 'department_id': 9}

# filter using is_not_null() # use two diffent filteration methods
employee = (
	Employees()
	.where(employee_id = 101)
	.is_not_null(manager_id = None) # calls internally Record.filter_.is_not_null()
	.where(Employees.manager_id.is_not_null()) # calls internally Record.filter_.where()
	.select()
)
employee.hire_date = str(employee.hire_date)[:10] # convert datetime to str
employee.salary = float(employee.salary)
assert employee.data == {'employee_id': 101, 'first_name': 'Neena', 'last_name': 'Kochhar', 'email': 'neena.kochhar@sqltutorial.org', 'phone_number': '515.123.4568', 'hire_date': '1989-09-21', 'job_id': 5, 'salary': 17000, 'commission_pct': None, 'manager_id': 100, 'department_id': 9}

# filter using in_() # use two diffent filteration methods
employee = (
	Employees()
	.in_(employee_id = [100]) # calls internally Record.filter_.in_()
	.where(Employees.employee_id.in_([100])) # calls internally Record.filter_.where()
	.select()
)
employee.hire_date = str(employee.hire_date)[:10] # convert datetime to str
employee.salary = float(employee.salary)
assert employee.data == {'employee_id': 100, 'first_name': 'Steven', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': '1987-06-17', 'job_id': 4, 'salary': 24000, 'commission_pct': None, 'manager_id': None, 'department_id': 9}

# filter using not_in() # use two diffent filteration methods
employee = (
	Employees()
	.where(Employees.first_name.like('Alex%'))
	.not_in(employee_id = [115]) # calls internally Record.filter_.like()
	.where(Employees.employee_id.not_in([115])) # calls internally Record.filter_.where()
	.select()
)
employee.hire_date = str(employee.hire_date)[:10] # convert datetime to str
employee.salary = float(employee.salary)
assert employee.data == {'employee_id': 103, 'first_name': 'Alexander', 'last_name': 'Hunold', 'email': 'alexander.hunold@sqltutorial.org', 'phone_number': '590.423.4567', 'hire_date': '1990-01-03', 'job_id': 9, 'salary': 9000, 'commission_pct': None, 'manager_id': 102, 'department_id': 6}

# filter using between() # use two diffent filteration methods
employee = (
	Employees()
	.between(employee_id = (100, 101)) # calls internally Record.filter_.between()
	.where(Employees.employee_id.between(100, 101)) # calls internally Record.filter_.where()
	.select()
)
for e in employee:
	e.hire_date = str(e.hire_date)[:10] # convert datetime to str
	e.salary = float(e.salary)
assert employee.recordset.data == [
	{'employee_id': 100, 'first_name': 'Steven', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': '1987-06-17', 'job_id': 4, 'salary': 24000, 'commission_pct': None, 'manager_id': None, 'department_id': 9},
	{'employee_id': 101, 'first_name': 'Neena', 'last_name': 'Kochhar', 'email': 'neena.kochhar@sqltutorial.org', 'phone_number': '515.123.4568', 'hire_date': '1989-09-21', 'job_id': 5, 'salary': 17000, 'commission_pct': None, 'manager_id': 100, 'department_id': 9}
]

# filter using gt(), ge(), le(), and lt() # use two diffent filteration methods
# use filter chaining # use & expressions
employee = (
	Employees()
	.gt(employee_id = 99).ge(employee_id = 100).le(employee_id = 101).lt(employee_id = 102) # calls internally Record.filter_.XY()
	.where(
		(Employees.employee_id > 99) &
		(Employees.employee_id >= 100) &
		(Employees.employee_id <= 101) &
		(Employees.employee_id < 102)
	) # calls internally Record.filter_.where()
	.select()
)
for e in employee:
	e.hire_date = str(e.hire_date)[:10] # convert datetime to str
	e.salary = float(e.salary)
assert employee.recordset.data == [
	{'employee_id': 100, 'first_name': 'Steven', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': '1987-06-17', 'job_id': 4, 'salary': 24000, 'commission_pct': None, 'manager_id': None, 'department_id': 9}, 
	{'employee_id': 101, 'first_name': 'Neena', 'last_name': 'Kochhar', 'email': 'neena.kochhar@sqltutorial.org', 'phone_number': '515.123.4568', 'hire_date': '1989-09-21', 'job_id': 5, 'salary': 17000, 'commission_pct': None, 'manager_id': 100, 'department_id': 9}
]

# & | filters and expressions
f1 = (
	((Employees.employee_id == 100) & (Employees.first_name == "Steven")) |
	((Employees.employee_id == 101) & (Employees.first_name == "Neena"))
)

f2 = (
	((Employees.employee_id == 102) & (Employees.first_name == "Lex")) |
	((Employees.employee_id == 103) & (Employees.first_name == "Alexander"))
)

employee = (
	Employees()
	.where(f1 | f2)
	.select()
)
for e in employee:
	e.hire_date = str(e.hire_date)[:10] # convert datetime to str
	e.salary = float(e.salary)
assert employee.recordset.data == [
	{'employee_id': 100, 'first_name': 'Steven', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': '1987-06-17', 'job_id': 4, 'salary': 24000, 'commission_pct': None, 'manager_id': None, 'department_id': 9}, 
	{'employee_id': 101, 'first_name': 'Neena', 'last_name': 'Kochhar', 'email': 'neena.kochhar@sqltutorial.org', 'phone_number': '515.123.4568', 'hire_date': '1989-09-21', 'job_id': 5, 'salary': 17000, 'commission_pct': None, 'manager_id': 100, 'department_id': 9}, 
	{'employee_id': 102, 'first_name': 'Lex', 'last_name': 'De Haan', 'email': 'lex.de haan@sqltutorial.org', 'phone_number': '515.123.4569', 'hire_date': '1993-01-13', 'job_id': 5, 'salary': 17000, 'commission_pct': None, 'manager_id': 100, 'department_id': 9}, 
	{'employee_id': 103, 'first_name': 'Alexander', 'last_name': 'Hunold', 'email': 'alexander.hunold@sqltutorial.org', 'phone_number': '590.423.4567', 'hire_date': '1990-01-03', 'job_id': 9, 'salary': 9000, 'commission_pct': None, 'manager_id': 102, 'department_id': 6}
]

# filter using multiple kwargs # use two diffent filteration methods
employee = (
	Employees()
	.like(first_name = 'Stev%', last_name = 'Ki%') # calls internally Record.filter_.like()
	.select()
)
employee.hire_date = str(employee.hire_date)[:10] # convert datetime to str
employee.salary = float(employee.salary)
assert employee.data == {'employee_id': 100, 'first_name': 'Steven', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': '1987-06-17', 'job_id': 4, 'salary': 24000, 'commission_pct': None, 'manager_id': None, 'department_id': 9}
#==============================================================================#
print("---------------------------------------02---------------------------------------")
#==============================================================================#
# select all and get recordset [all records] count, convert them to list of Dictionaries/lists
reg = Regions().all()

assert reg.recordset.count() == 4
assert reg.columns == ['region_id', 'region_name']
assert reg.recordset.toDicts() == [{'region_id': 1, 'region_name': 'Europe'}, {'region_id': 2, 'region_name': 'Americas'}, {'region_id': 3, 'region_name': 'Asia'}, {'region_id': 4, 'region_name': 'Middle East and Africa'}]
assert reg.recordset.toLists() == [[1, 'Europe'], [2, 'Americas'], [3, 'Asia'], [4, 'Middle East and Africa']]
#==============================================================================#
print("---------------------------------------03---------------------------------------")
#==============================================================================#
# insert single record
emp1 = Employees()
emp1.data = {'employee_id': 19950519, 'first_name': 'William', 'last_name': 'Wallace', 'email': None, 'phone_number': '555.666.777'}
emp1.insert()
# assert emp1.rowsCount() == 1 # confirm number of inserted rows

# update single record
emp1 = (
	Employees()
	.value(employee_id=19950519)
	.set(email='william.wallace@sqltutorial.org', phone_number=None)
	.update()
)
# assert emp1.rowsCount() == 1 # confirm number of updated rows

# check updated record
emp1 = Employees()
emp1.value(employee_id=19950519).select()
employee.hire_date = str(employee.hire_date)[:10] # convert datetime to str
employee.salary = float(employee.salary)
assert emp1.data == {'employee_id': 19950519, 'first_name': 'William', 'last_name': 'Wallace', 'email': 'william.wallace@sqltutorial.org', 'phone_number': None, 'hire_date': None, 'job_id': None, 'salary': None, 'commission_pct': None, 'manager_id': None, 'department_id': None}

# delete by exists and subquery
emp1 = (
	EmployeesAlias()
	.where(
		(Dependents.employee_id == EmployeesAlias.employee_id) &
		(EmployeesAlias.email == 'william.gietz@sqltutorial.org') &
		(EmployeesAlias.employee_id.in_([206]))
	)
)

emp2 = Employees().where(Employees.manager_id == 205)

dep1 = (
	Dependents()
	.exists( _ = emp1)
	.in_subquery(employee_id = emp2, selected="employee_id")
	.where(Dependents._.exists(emp1))
	.where(Dependents.employee_id.in_subquery(emp2, selected="employee_id"))
	.delete()
)

assert dep1.rowsCount() == 1

dep1 = Dependents()
dep1.where(Dependents.employee_id == 206).select()
assert dep1.data == {}

Record.database__.rollback()  # Force rollback
#==============================================================================#
print("---------------------------------------04---------------------------------------")
# #==============================================================================#
# filter and fetchmany records into recordset
jobs = Jobs().where(Jobs.job_title.like('%Accountant%')).select()

assert jobs.recordset.count() == 2
assert jobs.columns == ['job_id', 'job_title', 'min_salary', 'max_salary']
assert jobs.recordset.toLists() == [[1, 'Public Accountant', 4200, 9000], [6, 'Accountant', 4200, 9000]]
assert jobs.recordset.toDicts() == [{'job_id': 1, 'job_title': 'Public Accountant', 'min_salary': 4200, 'max_salary': 9000}, {'job_id': 6, 'job_title': 'Accountant', 'min_salary': 4200, 'max_salary': 9000}]
print("----------02A----------")
# iterate over recordset and update records one by one: (not recommended if you can update with one predicate)
for job in jobs:
	job.set(min_salary=4500)

jobs.recordset.set(min_salary=5000)

for job in jobs.recordset: # iterate over recordset
	assert job.job_id in [1,6], job.job_id


jobs.recordset.update()
recordsetLen = len(jobs.recordset) # get len() of a Recordset
assert recordsetLen == 2, recordsetLen

### it works because no field in any record of the recordset's records is set to Null.
### but if you are not sure that if your recordset's records have a Null value you have to set the onColumns parameter.
# jobs.recordset.update(onColumns=['job_id'])

jobs = Jobs().where(Jobs.job_title.like('%Accountant%')).select()
assert jobs.recordset.toLists() == [[1, 'Public Accountant', 5000, 9000], [6, 'Accountant', 5000, 9000]], jobs.recordset.toLists() # confirm recordset update

secondJobInRecordset = jobs.recordset[1] # access record instance by index
assert secondJobInRecordset.job_id == 6, secondJobInRecordset.job_id

print("----------02B----------")
jobs.recordset.delete()

### it works because no field in any record of the recordset's records is set to Null.
### but if you are not sure that if your recordset's records have a Null value you have to set the onColumns parameter.
# jobs.recordset.delete(onColumns=['job_id'])

print("----------02C----------")
jobs = Jobs().where(Jobs.job_title.like('%Accountant%')).select()

assert jobs.recordset.toLists() == []  # confirm recordset delete

Record.database__.rollback()  # Force rollback
#==============================================================================#
print("---------------------------------------05---------------------------------------")
#==============================================================================#
# recordset from list of dicts

recordset = Recordset.fromDicts(Employees,
	[
		{'employee_id': 5, 'first_name': "Mickey", 'last_name': "Mouse"},
		{'employee_id': 6, 'first_name': "Donald", 'last_name': "Duck"}
	]
)

assert recordset.data == [{'employee_id': 5, 'first_name': 'Mickey', 'last_name': 'Mouse'}, {'employee_id': 6, 'first_name': 'Donald', 'last_name': 'Duck'}], recordset.toDicts()

# instantiate recordset
recordset = Recordset()

# create employee(s)/record(s) instances
e1 = Employees().value(employee_id=5, first_name="Mickey", last_name="Mouse")
e2 = Employees().value(employee_id=6, first_name="Donald", last_name="Duck")

# add employee(s)/record(s) instances to the previously instantiated Recordset
recordset.add(e1, e2)

# Recordset insert:
recordset.insert()
if Record.database__.name == "MicrosoftSQL":
	pass
else:
	assert recordset.rowsCount() == 2, recordset.rowsCount() # not work for Azure/MicrosoftSQL only SQlite3/Oracle/MySQL/Postgres

e1.set(manager_id=77)
e2.set(manager_id=88)
e1.where(Employees.employee_id > 4) # add general condition to all records of the recordset

# Recordset update:
recordset.update()

if Record.database__.name == "MicrosoftSQL":
	employees = Employees().in_(manager_id = [77, 88]).select()
	assert employees.recordset.toLists() == [[5, 'Mickey', 'Mouse', None, None, None, None, None, None, 77, None], [6, 'Donald', 'Duck', None, None, None, None, None, None, 88, None]]
else:
	assert recordset.rowsCount() == 2 # not work for Azure/MicrosoftSQL only SQlite3/Oracle/MySQL/Postgres

# Recordset delete:
e1.where(Employees.manager_id < 100) # add general condition to all records of the recordset
recordset.delete()

if Record.database__.name == "MicrosoftSQL":
	employees = Employees().in_(manager_id = [77, 88]).select()
	assert employees.recordset.toLists() == []
else:
	assert recordset.rowsCount() == 2 # not work for Azure/MicrosoftSQL only SQlite3/Oracle/MySQL/Postgres

Record.database__.rollback()  # Force rollback
#==============================================================================#
print("---------------------------------------06---------------------------------------")
# #==============================================================================#
# Execute raw sql statement and get recordset of the returned rows
records = Record(statement="SELECT * FROM Employees WHERE employee_id IN(100, 101, 102) ", operation=Database.select)
assert records.recordset.count() == 3
for record in records:
	assert record.employee_id in [100, 101, 102]

# Execute parameterized sql statement and get recordset of the returned rows
placeholder = Record.database__.placeholder()
records = Record(statement=f"SELECT * FROM Employees WHERE employee_id IN({placeholder}, {placeholder}, {placeholder})", parameters=(100, 101, 102), operation=Database.select)
assert records.recordset.count() == 3
for record in records:
	assert record.employee_id in [100, 101, 102]

# instantiating Class's instance with fields' values
employee = Employees(statement=None, parameters=None, employee_id=1000, first_name="Super", last_name="Man", operation=Database.select)
employee.insert()

employee = Employees().value(employee_id=1000).select()
assert employee.data == {'employee_id': 1000, 'first_name': 'Super', 'last_name': 'Man', 'email': None, 'phone_number': None, 'hire_date': None, 'job_id': None, 'salary': None, 'commission_pct': None, 'manager_id': None, 'department_id': None}
#==============================================================================#
print("---------------------------------------07---------------------------------------")
# #==============================================================================#
# group_by with HAVING clause
employees = Employees().select(selected='manager_id, count(1) AS "count"', group_by='manager_id HAVING count(1) > 4', order_by='manager_id ASC')

assert employees.recordset.data == [
	{'manager_id': 100, 'count': 14}, {'manager_id': 101, 'count': 5}, 
	{'manager_id': 108, 'count': 5}, {'manager_id': 114, 'count': 5}
], employees.recordset.data
#==============================================================================#
print("---------------------------------------08---------------------------------------")
# #==============================================================================#
emp = Employees().where(Employees.first_name.in_(['Steven', 'Neena']))

emp1 = Employees().set(**{'employee_id': 100, 'first_name': 'Ahmed', 'salary': 4000})
emp2 = Employees().set(**{'employee_id': 101, 'first_name': 'Kamal', 'salary': 5000})

# you can also set_.new = {} directly if you are sure of the datatype(s) validation
emp1.set__.new = {'employee_id': 100, 'first_name': 'Ahmed', 'salary': 4000}
emp2.set__.new = {'employee_id': 101, 'first_name': 'Kamal', 'salary': 5000}

rs = Recordset()
rs.add(emp1, emp2)

if(Record.database__.name in ["SQLite3", "Postgres"]):
	### SQLite3 and Postgres
	emp1.where(
		(EXCLUDED.salary < Employees.salary) & 
		(Employees.last_name.in_subquery(emp, selected='last_name'))
	)
if(Record.database__.name in ["Oracle", "MicrosoftSQL"]):
	## Oracle and MicroftSQL
	emp1.where(
		(S.salary < T.salary) & 
		(T.last_name.in_subquery(emp, selected='last_name'))
	)

rs.upsert(onColumns='employee_id')
print(emp1.query__.statement)
print(emp1.query__.parameters)

emp = Employees().where(Employees.employee_id.in_([100,101])).select()

if(Record.database__.name == "SQLite3"):
	### SQLite3
	assert emp.recordset.data == [{'employee_id': 100, 'first_name': 'Ahmed', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': '1987-06-17', 'job_id': 4, 'salary': 4000, 'commission_pct': None, 'manager_id': None, 'department_id': 9}, {'employee_id': 101, 'first_name': 'Kamal', 'last_name': 'Kochhar', 'email': 'neena.kochhar@sqltutorial.org', 'phone_number': '515.123.4568', 'hire_date': '1989-09-21', 'job_id': 5, 'salary': 5000, 'commission_pct': None, 'manager_id': 100, 'department_id': 9}], emp.recordset.data
if(Record.database__.name == "Oracle"):
	### Oracle
	assert emp.recordset.data == [{'employee_id': 100, 'first_name': 'Ahmed', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': datetime(1987, 6, 17, 0, 0), 'job_id': 4, 'salary': 4000, 'commission_pct': None, 'manager_id': None, 'department_id': 9}, {'employee_id': 101, 'first_name': 'Kamal', 'last_name': 'Kochhar', 'email': 'neena.kochhar@sqltutorial.org', 'phone_number': '515.123.4568', 'hire_date': datetime(1989, 9, 21, 0, 0), 'job_id': 5, 'salary': 5000, 'commission_pct': None, 'manager_id': 100, 'department_id': 9}], emp.recordset.data
if(Record.database__.name in ["MySQL", "Postgres", "MicrosoftSQL"]):
	### MySQL | Postgres | Microsoft AzureSQL
	assert emp.recordset.data == [{'employee_id': 100, 'first_name': 'Ahmed', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': date(1987, 6, 17), 'job_id': 4, 'salary': Decimal('4000.00'), 'commission_pct': None, 'manager_id': None, 'department_id': 9}, {'employee_id': 101, 'first_name': 'Kamal', 'last_name': 'Kochhar', 'email': 'neena.kochhar@sqltutorial.org', 'phone_number': '515.123.4568', 'hire_date': date(1989, 9, 21), 'job_id': 5, 'salary': Decimal('5000.00'), 'commission_pct': None, 'manager_id': 100, 'department_id': 9}], emp.recordset.data

Record.database__.rollback()
#==============================================================================#
print("---------------------------------------09 Expression Tests---------------------------------------")
#==============================================================================#
emp = (
	Employees()
	.set(
		first_name=Expression("UPPER(first_name)")
		, last_name=Expression("LOWER(last_name)")
		, email=Expression("first_name || '.' || last_name || '@test.com'")
		, salary=Expression('salary + 100')
		, commission_pct=Expression('COALESCE(commission_pct, 1)')
	)
	.value(employee_id=100)
	.where(
		(Employees.salary == Expression('salary')) &
		(Employees.salary == Expression('salary + 0'))
	)
	.update()
	.select(selected="first_name, last_name, email, salary, commission_pct")
)

assert emp.data == {'first_name': 'STEVEN', 'last_name': 'king', 'email': 'Steven.King@test.com', 'salary': 24100, 'commission_pct': 1}, emp.data
print("---------------------------------------Expression Tests Complete---------------------------------------")

Record.database__.rollback() # Record.database__.commit()
Record.database__.close()
print("---------------------------------------ALL FEATURES TESTED---------------------------------------")
print(f"{Record.database__.name} Operations Count: {Record.database__.operationsCount}")
# assert Record.database__.operationsCount == 13

end = time.time()
print(end - start)
#==============================================================================#
print("---------------------------------------COMPREHENSIVE TEST---------------------------------------")
#==============================================================================#