# import database_config
import pymysql
import exceptions
import flask
import datetime
import operator
import os
import collections


# Attempts to login and creates a session w/ name, email and debit balance
try:

    """connection = pymysql.connect(
            host=database_config.host,
            database=database_config.database,
            user=database_config.user,
            password=database_config.password,
            port=database_config.port
    )"""

    connection = pymysql.connect(
            host=os.environ['host'],
            database=os.environ['database'],
            user=os.environ['user'],
            password=os.environ['password'],
            port=int(os.environ['port'])
    )

    if connection.open:
        print("Connected to MySQL db")

        cursor = connection.cursor()
        cursor.execute("select database();")
        record = cursor.fetchone()
        print("You're connected to - ", record[0])
    else:
        raise exceptions.DatabaseConnectionError

except exceptions.DatabaseConnectionError:
    print("Error while connecting to MySQL")


def close_connect():
    if connection.open:
        connection.close()
    print("MySQL connection is closed")


def login(email, post_password):
    # Attempts to login and creates a session w/ name, email and debit balance

    try:
        cursor = connection.cursor()

    except exceptions.NoDatabaseConnectionError:
        print("Connection is not open")
        return

    cursor.execute("select password from customer where\
                    email = '%s'" % email)
    password = cursor.fetchone()

    if password is None:
        result = False
    elif password[0] != post_password:
        result = False
    else:
        flask.session['email'] = email

        cursor.execute("select id, first_name, last_name, balance\
                       from customer where email = '%s'" % email)

        result = cursor.fetchone()
        flask.session['id'] = int(result[0])
        flask.session['first_name'] = result[1]
        flask.session['last_name'] = result[2]
        flask.session['balance'] = float(result[3])

        result = True

    cursor.close()
    return result


def get_debit_transactions(id):
    # Retrieves array of all debit transactions

    try:
        cursor = connection.cursor()

    except exceptions.NoDatabaseConnectionError:
        print("Connection is not open")
        return

    query = '\
             select vendor_name, day, month, year, hour, minutes, seconds,\
                amount\
             from vendor_name natural join\
             (\
              select vendor_id, day, month, year, hour, minutes, seconds,\
                amount\
              from customer natural join debit_purchase\
              where id = %d\
             ) as vid;' % id

    cursor.execute(query)
    raw_transactions = cursor.fetchall()
    transactions = []

    for i in range(0, len(raw_transactions)):
        transactions.append([])

        date = datetime.datetime(int(raw_transactions[i][3]),
                                 int(raw_transactions[i][2]),
                                 int(raw_transactions[i][1]),
                                 int(raw_transactions[i][4]),
                                 int(raw_transactions[i][5]),
                                 int(raw_transactions[i][6]))

        transactions[i].append(raw_transactions[i][0])
        transactions[i].append(date)
        transactions[i].append(float(raw_transactions[i][7]))

    print(transactions)
    print("Yo!")
    transactions.sort(reverse=True, key=operator.itemgetter(1))
    print(transactions)

    flask.session['debit_transactions'] = transactions
    cursor.close()


def get_credit_history(id):
    try:
        cursor = connection.cursor()

    except exceptions.NoDatabaseConnectionError:
        print("Connection is not open")
        return

    query = 'select id, first_name, last_name, account_number, vendor_name,\
     amount, day, month, year, hour, minutes, seconds from credit_purchase\
     natural join credit_owner natural join customer natural join vendor_name;'

    cursor.execute(query)
    raw_transactions = cursor.fetchall()

    if raw_transactions is None:
        return

    transactions = []


"""def get_savings_transactions(id):
    # Retrieves array of all savings transactions

    try:
        cursor = connection.cursor()

    except exceptions.NoDatabaseConnectionError:
        print("Connection is not open")
        return"""
