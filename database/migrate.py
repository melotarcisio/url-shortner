from database import get_db

if __name__ == '__main__':
    db = get_db()
    ddl = open('database/ddl.sql', 'r', encoding='utf-8').read()

    for query in ddl.split(';'):
        _ = query and db.execute_raw(query)

    db.close()