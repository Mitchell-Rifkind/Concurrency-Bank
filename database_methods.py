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

    query = "select password from customer where email = '%s';" % email
    cursor.execute(query)
    password = cursor.fetchone()

    if password is None:
        result = False
    elif password[0] != post_password:
        result = False
    else:
        flask.session['email'] = email

        cursor.execute("select id, first_name, last_name, balance\
                       from customer where email = '%s';" % email)

        result = cursor.fetchone()
        flask.session['id'] = int(result[0])
        flask.session['first_name'] = result[1]
        flask.session['last_name'] = result[2]
        flask.session['balance'] = float(result[3])

        result = True

    cursor.close()
    return result


def get_debit_transactions():
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
             ) as vid;' % flask.session['id']

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

    transactions.sort(reverse=True, key=operator.itemgetter(1))

    cursor.close()
    flask.session['debit_transactions'] = transactions


def get_credit_history():
    # Gets the credit history of all credit accounts associated with the user

    try:
        cursor = connection.cursor()

    except exceptions.NoDatabaseConnectionError:
        print("Connection is not open")
        return

    query = "select account_number, vendor_name, amount, day, month, year,\
             hour, minutes, seconds\
             from credit_purchase natural join credit_owner natural join\
             customer natural join vendor_name where id = %s\
             ;" % flask.session['id']

    cursor.execute(query)
    raw_transactions = cursor.fetchall()

    query = 'select account_number\
             from credit_owner\
             where id = %s;' % flask.session['id']

    cursor.execute(query)
    raw_accounts = cursor.fetchall()

    if raw_accounts is None:
        return

    accounts = {int(raw_account[0]): [] for raw_account in raw_accounts}
    account_balance = {}

    for account in accounts:
        query = "select account_number, line_of_credit, line_of_credit_left\
                 from credit\
                 where account_number = %d;" % account

        cursor.execute(query)
        raw_credit = cursor.fetchone()
        owed = float(raw_credit[1]) - float(raw_credit[2])
        account_balance[account] = owed

    for i in range(0, len(raw_transactions)):
        temp = []

        date = datetime.datetime(int(raw_transactions[i][5]),
                                 int(raw_transactions[i][4]),
                                 int(raw_transactions[i][3]),
                                 int(raw_transactions[i][6]),
                                 int(raw_transactions[i][7]),
                                 int(raw_transactions[i][8]))

        temp.append(raw_transactions[i][1])
        temp.append(float(raw_transactions[i][2]))
        temp.append(date)

        accounts[int(raw_transactions[i][0])].append(temp)

    for account in accounts:
        accounts[account].sort(reverse=True, key=operator.itemgetter(2))

    cursor.close()
    flask.session['amount_owed'] = account_balance
    flask.session['credit_transactions'] = accounts


def get_savings_transfers():
    # Retrieves array of all savings transfers

    try:
        cursor = connection.cursor()

    except exceptions.NoDatabaseConnectionError:
        print("Connection is not open")
        return

    query = "select balance, monthly_transfer from savings\
             where id = %d;" % flask.session['id']

    cursor.execute(query)
    raw_savings_summary = cursor.fetchone()

    if raw_savings_summary is None:
        return

    flask.session['savings_balance'] = float(raw_savings_summary[0])
    flask.session['savings_transfers_used'] = int(raw_savings_summary[1])

    query = "select *\
             from transfer\
             where\
             account_from = %d and type_from = 'savings';\
             " % flask.session['id']

    cursor.execute(query)
    raw_savings_transfers = cursor.fetchall()

    query = "select *\
             from transfer\
             where\
             account_to = %d and type_to = 'savings';\
             " % flask.session['id']

    cursor.execute(query)
    raw_savings_transfers += cursor.fetchall()

    savings_transfers = []

    for i in range(0, len(raw_savings_transfers)):
        savings_transfers.append([])

        account_from = int(raw_savings_transfers[i][7])
        type_from = raw_savings_transfers[i][8]
        account_to = int(raw_savings_transfers[i][9])
        type_to = raw_savings_transfers[i][10]

        date = datetime.datetime(int(raw_savings_transfers[i][3]),
                                 int(raw_savings_transfers[i][2]),
                                 int(raw_savings_transfers[i][1]),
                                 int(raw_savings_transfers[i][4]),
                                 int(raw_savings_transfers[i][5]),
                                 int(raw_savings_transfers[i][6]))

        savings_transfers[i].append(float(raw_savings_transfers[i][0]))
        savings_transfers[i].append(date)

        if type_from == "Savings":
            savings_transfers[i].append("Withdrawal")
        else:
            savings_transfers[i].append("Deposit")

        if account_from == account_to:
            savings_transfers[i].append("Personal - " + type_from)
            savings_transfers[i].append("Personal - " + type_to)
        elif account_from == flask.session['id']:
            savings_transfers[i].append("Personal - " + type_from)
            query = "select first_name, last_name\
                     from customer\
                     where id = %d;" % account_to

            cursor.execute(query)
            raw_receiver = cursor.fetchone()
            receiver = raw_receiver[0] + " " + raw_receiver[1]
            savings_transfers[i].append(receiver)
        else:
            query = "select first_name, last_name\
                     from customer\
                     where id = %d;" % account_from

            cursor.execute(query)
            raw_receiver = cursor.fetchone()
            receiver = raw_receiver[0] + " " + raw_receiver[1]
            savings_transfers[i].append(receiver)

            savings_transfers[i].append("Personal - " + type_to)

    savings_transfers.sort(reverse=True, key=operator.itemgetter(1))

    cursor.close()
    flask.session['savings_transfers'] = savings_transfers


def get_personal_info():
    # Retrieves the personal information of the current user

    try:
        cursor = connection.cursor()

    except exceptions.NoDatabaseConnectionError:
        print("Connection is not open")
        return

    query = "select first_name, last_name, phone, email,\
             street_name, street_number, city, zipcode, state\
             from customer natural join state\
             where id = %d;" % flask.session['id']

    cursor.execute(query)
    raw_info = cursor.fetchone()

    info = []

    info.append(raw_info[0])
    info.append(raw_info[1])
    info.append(int(raw_info[2]))
    info.append(raw_info[3])
    info.append(raw_info[4])
    info.append(int(raw_info[5]))
    info.append(raw_info[6])
    info.append(int(raw_info[7]))
    info.append(raw_info[8])

    cursor.close()
    flask.session['personal_info'] = info


def update_info(field, value):
    try:
        cursor = connection.cursor()

    except exceptions.NoDatabaseConnectionError:
        print("Connection is not open")
        return

    if field == "zipcode_state":
        value = value.split(",")
        query = 'insert ignore into state\
                 set\
                 zipcode = "%s", state = "%s";' % (value[0], value[1])
        cursor.execute(query)

        field = "zipcode"
        value = value[0]

    query = 'update customer\
             set %s = "%s"\
             where id = %d;' % (field, value, flask.session['id'])

    cursor.execute(query)
    cursor.close()
