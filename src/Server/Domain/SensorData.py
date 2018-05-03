#!/usr/bin/python3
# -*- coding: utf-8; mode: python -*-

# BSC Thesis
#
# Author
#  - José Ángel Martín Baos

from ServerConfig import *
from Persistence.DBBroker import DBBroker
import datetime
from dateutil.tz import tzlocal
import os
import time
import math
import pytz

class SensorData:
    """ Manage the data obtained by the sensors and displayed into the page. """

    def __init__(self):
        self.local_tz = pytz.timezone('Europe/Madrid')
        self.server_tz = tzlocal()

    def getDefaultData(self):
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
            'VehiclesPerHour' : 0
        }
        return data

    def getLastData(self, idDevice):
        """
        Obtain last data stored into de DB.

        Intput:   idDevice -> Raspberry Pi device from which obtain the data
        Output:   data -> Dictionary with the obtained data.
        """
        db = DBBroker()
        sql = "SELECT DateAndTime, Temperature, Humidity, Pressure, CO, LPG, VehiclesPerHour \
                FROM data t\
                inner join ( \
                    SELECT idDevice, max(DateAndTime) as LastDate \
                    FROM data \
                    GROUP BY idDevice \
                ) tmd on t.idDevice = tmd.idDevice and t.DateAndTime = tmd.LastDate \
                    WHERE t.idDevice = '%d'" % (idDevice)
        data = db.select(sql)[0]
        data['idDevice'] = idDevice
        if data == None:
            data = self.getDefaultData()

        return data


    def getData(self, devices, dates):
        """
        Obtain sensor data stored into de DB.

        Intput:   devices -> List of Raspberry Pi devices from which obtain the data
                  dates -> Initial and finish dates
        Output:   data -> List of dictionaries with the obtained data.
        """
        db = DBBroker()
        # Prepare SQL query to obtain the data
        sql = "SELECT idDevice, DateAndTime, Temperature, Humidity, Pressure, CO, LPG, VehiclesPerHour \
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
        data = db.select(sql)
        if data == None:
            data = []

        return data


    def getDevices(self):
        """
        Obtain the Raspberry Pi devices.

        Output:   devices -> List of dictionary with the obtained devices.
        """
        db = DBBroker()
        sql = "SELECT * \
        FROM devices t1 \
        LEFT OUTER JOIN( \
        	SELECT idDevice, max(DateAndTime) AS LastDate \
        	FROM data \
            GROUP BY idDevice \
        ) t2 ON t1.idDevice = t2.idDevice;"
        devices = db.select(sql)

        # Convert time to UTC - Europe/Madrid
        time_now = datetime.datetime.now().replace(tzinfo=self.server_tz).astimezone(self.local_tz)
        time_now = time_now.replace(tzinfo=None)

        for device in devices:
            if device['LastDate'] == None:
                device['status'] = False
            elif time_now - device['LastDate'] < datetime.timedelta(minutes=device['timeInterval']*3):
                device['status'] = True
            else:
                device['status'] = False

        return devices


    def getHistoricalData(self, selected_devices, dates, devices, smooth_factor):
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
        data_aux = self.getData(selected_devices, dates)
        temperature = dict()
        humidity = dict()
        pressure = dict()
        CO = dict()
        LPG = dict()
        VehiclesPerHour = dict()
        dates_list = []

        for dev in selected_devices:
            temperature[dev] = []
            humidity[dev] = []
            pressure[dev] = []
            CO[dev] = []
            LPG[dev] = []
            VehiclesPerHour[dev] = []

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
                    VehiclesPerHour[dev].append(round(elm['VehiclesPerHour'], 3))
                else:
                    temperature[dev].append('null')
                    humidity[dev].append('null')
                    pressure[dev].append('null')
                    CO[dev].append('null')
                    LPG[dev].append('null')
                    VehiclesPerHour[dev].append('null')

        # Smoothing - Moving average
        for idDevice in selected_devices:
            temperature[idDevice] = self.moving_average(temperature[idDevice], smooth_factor, dates_list)
            humidity[idDevice] = self.moving_average(humidity[idDevice], smooth_factor, dates_list)
            pressure[idDevice] = self.moving_average(pressure[idDevice], smooth_factor, dates_list)
            CO[idDevice] = self.moving_average(CO[idDevice], smooth_factor, dates_list)
            LPG[idDevice] = self.moving_average(LPG[idDevice], smooth_factor, dates_list)
            VehiclesPerHour[idDevice] = self.moving_average(VehiclesPerHour[idDevice], smooth_factor, dates_list)

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
                    'VehiclesPerHour' : VehiclesPerHour[idDevice]
                })
                i += 1

        return (labels, data)


    def moving_average(self, data, order, dates_list):
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
