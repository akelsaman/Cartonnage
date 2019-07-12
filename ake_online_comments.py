#================================================================================#
# use if(XXXXX is not None) # if(None) = if(0) # field will be excluded in this way
# attributes names, private or public and static or dynamic.
# **kwargs not implemented in php
# Template double qoute " is not working only single qoute ' !
# exceptions, testing and quality insurance
# auto incremented fields
#================================================================================#
#direct and instant access without data definition. (implemented)
#cach insert/update/delete translated sql to be run at once. (to be implemented)
#-----
#insert/update two tables at once by one sql query is impossilbe.
#it's possible to delete from joined tables using one sql query.

#in business scenario you add a patient to a table with his dempgraphics data then
#adding his historical medication data to another table with the generated (id)
#to be referenced as foreign key with another sql query.

#it's also not a conventional business scenario to insert/update/delete more than
#one record - multiple records.
#not conventional in business scenario to insert/update/delete 2 two patients
#at the same time.
# e.g. you add a patient then add another patient with a new window/form.

#in some business scenarios to insert more than one records at once like patient's
#allergies.
# allergies are entered in patient-allergy table with foreign key referencing
# patient's id in patient table - many-to-one relation.
#we can use the cached translated sql for this bulk inserting/updating/deleting
#or implementing executemany technique. (to be developed).
#-----
#insert record into table. (implemented)
#update record from table. (implemented)
#delete record from table. (implemented)

#-----
#record/records - table/tables - value/values
# 2^3 = 8 possible/probable combinations
#-
#select record from table using value per attribute. (implemented).
#select record from table using value(s) per attribute. (to be implemented).
#select record(s) from table using value per attribute. (implemented).
#select record(s) from table using value(s) per attribute. (to be implemented).
#-
#select record from table(s) using value per attribute. (sql query mapping).
#select record from table(s) using value(s) per attribute. (sql query mapping).
#select record(s) from table(s) using value per attribute. (sql query mapping).
#select record(s) from table(s) using value(s) per attribute. (sql query mapping).
#-----
#================================================================================#
#https://docs.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server?view=sql-server-2017
#==> msodbcsql17
"""
If you installed this formula with the registration option (default), you'll
need to manually remove [ODBC Driver 17 for SQL Server] section from
odbcinst.ini after the formula is uninstalled. This can be done by executing
the following command:
    odbcinst -u -d -n "ODBC Driver 17 for SQL Server"
"""
#================================================================================#
#how to be sure prepared statement's parameters is passed to the cursor.
#================================================================================#