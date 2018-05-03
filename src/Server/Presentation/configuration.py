# Import configugartion file
from ServerConfig import *

# Import Domain
from Domain.SensorData import SensorData
from Domain.Users import Users
from Domain.Notifications import Notifications

# Import other modules
from flask import Blueprint, render_template, redirect, url_for, request, make_response
import time
import os
import pytz
from dateutil.tz import tzlocal
import datetime

configuration = Blueprint('configuration', __name__, url_prefix='/', template_folder='templates')

local_tz = pytz.timezone('Europe/Madrid')
server_tz = tzlocal()

@configuration.route('configuration.html', methods=['GET', 'POST'])
def Configuration():
    """
    Render /configuration.html web page.
    """
    # Check if the user has log into the system
    auth = False
    try:
        user_id = int(request.cookies.get('user_id'))
        user_auth_token = request.cookies.get('user_auth_token')
        if user_id:
            users = Users()
            (auth, email) = users.checkUserSession(user_id, user_auth_token)
    except:
        pass

    if auth == False:
        return redirect(url_for('login.Login'))
    else: # Autentication is correct. Show configuration page
        selected_email = None
        selected_not = None
        notif = Notifications()
        if request.method == 'POST':
            try:
                if request.form['action'] == "Select":
                    # Get all the notifications
                    notifications = notif.getNotifications()
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
                    if request.form['vehiclesLimit'] == '':
                        vehicles = 'NULL'
                    else:
                        vehicles = request.form['vehiclesLimit']
                    notif.updateNotification(request.form['email'], CO_level, LPG_level, vehicles)
                    notifications = notif.getNotifications()

                elif request.form['action'] == "Remove":
                    # Remove an existing notification
                    notif.removeNotification(request.form['email'])
                    notifications = notif.getNotifications()

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
                    if request.form['vehiclesLimit'] == '':
                        vehicles = 'NULL'
                    else:
                        vehicles = request.form['vehiclesLimit']
                    notif.createNotification(request.form['email'], CO_level, LPG_level, vehicles)
                    notifications = notif.getNotifications()
            except KeyError:
                selected_email = None
        else:
            notifications = notif.getNotifications()

        time_now = datetime.datetime.now().replace(tzinfo=server_tz).astimezone(local_tz)
        last_update = time_now.replace(tzinfo=None).strftime("%Y-%m-%d at %H:%M:%S")

        return render_template('configuration.html', email=email, \
            notifications=notifications, last_update=last_update, \
            selected_not=selected_not)
