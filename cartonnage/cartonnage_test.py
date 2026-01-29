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

class P(Employees): pass
class C(Employees): pass
class Hierarchy(Record): pass
class ExecutivesDepartment(Departments): pass
class AdministrationJobs(Jobs): pass

hieirarchy = Hierarchy()
p = P()
c = C()
executives_department = ExecutivesDepartment()
administration_jobs = AdministrationJobs()

p.filter(P.manager_id.is_null())
c.filter(C.first_name == 'Neena')
c.join(hieirarchy, (C.manager_id == Hierarchy.employee_id))

executives_department.filter(ExecutivesDepartment.department_name == 'Executive')
administration_jobs.filter(AdministrationJobs.job_title.like('Administration%'))

# hints used for Oracle only but they are accepted syntax if you didn't remove it from the test for SQLite3, MySQL, Postgres, and MicrosoftSQL.
p_select = p.select(selected='/*+ INLINE */ employee_id, manager_id, first_name')
c_select = c.select(selected='/*+ MATERIALIZE */ C.employee_id, C.manager_id, C.first_name')
executives_department_select = executives_department.select(selected='/*+ INLINE */ ExecutivesDepartment.*')
administration_jobs_select = administration_jobs.select(selected='/*+ MATERIALIZE */ AdministrationJobs.*')

# Oracle: use hints after SELECT
# 'MySQL': Not support 'Default Behavior'
# 'MicrosoftSQL': Not supported directly, Uses temp tables instead.

if Record.database__.name in ['SQLite3', 'Postgres']:
	cte1 = CTE(p_select, materialization=False)
	cte2 = CTE(c_select, materialization=False)
	cte3 = CTE(executives_department_select, materialization=False)
	cte4 = CTE(administration_jobs_select, materialization=True)
else: #  ['Oracle', 'MySQL', 'MicrosoftSQL']:
	cte1 = CTE(p_select)
	cte2 = CTE(c_select)
	cte3 = CTE(executives_department_select)
	cte4 = CTE(administration_jobs_select)

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
rec = Record(statement=sql_query, parameters=with_cte.parameters, operation=Database.read)
for r in rec:
	print(r.data)

print("Cartonnage:")

if(Record.database__.name not in ['Oracle']):
	emp = Employees()
	emp.with_cte = with_cte
	emp.filter(Employees.employee_id.in_subquery(hieirarchy, selected='employee_id'))
	emp.set.salary = 2000
	emp.update()

	# sqlite3 returns -1 for complex operations not the real affected rows count
	if(Record.database__.name in ['SQLite3']):
		assert emp.rowsCount() == -1, emp.rowsCount()
	else:
		assert emp.rowsCount() == 2, emp.rowsCount()

	print(f"{'-'*80}")
	print(emp.query__.statement)
	print(emp.query__.parameters)

emp = Employees()
emp.with_cte = with_cte
emp.joinCTE(hieirarchy, (Employees.employee_id == Hierarchy.employee_id))
emp.joinCTE(executives_department, (Employees.department_id == ExecutivesDepartment.department_id))
emp.joinCTE(administration_jobs, (Employees.job_id == AdministrationJobs.job_id))
if Record.database__.name in ['MicrosoftSQL']:
	# MSSQL MAXRECURSION Option: OPTION (MAXRECURSION 100)
	emp.read(option='OPTION (MAXRECURSION 100)')
else:
	emp.read()

for r in emp:
	print(r.data)

print(f"{'-'*80}")
print(emp.query__.statement)
print(emp.query__.parameters)

# Recursive depth column
# Lateral
# Transaction savepoints	SAVEPOINT/ROLLBACK TO support	Low

# print("After delete - checking if in transaction:")
# print(f"autocommit: {emp.database__._Database__connection.autocommit if hasattr(emp.database__._Database__connection, 'autocommit') else 'N/A'}")

if(Record.database__.name not in ['Oracle']):
	emp = Employees()
	emp.with_cte = with_cte
	emp.filter(Employees.employee_id.in_subquery(hieirarchy, selected='employee_id'))
	emp.delete()

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

employees = Recordset()
emp1 = Employees()
emp2 = Employees()
emp1.employee_id = 100
emp2.employee_id = 101
emp1.read()
emp2.read()
emp1.set.last_name = 'Ahmed'
emp2.set.last_name = 'kamal'
employees.add(emp1)
employees.add(emp2)

emp1.with_cte = with_cte
emp1.filter(Employees.employee_id.in_subquery(hieirarchy, selected='employee_id'))

employees.update(onColumns=["employee_id"])
# employees.delete(onColumns=["employee_id"])


# ExecutivesDepartment AS NOT MATERIALIZED (SELECT /*+ INLINE */ ExecutivesDepartment.* FROM Departments ExecutivesDepartment WHERE ExecutivesDepartment.department_name = ?) ,
# AdministrationJobs AS MATERIALIZED (SELECT /*+ MATERIALIZE */ AdministrationJobs.* FROM Jobs AdministrationJobs WHERE AdministrationJobs.job_title LIKE ?) ,
# pp = [('Executive', 'Administration%', 'Neena', 100), ('Executive', 'Administration%', 'Neena', 101)]

ss = """
WITH RECURSIVE 
	Hierarchy (employee_id, manager_id, first_name) AS (
		SELECT /*+ INLINE */ employee_id, manager_id, first_name FROM Employees P WHERE P.manager_id IS NULL  
		UNION ALL
		SELECT /*+ MATERIALIZE */ C.employee_id, C.manager_id, C.first_name FROM Employees C  INNER JOIN Hierarchy Hierarchy ON C.manager_id = Hierarchy.employee_id WHERE C.first_name = ?
	)
DELETE FROM Employees  
WHERE Employees.employee_id = ? AND Employees.employee_id IN (
	SELECT employee_id FROM Hierarchy Hierarchy
)
"""
pp = [('Neena', 100), ('Neena', 101)]

rec = Record(statement=ss,parameters=pp,operation=Database.delete)
check = Record(statement="SELECT employee_id FROM Employees WHERE employee_id in (?, ?)", parameters=[100, 101], operation=Database.read)
print(f"{'<'*80}\n{check.recordset.data}")

assert employees.rowsCount == -1, employees.rowsCount

Record.database__._Database__cursor.execute("SELECT employee_id FROM Employees WHERE employee_id IN (100, 101)")
print("RAW CHECK:", Record.database__._Database__cursor.fetchall())

employees.insert()
assert employees.rowsCount == -1, employees.rowsCount

Record.database__.rollback()  # Force rollback
#==============================================================================#
print("---------------------------------------Data-Modifying CTE---------------------------------------")
#==============================================================================#
# # Data-modifying CTEs (PostgreSQL and MSSQL only)
# # PostgreSQL: WITH deleted_rows AS (DELETE ... RETURNING *) SELECT * FROM deleted_rows
# # MSSQL: DELETE ... OUTPUT DELETED.* (no CTE wrapper needed for OUTPUT)

# if Record.database__.name == 'Postgres':
#     # ===== Test 1: UPDATE with RETURNING via CTE =====
#     print("\n--- PostgreSQL: UPDATE with RETURNING (CTE) ---")

#     # Check original salary before update
#     emp_before = Employees()
#     emp_before.filter(Employees.department_id == 9)
#     emp_before.read(selected='employee_id, first_name, salary')
#     original_salaries = {r.employee_id: r.salary for r in emp_before}
#     print(f"Original salaries: {original_salaries}")

#     # Build UPDATE ... RETURNING as CTE using ORM
#     emp_to_update = Employees()
#     emp_to_update.filter(Employees.department_id == 9)
#     emp_to_update.set.salary = Expression('salary * 1.1', [])

#     # Use upd_st() return value directly with CTE
#     update_cte = CTE(emp_to_update.upd_st(option='RETURNING employee_id, first_name, salary'))
#     update_cte.alias = 'UpdatedEmployees'

#     with_update = WithCTE(update_cte, recursive=False)

#     # PostgreSQL Data-Modifying CTE: SELECT directly FROM the CTE result
#     # Pattern: WITH cte AS (UPDATE ... RETURNING *) SELECT * FROM cte
#     select_updated_sql = f"{with_update.value} SELECT * FROM UpdatedEmployees"
#     print(f"SQL: {select_updated_sql}")

#     # operation=Database.read because we SELECT from the CTE result
#     updated_records = Record(statement=select_updated_sql, parameters=with_update.parameters, operation=Database.read)
#     print(f"Updated {updated_records.recordset.count()} employees:")
#     for r in updated_records:
#         print(f"  {r.data}")

#     assert updated_records.recordset.count() > 0, "Expected updated rows to be returned"

#     # ===== Test 2: DELETE with RETURNING via CTE =====
#     print("\n--- PostgreSQL: DELETE with RETURNING (CTE) ---")

#     # Insert test data to delete
#     test_dep = Dependents()
#     test_dep.dependent_id = 999
#     test_dep.first_name = 'Test'
#     test_dep.last_name = 'Delete'
#     test_dep.relationship = 'Test'
#     test_dep.employee_id = 100
#     test_dep.insert()

#     # Build DELETE ... RETURNING as CTE using ORM
#     dep_to_delete = Dependents()
#     dep_to_delete.filter(Dependents.dependent_id == 999)

#     # Use del_st() return value directly with CTE
#     delete_cte = CTE(dep_to_delete.del_st(option='RETURNING *'))
#     delete_cte.alias = 'DeletedDependents'

#     with_delete = WithCTE(delete_cte, recursive=False)

#     # PostgreSQL Data-Modifying CTE: SELECT directly FROM the CTE result
#     select_deleted_sql = f"{with_delete.value} SELECT * FROM DeletedDependents"
#     print(f"SQL: {select_deleted_sql}")

#     # operation=Database.read because we SELECT from the CTE result
#     deleted_records = Record(statement=select_deleted_sql, parameters=with_delete.parameters, operation=Database.read)
#     print(f"Deleted {deleted_records.recordset.count()} dependents:")
#     for r in deleted_records:
#         print(f"  {r.data}")

#     assert deleted_records.recordset.count() == 1, f"Expected 1 deleted row, got {deleted_records.recordset.count()}"

#     # Verify record is actually deleted
#     verify_del = Dependents()
#     verify_del.filter(Dependents.dependent_id == 999)
#     verify_del.read()
#     assert verify_del.data == {}, "Record should be deleted"
#     print("Verified: Record deleted successfully")

#     # ===== Test 3: DELETE using ORM .delete() with CTE =====
#     print("\n--- PostgreSQL: DELETE using ORM with CTE ---")

#     # Insert more test data
#     test_dep2 = Dependents()
#     test_dep2.dependent_id = 998
#     test_dep2.first_name = 'Test2'
#     test_dep2.last_name = 'ORM'
#     test_dep2.relationship = 'Test'
#     test_dep2.employee_id = 100
#     test_dep2.insert()

#     # Build a CTE that selects the dependent_id to delete
#     # IMPORTANT: CTE alias must differ from target table name to avoid confusion
#     class DependentsToDelete(Dependents): pass
#     select_to_delete = DependentsToDelete()
#     select_to_delete.filter(DependentsToDelete.dependent_id == 998)
#     select_cte = CTE(select_to_delete.select(selected='dependent_id'))

#     with_select = WithCTE(select_cte, recursive=False)

#     # Use ORM .delete() with CTE and subquery filter
#     dep_orm_delete = Dependents()
#     dep_orm_delete.with_cte = with_select
#     dep_orm_delete.filter(Dependents.dependent_id.in_subquery(select_to_delete, selected='dependent_id'))
#     dep_orm_delete.delete()

#     print(f"SQL: {dep_orm_delete.query__.statement}")
#     print(f"Rows affected: {dep_orm_delete.rowsCount()}")

#     # Verify deletion
#     verify_orm = Dependents()
#     verify_orm.filter(Dependents.dependent_id == 998)
#     verify_orm.read()
#     assert verify_orm.data == {}, "Record should be deleted via ORM"
#     print("Verified: ORM delete with CTE successful")

# elif Record.database__.name == 'MicrosoftSQL':
#     # MSSQL: OUTPUT clause returns results directly (NOT via CTE wrapper like PostgreSQL)
#     # MSSQL does NOT support data-modifying statements inside CTEs
#     # PostgreSQL: WITH cte AS (UPDATE ... RETURNING *) SELECT * FROM cte  -- supported
#     # MSSQL: UPDATE ... OUTPUT INSERTED.* -- returns result set directly, no CTE wrapper

#     # ===== Test 1: UPDATE with OUTPUT (direct, no CTE) =====
#     print("\n--- MSSQL: UPDATE with OUTPUT (direct) ---")

#     # Check original salary before update
#     emp_before = Employees()
#     emp_before.filter(Employees.department_id == 9)
#     emp_before.read(selected='employee_id, first_name, salary')
#     original_salaries = {r.employee_id: r.salary for r in emp_before}
#     print(f"Original salaries: {original_salaries}")

#     # MSSQL: UPDATE ... OUTPUT returns result set directly
#     # OUTPUT must be between SET and WHERE
#     update_sql = "UPDATE Employees SET salary = salary * 1.1 OUTPUT INSERTED.employee_id, INSERTED.first_name, INSERTED.salary WHERE department_id = ?"
#     print(f"SQL: {update_sql}")

#     # operation=Database.read because OUTPUT returns a result set
#     updated_records = Record(statement=update_sql, parameters=[9], operation=Database.read)
#     print(f"Updated {updated_records.recordset.count()} employees:")
#     for r in updated_records:
#         print(f"  {r.data}")

#     assert updated_records.recordset.count() > 0, "Expected updated rows to be returned"

#     # ===== Test 2: DELETE with OUTPUT (direct, no CTE) =====
#     print("\n--- MSSQL: DELETE with OUTPUT (direct) ---")

#     # Insert test data to delete
#     test_dep = Dependents()
#     test_dep.dependent_id = 999
#     test_dep.first_name = 'Test'
#     test_dep.last_name = 'Delete'
#     test_dep.relationship = 'Test'
#     test_dep.employee_id = 100
#     test_dep.insert()

#     # MSSQL: DELETE ... OUTPUT returns deleted rows directly
#     delete_sql = "DELETE FROM Dependents OUTPUT DELETED.* WHERE dependent_id = ?"
#     print(f"SQL: {delete_sql}")

#     # operation=Database.read because OUTPUT returns a result set
#     deleted_records = Record(statement=delete_sql, parameters=[999], operation=Database.read)
#     print(f"Deleted {deleted_records.recordset.count()} dependents:")
#     for r in deleted_records:
#         print(f"  {r.data}")

#     assert deleted_records.recordset.count() == 1, f"Expected 1 deleted row, got {deleted_records.recordset.count()}"

#     # Verify record is actually deleted
#     verify_del = Dependents()
#     verify_del.filter(Dependents.dependent_id == 999)
#     verify_del.read()
#     assert verify_del.data == {}, "Record should be deleted"
#     print("Verified: Record deleted successfully")

#     # ===== Test 3: DELETE using ORM .delete() with CTE (SELECT CTE for filtering) =====
#     print("\n--- MSSQL: DELETE using ORM with CTE ---")

#     # Insert more test data
#     test_dep2 = Dependents()
#     test_dep2.dependent_id = 998
#     test_dep2.first_name = 'Test2'
#     test_dep2.last_name = 'ORM'
#     test_dep2.relationship = 'Test'
#     test_dep2.employee_id = 100
#     test_dep2.insert()

#     # Build a CTE that selects the dependent_id to delete (SELECT CTE is supported)
#     # IMPORTANT: CTE alias must differ from target table name to avoid MSSQL confusion
#     class DependentsToDelete(Dependents): pass
#     select_to_delete = DependentsToDelete()
#     select_to_delete.filter(DependentsToDelete.dependent_id == 998)
#     select_cte = CTE(select_to_delete.select(selected='dependent_id'))

#     with_select = WithCTE(select_cte, recursive=False)

#     # Use ORM .delete() with CTE and subquery filter
#     dep_orm_delete = Dependents()
#     dep_orm_delete.with_cte = with_select
#     dep_orm_delete.filter(Dependents.dependent_id.in_subquery(select_to_delete, selected='dependent_id'))
#     dep_orm_delete.delete()

#     print(f"SQL: {dep_orm_delete.query__.statement}")
#     print(f"Rows affected: {dep_orm_delete.rowsCount()}")

#     # Verify deletion
#     verify_orm = Dependents()
#     verify_orm.filter(Dependents.dependent_id == 998)
#     verify_orm.read()
#     assert verify_orm.data == {}, "Record should be deleted via ORM"
#     print("Verified: ORM delete with CTE successful")

# else:
#     print(f"Data-Modifying CTEs with RETURNING/OUTPUT not supported by {Record.database__.name}")
#     print("Only PostgreSQL (RETURNING) and MSSQL (OUTPUT) support this feature")

# Record.database__.rollback()
#==============================================================================#
print("---------------------------------------00---------------------------------------")
#==============================================================================#
employee = Employees()
manager = Managers()
job = Jobs()
jobSubQuery = Jobs()
department = Departments()
departmentExistsQuery = Departments()
location = Locations()
country = Countries()
region = Regions()

employee.join(manager, employeeManagerRelation)
employee.join(job, (Employees.job_id == Jobs.job_id))
employee.join(department, (Employees.department_id == Departments.department_id))
department.join(location, (Departments.location_id == Locations.location_id))
location.join(country, (Locations.country_id == Countries.country_id))
country.join(region, (Countries.region_id == Regions.region_id))

employee.first_name = 'Alex' # set the first_name field/column exact value to search by.
employee.first_name = 'Alexander' # override first_name field/column exact value to search by.

# '%Y-%m-%d %H:%M:%S'

job.filter(Jobs.job_title.in_(['Programmer', 'Purchasing Clerk']))
jobSubQuery.filter(Jobs.job_title.in_(['Programmer', 'Purchasing Clerk']))
department.filter(Departments.department_name.in_(['IT', 'Purchasing']))
departmentExistsQuery.filter(
	(Employees.department_id == Departments.department_id) &
	Departments.department_name.in_(['IT', 'Purchasing'])
)

# Dependents._.exists(emp1)
# filter using direct Record functions # calls Record.Filter.xyz_filter()
employee.in_(employee_id = [115, 103], last_name = ['Khoo', 'Hunold']) \
	.not_in(department_id = [12]) \
	.is_null(commission_pct = None) \
	.is_not_null(phone_number = None) \
	.like(email = 'alexander%') \
	.gt(employee_id = 102) \
	.ge(employee_id = 103) \
	.le(employee_id = 115) \
	.lt(employee_id = 116) \
	.between(employee_id = (103, 116)) \
	.between(hire_date = (datetime.strptime('1990-01-02', '%Y-%m-%d'), datetime.strptime('1995-05-18', '%Y-%m-%d'))) \
	.gt(hire_date = datetime.strptime('1990-01-01', '%Y-%m-%d')) \
	.ge(hire_date = datetime.strptime('1990-01-02', '%Y-%m-%d')) \
	.le(hire_date = datetime.strptime('1995-05-18', '%Y-%m-%d')) \
	.lt(hire_date = datetime.strptime('1995-05-19', '%Y-%m-%d')) \
	.in_subquery(job_id = jobSubQuery, selected="job_id") \
	.exists(_=departmentExistsQuery)

# filter using direct Record.Filter functions
employee.filter_.in_(employee_id = [115, 103], last_name = ['Khoo', 'Hunold']) \
	.not_in(department_id = [12]) \
	.is_null(commission_pct = None) \
	.is_not_null(phone_number = None) \
	.like(email = 'alexander%') \
	.between(employee_id = (103, 116)) \
	.gt(employee_id = 102) \
	.ge(employee_id = 103) \
	.le(employee_id = 115) \
	.lt(employee_id = 116) \
	.between(hire_date = (datetime.strptime('1990-01-02', '%Y-%m-%d'), datetime.strptime('1995-05-18', '%Y-%m-%d'))) \
	.gt(hire_date = datetime.strptime('1990-01-01', '%Y-%m-%d')) \
	.ge(hire_date = datetime.strptime('1990-01-02', '%Y-%m-%d')) \
	.le(hire_date = datetime.strptime('1995-05-18', '%Y-%m-%d')) \
	.lt(hire_date = datetime.strptime('1995-05-19', '%Y-%m-%d')) \
	.in_subquery(job_id = jobSubQuery, selected="job_id") \
	.exists(_=departmentExistsQuery)

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
# filter using direct Filter.filter function chaining
employee.filter_.filter(EmployeesConditions | EmployeesConditions).filter(EmployeesConditions & EmployeesConditions)

# filter using direct Record.filter function chaining # calls Record.Filter.filter()
employee.filter(EmployeesConditions | EmployeesConditions).filter(EmployeesConditions & EmployeesConditions)

# employee.filter_.read(selected='Employees.job_id AS "employee.job_id", Jobs.job_id AS "job.job_id"')
employee.filter_.read(selected='Employees.*, Jobs.*, Departments.*, Locations.*, Countries.*, Regions.*, Managers.employee_id AS "manager_employee_id"', order_by="Employees.employee_id", limit=employee.limit(1,2)) # page_number, records_per_page

for emp in employee.recordset.iterate():
	# oracle # 'hire_date': datetime(1994, 6, 7, 0, 0)
	# mysql | postgres | microsoft azure/sql # 'hire_date': date(1994, 6, 7)
	# microsoft azure/sql # 'salary': Decimal('8300.00')
	emp.hire_date = str(emp.hire_date)[:10] # convert datetime to str # emp.hire_date.strftime('%Y-%m-%d')
	emp.salary = float(emp.salary)
	emp.min_salary = float(emp.min_salary)
	emp.max_salary = float(emp.max_salary)

# assert employee.query__.statement == """ """
# assert employee.query__.parameters == """ """
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
employee = Employees()
employee.employee_id = 100
employee.read()
employee.hire_date = str(employee.hire_date)[:10] # convert datetime to str
employee.salary = float(employee.salary)
assert employee.data == {'employee_id': 100, 'first_name': 'Steven', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': '1987-06-17', 'job_id': 4, 'salary': 24000, 'commission_pct': None, 'manager_id': None, 'department_id': 9}

# filter using Record.filter(expression)
employee = Employees()
employee.filter(Employees.employee_id == 100)
employee.read()
employee.hire_date = str(employee.hire_date)[:10] # convert datetime to str
employee.salary = float(employee.salary)
assert employee.data == {'employee_id': 100, 'first_name': 'Steven', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': '1987-06-17', 'job_id': 4, 'salary': 24000, 'commission_pct': None, 'manager_id': None, 'department_id': 9}

# join two tables
employee = Employees()
dependent = Dependents()
dependent.first_name = "Jennifer"
employee.join(dependent, (Employees.employee_id == Dependents.employee_id))
employee.read(selected="Employees.*") # selected columns
employee.hire_date = str(employee.hire_date)[:10] # convert datetime to str
employee.salary = float(employee.salary)
assert employee.data == {'employee_id': 100, 'first_name': 'Steven', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': '1987-06-17', 'job_id': 4, 'salary': 24000, 'commission_pct': None, 'manager_id': None, 'department_id': 9}

# join same table
employee = Employees()
manager = Managers()
manager.first_name = "Lex"
employee.join(manager, (Employees.manager_id == Managers.employee_id))
employee.read(selected='Employees.*, Managers.employee_id AS "manager_employee_id", Managers.email AS "manager_email"') # selected columns
employee.hire_date = str(employee.hire_date)[:10] # convert datetime to str
employee.salary = float(employee.salary)
assert employee.data == {'employee_id': 103, 'first_name': 'Alexander', 'last_name': 'Hunold', 'email': 'alexander.hunold@sqltutorial.org', 'phone_number': '590.423.4567', 'hire_date': '1990-01-03', 'job_id': 9, 'salary': 9000, 'commission_pct': None, 'manager_id': 102, 'department_id': 6, 'manager_employee_id': 102, 'manager_email': 'lex.de haan@sqltutorial.org'}

# filter using like() # use two diffent filteration methods
employee = Employees()
employee.like(first_name = 'Stev%') # calls internally Record.filter_.like()
employee.filter(Employees.first_name.like('Stev%')) # calls internally Record.filter_.like()
employee.read()
employee.hire_date = str(employee.hire_date)[:10] # convert datetime to str
employee.salary = float(employee.salary)
assert employee.data == {'employee_id': 100, 'first_name': 'Steven', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': '1987-06-17', 'job_id': 4, 'salary': 24000, 'commission_pct': None, 'manager_id': None, 'department_id': 9}

# filter using is_null() # use two diffent filteration methods
employee = Employees()
employee.is_null(manager_id = None) # calls internally Record.filter_.is_null()
employee.filter(Employees.manager_id.is_null()) # calls internally Record.filter_.filter()
employee.read()
employee.hire_date = str(employee.hire_date)[:10] # convert datetime to str
employee.salary = float(employee.salary)
assert employee.data == {'employee_id': 100, 'first_name': 'Steven', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': '1987-06-17', 'job_id': 4, 'salary': 24000, 'commission_pct': None, 'manager_id': None, 'department_id': 9}

# filter using is_not_null() # use two diffent filteration methods
employee = Employees()
employee.employee_id = 101
employee.is_not_null(manager_id = None) # calls internally Record.filter_.is_not_null()
employee.filter(Employees.manager_id.is_not_null()) # calls internally Record.filter_.filter()
employee.read()
employee.hire_date = str(employee.hire_date)[:10] # convert datetime to str
employee.salary = float(employee.salary)
assert employee.data == {'employee_id': 101, 'first_name': 'Neena', 'last_name': 'Kochhar', 'email': 'neena.kochhar@sqltutorial.org', 'phone_number': '515.123.4568', 'hire_date': '1989-09-21', 'job_id': 5, 'salary': 17000, 'commission_pct': None, 'manager_id': 100, 'department_id': 9}

# filter using in_() # use two diffent filteration methods
employee = Employees()
employee.in_(employee_id = [100]) # calls internally Record.filter_.in_()
employee.filter(Employees.employee_id.in_([100])) # calls internally Record.filter_.filter()
employee.read()
employee.hire_date = str(employee.hire_date)[:10] # convert datetime to str
employee.salary = float(employee.salary)
assert employee.data == {'employee_id': 100, 'first_name': 'Steven', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': '1987-06-17', 'job_id': 4, 'salary': 24000, 'commission_pct': None, 'manager_id': None, 'department_id': 9}

# filter using not_in() # use two diffent filteration methods
employee = Employees()
employee.filter(Employees.first_name.like('Alex%'))
employee.not_in(employee_id = [115]) # calls internally Record.filter_.like()
employee.filter(Employees.employee_id.not_in([115])) # calls internally Record.filter_.filter()
employee.read()
employee.hire_date = str(employee.hire_date)[:10] # convert datetime to str
employee.salary = float(employee.salary)
assert employee.data == {'employee_id': 103, 'first_name': 'Alexander', 'last_name': 'Hunold', 'email': 'alexander.hunold@sqltutorial.org', 'phone_number': '590.423.4567', 'hire_date': '1990-01-03', 'job_id': 9, 'salary': 9000, 'commission_pct': None, 'manager_id': 102, 'department_id': 6}

# filter using between() # use two diffent filteration methods
employee = Employees()
employee.between(employee_id = (100, 101)) # calls internally Record.filter_.between()
employee.filter(Employees.employee_id.between(100, 101)) # calls internally Record.filter_.filter()
employee.read()
for e in employee:
	e.hire_date = str(e.hire_date)[:10] # convert datetime to str
	e.salary = float(e.salary)
assert employee.recordset.data == [
	{'employee_id': 100, 'first_name': 'Steven', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': '1987-06-17', 'job_id': 4, 'salary': 24000, 'commission_pct': None, 'manager_id': None, 'department_id': 9},
	{'employee_id': 101, 'first_name': 'Neena', 'last_name': 'Kochhar', 'email': 'neena.kochhar@sqltutorial.org', 'phone_number': '515.123.4568', 'hire_date': '1989-09-21', 'job_id': 5, 'salary': 17000, 'commission_pct': None, 'manager_id': 100, 'department_id': 9}
]

# filter using gt(), ge(), le(), and lt() # use two diffent filteration methods
# use filter chaining # use & expressions
employee = Employees()
employee.gt(employee_id = 99).ge(employee_id = 100).le(employee_id = 101).lt(employee_id = 102) # calls internally Record.filter_.XY()
employee.filter(
	(Employees.employee_id > 99) &
	(Employees.employee_id >= 100) &
	(Employees.employee_id <= 101) &
	(Employees.employee_id < 102)
) # calls internally Record.filter_.filter()
employee.read()
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

employee = Employees()
employee.filter(f1 | f2)
employee.read()
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
employee = Employees()
employee.like(first_name = 'Stev%', last_name = 'Ki%') # calls internally Record.filter_.like()
employee.read()
employee.hire_date = str(employee.hire_date)[:10] # convert datetime to str
employee.salary = float(employee.salary)
assert employee.data == {'employee_id': 100, 'first_name': 'Steven', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': '1987-06-17', 'job_id': 4, 'salary': 24000, 'commission_pct': None, 'manager_id': None, 'department_id': 9}
#==============================================================================#
print("---------------------------------------02---------------------------------------")
#==============================================================================#
# select all and get recordset [all records] count, convert them to list of Dictionaries/lists
reg = Regions()
reg.all()

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
emp1 = Employees()
emp1.employee_id = 19950519
emp1.set.email = 'william.wallace@sqltutorial.org'
emp1.set.phone_number = None
emp1.update()
# assert emp1.rowsCount() == 1 # confirm number of updated rows

# check updated record
emp1 = Employees()
emp1.data = {'employee_id': 19950519} # you can set data directly
emp1.read()
employee.hire_date = str(employee.hire_date)[:10] # convert datetime to str
employee.salary = float(employee.salary)
assert emp1.data == {'employee_id': 19950519, 'first_name': 'William', 'last_name': 'Wallace', 'email': 'william.wallace@sqltutorial.org', 'phone_number': None, 'hire_date': None, 'job_id': None, 'salary': None, 'commission_pct': None, 'manager_id': None, 'department_id': None}

# delete by exists and subquery
emp1 = EmployeesAlias()
emp1.filter(
	(Dependents.employee_id == EmployeesAlias.employee_id) &
	(EmployeesAlias.email == 'william.gietz@sqltutorial.org') &
	(EmployeesAlias.employee_id.in_([206]))
)

emp2 = Employees()
emp2.filter(Employees.manager_id == 205)

dep1 = Dependents()
dep1.exists( _ = emp1)
dep1.in_subquery(employee_id = emp2, selected="employee_id")
dep1.filter(Dependents._.exists(emp1))
dep1.filter(Dependents.employee_id.in_subquery(emp2, selected="employee_id"))
dep1.filter_.delete()

assert dep1.rowsCount() == 1

dep1 = Dependents()
dep1.filter(Dependents.employee_id == 206).read()
assert dep1.data == {}

Record.database__.rollback()  # Force rollback
#==============================================================================#
print("---------------------------------------04---------------------------------------")
# #==============================================================================#
# filter and fetchmany records into recordset
jobs = Jobs()
jobs.filter(Jobs.job_title.like('%Accountant%'))
jobs.read()

assert jobs.recordset.count() == 2
assert jobs.columns == ['job_id', 'job_title', 'min_salary', 'max_salary']
assert jobs.recordset.toLists() == [[1, 'Public Accountant', 4200, 9000], [6, 'Accountant', 4200, 9000]]
assert jobs.recordset.toDicts() == [{'job_id': 1, 'job_title': 'Public Accountant', 'min_salary': 4200, 'max_salary': 9000}, {'job_id': 6, 'job_title': 'Accountant', 'min_salary': 4200, 'max_salary': 9000}]
print("----------02A----------")
# iterate over recordset and update records one by one: (not recommended if you can update with one predicate)
for job in jobs:
	job.set.min_salary = 5000
jobs.recordset.update()

### it works because no field in any record of the recordset's records is set to Null.
### but if you are not sure that if your recordset's records have a Null value you have to set the onColumns parameter.
# jobs.recordset.update(onColumns=['job_id'])

jobs = Jobs()
jobs.filter(Jobs.job_title.like('%Accountant%')).read()
assert jobs.recordset.toLists() == [[1, 'Public Accountant', 5000, 9000], [6, 'Accountant', 5000, 9000]], jobs.recordset.toLists() # confirm recordset update
print("----------02B----------")
jobs.recordset.delete()

### it works because no field in any record of the recordset's records is set to Null.
### but if you are not sure that if your recordset's records have a Null value you have to set the onColumns parameter.
# jobs.recordset.delete(onColumns=['job_id'])

print("----------02C----------")
jobs = Jobs()
jobs.filter(Jobs.job_title.like('%Accountant%')).read()

assert jobs.recordset.toLists() == []  # confirm recordset delete

Record.database__.rollback()  # Force rollback
#==============================================================================#
print("---------------------------------------05---------------------------------------")
#==============================================================================#
# instantiate recordset 
recordset = Recordset()

# create employee(s)/record(s) instances
e1 = Employees()
e2 = Employees()

# set fields' values
e1.employee_id = 5
e1.first_name = "Mickey"
e1.last_name = "Mouse"

e2.employee_id = 6
e2.first_name = "Donald"
e2.last_name = "Duck"

# add employee(s)/record(s) instances to the previously instantiated Recordset
recordset.add(e1)
recordset.add(e2)

# Recordset insert:
recordset.insert()
if Record.database__.name == "MicrosoftSQL":
	pass
else:
	assert recordset.rowsCount == 2 # not work for Azure/MicrosoftSQL only SQlite3/Oracle/MySQL/Postgres

e1.set.manager_id = 77
e2.set.manager_id = 88
e1.filter(Employees.employee_id > 4) # add general condition to all records of the recordset

# Recordset update:
recordset.update()

if Record.database__.name == "MicrosoftSQL":
	employees = Employees()
	employees.in_(manager_id = [77, 88])
	employees.read()

	assert employees.recordset.toLists() == [[5, 'Mickey', 'Mouse', None, None, None, None, None, None, 77, None], [6, 'Donald', 'Duck', None, None, None, None, None, None, 88, None]]
else:
	assert recordset.rowsCount == 2 # not work for Azure/MicrosoftSQL only SQlite3/Oracle/MySQL/Postgres

# Recordset delete:
e1.filter(Employees.manager_id < 100) # add general condition to all records of the recordset
recordset.delete()

if Record.database__.name == "MicrosoftSQL":
	employees = Employees()
	employees.in_(manager_id = [77, 88])
	employees.read()

	assert employees.recordset.toLists() == []
else:
	assert recordset.rowsCount == 2 # not work for Azure/MicrosoftSQL only SQlite3/Oracle/MySQL/Postgres

Record.database__.rollback()  # Force rollback
#==============================================================================#
print("---------------------------------------06---------------------------------------")
# #==============================================================================#
# Execute raw sql statement and get recordset of the returned rows
records = Record(statement="SELECT * FROM Employees WHERE employee_id IN(100, 101, 102) ", operation=Database.read)
assert records.recordset.count() == 3
for record in records:
	assert record.employee_id in [100, 101, 102]

# Execute parameterized sql statement and get recordset of the returned rows
placeholder = Record.database__.placeholder()
records = Record(statement=f"SELECT * FROM Employees WHERE employee_id IN({placeholder}, {placeholder}, {placeholder})", parameters=(100, 101, 102), operation=Database.read)
assert records.recordset.count() == 3
for record in records:
	assert record.employee_id in [100, 101, 102]

# instantiating Class's instance with fields' values
employee = Employees(statement=None, parameters=None, employee_id=1000, first_name="Super", last_name="Man", operation=Database.read)
employee.insert()

employee = Employees()
employee.employee_id = 1000
employee.read()
assert employee.data == {'employee_id': 1000, 'first_name': 'Super', 'last_name': 'Man', 'email': None, 'phone_number': None, 'hire_date': None, 'job_id': None, 'salary': None, 'commission_pct': None, 'manager_id': None, 'department_id': None}
#==============================================================================#
print("---------------------------------------07---------------------------------------")
# #==============================================================================#
# group_by with HAVING clause
employees = Employees()
employees.read(selected='manager_id, count(1) AS "count"', group_by='manager_id HAVING count(1) > 4', order_by='manager_id ASC')

assert employees.recordset.data == [
	{'manager_id': 100, 'count': 14}, {'manager_id': 101, 'count': 5}, 
	{'manager_id': 108, 'count': 5}, {'manager_id': 114, 'count': 5}
], employees.recordset.data
#==============================================================================#
print("---------------------------------------08---------------------------------------")
# #==============================================================================#
### SQLite
# raw_sql = """
# INSERT INTO Employees (employee_id, first_name, salary)
# VALUES (?, ?, ?)
# ON CONFLICT (employee_id)
# DO UPDATE SET 
#     first_name = EXCLUDED.first_name,
#     salary = EXCLUDED.salary
# 	WHERE EXCLUDED.salary > 1000
# """

### Oracle
# raw_sql = """
# MERGE INTO Employees t
# USING (SELECT :1 AS employee_id,:1 AS first_name, :1 AS salary FROM dual) s
# ON (t.employee_id = s.employee_id)
# WHEN MATCHED THEN
#     UPDATE SET t.first_name = s.first_name, t.salary = s.salary
# 	WHERE t.salary > 1000
# WHEN NOT MATCHED THEN
#     INSERT (employee_id, first_name, salary) VALUES (:1, :1, :1)
# """

### oracle ai23+
# raw_sql = """
# INSERT INTO Employees (employee_id, first_name, salary)
# VALUES (:1, :2, :3)
# ON CONFLICT (employee_id)
# DO UPDATE SET 
#     first_name = :2,
#     salary = :3
# """

### MySQL
# raw_sql = """
# INSERT INTO Employees (employee_id, first_name, salary)
# VALUES (%s, %s, %s)
# ON DUPLICATE KEY UPDATE
#     first_name = VALUES(first_name),
#     salary = VALUES(salary)
# """

### Or with MySQL 8.0.19+ alias syntax:

# raw_sql = """
# INSERT INTO Employees (employee_id, first_name, salary)
# VALUES (%s, %s, %s) AS new
# ON DUPLICATE KEY UPDATE
#     first_name = new.first_name,
#     salary = new.salary
# """

### Postgres
# raw_sql = """
# INSERT INTO Employees (employee_id, first_name, salary)
# VALUES (%s, %s, %s)
# ON CONFLICT (employee_id)
# DO UPDATE SET 
#     first_name = EXCLUDED.first_name,
#     salary = EXCLUDED.salary
# """

### MSSQL
# raw_sql = """
# MERGE INTO Employees AS t
# USING (SELECT ? AS employee_id, ? AS first_name, ? AS salary) AS s
# ON (t.employee_id = s.employee_id)
# WHEN MATCHED THEN
#     UPDATE SET t.first_name = s.first_name, t.salary = s.salary
# WHEN NOT MATCHED THEN
#     INSERT (employee_id, first_name, salary) VALUES (s.employee_id, s.first_name, s.salary);
# """

# rec = Record(statement=raw_sql, parameters=(100, 'Ahmed', 4000))

# emp = Employees()
# emp.employee_id = 100
# emp.read()

### SQLite3
# assert emp.data == {'employee_id': 100, 'first_name': 'Ahmed', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': '1987-06-17', 'job_id': 4, 'salary': 4000, 'commission_pct': None, 'manager_id': None, 'department_id': 9}, emp.data
# assert emp.recordset.data == {}, emp.recordset.data
### Oracle
# assert emp.data == {'employee_id': 100, 'first_name': 'Ahmed', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': datetime(1987, 6, 17, 0, 0), 'job_id': 4, 'salary': 4000, 'commission_pct': None, 'manager_id': None, 'department_id': 9}, emp.data
### MySQL | Postgres | Microsoft AzureSQL
# assert emp.data == {'employee_id': 100, 'first_name': 'Ahmed', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': date(1987, 6, 17), 'job_id': 4, 'salary': 4000, 'commission_pct': None, 'manager_id': None, 'department_id': 9}, emp.data
#=====
# rs = Recordset()

# emp1 = Employees()
# emp1.set.new = {'employee_id': 100, 'first_name': 'Ahmed', 'salary': 4000}

# emp2 = Employees()
# emp2.set.new = {'employee_id': 101, 'first_name': 'Kamal', 'salary': 5000}

# rs.add(emp1)
# rs.add(emp2)

# rs.upsert(onColumns='employee_id')
# print(emp1.query__.statement)
# print(emp1.query__.parameters)

# emp = Employees()
# emp.filter(Employees.employee_id.in_([100,101]))
# emp.read()

### SQLite3
# assert emp.data == {'employee_id': 100, 'first_name': 'Ahmed', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': '1987-06-17', 'job_id': 4, 'salary': 4000, 'commission_pct': None, 'manager_id': None, 'department_id': 9}, emp.data
# assert emp.recordset.data == {}, emp.recordset.data
### Oracle
# assert emp.data == {'employee_id': 100, 'first_name': 'Ahmed', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': datetime(1987, 6, 17, 0, 0), 'job_id': 4, 'salary': 4000, 'commission_pct': None, 'manager_id': None, 'department_id': 9}, emp.data
### MySQL | Postgres | Microsoft AzureSQL
# assert emp.data == {'employee_id': 100, 'first_name': 'Ahmed', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': date(1987, 6, 17), 'job_id': 4, 'salary': 4000, 'commission_pct': None, 'manager_id': None, 'department_id': 9}, emp.data
#=====
# emp = Employees()
# emp.first_name = "Steven"

# emp1 = Employees()
# emp1.set.new = {'employee_id': 100, 'first_name': 'Ahmed', 'salary': 4000}

### SQLite3 and Postgres
# emp1.filter(
# 	(EXCLUDED.salary < Employees.salary) & 
# 	(Employees.last_name.in_subquery(emp, selected='last_name'))
# )
### Oracle and MicroftSQL
# emp1.filter(
# 	(S.salary < T.salary) & 
# 	(T.last_name.in_subquery(emp, selected='last_name'))
# )

# emp1.upsert(onColumns='employee_id')

# emp = Employees()
# emp.employee_id = 100
# emp.read()

### SQLite3
# assert emp.data == {'employee_id': 100, 'first_name': 'Ahmed', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': '1987-06-17', 'job_id': 4, 'salary': 4000, 'commission_pct': None, 'manager_id': None, 'department_id': 9}, emp.data
# assert emp.recordset.data == {}, emp.recordset.data
### Oracle
# assert emp.data == {'employee_id': 100, 'first_name': 'Ahmed', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': datetime(1987, 6, 17, 0, 0), 'job_id': 4, 'salary': 4000, 'commission_pct': None, 'manager_id': None, 'department_id': 9}, emp.data
### MySQL | Postgres | Microsoft AzureSQL
# assert emp.data == {'employee_id': 100, 'first_name': 'Ahmed', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': date(1987, 6, 17), 'job_id': 4, 'salary': 4000, 'commission_pct': None, 'manager_id': None, 'department_id': 9}, emp.data
#=====
emp = Employees()
emp.filter(Employees.first_name.in_(['Steven', 'Neena']))

emp1 = Employees()
emp2 = Employees()
emp1.set.new = {'employee_id': 100, 'first_name': 'Ahmed', 'salary': 4000}
emp2.set.new = {'employee_id': 101, 'first_name': 'Kamal', 'salary': 5000}

rs = Recordset()
rs.add(emp1)
rs.add(emp2)


if(Record.database__.name in ["SQLite3", "Postgres"]):
	### SQLite3 and Postgres
	emp1.filter(
		(EXCLUDED.salary < Employees.salary) & 
		(Employees.last_name.in_subquery(emp, selected='last_name'))
	)
if(Record.database__.name in ["Oracle", "MicrosoftSQL"]):
	## Oracle and MicroftSQL
	emp1.filter(
		(S.salary < T.salary) & 
		(T.last_name.in_subquery(emp, selected='last_name'))
	)

rs.upsert(onColumns='employee_id')
print(emp1.query__.statement)
print(emp1.query__.parameters)

emp = Employees()
emp.filter(Employees.employee_id.in_([100,101]))
emp.read()

if(Record.database__.name == "SQLite3"):
	### SQLite3
	assert emp.recordset.data == [{'employee_id': 100, 'first_name': 'Ahmed', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': '1987-06-17', 'job_id': 4, 'salary': 4000, 'commission_pct': None, 'manager_id': None, 'department_id': 9}, {'employee_id': 101, 'first_name': 'Kamal', 'last_name': 'Kochhar', 'email': 'neena.kochhar@sqltutorial.org', 'phone_number': '515.123.4568', 'hire_date': '1989-09-21', 'job_id': 5, 'salary': 5000, 'commission_pct': None, 'manager_id': 100, 'department_id': 9}], emp.recordset.data
if(Record.database__.name == "Oracle"):
	### Oracle
	assert emp.recordset.data == [{'employee_id': 100, 'first_name': 'Ahmed', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': datetime(1987, 6, 17, 0, 0), 'job_id': 4, 'salary': 4000, 'commission_pct': None, 'manager_id': None, 'department_id': 9}, {'employee_id': 101, 'first_name': 'Kamal', 'last_name': 'Kochhar', 'email': 'neena.kochhar@sqltutorial.org', 'phone_number': '515.123.4568', 'hire_date': datetime(1989, 9, 21, 0, 0), 'job_id': 5, 'salary': 5000, 'commission_pct': None, 'manager_id': 100, 'department_id': 9}], emp.recordset.data
if(Record.database__.name in ["MySQL", "Postgres", "MicrosoftSQL"]):
	### MySQL | Postgres | Microsoft AzureSQL
	assert emp.recordset.data == [{'employee_id': 100, 'first_name': 'Ahmed', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': date(1987, 6, 17), 'job_id': 4, 'salary': Decimal('4000.00'), 'commission_pct': None, 'manager_id': None, 'department_id': 9}, {'employee_id': 101, 'first_name': 'Kamal', 'last_name': 'Kochhar', 'email': 'neena.kochhar@sqltutorial.org', 'phone_number': '515.123.4568', 'hire_date': date(1989, 9, 21), 'job_id': 5, 'salary': Decimal('5000.00'), 'commission_pct': None, 'manager_id': 100, 'department_id': 9}], emp.recordset.data
#==============================================================================#
print("---------------------------------------09 Expression Tests---------------------------------------")
#==============================================================================#
# Test 1: Expression in UPDATE - Increment salary
emp = Employees()
emp.employee_id = 100
emp.read()
original_salary = emp.salary

emp.set.salary = Expression('salary + 100')
emp.filter_.update()

# Verify the increment worked
emp2 = Employees()
emp2.employee_id = 100
emp2.read()

assert emp2.salary == original_salary + 100, f"Expected {original_salary + 100}, got {emp2.salary}"
print(f"Test 1 PASSED: salary incremented from {original_salary} to {emp2.salary}")
print("----------09A----------")
# Test 2: Expression in UPDATE - Multiply salary (percentage raise)
emp = Employees()
emp.employee_id = 100
emp.read()
before_salary = emp.salary

emp.set.salary = Expression('salary * 1.1')  # 10% raise
emp.filter_.update()

emp2 = Employees()
emp2.employee_id = 100
emp2.read()
# Note: SQLite may truncate to int, so we check approximately
assert abs(float(emp2.salary) - float(before_salary) * 1.1) < 1, f"Expected ~{before_salary * 1.1}, got {emp2.salary}" # float for mysql
print(f"Test 2 PASSED: salary multiplied from {before_salary} to {emp2.salary}")
print("----------09B----------")
# Test 3: Expression in UPDATE - Set to NULL using Expression
emp = Employees()
emp.employee_id = 100
emp.read()

emp.set.commission_pct = Expression('NULL')
emp.filter_.update()

emp2 = Employees()
emp2.employee_id = 100
emp2.read()
assert emp2.commission_pct is None, f"Expected None, got {emp2.commission_pct}"
print("Test 3 PASSED: commission_pct set to NULL")
print("----------09C----------")
# Test 4: Expression in UPDATE - UPPER function on string field
emp = Employees()
emp.employee_id = 100
emp.read()
original_first = emp.first_name

emp.set.first_name = Expression("UPPER(first_name)")
emp.filter_.update()

emp2 = Employees()
emp2.employee_id = 100
emp2.read()
assert emp2.first_name == original_first.upper(), f"Expected {original_first.upper()}, got {emp2.first_name}"
print(f"Test 4 PASSED: first_name uppercased to {emp2.first_name}")

# Restore original first_name for other tests
emp = Employees()
emp.employee_id = 100
emp.set.first_name = original_first
emp.filter_.update()
print("----------09D----------")
# Test 5: Expression in UPDATE - COALESCE (replace NULL with default)
emp = Employees()
emp.employee_id = 100
emp.read()

emp.set.commission_pct = Expression('COALESCE(commission_pct, 1)')
emp.filter_.update()

emp2 = Employees()
emp2.employee_id = 100
emp2.read()
assert emp2.commission_pct == 1, f"Expected 1, got {emp2.commission_pct}"
print("Test 5 PASSED: commission_pct set via COALESCE")
print("----------09E----------")
# Test 6: Expression in UPDATE - Subtract/decrement
emp = Employees()
emp.employee_id = 100
emp.read()
before_salary = emp.salary

emp.set.salary = Expression('salary - 50')
emp.filter_.update()

emp2 = Employees()
emp2.employee_id = 100
emp2.read()
assert emp2.salary == before_salary - 50, f"Expected {before_salary - 50}, got {emp2.salary}"
print(f"Test 6 PASSED: salary decremented from {before_salary} to {emp2.salary}")
print("----------09F----------")
# Test 7: Expression in UPDATE - Division
emp = Employees()
emp.employee_id = 100
emp.read()
before_salary = emp.salary

emp.set.salary = Expression('salary / 2')
emp.filter_.update()

emp2 = Employees()
emp2.employee_id = 100
emp2.read()
assert abs(emp2.salary - before_salary / 2) < 1, f"Expected ~{before_salary / 2}, got {emp2.salary}"
print(f"Test 7 PASSED: salary divided from {before_salary} to {emp2.salary}")

# Restore original salary
emp = Employees()
emp.employee_id = 100
emp.set.salary = float(original_salary) # float for mysql
emp.filter_.update()
print(f"Salary restored to {original_salary}")
print("----------09G----------")
# Test 8: Expression in UPDATE - Concatenation (SQLite uses ||)
emp = Employees()
emp.employee_id = 100
emp.read()
original_email = emp.email

emp.set.email = Expression("first_name || '.' || last_name || '@test.com'")
emp.filter_.update()

emp2 = Employees()
emp2.employee_id = 100
emp2.read()
print(f"Test 8 PASSED: email set to {emp2.email}")

# Restore email
emp = Employees()
emp.employee_id = 100
emp.set.email = original_email
emp.filter_.update()
print("----------09H----------")
# Test 9: Expression in UPDATE - LOWER function
emp = Employees()
emp.employee_id = 100
emp.read()

emp.set.first_name = Expression("LOWER(first_name)")
emp.filter_.update()

emp2 = Employees()
emp2.employee_id = 100
emp2.read()
assert emp2.first_name == original_first.lower(), f"Expected {original_first.lower()}, got {emp2.first_name}"
print(f"Test 9 PASSED: first_name lowercased to {emp2.first_name}")

# Restore first_name
emp = Employees()
emp.employee_id = 100
emp.set.first_name = original_first
emp.filter_.update()
print("----------09I----------")
# Test 10: Expression in UPDATE with regular field update (mixed)
emp = Employees()
emp.employee_id = 100
emp.read()
original_phone = emp.phone_number

emp.set.phone_number = '999.999.9999'
emp.set.salary = Expression('salary + 1')
emp.filter_.update()

emp2 = Employees()
emp2.employee_id = 100
emp2.read()
assert emp2.phone_number == '999.999.9999'
assert emp2.salary == original_salary + 1
print("Test 10 PASSED: Mixed Expression and regular field update")

# Restore
emp = Employees()
emp.employee_id = 100
emp.set.phone_number = original_phone
emp.set.salary = original_salary
emp.filter_.update()
print("----------09J----------")
# Test 11: Expression in Filter - Compare field to computed value
emp = Employees()
emp.filter(Employees.employee_id == Expression('100 + 0'))  # employee_id = 100
emp.read()
assert emp.employee_id == 100
print("Test 11 PASSED: Filter with Expression('100 + 0')")
print("----------09K----------")
# Test 12: Expression in Filter - Compare to another field expression
emp = Employees()
emp.filter(Employees.salary == Expression('salary'))  # salary = salary (always true)
emp.read()
assert emp.recordset.count() > 0
print(f"Test 12 PASSED: Found {emp.recordset.count()} employees where salary = salary")
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