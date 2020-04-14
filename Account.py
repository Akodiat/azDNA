import os
import time
import uuid
import subprocess
import mysql.connector

cnx = mysql.connector.connect(user='root', password='', database='azdna')
cursor = cnx.cursor()

find_email_by_user_id_query = ("SELECT email FROM Users WHERE id = %s")
set_email = ("UPDATE Users SET email = %s WHERE id = %s")
find_date_by_user_id_query = ("SELECT creationDate FROM Users WHERE id = %s")
find_status_by_user_id_query = ("SELECT status FROM Users WHERE id = %s")
get_verify_code_query = ("SELECT verifycode FROM Users WHERE id = %s")
verify_user = ("UPDATE Users SET verified = %s WHERE id = %s")
get_username_query("SELECT username FROM Users WHERE id = %s")
delete_unverified = ("DELETE FROM Users WHERE verified = False AND creationDate > %s")

def getEmail(userId):
    cursor.execute(find_email_by_user_id_query(userId))
    return cursor.email

def setEmail(email, userId):
    cursor.execute(set_email(email, userId))
    return "Email successfully updated!"

def getCreationDate(userId):
    cursor.execute(find_date_by_user_id_query(userId))
    return cursor.creationDate

def getStatus(userId):
    cursor.execute(find_status_by_user_id_query(userId))
    return cursor.status

def getVerificationCode(userId):
    cursor.execute(get_verify_code_query(userId))
    return cursor.verifycode

def getUsername(userId):
    cursor.execute(get_username_query(userId))
    return cursor.username

#CreationTime in seconds
def deleteUnverified(CreationTime):
    try:
        cursor.execute(deleted_unverified(int(time.time() - CreationTime)))
        cnx.commit()
    except:
        pass

#checks verification code for user
def verifyUser(userId, VerifyCode):
    #not sure how mysql.connector works if entry does not exist/none found, so wrapping in try catch just in case
    try:
        #query the database for the user's verification code
        iterator = cursor.execute(get_verify_code_query(userId))
        #check that they match
        if(iterator.verifycode == VerifyCode):
            #verify the user
            cursor.execute(verify_user("True", userId))
            cnx.commit()
            return True;
        else:
            return False;
    except:
        return False;
