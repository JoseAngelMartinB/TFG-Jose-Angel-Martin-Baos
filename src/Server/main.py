#!/usr/bin/python3
# -*- coding: utf-8; mode: python -*-

# BSC Thesis
#
# Author
#  - José Ángel Martín Baos

from ServerConfig import *
from flask import Flask, render_template, redirect, url_for, request, make_response
import os
import sys
import time
import pymysql
import pytz
import datetime
import hashlib
import base64
import uuid
from Crypto.Cipher import AES
import ibmiotf.application

# Create a python Flask app
app = Flask(__name__)
port = os.getenv('PORT', PORT)

local_tz = pytz.timezone('Europe/Madrid')

BS = 16
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS).encode()
unpad = lambda s: s[:-ord(s[len(s)-1:])]
def iv():
    """
    The initialization vector to use for encryption or decryption.
    """
    return chr(0) * 16

class AESCipher():
    """
    Encript a message using AES alorithm
    """
    def __init__(self, key):
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, message):
        message = message.encode()
        raw_msg = pad(message)
        cipher = AES.new(self.key, AES.MODE_CBC, iv())
        enc_msg = cipher.encrypt(raw_msg)
        return base64.b64encode(enc_msg).decode('utf-8')

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        cipher = AES.new(self.key, AES.MODE_CBC, iv())
        dec = cipher.decrypt(enc)
        return unpad(dec).decode('utf-8')


def getDefaultData():
    """
    Return defacult data in case there is an error.

    Output:   data -> Default data.
    """
    data = {
        'idDevice' : None,
        'DateAndTime' : None,
        'Temperature' : 0,
        'Humidity' : 0,
        'Pressure' : 0,
        'CO' : 0,
        'LPG' : 0,
        'Cars' : 0
    }
    return data

def getLastData(idDevice): # TODO
    """
    Obtain last data stored into de DB.

    Intput:   idDevice -> Raspberry Pi device from which obtain the data
    Output:   data -> Dictionary with the obtained data.
    """
    try:
        # Open database connection
        db = pymysql.connect(DB_HOST, DB_USER, DB_PASS, DB_NAME, charset='utf8', use_unicode=True)

        # Prepare a cursor object
        cursor = db.cursor(pymysql.cursors.DictCursor)

        # Prepare SQL query to obtain the data
        sql = "SELECT DateAndTime, Temperature, Humidity, Pressure, CO, LPG, Cars \
                FROM data t\
                inner join ( \
                    SELECT idDevice, max(DateAndTime) as LastDate \
                    FROM data \
                    GROUP BY idDevice \
                ) tmd on t.idDevice = tmd.idDevice and t.DateAndTime = tmd.LastDate \
                    WHERE t.idDevice = '%d'" % (idDevice)

        # Execute the SQL querry
        cursor.execute(sql)

        # Obtain the data
        rows = cursor.fetchall()
        data = rows[0]
        data['idDevice'] = idDevice
        db.close()
    except:
        data = getDefaultData()
        db.close()

    return data


def getDevices():
    """
    Obtain the Raspberry Pi devices.

    Output:   devices -> List of dictionary with the obtained devices.
    """
    # Open database connection
    db = pymysql.connect(DB_HOST, DB_USER, DB_PASS, DB_NAME, charset='utf8', use_unicode=True)

    # Prepare a cursor object
    cursor = db.cursor(pymysql.cursors.DictCursor)

    # Prepare SQL query to obtain the data
    sql = "SELECT * \
    FROM devices t1 \
    LEFT OUTER JOIN( \
    	SELECT idDevice, max(DateAndTime) AS LastDate \
    	FROM data \
        GROUP BY idDevice \
    ) t2 ON t1.idDevice = t2.idDevice;"

    # Execute the SQL querry
    cursor.execute(sql)

    # Obtain the data
    devices = cursor.fetchall()
    db.close()

    # Convert time to UTC - Europe/Madrid
    time_now = datetime.datetime.now().replace(tzinfo=pytz.utc).astimezone(local_tz)
    time_now = time_now.replace(tzinfo=None)

    for device in devices:
        if device['LastDate'] == None:
            device['status'] = False
        elif time_now - device['LastDate'] < datetime.timedelta(minutes=device['timeInterval']*3):
            device['status'] = True
        else:
            device['status'] = False

    return devices


def user_login(email, password):
    """
    Check if the user exist and if the password is the correct one.

    Intput:   email -> User email
              password -> User password
    Output:   success -> True if the email and password match
              user_id -> The user identification
              user_auth_token -> An identifier to check the user autenticity during
                the sesion
    """
    success = False
    user_id = None
    user_auth_token = None

    try:
        # Open database connection
        db = pymysql.connect(DB_HOST, DB_USER, DB_PASS, DB_NAME, charset='utf8', use_unicode=True)

        # Prepare a cursor object
        cursor = db.cursor(pymysql.cursors.DictCursor)

        # Prepare SQL query to obtain the data
        sql = "SELECT user_id, password \
                FROM users \
                WHERE email = '%s'" % (email)

        # Execute the SQL querry
        cursor.execute(sql)

        # Obtain the data
        rows = cursor.fetchall()
        user_data = rows[0]

        raw_pass = str(user_data['user_id']) + email
        encrip_pass = AESCipher(password).encrypt(raw_pass)

        if encrip_pass == user_data['password']:
            success = True
            user_id = user_data['user_id']
            user_auth_token = str(uuid.uuid4())

            cursor = db.cursor(pymysql.cursors.DictCursor)

            # Prepare SQL query to obtain the data
            sql = "UPDATE users \
                    SET last_token = '%s' \
                    WHERE user_id = %d" % (user_auth_token, user_id)

            # Execute the SQL querry
            cursor.execute(sql)
            db.commit()

        db.close()
    except:
        db.close()

    return (success, user_id, user_auth_token)


def checkUserSession(user_id, user_auth_token):
    """
    Verify the user session.

    Intput:   user_id -> The user identification
              user_auth_token -> An identifier to check the user autenticity during
                the sesion
    Output:   success -> True if the user session exists
    """
    success = False

    try:
        # Open database connection
        db = pymysql.connect(DB_HOST, DB_USER, DB_PASS, DB_NAME, charset='utf8', use_unicode=True)

        # Prepare a cursor object
        cursor = db.cursor(pymysql.cursors.DictCursor)

        # Prepare SQL query to obtain the data
        sql = "SELECT last_token, email \
                FROM users \
                WHERE user_id = %d" % (user_id)

        # Execute the SQL querry
        cursor.execute(sql)

        # Obtain the data
        rows = cursor.fetchall()
        user_data = rows[0]

        if user_auth_token == user_data['last_token']:
            success = True
            email = user_data['email']

        db.close()
    except:
        db.close()

    return (success, email)


# Python Flask Functions:
@app.route('/')
@app.route('/index.html')
def main():
    """
    Render / web page.
    """
    return redirect(url_for('about'))


@app.route('/real_time.html', methods=['GET', 'POST'])
def realTime():
    """
    Render /real_time.html web page.
    """
    devices = getDevices()
    location = ""
    update_interval = 300

    if request.method == 'POST':
        try:
            idDevice = int(request.form['device'])
        except KeyError:
            idDevice = devices[0]['idDevice']
            location = None
    elif 'device' in request.cookies:
        idDevice = int(request.cookies.get('device'))
    else:
        idDevice = devices[0]['idDevice']

    if location != None:
        location = None
        for device in devices:
            if device['idDevice'] == idDevice:
                location = device['Location']
                update_interval = 60*device['timeInterval']
                break

    last_update = datetime.datetime.now().replace(tzinfo=pytz.utc).astimezone(local_tz)
    last_update = last_update.replace(tzinfo=None).strftime("%Y-%m-%d at %H:%M:%S")
    data = getLastData(idDevice)

    resp = make_response(render_template('real_time.html', devices=devices, data=data, limits=LIMITS, \
        last_update=last_update, location=location, update_interval=update_interval))
    resp.set_cookie('device', str(idDevice))

    return resp


@app.route('/historical.html')
def historical():
    """
    Render /historical.html web page.
    """

    labels = ["01-04-2018 12:35", "01-04-2018 12:40", "01-04-2018 12:45", "01-04-2018 12:50"]

    data = [
        {'idDevice' : 1,
        'location': unicode("Device " + str(1) + ": Escuela Superior de Informática. Ciudad Real, España.", 'utf-8'),
        'color' : CHART_COLORS[1 % len(CHART_COLORS)],
        'temperature': [27, 29, 32, 31],
        'humidity': [38.1, 38.2, 38.2, 38.5]
        },
        {'idDevice' : 2,
        'location': unicode("Device " + str(2) + ": Bolaños de Calatrava, España.", 'utf-8'),
        'color' : CHART_COLORS[2 % len(CHART_COLORS)],
        'temperature': [21, 22, 20, 20],
        'humidity': [32.1, 32.2, 32.2, 32.3]
        }
    ]


    return render_template('historical.html', labels=labels, data=data)


@app.route('/configuration.html')
def configuration():
    """
    Render /configuration.html web page.
    """

    # Check if the user has log into the system
    auth = False
    try:
        user_id = int(request.cookies.get('user_id'))
        user_auth_token = request.cookies.get('user_auth_token')
        if user_id:
            (auth, email) = checkUserSession(user_id, user_auth_token)
    except:
        pass

    if auth == False:
        return redirect(url_for('login'))
    else:
        return render_template('configuration.html', email=email)


@app.route('/login.html', methods=['GET', 'POST'])
def login():
    """
    Render /login.html web page.
    """
    bad_login = False

    try:
        if request.args.get('logout') == "1":
            resp = make_response(render_template('login.html', bad_login=bad_login))
            resp.set_cookie('user_id', '', expires=0)
            resp.set_cookie('user_auth_token', '', expires=0)
            return resp
    except:
        pass

    if request.method == 'POST':
        try:
            if request.form['submit'] == "True":
                email = request.form['Email']
                password = request.form['Password']

                (success, user_id, user_auth_token) = user_login(email, password)

                if success:
                    expire_date = datetime.datetime.now()
                    expire_date = expire_date + datetime.timedelta(hours=1)

                    resp = make_response(redirect(url_for('configuration')))
                    resp.set_cookie('user_id', str(user_id), expires=expire_date)
                    resp.set_cookie('user_auth_token', user_auth_token, expires=expire_date)
                    return resp
                else:
                    bad_login = True

        except KeyError:
            pass

    return render_template('login.html', bad_login=bad_login)



@app.route('/about.html')
def about():
    """
    Render /about.html web page.
    """
    return render_template('about.html',)



def sensorUpdate(event):
    """
    This method is executed everytime an event arrives with new data from the
    Raspberry Pi devices. The data is processed and stored into the database.

    Input:   event -> Event recived from IBM IoT.
    """
    data = event.data
    date_time = event.timestamp

    # Open database connection
    db = pymysql.connect(DB_HOST, DB_USER, DB_PASS, DB_NAME)

    # prepare a cursor object
    cursor = db.cursor()

    # Prepare SQL query to INSERT a record into the database
    sql = "INSERT INTO data(idDevice, DateAndTime, Temperature, Humidity, Pressure, CO, LPG, Cars) \
            VALUES ('%s', '%s', '%f', '%f', '%f', '%f', '%f', '%f')" % \
            (data['idDevice'], data['date_time'], data['temperature'], data['humidity'], data['pressure'], data['CO'], data['LPG_gas'], data['car_count'])

    try:
        # Execute the SQL command and commit the changes in the database
        cursor.execute(sql)
        db.commit()
    except:
        # Rollback in case there is any error
        db.rollback()

    db.close()
    print("Stored live data from %s (%s) sent at %s into DB" % (event.deviceId, event.deviceType, date_time))

def removeLogFiles():
    """
    Remove log files generated by IBM IoT platform.
    """
    directory = "./"
    list_files = os.listdir( directory )

    for item in list_files:
        if item.endswith(".log"):
            os.remove(os.path.join(directory, item ))


if __name__ == "__main__":
    removeLogFiles()
    connect = True

    # Initialize the application client
    try:
        applicationFile = "application.conf"
        options = ibmiotf.application.ParseConfigFile(applicationFile)
        client = ibmiotf.application.Client(options)
    except Exception as e:
    	print("Caught exception connecting: %s" % str(e))
    	sys.exit()

    client.connect()
    client.subscribeToDeviceEvents(deviceType="Raspberry_Pi", event="sensor_update")
    client.deviceEventCallback = sensorUpdate

    # Execute Python Flask App
    app.run(host='0.0.0.0', port=int(port), debug=False)

    # Disconnect from server
    client.disconnect()
