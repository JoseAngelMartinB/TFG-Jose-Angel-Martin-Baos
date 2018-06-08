#!/usr/bin/python3
# -*- coding: utf-8; mode: python -*-

# BSC Thesis
#
# Author
#  - José Ángel Martín Baos

from ServerConfig import *
import pymysql

class Singleton(type):
    """ Metaclass with allows to implement the singleton design pattern. """

    def __init__(cls, name, bases, dct):
        cls.__instance = None
        type.__init__(cls, name, bases, dct)

    def __call__(cls):
        if cls.__instance is None:
            cls.__instance = type.__call__(cls)
        return cls.__instance


class DBBroker:
    """ Class to access the database and execute queries. """

    __metaclass__ = Singleton

    def __init__(self):
        self.__connection = None
        self.db_host = DB_HOST
        self.db_user = DB_USER
        self.db_pass = DB_PASS
        self.db_name = DB_NAME


    def __connect(self):
        """
        Open the database connection
        """
        success = False

        try:
            self.__connection = pymysql.connect(self.db_host, self.db_user,
                                                self.db_pass, self.db_name,
                                                charset='utf8', use_unicode=True)
            success = True
        except:
            print("Error conecting to the database.")

        return success


    def __close_connection(self):
        """
        Close the database connection
        """
        self.__connection.close()


    def select(self, query):
        """
        Executes a select query against the database.
        """
        data = None
        success = self.__connect()

        if success:
            try:
                # Prepare a cursor object
                cursor = self.__connection.cursor(pymysql.cursors.DictCursor)
                cursor.execute(query)
                data = cursor.fetchall()
            except pymysql.InternalError as error:
                _ , message = error.args
                print("Error in select query from data base. %s", message)

            self.__close_connection()

        return data


    def update(self, query):
        """
        Executes an update/add or remove query against the database.
        """
        success = self.__connect()

        if success:
            try:
                # Prepare a cursor object
                cursor = self.__connection.cursor(pymysql.cursors.DictCursor)
                cursor.execute(query)
                self.__connection.commit()
            except pymysql.InternalError as error:
                _ , message = error.args
                self.__connection.rollback()
                print("Error in update query from database. %s", message)

            self.__close_connection()
