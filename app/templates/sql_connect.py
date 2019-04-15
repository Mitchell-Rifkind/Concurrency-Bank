import database_config
import pymysql

try:
    connection = pymysql.connect(
            host=database_config.host,
            database=database_config.database,
            user=database_config.user,
            password=database_config.password,
            port=database_config.port
    )

    if connection.open:
        print("Connected to MySQL db")

        cursor = connection.cursor()
        cursor.execute("select database();")
        record = cursor.fetchone()
        print("You're connected to - ", record)

except:
    print("Error while connecting to MySQL")

finally:

    if connection.open:
        cursor.execute("select * from customer where ssn = 100438609;")
        record = cursor.fetchone()
        for attribute in record:
            print(attribute)

        cursor.close()
        connection.close()
        print("MySQL connection is closed")
