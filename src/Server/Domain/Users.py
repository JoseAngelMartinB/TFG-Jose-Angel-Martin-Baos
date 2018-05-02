#!/usr/bin/python3
# -*- coding: utf-8; mode: python -*-

# BSC Thesis
#
# Author
#  - José Ángel Martín Baos

from ServerConfig import *
from Persistence.DBBroker import DBBroker
from Domain.AESCipher import AESCipher
import uuid

class Users:
    """ Manage the users sesions and login. """

    def user_login(self, email, password):
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

        db = DBBroker()
        sql = "SELECT user_id, password \
                FROM users \
                WHERE email = '%s'" % (email)
        user_data = db.select(sql)[0]
        raw_pass = str(user_data['user_id']) + email
        encrip_pass = AESCipher(password).encrypt(raw_pass)

        if encrip_pass == user_data['password']:
            success = True
            user_id = user_data['user_id']
            user_auth_token = str(uuid.uuid4())

            db = DBBroker()
            sql = "UPDATE users \
                    SET last_token = '%s' \
                    WHERE user_id = %d" % (user_auth_token, user_id)
            db.update(sql)

        return (success, user_id, user_auth_token)


    def checkUserSession(self, user_id, user_auth_token):
        """
        Verify the user session.

        Intput:   user_id -> The user identification
                  user_auth_token -> An identifier to check the user autenticity during
                    the sesion
        Output:   success -> True if the user session exists
        """
        success = False
        db = DBBroker()
        sql = "SELECT last_token, email \
                FROM users \
                WHERE user_id = %d" % (user_id)
        user_data = db.select(sql)[0]

        if user_auth_token == user_data['last_token']:
            success = True
            email = user_data['email']

        return (success, email)
