# Import configugartion file
from ServerConfig import *

# Import Domain
from Domain.Users import Users

# Import other modules
from flask import Blueprint, render_template, redirect, url_for, request, make_response
import time
import os
import datetime

login = Blueprint('login', __name__, url_prefix='/', template_folder='templates')

@login.route('login.html', methods=['GET', 'POST'])
def Login():
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

                users = Users()
                (success, user_id, user_auth_token) = users.user_login(email, password)

                if success:
                    expire_date = datetime.datetime.now()
                    expire_date = expire_date + datetime.timedelta(hours=1)

                    resp = make_response(redirect(url_for('configuration.Configuration')))
                    resp.set_cookie('user_id', str(user_id), expires=expire_date)
                    resp.set_cookie('user_auth_token', user_auth_token, expires=expire_date)
                    return resp
                else:
                    bad_login = True

        except KeyError:
            pass

    return render_template('login.html', bad_login=bad_login)
