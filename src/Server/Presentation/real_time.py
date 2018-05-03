# Import configugartion file
from ServerConfig import *

# Import Domain
from Domain.SensorData import SensorData

# Import other modules
from flask import Blueprint, render_template, redirect, url_for, request, make_response
import time
import pytz
from dateutil.tz import tzlocal
import datetime

real_time = Blueprint('real_time', __name__, url_prefix='/', template_folder='templates')

local_tz = pytz.timezone('Europe/Madrid')
server_tz = tzlocal()

@real_time.route('real_time.html', methods=['GET', 'POST'])
def RealTime():
    """
    Render /real_time.html web page.
    """
    sensorData = SensorData()
    devices = sensorData.getDevices()
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
    data = sensorData.getLastData(idDevice)
    data['Vehicles_per_line'] = data['VehiclesPerHour'] / numberLines

    resp = make_response(render_template('real_time.html', devices=devices, data=data, limits=LIMITS, \
        last_update=last_update, location=location, update_interval=update_interval))
    expire_date = datetime.datetime.now()
    expire_date = expire_date + datetime.timedelta(days=1)
    resp.set_cookie('device', str(idDevice), expires=expire_date)

    return resp
