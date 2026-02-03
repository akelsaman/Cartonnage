# Cartonnage

Cartonnage is a Database-First ORM—designed as a 'Live Database Reflection ORM' or 'Record Reflection Layer (RRL)'—that reflects your existing database at runtime, speaking its schema fluently: not model-first, not schema-first, but runtime-bound, making it the ORM for existing databases:

- SQLite
- MySQL
- PostgreSQL
- Oracle
- Microsoft SQL Server

## Installation

```bash
pip install cartonnage
```

With database drivers:
```bash
pip install cartonnage[mysql]     # MySQL support
pip install cartonnage[postgres]  # PostgreSQL support
pip install cartonnage[oracle]    # Oracle support
pip install cartonnage[mssql]     # SQL Server support
pip install cartonnage[all]       # All databases
```

## License

MIT
