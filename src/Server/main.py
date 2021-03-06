#!/usr/bin/python3
# -*- coding: utf-8; mode: python -*-

# BSC Thesis
#
# Author
#  - José Ángel Martín Baos

# Import configugartion file
from ServerConfig import *

# Import Persistence layer
from Persistence.DBBroker import DBBroker

# Import Domain
from Domain.SensorData import SensorData
from Domain.Users import Users
from Domain.Notifications import Notifications

# Import Presentation layer
from Presentation.index import index
from Presentation.real_time import real_time
from Presentation.historical import historical
from Presentation.configuration import configuration
from Presentation.login import login
from Presentation.about import about

# Import other modules
from flask import Flask, render_template, redirect, url_for, request, make_response
import os
import sys
import ibmiotf.application

# Auxiliar functions:
def sensorUpdate(event):
    """
    This method is executed everytime an event arrives with new data from the
    Raspberry Pi devices. The data is processed and stored into the database.

    Input:   event -> Event recived from IBM IoT.
    """
    data = event.data
    date_time = event.timestamp

    db = DBBroker()
    sql = "INSERT INTO data(idDevice, DateAndTime, Temperature, Humidity, Pressure, CO, LPG, VehiclesPerHour) \
            VALUES ('%s', '%s', '%f', '%f', '%f', '%f', '%f', '%f')" % \
            (data['idDevice'], data['date_time'], data['temperature'], data['humidity'], data['pressure'], data['CO'], data['LPG_gas'], data['vehicles_per_hour'])
    db.update(sql)

    print("Stored into the DB live data from %s (%s) sent at %s" % (event.deviceId, event.deviceType, date_time))

    # Check check notifications
    devices = SensorData().getDevices()
    Notifications().checkNotifications(devices, data)


def removeLogFiles():
    """
    Remove log files generated by IBM IoT platform.
    """
    directory = "./"
    list_files = os.listdir( directory )

    for item in list_files:
        if item.endswith(".log"):
            os.remove(os.path.join(directory, item ))


# Main Function
if __name__ == "__main__":
    removeLogFiles()

    # Initialize the application client for IBM IoT
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

    # Create a python Flask app
    app = Flask(__name__)
    port = os.getenv('PORT', PORT)

    # Register blueprints for the app
    app.register_blueprint(index)
    app.register_blueprint(real_time)
    app.register_blueprint(historical)
    app.register_blueprint(configuration)
    app.register_blueprint(login)
    app.register_blueprint(about)
    print(app.url_map)

    # Execute Python Flask App
    app.run(host='0.0.0.0', port=int(port), debug=False)

    # Disconnect from server
    client.disconnect()
