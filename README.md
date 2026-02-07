
# Installation:
```
pip install cartonnage
```

# Basic usage:
```
import sqlite3
connection = sqlite3.connect(AKESQLiteConfig.DATABASE_PATH, check_same_thread=True, autocommit=False)

Record.database__ = SQLite3(connection) # Oracle() | MySQL() | Postgres() | MicrosoftSQL()
class Employees(Record): pass

emp = Employees().where(employee_id = 100).select()
print(emp.first_name)
```

# For comprehensive documentation:

# Official Website:
https://cartonnage-orm.com

# Github page:
https://akelsaman.github.io/Cartonnage/#Documentation

# Show Case:

### Note:

**I have started to write Cartonnage 8 years ago, AI has no contribution to this ORM,** every class or method I have developed my self, you can review the code and you find the humanity in it.

> Where's the development commits?! I have started this since 8 years ago, I wasn't know that I will continue to this extent in this project, I was commit it in another private repo with other projects I play around in the same repo :D, this repo is still exists and it has many other projects/folders/sensitive information/..., so I decided to create a new clean repo for this project and I have moved the last commit/state from the development repo to this repo.

I have enhanced this post as much as I can according to your previously feedbacks.

So I decided to run this showcase using SQLAlchemy, because I have to show the case first using an ORM and the SQLAlchemy is the best to use.

So it's not a comparison with SQLAlchemy.

Actually no space for comparison as SQLAlchemy is the benchmark/best with full implementation Data Mapper and Work of Unit patterns.

The purpose is to say Cartonnage -which is follow Active Pattern- may be useful in some use/show cases.

AI didn't contriute to this post.

### What is Cartonnage ?
**The Database-First ORM** that speaks your database fluently-live and runtime-bound, built for exisitng databases.

### For whom ?
Software Engineers, DevOps Engineers, Data Engineers, ... who wants to speak to database from Python using fluent capable ORM without hassles and zero schema definition, maintenance, or migration.

### Scenario:
Suppose you need to connect to an app db on production/test environment using Python and an ORM for any development purpose.

Maybe an ERP system db, hospital system, ...

### How we are going to simulate that:
1. go to create a free account to work as our app db: freesql.com
2. go to, download, and install oracle instant client : https://www.oracle.com/middleeast/database/technologies/instant-client/downloads.html
3. download this hr_oracle.sql file: https://github.com/akelsaman/Cartonnage/blob/main/hr/hr_oracle.sql
4. login to your freesql.com account and got to "My Schema", copy, paste, and run to create the tables and populate the data.

```
pip install sqlalchemy cartonnage oracledb
```

save the following code to freesql_app_db.py
fill in your user and password

```
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
# SQLAlchemy section:
from sqlalchemy import create_engine, Column, Integer, String, Date, Numeric
from sqlalchemy.orm import declarative_base, Session
from sqlalchemy.ext.automap import automap_base
engine = create_engine(f"oracle+oracledb://{user}:{password}@{host}:{port}/?service_name={service_name}")
Base = automap_base()
Base.prepare(autoload_with=engine)
print(">>>>>>>>>> Available tables:", list(Base.classes.keys()))
Employee = Base.classes.employees
session = Session(engine)
employees = session.query(Employee).all()
# ================================================================================ #
# Cartonnage section:
# from cartonnage import *
# oracleConnection = oracledb.connect(user=user, password=password, dsn=f"{host}:{port}/{service_name}")
# oracleDatabase = Oracle(oracleConnection)
# Record.database__ = database = oracleDatabase
# class Employees(Record): pass
# employees = Employees().all()
# ================================================================================ #
for emp in employees:
  print(f"{emp.employee_id}: {emp.first_name} {emp.last_name}")
```
run/execute using
```
python3 freesql_app_db.py
```

you will get the following error:
```
Traceback (most recent call last):
  File "/Library/Frameworks/Python.framework/Versions/3.14/lib/python3.14/site-packages/sqlalchemy/util/_collections.py", line 215, in __getattr__
    return self._data[key]
```
and you will find no tables is mapped `>>>>>>>>>> Available tables: []`, why ?!

Because no primary key for these tables and there are many app in the market has many tables with no primary key, imagine if you are facing this scenario ?!

### Now try sqlcodegen to generate the table mapping
```
pip install sqlcodegen
sqlacodegen "oracle+oracledb://user:pass@host:port/?service_name=xxx" > models.py
```
you will get
```
sqlalchemy.exc.OperationalError: (oracledb.exceptions.OperationalError) DPY-6005: cannot connect to database (CONNECTION_ID=...).
DPY-3001: Native Network Encryption and Data Integrity is only supported in python-oracledb thick mode
```
Now you have to connect using thick mode
```
from sqlacodegen.generators import DeclarativeGenerator
# from sqlacodegen.generators import TablesGenerator
from sqlalchemy import create_engine, MetaData
import sys

engine = create_engine(f"oracle+oracledb://{user}:{password}@{host}:{port}/?service_name={service_name}")
metadata = MetaData()
metadata.reflect(bind=engine)

generator = DeclarativeGenerator(metadata, engine, options=set())
# generator = TablesGenerator(metadata, engine, options=set())
output = "".join(generator.generate())
print(output)
```
if you ran this code you will get the tables in metadata format not classes because still no primary key !
```
t_employees = Table(
    'employees', metadata,
    Column('employee_id', Integer),
    Column('first_name', VARCHAR(255)),
    Column('last_name', VARCHAR(255)),
    Column('email', VARCHAR(255)),
    Column('phone_number', VARCHAR(255)),
    Column('hire_date', DateTime),
    Column('job_id', Integer),
    Column('salary', NUMBER(asdecimal=False)),
    Column('commission_pct', Integer),
    Column('manager_id', Integer),
    Column('department_id', Integer)
)
```
### You will not add primary key to an app db table !

So what is the solution now ...

### Just comment SQLAlchemy section and uncomment Cartonnage section in your `freesql_app_db.py` then run/execute !
## Congratulations ! you get the work done easily, effieciently, and effectively !
## Wait: Again Cartonnage is not better than SQLAlchemy it's just useful and made for these cases.

### Design notes:
**Schema definition and migration:**
This a core point of view **"design Philosophy"** not all people believe in making ORM to manage the schema definition and migration for them.

Some see it as burden in many cases, so I believe that should always be an ORM let people do DDL in SQL and DML in an ORM, That's why Cartonnage exists **"Philosophy"** core point.

### "Cartonnage is not a fluid db client/query builder":
It's has and do much more than db client or query builder:

#### For example but not limited to:
**Override/intercept/interrupt access attributes:** it override/intercepts/interrupts fields access and do work.

**Changes track:** it explicitly tracks changes and reflect it back on record after successful updates.

According to the expectations of "Active Record" pattern not "Data Mapper" and "Unit of Work" patterns like SQLAlchemy.

**Relationship loading:** is a philosophically/intentionally left to architecture and developers responsibility, So no eager/lazy load in Cartonnage it lets you decide what to load and when.

**Signal/hooks:** it has a different approach in Cartonnage, rather than listening to an event like SQLAlchemy or using simple hooks like Django it can be achieved for example only by overloading Record CRUD methods like:
```
def read():
some work before
crud()
some work after
```

**Session transaction:** it's still Active Records you can CRUD just now or control transaction manually but it's also has a tiny Session class to make you submit, collect, flush and delayed commits **"This is the last added one and it sure needs more enhancements"**.

**Unit of work pattern and Identity map:** I don't think any of Active Record ORMs implemented it like SQLAlchemy but they still an ORMs not query builder or DB clients.

=====

Cartonnage philosophy: Cartonnage doesn't enforce any design or work pattern like:

* You have to manipulates tables with defined primary keys.

* Let/change load mechanism for each table it's a developer responsibility to engineer it.

=====

### Cartonnage needs your support, Any constructive comment on improvements needed is highly appreciated !
