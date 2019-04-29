import database_config
import pymysql
import exceptions
import flask
import datetime
import operator
import os
import collections


# Attempts to login and creates a session w/ name, email and debit balance
try:

    connection = pymysql.connect(
            host=database_config.host,
            database=database_config.database,
            user=database_config.user,
            password=database_config.password,
            port=database_config.port,
            autocommit=True
    )

    """connection = pymysql.connect(
            host=os.environ['host'],
            database=os.environ['database'],
            user=os.environ['user'],
            password=os.environ['password'],
            port=int(os.environ['port']),
            autocommit=True
    )"""

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

        cursor.execute("select id\
                       from customer where email = '%s';" % email)

        result = cursor.fetchone()
        flask.session['id'] = int(result[0])

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

    query = "select first_name, last_name, balance\
             from customer\
             where id = %s;" % flask.session['id']

    cursor.execute(query)
    result = cursor.fetchone()

    flask.session['first_name'] = result[0]
    flask.session['last_name'] = result[1]
    flask.session['balance'] = float(result[2])

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


def get_debit_transfers():

    try:
        cursor = connection.cursor()

    except exceptions.NoDatabaseConnectionError:
        print("Connection is not open")
        return

    query = "select *\
             from transfer\
             where\
             account_from = %d and type_from = 'checking'\
             and type_to <> 'credit';\
             " % flask.session['id']

    cursor.execute(query)
    raw_checking_transfers = cursor.fetchall()

    query = "select *\
             from transfer\
             where\
             account_to = %d and type_to = 'checking';\
             " % flask.session['id']

    cursor.execute(query)
    raw_checking_transfers += cursor.fetchall()

    query = "select amount, day, month, year, hour, minutes,\
             seconds, account_from, type_from, account_to, type_to\
             from credit_owner inner join transfer\
             on credit_owner.account_number = transfer.account_to\
             where account_from = %d and type_from = 'checking'\
             " % (flask.session['id'])

    cursor.execute(query)

    raw_checking_transfers += cursor.fetchall()

    if raw_checking_transfers is None:
        return

    checking_transfers = []

    for i in range(0, len(raw_checking_transfers)):
        checking_transfers.append([])

        account_from = int(raw_checking_transfers[i][7])
        type_from = raw_checking_transfers[i][8]
        account_to = int(raw_checking_transfers[i][9])
        type_to = raw_checking_transfers[i][10]

        date = datetime.datetime(int(raw_checking_transfers[i][3]),
                                 int(raw_checking_transfers[i][2]),
                                 int(raw_checking_transfers[i][1]),
                                 int(raw_checking_transfers[i][4]),
                                 int(raw_checking_transfers[i][5]),
                                 int(raw_checking_transfers[i][6]))

        checking_transfers[i].append(float(raw_checking_transfers[i][0]))
        checking_transfers[i].append(date)

        if type_from == "checking" and type_to == "credit":
            checking_transfers[i].append("Payment")
        elif type_from == "checking":
            checking_transfers[i].append("Withdrawal")
        else:
            checking_transfers[i].append("Deposit")

        if account_from == account_to or type_to == "credit":
            checking_transfers[i].append("Personal - " + type_from)
            checking_transfers[i].append("Personal - " + type_to)
        elif account_from == flask.session['id']:
            checking_transfers[i].append("Personal - " + type_from)
            query = "select first_name, last_name\
                     from customer\
                     where id = %d;" % account_to

            cursor.execute(query)
            raw_receiver = cursor.fetchone()
            receiver = raw_receiver[0] + " " + raw_receiver[1]
            checking_transfers[i].append(receiver)
        else:
            query = "select first_name, last_name\
                     from customer\
                     where id = %d;" % account_from

            cursor.execute(query)
            raw_receiver = cursor.fetchone()
            receiver = raw_receiver[0] + " " + raw_receiver[1]
            checking_transfers[i].append(receiver)

            checking_transfers[i].append("Personal - " + type_to)

    checking_transfers.sort(reverse=True, key=operator.itemgetter(1))

    cursor.close()
    flask.session['checking_transfers'] = checking_transfers


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

        if type_from == "savings":
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


def personal_transfer(transfer_type, amount):
    try:
        cursor = connection.cursor()

    except exceptions.NoDatabaseConnectionError:
        print("Connection is not open")
        return

    if transfer_type == "checking_to_savings":
        query = "select balance\
                 from customer\
                 where id = %s;" % flask.session['id']
    else:
        query = "select balance\
                 from savings\
                 where id = %s;" % flask.session['id']

    cursor.execute(query)
    balance = float(cursor.fetchone()[0])

    if balance < amount:
        flask.session['message'] = "Insufficient Funds"
        return

    if transfer_type == "checking_to_savings":
        query = "update customer\
                 set balance = balance - %d\
                 where id = %d;" % (float(amount), flask.session['id'])

        cursor.execute(query)

        query = "update savings\
                 set balance = balance + %d\
                 where id = %d;" % (float(amount), flask.session['id'])

        cursor.execute(query)

        type_from = "checking"
        type_to = "savings"

    else:
        query = "update savings\
                 set balance = balance - %d\
                 where id = %d;" % (float(amount), flask.session['id'])

        cursor.execute(query)

        query = "update customer\
                 set balance = balance + %d\
                 where id = %d;" % (float(amount), flask.session['id'])

        cursor.execute(query)

        type_from = "savings"
        type_to = "checking"

    now = datetime.datetime.now()
    year = now.year
    month = now.month
    day = now.day
    hour = now.hour
    minute = now.minute
    second = now.second

    query = 'insert into transfer\
             (amount, day, month, year, hour, minutes, seconds, account_from,\
              type_from, account_to, type_to)\
              values\
              (%d, %d, %d, %d, %d, %d, %d, %d, "%s", %d, "%s");\
              ' % (amount, day, month, year, hour, minute, second,
                   flask.session['id'], type_from, flask.session['id'],
                   type_to)

    cursor.execute(query)
    cursor.close()


def credit_payment(account, amount):
    try:
        cursor = connection.cursor()

    except exceptions.NoDatabaseConnectionError:
        print("Connection is not open")
        return

    query = "select balance\
             from customer\
             where id = %s;" % flask.session['id']

    cursor.execute(query)
    balance = float(cursor.fetchone()[0])

    if balance < amount:
        flask.session['message'] = "Insufficient Funds"
        return

    query = "select line_of_credit, line_of_credit_left\
             from credit\
             where account_number = %s;" % account

    cursor.execute(query)
    raw_info = cursor.fetchone()
    line_of_credit = float(raw_info[0])
    line_of_credit_left = float(raw_info[1])

    if line_of_credit_left + amount > line_of_credit:
        flask.session['message'] = "Payment exceeds line of credit by \
                                    " + str(line_of_credit_left + amount - line_of_credit)
        return

    query = "update customer\
             set balance = balance - %d\
             where id = %d;" % (float(amount), flask.session['id'])

    cursor.execute(query)

    query = "update credit\
             set line_of_credit_left = line_of_credit_left + %s\
             where account_number = %s;" % (float(amount), account)

    cursor.execute(query)

    now = datetime.datetime.now()
    year = now.year
    month = now.month
    day = now.day
    hour = now.hour
    minute = now.minute
    second = now.second

    query = 'insert into transfer\
             (amount, day, month, year, hour, minutes, seconds, account_from,\
              type_from, account_to, type_to)\
              values\
              (%d, %d, %d, %d, %d, %d, %d, %d, "%s", %d, "%s");\
              ' % (amount, day, month, year, hour, minute, second,
                   int(flask.session['id']), 'checking', int(account),
                   'credit')

    cursor.execute(query)
    cursor.close()


def send_money(recipient, amount):
    try:
        cursor = connection.cursor()

    except exceptions.NoDatabaseConnectionError:
        print("Connection is not open")
        return

    query = "select balance\
             from customer\
             where id = %s;" % flask.session['id']

    cursor.execute(query)
    balance = float(cursor.fetchone()[0])

    if balance < amount:
        flask.session['message'] = "Insufficient Funds"
        return

    query = "select balance\
             from customer\
             where id = %s;" % flask.session['id']

    cursor.execute(query)
    balance = float(cursor.fetchone()[0])

    if balance < amount:
        flask.session['message'] = "Insufficient Funds"
        return

    query = "update customer\
             set balance = balance - %d\
             where id = %d;" % (float(amount), flask.session['id'])

    cursor.execute(query)

    query = "update customer\
             set balance = balance + %d\
             where id = %d;" % (float(amount), int(recipient))

    cursor.execute(query)

    now = datetime.datetime.now()
    year = now.year
    month = now.month
    day = now.day
    hour = now.hour
    minute = now.minute
    second = now.second

    query = 'insert into transfer\
             (amount, day, month, year, hour, minutes, seconds, account_from,\
              type_from, account_to, type_to)\
              values\
              (%d, %d, %d, %d, %d, %d, %d, %d, "%s", %d, "%s");\
              ' % (amount, day, month, year, hour, minute, second,
                   int(flask.session['id']), 'checking', int(recipient),
                   'checking')

    cursor.execute(query)
    cursor.close()


def open_savings_account():
    try:
        cursor = connection.cursor()

    except exceptions.NoDatabaseConnectionError:
        print("Connection is not open")
        return

    query = "insert into savings\
             (id, balance, monthly_transfer)\
             values\
             (%d, 0, 0);" % flask.session['id']

    cursor.execute(query)
    cursor.close()
