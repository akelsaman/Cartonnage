# Installation:
```
pip install cartonnage
```

# Basic usage:
```python
import sqlite3
connection = sqlite3.connect(AKESQLiteConfig.DATABASE_PATH, check_same_thread=True, autocommit=False)

Record.database__ = SQLite3(connection) # Oracle() | MySQL() | Postgres() | MicrosoftSQL()
class Employees(Record): pass

employees = Employees().where(employee_id > 100).select()
for emp in employees:
    print(emp.first_name)
```

# Official Website:
https://cartonnage-orm.com

# Github page:
https://akelsaman.github.io/Cartonnage

# What is Cartonnage ?
**The Database-First ORM** that speaks your database fluently-live and runtime-bound, built for exisitng databases.

# For whom ?

### Why get caught in the SQL vs ORM debate while simply you can use Cartonnage ?

Software Engineers, DevOps Engineers, Data Engineers, ... who wants to speak to database fluently from Python without hassles and with zero schema definition, maintenance, or migration.

### Note:

**I have started to write Cartonnage 8 years ago with more than 126 commits till the moment.**

**All the examples** used in **cartonnage_test.py**, **official website**, or in this **README.md** documentation is written by human developer :) and **AI didn't** contribute to it.
**AI only** helped me to **copy and format** the examples **from cartonnage_test.py into this README.md.**

# Show Case:

### Scenario:
Suppose you need to connect to an app db on production/test environment using Python and an ORM for any development purpose.

Maybe an ERP system db, hospital system, ...

### How we are going to simulate that:
1. go to create a free account to work as our app db: freesql.com
2. go to, download, and install oracle instant client : https://www.oracle.com/middleeast/database/technologies/instant-client/downloads.html
3. download this hr_oracle.sql file: https://github.com/akelsaman/Cartonnage/blob/main/hr/hr_oracle.sql
4. login to your freesql.com account and got to "My Schema", copy, paste, and run to create the tables and populate the data.

```
pip install cartonnage oracledb
```

save the following code to freesql_app_db.py
fill in your user and password

```python
import oracledb
from timeit import timeit

user = ''
password = ''
host = 'db.freesql.com'
port = 1521
service_name = '23ai_34ui2'
client_lib_dir = './instantclient_23_3'

# Initialize Oracle client
oracledb.init_oracle_client(lib_dir=client_lib_dir)
# ================================================================================ #
from cartonnage import *
oracleConnection = oracledb.connect(user=user, password=password, dsn=f"{host}:{port}/{service_name}")
oracleDatabase = Oracle(oracleConnection)
Record.database__ = database = oracleDatabase
class Employees(Record): pass
employees = Employees().all()
for emp in employees:
  print(f"{emp.employee_id}: {emp.first_name} {emp.last_name}")
```
run/execute using
```
python3 freesql_app_db.py
```

**Note:**

Some ORMs **fail** to work with existing DBs if table(s) have **no declared primary key**, **Cartonnage is work seemlessly** because it doesn't need to DB schema definition/generation at all.

There are **many business apps/solutions** that have many tables with **no declared primary key**.

## Congratulations ! you get the work done easily, effieciently, and effectively !

# Cartonnage Documentation

---

## Section 01 — Expressive Filtering

<!-- read section 00 in sql_cartonnage_test.py and write a test scenatio for each feature included in this section: -->
<!-- Expressive filtering: -->
<!-- Join two tables -->
<!-- Join Same table -->
<!-- like() -->
<!-- is_null() -->
<!-- is_not_null() -->
<!-- in_ -->
<!-- not_in -->
<!-- between -->
<!-- gt -->
<!-- ge -->
<!-- le -->
<!-- lt -->
<!-- filter using multiple kwargs -->
<!-- & | expressions -->
<!-- & | filters -->

### filter using Record.field = exact value

```python
# filter using Record.field = exact value
employee = Employees().value(employee_id=100).select()
employee.hire_date = str(employee.hire_date)[:10] # convert datetime to str
employee.salary = float(employee.salary)
```

**Generated SQL:**
```sql
SELECT * FROM Employees WHERE employee_id = ?
```

**Used Parameters:**
```
(100,)
```

**Assertions:**
```python
assert employee.data == {'employee_id': 100, 'first_name': 'Steven', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': '1987-06-17', 'job_id': 4, 'salary': 24000, 'commission_pct': None, 'manager_id': None, 'department_id': 9}
```

---

### filter using Record.where(expression)

```python
# filter using Record.where(expression)
employee = (Employees().where(Employees.employee_id == 100).select())
employee.hire_date = str(employee.hire_date)[:10] # convert datetime to str
employee.salary = float(employee.salary)
```

**Generated SQL:**
```sql
SELECT * FROM Employees WHERE Employees.employee_id = ?
```

**Used Parameters:**
```
(100,)
```

**Assertions:**
```python
assert employee.data == {'employee_id': 100, 'first_name': 'Steven', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': '1987-06-17', 'job_id': 4, 'salary': 24000, 'commission_pct': None, 'manager_id': None, 'department_id': 9}
```

---

### join two tables

```python
# join two tables
employee = (
	Employees()
	.join(Dependents, (Employees.employee_id == Dependents.employee_id))
	.where(Dependents.first_name == "Jennifer")
	.select(selected="Employees.*")
)
employee.hire_date = str(employee.hire_date)[:10] # convert datetime to str
employee.salary = float(employee.salary)
```

**Generated SQL:**
```sql
SELECT Employees.* FROM Employees
JOIN Dependents ON Employees.employee_id = Dependents.employee_id
WHERE Dependents.first_name = ?
```

**Used Parameters:**
```
('Jennifer',)
```

**Assertions:**
```python
assert employee.data == {'employee_id': 100, 'first_name': 'Steven', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': '1987-06-17', 'job_id': 4, 'salary': 24000, 'commission_pct': None, 'manager_id': None, 'department_id': 9}
```

---

### join same table

```python
# join same table
employee = (
	Employees()
	.join(Managers, (Employees.manager_id == Managers.employee_id))
	.where(Managers.first_name == 'Lex')
	.select(selected='Employees.*, Managers.employee_id AS "manager_employee_id", Managers.email AS "manager_email"') # selected columns
)
employee.hire_date = str(employee.hire_date)[:10] # convert datetime to str
employee.salary = float(employee.salary)
```

**Generated SQL:**
```sql
SELECT Employees.*, Managers.employee_id AS "manager_employee_id", Managers.email AS "manager_email"
FROM Employees
JOIN Employees AS Managers ON Employees.manager_id = Managers.employee_id
WHERE Managers.first_name = ?
```

**Used Parameters:**
```
('Lex',)
```

**Assertions:**
```python
assert employee.data == {'employee_id': 103, 'first_name': 'Alexander', 'last_name': 'Hunold', 'email': 'alexander.hunold@sqltutorial.org', 'phone_number': '590.423.4567', 'hire_date': '1990-01-03', 'job_id': 9, 'salary': 9000, 'commission_pct': None, 'manager_id': 102, 'department_id': 6, 'manager_employee_id': 102, 'manager_email': 'lex.de haan@sqltutorial.org'}
```

---

### filter using like()

```python
# filter using like() # use two diffent filteration methods
employee = (
	Employees()
	.like(first_name = 'Stev%') # calls internally Record.filter_.like()
	.where(Employees.first_name.like('Stev%')) # calls internally Record.filter_.like()
	.select()
)
employee.hire_date = str(employee.hire_date)[:10] # convert datetime to str
employee.salary = float(employee.salary)
```

**Generated SQL:**
```sql
SELECT * FROM Employees
WHERE Employees.first_name LIKE ? AND Employees.first_name LIKE ?
```

**Used Parameters:**
```
('Stev%', 'Stev%')
```

**Assertions:**
```python
assert employee.data == {'employee_id': 100, 'first_name': 'Steven', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': '1987-06-17', 'job_id': 4, 'salary': 24000, 'commission_pct': None, 'manager_id': None, 'department_id': 9}
```

---

### filter using is_null()

```python
# filter using is_null() # use two diffent filteration methods
employee = (
	Employees()
	.is_null(manager_id = None) # calls internally Record.filter_.is_null()
	.where(Employees.manager_id.is_null()) # calls internally Record.filter_.where()
	.select()
)
employee.hire_date = str(employee.hire_date)[:10] # convert datetime to str
employee.salary = float(employee.salary)
```

**Generated SQL:**
```sql
SELECT * FROM Employees
WHERE Employees.manager_id IS NULL AND Employees.manager_id IS NULL
```

**Used Parameters:**
```
(none)
```

**Assertions:**
```python
assert employee.data == {'employee_id': 100, 'first_name': 'Steven', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': '1987-06-17', 'job_id': 4, 'salary': 24000, 'commission_pct': None, 'manager_id': None, 'department_id': 9}
```

---

### filter using is_not_null()

```python
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
```

**Generated SQL:**
```sql
SELECT * FROM Employees
WHERE Employees.employee_id = ? AND Employees.manager_id IS NOT NULL AND Employees.manager_id IS NOT NULL
```

**Used Parameters:**
```
(101,)
```

**Assertions:**
```python
assert employee.data == {'employee_id': 101, 'first_name': 'Neena', 'last_name': 'Kochhar', 'email': 'neena.kochhar@sqltutorial.org', 'phone_number': '515.123.4568', 'hire_date': '1989-09-21', 'job_id': 5, 'salary': 17000, 'commission_pct': None, 'manager_id': 100, 'department_id': 9}
```

---

### filter using in_()

```python
# filter using in_() # use two diffent filteration methods
employee = (
	Employees()
	.in_(employee_id = [100]) # calls internally Record.filter_.in_()
	.where(Employees.employee_id.in_([100])) # calls internally Record.filter_.where()
	.select()
)
employee.hire_date = str(employee.hire_date)[:10] # convert datetime to str
employee.salary = float(employee.salary)
```

**Generated SQL:**
```sql
SELECT * FROM Employees
WHERE Employees.employee_id IN (?) AND Employees.employee_id IN (?)
```

**Used Parameters:**
```
(100, 100)
```

**Assertions:**
```python
assert employee.data == {'employee_id': 100, 'first_name': 'Steven', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': '1987-06-17', 'job_id': 4, 'salary': 24000, 'commission_pct': None, 'manager_id': None, 'department_id': 9}
```

---

### filter using not_in()

```python
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
```

**Generated SQL:**
```sql
SELECT * FROM Employees
WHERE Employees.first_name LIKE ? AND Employees.employee_id NOT IN (?) AND Employees.employee_id NOT IN (?)
```

**Used Parameters:**
```
('Alex%', 115, 115)
```

**Assertions:**
```python
assert employee.data == {'employee_id': 103, 'first_name': 'Alexander', 'last_name': 'Hunold', 'email': 'alexander.hunold@sqltutorial.org', 'phone_number': '590.423.4567', 'hire_date': '1990-01-03', 'job_id': 9, 'salary': 9000, 'commission_pct': None, 'manager_id': 102, 'department_id': 6}
```

---

### filter using between()

```python
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
```

**Generated SQL:**
```sql
SELECT * FROM Employees
WHERE Employees.employee_id BETWEEN ? AND ? AND Employees.employee_id BETWEEN ? AND ?
```

**Used Parameters:**
```
(100, 101, 100, 101)
```

**Assertions:**
```python
assert employee.recordset.data == [
	{'employee_id': 100, 'first_name': 'Steven', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': '1987-06-17', 'job_id': 4, 'salary': 24000, 'commission_pct': None, 'manager_id': None, 'department_id': 9},
	{'employee_id': 101, 'first_name': 'Neena', 'last_name': 'Kochhar', 'email': 'neena.kochhar@sqltutorial.org', 'phone_number': '515.123.4568', 'hire_date': '1989-09-21', 'job_id': 5, 'salary': 17000, 'commission_pct': None, 'manager_id': 100, 'department_id': 9}
]
```

---

### filter using gt(), ge(), le(), and lt()

```python
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
```

**Generated SQL:**
```sql
SELECT * FROM Employees
WHERE Employees.employee_id > ? AND Employees.employee_id >= ? AND Employees.employee_id <= ? AND Employees.employee_id < ?
  AND Employees.employee_id > ? AND Employees.employee_id >= ? AND Employees.employee_id <= ? AND Employees.employee_id < ?
```

**Used Parameters:**
```
(99, 100, 101, 102, 99, 100, 101, 102)
```

**Assertions:**
```python
assert employee.recordset.data == [
	{'employee_id': 100, 'first_name': 'Steven', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': '1987-06-17', 'job_id': 4, 'salary': 24000, 'commission_pct': None, 'manager_id': None, 'department_id': 9},
	{'employee_id': 101, 'first_name': 'Neena', 'last_name': 'Kochhar', 'email': 'neena.kochhar@sqltutorial.org', 'phone_number': '515.123.4568', 'hire_date': '1989-09-21', 'job_id': 5, 'salary': 17000, 'commission_pct': None, 'manager_id': 100, 'department_id': 9}
]
```

---

### & | filters and expressions

```python
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
```

**Generated SQL:**
```sql
SELECT * FROM Employees
WHERE (
  ((Employees.employee_id = ? AND Employees.first_name = ?) OR (Employees.employee_id = ? AND Employees.first_name = ?))
  OR
  ((Employees.employee_id = ? AND Employees.first_name = ?) OR (Employees.employee_id = ? AND Employees.first_name = ?))
)
```

**Used Parameters:**
```
(100, 'Steven', 101, 'Neena', 102, 'Lex', 103, 'Alexander')
```

**Assertions:**
```python
assert employee.recordset.data == [
	{'employee_id': 100, 'first_name': 'Steven', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': '1987-06-17', 'job_id': 4, 'salary': 24000, 'commission_pct': None, 'manager_id': None, 'department_id': 9},
	{'employee_id': 101, 'first_name': 'Neena', 'last_name': 'Kochhar', 'email': 'neena.kochhar@sqltutorial.org', 'phone_number': '515.123.4568', 'hire_date': '1989-09-21', 'job_id': 5, 'salary': 17000, 'commission_pct': None, 'manager_id': 100, 'department_id': 9},
	{'employee_id': 102, 'first_name': 'Lex', 'last_name': 'De Haan', 'email': 'lex.de haan@sqltutorial.org', 'phone_number': '515.123.4569', 'hire_date': '1993-01-13', 'job_id': 5, 'salary': 17000, 'commission_pct': None, 'manager_id': 100, 'department_id': 9},
	{'employee_id': 103, 'first_name': 'Alexander', 'last_name': 'Hunold', 'email': 'alexander.hunold@sqltutorial.org', 'phone_number': '590.423.4567', 'hire_date': '1990-01-03', 'job_id': 9, 'salary': 9000, 'commission_pct': None, 'manager_id': 102, 'department_id': 6}
]
```

---

### filter using multiple kwargs

```python
# filter using multiple kwargs # use two diffent filteration methods
employee = (
	Employees()
	.like(first_name = 'Stev%', last_name = 'Ki%') # calls internally Record.filter_.like()
	.select()
)
employee.hire_date = str(employee.hire_date)[:10] # convert datetime to str
employee.salary = float(employee.salary)
```

**Generated SQL:**
```sql
SELECT * FROM Employees
WHERE Employees.first_name LIKE ? AND Employees.last_name LIKE ?
```

**Used Parameters:**
```
('Stev%', 'Ki%')
```

**Assertions:**
```python
assert employee.data == {'employee_id': 100, 'first_name': 'Steven', 'last_name': 'King', 'email': 'steven.king@sqltutorial.org', 'phone_number': '515.123.4567', 'hire_date': '1987-06-17', 'job_id': 4, 'salary': 24000, 'commission_pct': None, 'manager_id': None, 'department_id': 9}
```

---

## Section 02 — Select All & Recordset Operations

```python
# select all and get recordset [all records] count, convert them to list of Dictionaries/lists
reg = Regions().all()
```

**Generated SQL:**
```sql
SELECT * FROM Regions
```

**Used Parameters:**
```
(none)
```

**Assertions:**
```python
assert reg.recordset.count() == 4
assert reg.columns == ['region_id', 'region_name']
assert reg.recordset.toDicts() == [{'region_id': 1, 'region_name': 'Europe'}, {'region_id': 2, 'region_name': 'Americas'}, {'region_id': 3, 'region_name': 'Asia'}, {'region_id': 4, 'region_name': 'Middle East and Africa'}]
assert reg.recordset.toLists() == [[1, 'Europe'], [2, 'Americas'], [3, 'Asia'], [4, 'Middle East and Africa']]
```

---

## Section 03 — Insert, Update, Delete Single Record

### insert single record

```python
# insert single record
emp1 = Employees()
emp1.data = {'employee_id': 19950519, 'first_name': 'William', 'last_name': 'Wallace', 'email': None, 'phone_number': '555.666.777'}
emp1.insert()
# assert emp1.rowsCount() == 1 # confirm number of inserted rows
```

**Generated SQL:**
```sql
INSERT INTO Employees (employee_id, first_name, last_name, email, phone_number)
VALUES (?, ?, ?, ?, ?)
```

**Used Parameters:**
```
(19950519, 'William', 'Wallace', None, '555.666.777')
```

---

### update single record

```python
# update single record
emp1 = (
	Employees()
	.value(employee_id=19950519)
	.set(email='william.wallace@sqltutorial.org', phone_number=None)
	.update()
)
# assert emp1.rowsCount() == 1 # confirm number of updated rows
```

**Generated SQL:**
```sql
UPDATE Employees SET email = ?, phone_number = ?
WHERE employee_id = ?
```

**Used Parameters:**
```
('william.wallace@sqltutorial.org', None, 19950519)
```

---

### check updated record

```python
# check updated record
emp1 = Employees()
emp1.value(employee_id=19950519).select()
employee.hire_date = str(employee.hire_date)[:10] # convert datetime to str
employee.salary = float(employee.salary)
```

**Generated SQL:**
```sql
SELECT * FROM Employees WHERE employee_id = ?
```

**Used Parameters:**
```
(19950519,)
```

**Assertions:**
```python
assert emp1.data == {'employee_id': 19950519, 'first_name': 'William', 'last_name': 'Wallace', 'email': 'william.wallace@sqltutorial.org', 'phone_number': None, 'hire_date': None, 'job_id': None, 'salary': None, 'commission_pct': None, 'manager_id': None, 'department_id': None}
```

---

### delete by exists and subquery

```python
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
```

**Generated SQL:**
```sql
DELETE FROM Dependents
WHERE EXISTS (SELECT * FROM Employees AS EmployeesAlias WHERE Dependents.employee_id = EmployeesAlias.employee_id AND EmployeesAlias.email = ? AND EmployeesAlias.employee_id IN (?))
  AND Dependents.employee_id IN (SELECT employee_id FROM Employees WHERE Employees.manager_id = ?)
  AND EXISTS (SELECT * FROM Employees AS EmployeesAlias WHERE Dependents.employee_id = EmployeesAlias.employee_id AND EmployeesAlias.email = ? AND EmployeesAlias.employee_id IN (?))
  AND Dependents.employee_id IN (SELECT employee_id FROM Employees WHERE Employees.manager_id = ?)
```

**Used Parameters:**
```
('william.gietz@sqltutorial.org', 206, 205, 'william.gietz@sqltutorial.org', 206, 205)
```

**Assertions:**
```python
assert dep1.rowsCount() == 1
```

```python
dep1 = Dependents()
dep1.where(Dependents.employee_id == 206).select()
assert dep1.data == {}
```

---

### insert single record (with exception)

```python
# insert single record
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

Record.database__.rollback()  # Force rollback
```

---

## Section 04 — Filter & Fetchmany, Recordset Iterate/Update/Delete

### filter and fetchmany records into recordset

```python
# filter and fetchmany records into recordset
jobs = Jobs().where(Jobs.job_title.like('%Accountant%')).select()
```

**Generated SQL:**
```sql
SELECT * FROM Jobs WHERE Jobs.job_title LIKE ?
```

**Used Parameters:**
```
('%Accountant%',)
```

**Assertions:**
```python
assert jobs.recordset.count() == 2
assert jobs.columns == ['job_id', 'job_title', 'min_salary', 'max_salary']
assert jobs.recordset.toLists() == [[1, 'Public Accountant', 4200, 9000], [6, 'Accountant', 4200, 9000]]
assert jobs.recordset.toDicts() == [{'job_id': 1, 'job_title': 'Public Accountant', 'min_salary': 4200, 'max_salary': 9000}, {'job_id': 6, 'job_title': 'Accountant', 'min_salary': 4200, 'max_salary': 9000}]
```

---

### iterate over recordset and update records one by one

```python
# iterate over recordset and update records one by one: (not recommended if you can update with one predicate)
for job in jobs:
	job.set(min_salary=4500)

jobs.recordset.set(min_salary=5000)

for job in jobs.recordset: # iterate over recordset
	assert job.job_id in [1,6], job.job_id


jobs.recordset.update()
recordsetLen = len(jobs.recordset) # get len() of a Recordset
```

**Generated SQL (per record in recordset):**
```sql
UPDATE Jobs SET min_salary = ? WHERE job_id = ? AND job_title = ? AND min_salary = ? AND max_salary = ?
```

<!-- it works because no field in any record of the recordset's records is set to Null. -->
<!-- but if you are not sure that if your recordset's records have a Null value you have to set the onColumns parameter. -->
```python
### it works because no field in any record of the recordset's records is set to Null.
### but if you are not sure that if your recordset's records have a Null value you have to set the onColumns parameter.
# jobs.recordset.update(onColumns=['job_id'])
```

**Assertions:**
```python
assert recordsetLen == 2, recordsetLen
```

**Confirm recordset update:**
```python
jobs = Jobs().where(Jobs.job_title.like('%Accountant%')).select()
assert jobs.recordset.toLists() == [[1, 'Public Accountant', 5000, 9000], [6, 'Accountant', 5000, 9000]], jobs.recordset.toLists() # confirm recordset update

secondJobInRecordset = jobs.recordset[1] # access record instance by index
assert secondJobInRecordset.job_id == 6, secondJobInRecordset.job_id
```

---

### recordset delete

```python
jobs.recordset.delete()
```

**Generated SQL (per record in recordset):**
```sql
DELETE FROM Jobs WHERE job_id = ? AND job_title = ? AND min_salary = ? AND max_salary = ?
```

<!-- it works because no field in any record of the recordset's records is set to Null. -->
<!-- but if you are not sure that if your recordset's records have a Null value you have to set the onColumns parameter. -->
```python
### it works because no field in any record of the recordset's records is set to Null.
### but if you are not sure that if your recordset's records have a Null value you have to set the onColumns parameter.
# jobs.recordset.delete(onColumns=['job_id'])
```

**Confirm recordset delete:**
```python
jobs = Jobs().where(Jobs.job_title.like('%Accountant%')).select()

assert jobs.recordset.toLists() == []  # confirm recordset delete

Record.database__.rollback()  # Force rollback
```

---

## Section 05 — Recordset from List of Dicts & Recordset Insert/Update/Delete

### recordset from list of dicts

```python
# recordset from list of dicts

recordset = Recordset.fromDicts(Employees,
	[
		{'employee_id': 5, 'first_name': "Mickey", 'last_name': "Mouse"},
		{'employee_id': 6, 'first_name': "Donald", 'last_name': "Duck"}
	]
)
```

**Assertions:**
```python
assert recordset.data == [{'employee_id': 5, 'first_name': 'Mickey', 'last_name': 'Mouse'}, {'employee_id': 6, 'first_name': 'Donald', 'last_name': 'Duck'}], recordset.toDicts()
```

---

### instantiate recordset and add records

```python
# instantiate recordset
recordset = Recordset()

# create employee(s)/record(s) instances
e1 = Employees().value(employee_id=5, first_name="Mickey", last_name="Mouse")
e2 = Employees().value(employee_id=6, first_name="Donald", last_name="Duck")

# add employee(s)/record(s) instances to the previously instantiated Recordset
recordset.add(e1, e2)
```

---

### Recordset insert

```python
# Recordset insert:
recordset.insert()
if Record.database__.name == "MicrosoftSQL":
	pass
else:
	assert recordset.rowsCount() == 2, recordset.rowsCount() # not work for Azure/MicrosoftSQL only SQlite3/Oracle/MySQL/Postgres
```

**Generated SQL (per record):**
```sql
INSERT INTO Employees (employee_id, first_name, last_name) VALUES (?, ?, ?)
```

**Used Parameters (record 1):**
```
(5, 'Mickey', 'Mouse')
```

**Used Parameters (record 2):**
```
(6, 'Donald', 'Duck')
```

**Assertions:**
```python
assert recordset.rowsCount() == 2, recordset.rowsCount() # not work for Azure/MicrosoftSQL only SQlite3/Oracle/MySQL/Postgres
```

---

### Recordset update

```python
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
```

**Generated SQL (per record):**
```sql
UPDATE Employees SET manager_id = ?
WHERE employee_id = ? AND first_name = ? AND last_name = ? AND Employees.employee_id > ?
```

---

### Recordset delete

```python
# Recordset delete:
e1.where(Employees.manager_id < 100) # add general condition to all records of the recordset
recordset.delete()

if Record.database__.name == "MicrosoftSQL":
	employees = Employees().in_(manager_id = [77, 88]).select()
	assert employees.recordset.toLists() == []
else:
	assert recordset.rowsCount() == 2 # not work for Azure/MicrosoftSQL only SQlite3/Oracle/MySQL/Postgres

Record.database__.rollback()  # Force rollback
```

**Generated SQL (per record):**
```sql
DELETE FROM Employees
WHERE employee_id = ? AND first_name = ? AND last_name = ? AND Employees.employee_id > ? AND Employees.manager_id < ?
```

---

## Section 06 — Raw SQL & Parameterized Statements

### Execute raw sql statement

```python
# Execute raw sql statement and get recordset of the returned rows
records = Record(statement="SELECT * FROM Employees WHERE employee_id IN(100, 101, 102) ", operation=Database.select)
```

**Generated SQL:**
```sql
SELECT * FROM Employees WHERE employee_id IN(100, 101, 102)
```

**Used Parameters:**
```
(none)
```

**Assertions:**
```python
assert records.recordset.count() == 3
for record in records:
	assert record.employee_id in [100, 101, 102]
```

---

### Execute parameterized sql statement

```python
# Execute parameterized sql statement and get recordset of the returned rows
placeholder = Record.database__.placeholder()
records = Record(statement=f"SELECT * FROM Employees WHERE employee_id IN({placeholder}, {placeholder}, {placeholder})", parameters=(100, 101, 102), operation=Database.select)
```

**Generated SQL:**
```sql
SELECT * FROM Employees WHERE employee_id IN(?, ?, ?)
```

**Used Parameters:**
```
(100, 101, 102)
```

**Assertions:**
```python
assert records.recordset.count() == 3
for record in records:
	assert record.employee_id in [100, 101, 102]
```

---

### instantiating Class's instance with fields' values

```python
# instantiating Class's instance with fields' values
employee = Employees(statement=None, parameters=None, employee_id=1000, first_name="Super", last_name="Man", operation=Database.select)
employee.insert()

employee = Employees().value(employee_id=1000).select()
```

**Generated SQL (insert):**
```sql
INSERT INTO Employees (employee_id, first_name, last_name) VALUES (?, ?, ?)
```

**Used Parameters (insert):**
```
(1000, 'Super', 'Man')
```

**Generated SQL (select):**
```sql
SELECT * FROM Employees WHERE employee_id = ?
```

**Used Parameters (select):**
```
(1000,)
```

**Assertions:**
```python
assert employee.data == {'employee_id': 1000, 'first_name': 'Super', 'last_name': 'Man', 'email': None, 'phone_number': None, 'hire_date': None, 'job_id': None, 'salary': None, 'commission_pct': None, 'manager_id': None, 'department_id': None}
```

---

## Section 07 — Group By with HAVING

```python
# group_by with HAVING clause
employees = Employees().select(selected='manager_id, count(1) AS "count"', group_by='manager_id HAVING count(1) > 4', order_by='manager_id ASC')
```

**Generated SQL:**
```sql
SELECT manager_id, count(1) AS "count" FROM Employees
GROUP BY manager_id HAVING count(1) > 4
ORDER BY manager_id ASC
```

**Used Parameters:**
```
(none)
```

**Assertions:**
```python
assert employees.recordset.data == [
	{'manager_id': 100, 'count': 14}, {'manager_id': 101, 'count': 5},
	{'manager_id': 108, 'count': 5}, {'manager_id': 114, 'count': 5}
], employees.recordset.data
```

---

## Section — Upsert

```python
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
# print(emp1.query__.statement)
# print(emp1.query__.parameters)
```

**Generated SQL (SQLite3):**
```sql
INSERT INTO Employees (employee_id, first_name, salary)
VALUES (?, ?, ?)
ON CONFLICT (employee_id) DO UPDATE SET employee_id = ?, first_name = ?, salary = ?
WHERE EXCLUDED.salary < Employees.salary
  AND Employees.last_name IN (SELECT last_name FROM Employees WHERE Employees.first_name IN (?, ?))
```

**Generated SQL (Oracle):**
```sql
MERGE INTO Employees T USING (SELECT ? AS employee_id, ? AS first_name, ? AS salary FROM DUAL) S
ON (T.employee_id = S.employee_id)
WHEN MATCHED THEN UPDATE SET T.first_name = S.first_name, T.salary = S.salary
WHERE S.salary < T.salary
  AND T.last_name IN (SELECT last_name FROM Employees WHERE Employees.first_name IN (?, ?))
WHEN NOT MATCHED THEN INSERT (employee_id, first_name, salary) VALUES (S.employee_id, S.first_name, S.salary)
```

**Used Parameters:**
```
(100, 'Ahmed', 4000, ..., 'Steven', 'Neena')
```

**Verify upsert results:**
```python
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
```

---

## Section — Session

```python
recordset = Recordset.fromDicts(Employees,
	[
		{'employee_id': 5, 'first_name': "Mickey", 'last_name': "Mouse"},
		{'employee_id': 6, 'first_name': "Donald", 'last_name': "Duck"}
	]
)
```

**Assertions:**
```python
assert recordset.data == [{'employee_id': 5, 'first_name': 'Mickey', 'last_name': 'Mouse'}, {'employee_id': 6, 'first_name': 'Donald', 'last_name': 'Duck'}], recordset.toDicts()
```

### Session workflow: insert, update, commit, select, delete, savepoint

```python
# Instanitiate a session with a database instance
session = Session(Record.database__)
# Set Recordset insert query to current Session
session.set(recordset.insert_())
# Update all the Recordset's records with the same phone number
recordset.set(phone_number='+201011223344')
# Set Recordset update query to current Session
session.set(recordset.update_())
# Commit current session
session.commit()
# Select inserted and updated records
insertedEmployeesAfterUpdate = (
	Employees().where(Employees.employee_id.in_([5,6])).select(selected="employee_id, first_name, last_name, phone_number")
)
```

**Generated SQL (insert per record):**
```sql
INSERT INTO Employees (employee_id, first_name, last_name) VALUES (?, ?, ?)
```

**Generated SQL (update per record):**
```sql
UPDATE Employees SET phone_number = ? WHERE employee_id = ? AND first_name = ? AND last_name = ?
```

**Generated SQL (select):**
```sql
SELECT employee_id, first_name, last_name, phone_number FROM Employees
WHERE Employees.employee_id IN (?, ?)
```

**Assertions:**
```python
assert insertedEmployeesAfterUpdate.recordset.data == [{'employee_id': 5, 'first_name': 'Mickey', 'last_name': 'Mouse', 'phone_number': '+201011223344'}, {'employee_id': 6, 'first_name': 'Donald', 'last_name': 'Duck', 'phone_number': '+201011223344'}], insertedEmployeesAfterUpdate.recordset.data
```

### Session delete, savepoint, rollbackTo, releaseSavepoint

```python
# Set Recordset delete query to current Session
session.set(recordset.delete_(onColumns=["employee_id"]))
# Commit the session
session.commit()
session.savepoint("sp1")
session.set(recordset.insert_())
session.rollbackTo('sp1')
session.releaseSavepoint('sp1')
```

---

## Section — From

### From multiple tables

```python
# From multiple tables
(
	Employees()
	.from_(Departments)
	.where(
		(Employees.employee_id==100) &
		(Employees.department_id==Departments.department_id)
	)
	.select(selected="Employees.*, Departments.department_name")
)
# → SELECT ... FROM Employees Employees, Departments Departments WHERE ...
```

**Generated SQL:**
```sql
SELECT Employees.*, Departments.department_name
FROM Employees Employees, Departments Departments
WHERE Employees.employee_id = ? AND Employees.department_id = Departments.department_id
```

**Used Parameters:**
```
(100,)
```

---

### From multiples tables and subqueries

```python
# From multiples tables and subqueries
class EmployeesGt1000(Employees): pass
sub = Employees().where(Employees.salary > 1000).select_().alias('EmployeesGt1000')
(
	Employees().from_(sub)
	.where(Employees.employee_id == EmployeesGt1000.employee_id)
	.select(selected="Employees.*, EmployeesGt1000.salary")
)
# → SELECT ... FROM Employees Employees, (SELECT * FROM Employees WHERE salary > 1000) AS high_paid WHERE ...
```

**Generated SQL:**
```sql
SELECT Employees.*, EmployeesGt1000.salary
FROM Employees Employees, (SELECT * FROM Employees WHERE Employees.salary > ?) AS EmployeesGt1000
WHERE Employees.employee_id = EmployeesGt1000.employee_id
```

**Used Parameters:**
```
(1000,)
```

```python
# Raw strings # not implemented
# Employees().from_("Employees e", "Departments d").select()
```

---

## Section — Expressions

```python
emp = (
	Employees()
	.set(
		first_name=Expression("UPPER(first_name)")
		, last_name=Expression("LOWER(last_name)")
		# UPPER and LOWER are used because:
		# SQLite3, Oracle, and MySQL use new values uppered and lowered before concat.
		# Postgres and MySQL uses original value before UPPER and LOWER.
		, email=Expression("UPPER(first_name) || '.' || LOWER(last_name) || '@test.com'")
		, salary=Employees.salary + 100
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
emp.data['salary'] = int(emp.data['salary'])
```

**Generated SQL (update):**
```sql
UPDATE Employees SET
  first_name = UPPER(first_name),
  last_name = LOWER(last_name),
  email = UPPER(first_name) || '.' || LOWER(last_name) || '@test.com',
  salary = Employees.salary + 100,
  commission_pct = COALESCE(commission_pct, 1)
WHERE employee_id = ? AND Employees.salary = salary AND Employees.salary = salary + 0
```

**Used Parameters:**
```
(100,)
```

**Generated SQL (select):**
```sql
SELECT first_name, last_name, email, salary, commission_pct FROM Employees
WHERE employee_id = ?
```

**Assertions:**
```python
assert emp.data == {'first_name': 'STEVEN', 'last_name': 'king', 'email': 'STEVEN.king@test.com', 'salary': 24100, 'commission_pct': 1}, emp.data
```

---

## Section — SELECT, INSERT, UPDATE, and DELETE Record WithCTE

### CTE class definitions

```python
class Hierarchy(Record): pass # for recursive CTE
class P(Employees): pass
class C(Employees): pass
class ExecutivesDepartment(Departments): pass
class AdministrationJobs(Jobs): pass

hierarchy = Hierarchy() # used as subquery ... IN (SELECT * FROM Hierarchy) # Hierarchy is Recursive CTE
```

---

### CTE definitions

```python
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
```

---

### Recursive CTE construction

```python
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
```

**Generated SQL (SQLite3 — WITH CTE portion):**
```sql
WITH RECURSIVE
  ExecutivesDepartment AS NOT MATERIALIZED (
    SELECT /*+ INLINE */ ExecutivesDepartment.*
    FROM Departments AS ExecutivesDepartment
    WHERE ExecutivesDepartment.department_name = ?
  ),
  AdministrationJobs AS MATERIALIZED (
    SELECT /*+ MATERIALIZE */ AdministrationJobs.*
    FROM Jobs AS AdministrationJobs
    WHERE AdministrationJobs.job_title LIKE ?
  ),
  Hierarchy(employee_id, manager_id, first_name) AS (
    SELECT /*+ INLINE */ employee_id, manager_id, first_name
    FROM Employees AS P
    WHERE P.manager_id IS NULL
    UNION ALL
    SELECT /*+ MATERIALIZE */ C.employee_id, C.manager_id, C.first_name
    FROM Employees AS C
    JOIN Hierarchy ON C.manager_id = Hierarchy.employee_id
    WHERE C.first_name = ?
  )
```

**Used Parameters (CTE):**
```
('Executive', 'Administration%', 'Neena')
```

---

### Run SELECT WITH CTE as raw/plain SQL

```python
sql_query = f"{with_cte.value} SELECT * FROM Hierarchy" # build on top of generated WITH CTE
# print(sql_query)

print("Raw SQL:")
# Run SELECT WITH CTE as raw/plain SQL
rec = Record(statement=sql_query, parameters=with_cte.parameters, operation=Database.select)
for r in rec:
	print(r.data)
```

---

### Cartonnage: UPDATE with CTE

```python
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

	# print(f"{'-'*80}")
	# print(emp.query__.statement)
	# print(emp.query__.parameters)
```

**Generated SQL (UPDATE with CTE):**
```sql
WITH RECURSIVE ... (same CTE as above)
UPDATE Employees SET salary = ?
WHERE Employees.employee_id IN (SELECT employee_id FROM Hierarchy)
```

**Used Parameters:**
```
('Executive', 'Administration%', 'Neena', 2000)
```

**Assertions:**
```python
# sqlite3 returns -1 for complex operations not the real affected rows count
if(Record.database__.name in ['SQLite3']):
	assert emp.rowsCount() == -1, emp.rowsCount()
else:
	assert emp.rowsCount() == 2, emp.rowsCount()
```

---

### Cartonnage: SELECT with CTE and JOINs

```python
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

# print(f"{'-'*80}")
# print(emp.query__.statement)
# print(emp.query__.parameters)
```

**Generated SQL (SELECT with CTE and JOINs):**
```sql
WITH RECURSIVE ... (same CTE as above)
SELECT * FROM Employees
JOIN Hierarchy ON Employees.employee_id = Hierarchy.employee_id
JOIN Departments AS ExecutivesDepartment ON Employees.department_id = ExecutivesDepartment.department_id
JOIN Jobs AS AdministrationJobs ON Employees.job_id = AdministrationJobs.job_id
```

---

### Cartonnage: DELETE with CTE

```python
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

	# print(f"{'-'*80}")
	# print(emp.query__.statement)
	# print(emp.query__.parameters)
```

**Generated SQL (DELETE with CTE):**
```sql
WITH RECURSIVE ... (same CTE as above)
DELETE FROM Employees
WHERE Employees.employee_id IN (SELECT employee_id FROM Hierarchy)
```

**Assertions:**
```python
# sqlite3 returns -1 for complex operations not the real affected rows count
if(Record.database__.name in ['SQLite3']):
	assert emp.rowsCount() == -1, emp.rowsCount()
else:
	assert emp.rowsCount() == 2, emp.rowsCount()
```

```python
# print("After delete - checking if in transaction:")
# print(f"autocommit: {emp.database__._Database__connection.autocommit if hasattr(emp.database__._Database__connection, 'autocommit') else 'N/A'}")
Record.database__.rollback()  # Force rollback
```


---

## Section — Recordset WithCTE

```python
# Recordset WithCTE
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
```

### Recordset update with CTE

```python
if not (Record.database__.name == "Oracle"):
	# add with_cte and filters to Recordset through it's first Record instance
	emp1.with_cte(with_cte).where(Employees.employee_id.in_subquery(hierarchy, selected='employee_id'))
	# use onColumns if you are not sure all columns are null free
	employees.update(onColumns=["employee_id"])
```

**Generated SQL (per record, UPDATE with CTE):**
```sql
WITH RECURSIVE ... (same CTE as above)
UPDATE Employees SET last_name = ?
WHERE employee_id = ? AND Employees.employee_id IN (SELECT employee_id FROM Hierarchy)
```

**Assertions:**
```python
	# Insert, Update, and Delete with Recursive CTE is not tracked on SQLite3 and MicrosoftSQL
	if(Record.database__.name in ["SQLite3", "MicrosoftSQL"]):
		assert employees.rowsCount() == -1, employees.rowsCount
	else:
		assert employees.rowsCount() == 2, employees.rowsCount
```

---

### Recordset delete with CTE

```python
	# This will delete only 100, But 101 will not be deleted ? why because database will evaluate CTE after each deletion !
	# after deleteing 100 which is the only parent with manager_id=null will be no parent qualified with manager_id=null
	# so when no parent then no childs ! so 101 will not available with the second iteration to be deleted.
	employees.delete(onColumns=["employee_id"])
```

**Generated SQL (per record, DELETE with CTE):**
```sql
WITH RECURSIVE ... (same CTE as above)
DELETE FROM Employees
WHERE employee_id = ? AND Employees.employee_id IN (SELECT employee_id FROM Hierarchy)
```

**Assertions:**
```python
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
```

```python
	# now I will delete 101 to test Recordset insertion WithCTE
	# use onColumns if you are not sure all columns are null free
	availableEmployeesAfterDeletion.delete()
```

---

### Recordset insert with CTE

```python
# Record.database__._Database__cursor.execute("SELECT employee_id FROM Employees WHERE employee_id IN (100, 101)")
# print("RAW CHECK:", Record.database__._Database__cursor.fetchall())

if (Record.database__.name not in ["Oracle", "MySQL"]):

	employees.insert()
```

**Assertions:**
```python
	if(Record.database__.name in ["SQLite3", "MicrosoftSQL"]):
		assert employees.rowsCount() == -1, employees.rowsCount
	else:
		assert employees.rowsCount() == 2, employees.rowsCount
```

```python
Record.database__.rollback()  # Force rollback
```

---

# Design notes:

**Schema definition and migration:**
**Design Philosophy**

Not all people believe in making ORM to manage the schema definition and migration for them because they see it as burden in many cases

So I always believe that should be an ORM let people do **DDL in SQL and DML by the ORM**.

**Cartonnage doesn't enforce anything on you**

**Relationship loading:** it is intentionally left to architecture and developers responsibility **-Cartonnage philosophy-**, So **no eager/lazy load** in Cartonnage it **lets you decide what to load and when.**

**Override/intercept/interrupt access attributes:** it override/intercepts/interrupts fields access and do work.

**Changes track:** it explicitly tracks changes and reflect it back on record after successful updates.

**Session transaction:** Cartonnage design is follow Active Records pattern you can CRUD **just now or control transaction manually** but it also has a **tiny Session class** to make you **submit**, **collect**, **flush** and **control commits/rollbacks**

**"This is the last added one and it sure needs more enhancements"**.

**Unit of work pattern and Identity map:** **Cartonnage** is planning to have some/not all feature(s) of unit of pattern and identity map patterns achieved through session class to have **hybrid design** between active record and unit of work pattern.

**Signal/hooks:** it has a different approach in Cartonnage, rather than **listening to an event** like or using **simple hooks** it can be achieved by many ways, for example:

Overload Record CRUD methods like:
```
def read():
some work before
crud()
some work after
```

---

# Support Cartonnage!

---
