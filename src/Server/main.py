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
from dateutil.tz import tzlocal
import hashlib
import base64
import uuid
from Crypto.Cipher import AES
import math
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
import ibmiotf.application

# Create a python Flask app
app = Flask(__name__)
port = os.getenv('PORT', PORT)

local_tz = pytz.timezone('Europe/Madrid')
server_tz = tzlocal()

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

def getLastData(idDevice):
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


def getData(devices, dates):
    """
    Obtain sensor data stored into de DB.

    Intput:   devices -> List of Raspberry Pi devices from which obtain the data
              dates -> Initial and finish dates
    Output:   data -> List of dictionaries with the obtained data.
    """
    data = []
    try:
        # Open database connection
        db = pymysql.connect(DB_HOST, DB_USER, DB_PASS, DB_NAME, charset='utf8', use_unicode=True)

        # Prepare a cursor object
        cursor = db.cursor(pymysql.cursors.DictCursor)

        # Prepare SQL query to obtain the data
        sql = "SELECT idDevice, DateAndTime, Temperature, Humidity, Pressure, CO, LPG, Cars \
                FROM data \
                WHERE idDevice IN ("

        for i in range(0,len(devices)):
            sql += "'%d'" % (devices[i])
            if i != len(devices)-1:
                sql += ", "

        sql += ") \
                AND DateAndTime BETWEEN '%s' AND '%s' \
                ORDER BY DateAndTime ASC" % (dates[0], dates[1])

        # Execute the SQL querry
        cursor.execute(sql)

        # Obtain the data
        data = cursor.fetchall()
        db.close()
    except:
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
    time_now = datetime.datetime.now().replace(tzinfo=server_tz).astimezone(local_tz)
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


def getHistoricalData(selected_devices, dates, devices, smooth_factor):
    """
    Obtain sensor data stored into de DB and prepare it for plot.js.

    Intput:   selected_devices -> List of Raspberry Pi devices from which obtain the data
              dates -> Initial and finish dates
              devices -> Devices information
              smooth_factor -> Mooving average order
    Output:   labels -> List of the plot labels
              data -> Dictionary with plot data
    """
    labels = []
    data = []
    data_aux = getData(selected_devices, dates)
    temperature = dict()
    humidity = dict()
    pressure = dict()
    CO = dict()
    LPG = dict()
    Cars = dict()
    dates_list = []

    for dev in selected_devices:
        temperature[dev] = []
        humidity[dev] = []
        pressure[dev] = []
        CO[dev] = []
        LPG[dev] = []
        Cars[dev] = []

    for elm in data_aux:
        dates_list.append(elm['DateAndTime'])
        labels.append(elm['DateAndTime'].strftime("%d-%m-%Y %H:%M"))
        idDevice = int(elm['idDevice'])
        for dev in selected_devices:
            if dev == idDevice:
                temperature[dev].append(round(elm['Temperature'], 1))
                humidity[dev].append(round(elm['Humidity'], 1))
                pressure[dev].append(round(elm['Pressure'], 1))
                CO[dev].append(round(elm['CO'], 3))
                LPG[dev].append(round(elm['LPG'], 3))
                Cars[dev].append(round(elm['Cars'], 3))
            else:
                temperature[dev].append('null')
                humidity[dev].append('null')
                pressure[dev].append('null')
                CO[dev].append('null')
                LPG[dev].append('null')
                Cars[dev].append('null')

    # Smoothing - Moving average
    for idDevice in selected_devices:
        temperature[idDevice] = moving_average(temperature[idDevice], smooth_factor, dates_list)
        humidity[idDevice] = moving_average(humidity[idDevice], smooth_factor, dates_list)
        pressure[idDevice] = moving_average(pressure[idDevice], smooth_factor, dates_list)
        CO[idDevice] = moving_average(CO[idDevice], smooth_factor, dates_list)
        LPG[idDevice] = moving_average(LPG[idDevice], smooth_factor, dates_list)
        Cars[idDevice] = moving_average(Cars[idDevice], smooth_factor, dates_list)

    i = 0
    for device in devices:
        idDevice = device['idDevice']
        if idDevice in selected_devices:
            data.append({
                'idDevice': idDevice,
                'location': "Device %d: %s" % (idDevice, device['Location']),
                'color' : CHART_COLORS[i % len(CHART_COLORS)],
                'temperature' : temperature[idDevice],
                'humidity' : humidity[idDevice],
                'pressure' : pressure[idDevice],
                'CO' : CO[idDevice],
                'LPG' : LPG[idDevice],
                'cars' : Cars[idDevice]
            })
            i += 1

    return (labels, data)


def moving_average(data, order, dates_list):
    #order = 3
    smoot_data = []
    if order == 1:
        return data
    else:
        for i in range(0, len(data)):
            if data[i] == 'null':
                smoot_data.append('null')
            else:
                aux = data[i]
                if order%2 == 1:
                    for j in range(1,int(math.floor(float(order)/2))+1):
                        if (i-j < 0 or data[i-j] == 'null' or
                                abs(dates_list[i-j] - dates_list[i]).seconds > MAX_SMOOT_SECONDS):
                            aux += data[i]
                        else:
                            aux += data[i-j]
                        if (i+j >= len(data) or data[i+j] == 'null' or
                                abs(dates_list[i+j] - dates_list[i]).seconds > MAX_SMOOT_SECONDS):
                            aux += data[i]
                        else:
                            aux += data[i+j]
                else:
                    for j in range(1,order/2+1):
                        if (i-j < 0 or data[i-j] == 'null' or
                                abs(dates_list[i-j] - dates_list[i]).seconds > MAX_SMOOT_SECONDS):
                            aux += data[i]
                        else:
                            aux += data[i-j]
                    for j in range(1,order/2):
                        if (i+j >= len(data) or data[i+j] == 'null' or
                                abs(dates_list[i+j] - dates_list[i]).seconds > MAX_SMOOT_SECONDS):
                            aux += data[i]
                        else:
                            aux += data[i+j]
                smoot_data.append(aux/order)
        return smoot_data


def getNotifications():
    """
    Get all the email notifications.

    Output:   notifications -> List with all the notifications stored.
    """
    notifications = []

    try:
        # Open database connection
        db = pymysql.connect(DB_HOST, DB_USER, DB_PASS, DB_NAME, charset='utf8', use_unicode=True)
        # Prepare a cursor object
        cursor = db.cursor(pymysql.cursors.DictCursor)
        # Prepare SQL query to obtain the data
        sql = "SELECT * FROM notifications "
        # Execute the SQL querry
        cursor.execute(sql)
        # Obtain the data
        notifications = cursor.fetchall()
        db.close()
    except:
        db.close()
    return notifications


def createNotification(email, CO_level, LPG_level, cars):
    """
    Create a new notification.

    Input:   email -> Notification email
             CO_level -> CO notification level
             LPG_level -> LPG notification level
             cars -> vehicles per hour notification level
    """
    # Open database connection
    db = pymysql.connect(DB_HOST, DB_USER, DB_PASS, DB_NAME)

    # prepare a cursor object
    cursor = db.cursor()

    # Prepare SQL query to INSERT a record into the database
    sql = "INSERT INTO notifications(email, COLimit, LPGLimit, carsLimit) \
            VALUES ('%s', %s, %s, %s)" % \
            (email, CO_level, LPG_level, cars)

    try:
        # Execute the SQL command and commit the changes in the database
        cursor.execute(sql)
        db.commit()
    except:
        # Rollback in case there is any error
        db.rollback()

    db.close()


def removeNotification(email):
    """
    Remove an existing notification.

    Input:   email -> Notification email
    """
    # Open database connection
    db = pymysql.connect(DB_HOST, DB_USER, DB_PASS, DB_NAME)

    # prepare a cursor object
    cursor = db.cursor()

    # Prepare SQL query to DELETE the record into the database
    sql = "DELETE FROM notifications \
            WHERE email = '%s'" % (email)

    print sql

    try:
        # Execute the SQL command and commit the changes in the database
        cursor.execute(sql)
        db.commit()
    except:
        # Rollback in case there is any error
        db.rollback()

    db.close()



def updateNotification(email, CO_level, LPG_level, cars):
    """
    Update and existing notifications.

    Input:   email -> Notification email
             CO_level -> CO notification level
             LPG_level -> LPG notification level
             cars -> vehicles per hour notification level
    """
    # Open database connection
    db = pymysql.connect(DB_HOST, DB_USER, DB_PASS, DB_NAME)

    # prepare a cursor object
    cursor = db.cursor()

    # Prepare SQL query to UPDATE the record into the database
    sql = "UPDATE notifications \
            SET COLimit =  %s, LPGLimit =  %s, carsLimit =  %s \
            WHERE email = '%s'" % \
            (CO_level, LPG_level, cars, email)

    try:
        # Execute the SQL command and commit the changes in the database
        cursor.execute(sql)
        db.commit()
    except:
        # Rollback in case there is any error
        db.rollback()

    db.close()


def checkNotifications(data):
    """
    Check if the input data triggers any existing notifications.

    Input:   data -> Sensor data obtained from the devices
    """
    devices = getDevices()
    notifications = getNotifications()
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(NOTIFY_EMAIL, NOTIFY_PASS)

    for notification in notifications:
        count = 0
        for device in devices:
            if device['idDevice'] == data['idDevice']:
                location = device['Location']
                break

        msg = MIMEMultipart()
        destination_addr = notification['email']
        msg['From'] = NOTIFY_EMAIL
        msg['To'] = destination_addr
        msg['Subject'] = "Level alert! - Jose Angel BSc. Thesis"

        body = "This is an automated message generated by the Jose Angel BSc. Thesis \
            webpage to inform you that some levels stored for your account in the \
            Notification system of the app have been gotten over by the device with \
            id: %d, and located in %s <br><br> <ul>" % (data['idDevice'], location)

        if notification['COLimit'] != None and data['CO'] > notification['COLimit']:
            count += 1
            body += "<li>The CO gas limit has been gotten over!<br> \
                \t Current CO gas ppm: %.2f <br> \
                \t Notification CO gas ppm limit: %.2f </li> <br><br>" % (data['CO'], notification['COLimit'])
        if notification['LPGLimit'] != None and data['LPG_gas'] > notification['LPGLimit']:
            count += 1
            body += "<li>The LPG limit has been gotten over!<br> \
                \t Current LPG ppm: %.2f <br> \
                \t Notification LPG ppm limit: %.2f </li> <br><br>" % (data['LPG'], notification['LPGLimit'])
        if notification['carsLimit'] != None and data['car_count'] > notification['carsLimit']:
            count += 1
            body += "<li>The vehicles per hour limit has been gotten over! <br> \
                \t Current vehicles per hour: %.2f <br> \
                \t Notification vehicles per hour: %.2f </li> <br><br>" % (data['car_count'], notification['carsLimit'])

        body += "This is just an informative email, please do not respond to it."

        if count > 0:
            msg.attach(MIMEText(body, 'html', 'utf-8'))
            text = msg.as_string().encode('ascii')
            # Sent the email
            server.sendmail(NOTIFY_EMAIL, destination_addr, text)

    server.quit()



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
    numberLines = 1

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
                numberLines = device['numberLines']
                break

    #last_update = datetime.datetime.now().replace(tzinfo=pytz.utc).astimezone(local_tz)
    last_update = datetime.datetime.now().replace(tzinfo=server_tz).astimezone(local_tz)
    last_update = last_update.replace(tzinfo=None).strftime("%Y-%m-%d at %H:%M:%S")
    data = getLastData(idDevice)
    data['Cars_per_line'] = data['Cars'] / numberLines

    resp = make_response(render_template('real_time.html', devices=devices, data=data, limits=LIMITS, \
        last_update=last_update, location=location, update_interval=update_interval))
    expire_date = datetime.datetime.now()
    expire_date = expire_date + datetime.timedelta(days=1)
    resp.set_cookie('device', str(idDevice), expires=expire_date)

    return resp


@app.route('/historical.html', methods=['GET', 'POST'])
def historical():
    """
    Render /historical.html web page.
    """
    no_data = False
    selected_devices = []
    labels = []
    data = []
    devices = getDevices()
    #time_now = datetime.datetime.now().replace(tzinfo=pytz.utc).astimezone(local_tz)
    time_now = datetime.datetime.now().replace(tzinfo=server_tz).astimezone(local_tz)
    last_update = time_now.replace(tzinfo=None).strftime("%Y-%m-%d at %H:%M:%S")
    time_last_week = time_now - datetime.timedelta(days=7)
    dates = [time_last_week.strftime("%Y-%m-%dT%H:%M"), time_now.replace(tzinfo=None).strftime("%Y-%m-%dT%H:%M")]

    if request.method == 'POST':
        try:
            selected_devices_str = request.form.getlist('device')
            selected_devices = [ int(x) for x in selected_devices_str ]
            selected_dates = [request.form['init-date'].replace("T", " "),
                              request.form['finish-date'].replace("T", " ")]
            dates = [request.form['init-date'], request.form['finish-date']]
        except KeyError:
            selected_devices = []

    if len(selected_devices) == 0:
        no_data = True
    else:
        smooth_factor = 3
        (labels, data) = getHistoricalData(selected_devices, selected_dates, devices, smooth_factor)

    return render_template('historical.html', devices=devices, dates=dates,
        no_data=no_data, labels=labels, data=data, selected_devices=selected_devices,
        last_update=last_update)


@app.route('/configuration.html', methods=['GET', 'POST'])
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
    else: # Autentication is correct. Show configuration page
        selected_email = None
        selected_not = None
        if request.method == 'POST':
            try:
                if request.form['action'] == "Select":
                    # Get all the notifications
                    notifications = getNotifications()
                    selected_email = request.form['notification']
                    for i in range(0,len(notifications)):
                        if notifications[i]['email'] == selected_email:
                            selected_not = notifications[i]

                elif request.form['action'] == "Update":
                    # Update an existing notification
                    if request.form['COLimit'] == '':
                        CO_level = 'NULL'
                    else:
                        CO_level = request.form['COLimit']
                    if request.form['LPGLimit'] == '':
                        LPG_level = 'NULL'
                    else:
                        LPG_level = request.form['LPGLimit']
                    if request.form['carsLimit'] == '':
                        cars = 'NULL'
                    else:
                        cars = request.form['carsLimit']
                    updateNotification(request.form['email'], CO_level, LPG_level, cars)
                    notifications = getNotifications()

                elif request.form['action'] == "Remove":
                    # Remove an existing notification
                    removeNotification(request.form['email'])
                    notifications = getNotifications()

                elif request.form['action'] == "Create":
                    # Create a new notification
                    if request.form['COLimit'] == '':
                        CO_level = 'NULL'
                    else:
                        CO_level = request.form['COLimit']
                    if request.form['LPGLimit'] == '':
                        LPG_level = 'NULL'
                    else:
                        LPG_level = request.form['LPGLimit']
                    if request.form['carsLimit'] == '':
                        cars = 'NULL'
                    else:
                        cars = request.form['carsLimit']
                    createNotification(request.form['email'], CO_level, LPG_level, cars)
                    notifications = getNotifications()
            except KeyError:
                selected_email = None
        else:
            notifications = getNotifications()

        time_now = datetime.datetime.now().replace(tzinfo=server_tz).astimezone(local_tz)
        last_update = time_now.replace(tzinfo=None).strftime("%Y-%m-%d at %H:%M:%S")

        return render_template('configuration.html', email=email, \
            notifications=notifications, last_update=last_update, \
            selected_not=selected_not)


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
    print("Stored into the DB live data from %s (%s) sent at %s" % (event.deviceId, event.deviceType, date_time))

    # Check check notifications
    checkNotifications(data)


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
