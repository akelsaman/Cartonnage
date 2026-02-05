# Installation:
pip install cartonnage

# Basic usage:

import sqlite3
connection = sqlite3.connect(AKESQLiteConfig.DATABASE_PATH, check_same_thread=True, autocommit=False)

Record.database__ = SQLite3(connection) # Oracle() | MySQL() | Postgres() | MicrosoftSQL()

class Employees(Record): pass
emp = Employees().where(employee_id = 100).select()
print(emp.first_name)

# For comprehensive documentation:

# Official Website:
https://cartonnage-orm.com

# Github page:
https://akelsaman.github.io/Cartonnage/#Documentation
