from __future__ import print_function
from datetime import date, datetime, timedelta
import mysql.connector
import time
import Login
import bcrypt
import os

cnx = mysql.connector.connect(user='root', password='', database='azdna')
cursor = cnx.cursor()


add_user_query = (
"INSERT INTO Users "
"(`username`, `password`, `email`, `group`, `creationDate`, `verifycode`, `verified`)"
"VALUES (%s, %s, %s, %s)"
)

#needs input cleaning/escaping/validation
#throws no errors atm if user already exists
def registerUser(name, password, email):
    verifycode = os.binascii.b2a_hex(os.urandom(15))
    user_data = (name, bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()), email, 0, int(time.time()), verifycode, "False")
    cursor.execute(add_user_query, user_data)
    cnx.commit()

    user_id = Login.loginUser(name, password)

    #call emailing script with verification link
    verifylink = "www.oxdna.org/verify?id={userId}&verify={verifycode}".format(userId = user_id, verifycode = verifycode)

    os.system("python3 /vagrant/azDNA/EmailScript.py -t 0 -n {username} -u {verifylink} -d {email}".format(username = name, verifylink = verifylink, email = email))

    return user_id

'''
import random
letters = "abcdefghijklmnopqrstuvwxyz"
random_name = "".join([random.choice(letters) for _ in range(5)])
registerUser(random_name, "pass123")
'''
