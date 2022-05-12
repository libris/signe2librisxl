import re


def connect(connection: str):
    import pyodbc

    parsed = re.match(
        r'sqlserver://(\w+):([^@]+)@([^:]+):(\d+);databaseName=(\w+)',
        connection,
    )
    assert parsed is not None
    dbuid, dbpasswd, dbhost, dbport, dbname = parsed.groups()

    return pyodbc.connect(
        driver='{ODBC Driver 18 for SQL Server}',
        server=f'{dbhost},{dbport}',
        database=dbname,
        encrypt='no',
        uid=dbuid,
        pwd=dbpasswd,
    )


def dump(connection: str, table: str):
    cursor = connect(connection).cursor()
    cursor.execute(f'SELECT * FROM {table}')
    yield from cursor
