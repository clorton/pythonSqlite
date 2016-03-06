#!/usr/bin/python

import sqlite3
import time


class DbRow(object):

    def __init__(self, row, columns):
        self.row = row
        self.columns = columns
        pass

    def __getitem__(self, item):
        return self.row[self.columns.index(item)]

    def __setitem__(self, key, value):
        pass

    def __delitem__(self, key):
        pass


def main(filename):

    # http://stackoverflow.com/questions/2887878/importing-a-csv-file-into-a-sqlite3-database-table-using-python

    print(time.strftime('%H:%M:%S') + ' Reading CSV file...')
    with open(filename, 'rb') as f:
        columns = get_column_headers(f)
        connection, cursor = open_database(':memory:')
        create_table('data', columns, cursor, connection)
        insert_data(f, 'data', columns, cursor, connection)

    c0 = time.clock()
    rows = select_where('Year = 1980 AND Gender = 0 AND Age >= 15 AND Age < 50', cursor)
#    # Year,Node_ID,ID,Age,Gender,CD4,StartingART
#    rows = select_data('Year >= 2004 And Age >= 7300 And Age < 10950', cursor)
    c1 = time.clock()
    table = []
    for row in rows:
        table.append(DbRow(row, columns))
    c2 = time.clock()
    count = 0
    sum = 0
    for row in table:
        sum += row['Age']
        count += 1
    c3 = time.clock()
    average_age = sum / count
    print('Select returned {0} rows.'.format(len(rows)))
    for i in range(0, 10):
        print(rows[i])
    print('Average age: {0}'.format(average_age))
    print('Query table:  {0}'.format(c1 - c0))
    print('Create table: {0}'.format(c2 - c1))
    print('Access table: {0}'.format(c3 - c2))

    rows = select('SELECT DISTINCT Year FROM data', cursor)
    print('{0} distinct reporting years.'.format(len(rows)))

    connection.close()
    print(time.strftime('%H:%M:%S') + ' Closed database.')

    pass


def get_column_headers(f):
    header = f.readline()
    columns = tuple([s.strip() for s in header.split(',')])

    return columns


def open_database(name):
    connection = sqlite3.connect(name)
    cursor = connection.cursor()

    return connection, cursor


def create_table(name, columns, cursor, connection):
    column_spec = ','.join(["'{0}' REAL".format(c) for c in columns])
    cursor.execute("CREATE TABLE {0} ({1})".format(name, column_spec))
    connection.commit()

    pass


def insert_data(source_file, table, columns, cursor, connection):
    column_names = ','.join(["'{0}'".format(c) for c in columns])
    sql_prefix = "INSERT INTO {0} ({1}) VALUES ".format(table, column_names) + "({0})"
    row_count = 0
    for row in source_file.readlines():
        sql = sql_prefix.format(row)
        cursor.execute(sql)
        row_count += 1

    connection.commit()
    print(time.strftime('%H:%M:%S') + ' Finished reading file and inserting data ({0} rows).'.format(row_count))

    pass


def select_where(where, cursor):
    cursor.execute("SELECT * FROM data WHERE {0}".format(where))
    rows = cursor.fetchall()
    print(time.strftime('%H:%M:%S') + ' Finished fetchall().')

    return rows


def select(sql, cursor):
    cursor.execute(sql)
    rows = cursor.fetchall()
    print(time.strftime('%H:%M:%S') + ' Finished select().')

    return rows


if __name__ == '__main__':
    main('ReportHIVByAgeAndGender.csv')
#    main('ReportHIVART.csv')
    pass
