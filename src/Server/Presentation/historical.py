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

historical = Blueprint('historical', __name__, url_prefix='/', template_folder='templates')

local_tz = pytz.timezone('Europe/Madrid')
server_tz = tzlocal()

@historical.route('historical.html', methods=['GET', 'POST'])
def Historical():
    """
    Render /historical.html web page.
    """
    no_data = False
    selected_devices = []
    labels = []
    data = []
    sensorData = SensorData()
    devices = sensorData.getDevices()
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
        smooth_factor = SMOOTH_FACTOR
        (labels, data) = sensorData.getHistoricalData(selected_devices, selected_dates, devices, smooth_factor)

    return render_template('historical.html', devices=devices, dates=dates,
        no_data=no_data, labels=labels, data=data, selected_devices=selected_devices,
        last_update=last_update)
