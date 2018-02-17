#!/usr/bin/python3
# -*- coding: utf-8; mode: python -*-

# BSC Thesis
#
# Author
#  - José Ángel Martín Baos

import time
import math
from config import *
from spiCommunicator import spiCommunicator
from sense_hat import SenseHat


class Sensors():
    """Obtain data from the Atmospheric sensors"""

    def __init__(self, MQ7_Ro, MQ2_Ro):

        # Gas sensor ajustments
        self.MQ7_Ro = MQ7_Ro   # Sensor resistance at 100 ppm of CO
        self.MQ2_Ro = MQ2_Ro # Sensor resistance at 1000 ppm of H2

        # Initializing
        self.spi_comm = spiCommunicator(SPICLK, SPIMOSI, SPIMISO, SPICS)
        self.sense = SenseHat()

        print("Initializing sensors. Please wait 20 seconds...")
        self.sense.set_rotation(0)
        self.sense.show_message("INITIALIZING...", text_colour=[255, 255, 255], scroll_speed=0.2)
        time.sleep(20)


    def calibration(self, mq_channel):
        """
        Assuming that the sensor is in clean air, this function calculates the
        sensor resistance in clean air, and divide it by RO_CLEAN_AIR_FACTOR.

        Input:   mq_channel -> Analog channel where the MQ sensor is connected
        Output:  Ro of the sensor
        """
        ro = 0.0
        for i in range(CALIBARAION_SAMPLE_TIMES):
            ro += self.getResistance(self.spi_comm.read(mq_channel), mq_channel)
            time.sleep(CALIBRATION_SAMPLE_INTERVAL/1000.0)

        ro = ro/CALIBARAION_SAMPLE_TIMES

        if(mq_channel == MQ7_CHANNEL):
            ro = ro/MQ7_RO_CLEAN_AIR_FACTOR
        elif(mq_channel == MQ2_CHANNEL):
            ro = ro/MQ2_RO_CLEAN_AIR_FACTOR

        return ro


    def getSensorData(self):
        """
        Obtain the data from the different sensors and return it.

        Output:  Current sensor data
        """
        data = {}
        mq7_Rs = self.read(MQ7_CHANNEL)
        mq2_Rs = self.read(MQ2_CHANNEL)

        # Avoid Rs to be 0
        if mq7_Rs == 0:
            mq7_Rs = 0.001
        if mq2_Rs == 0:
            mq2_Rs = 0.001

        # Gas sensors
        data["CO"] = self.getGasPPM(float(mq7_Rs)/self.MQ7_Ro, MQ7_CHANNEL)
        data["LGP"] = self.getGasPPM(float(mq2_Rs)/self.MQ2_Ro, MQ7_CHANNEL)

        # Environment sensors
        data["Temperature"] = self.sense.get_temperature()
        data["Humidity"] = self.sense.get_humidity()
        data["Pressure"] = self.sense.get_pressure()

        return data


    def read(self, mq_channel):
        """
        Calculate the current sensor resistance which depens on the different
        concentration of the target gas.

        Input:   mq_channel -> Analog channel where the MQ sensor is connected
        Output:  Rs of the sensor
        """
        Rs = 0.0
        for i in range(READ_SAMPLE_TIMES):
            Rs += self.getResistance(self.spi_comm.read(mq_channel), mq_channel)
            time.sleep(READ_SAMPLE_INTERVAL/1000.0)

        Rs = Rs/READ_SAMPLE_TIMES

        return Rs


    def getResistance(self, voltage, mq_channel):
        """
        Calculate the current resistance of the sensor given its current voltage.

        Input:   voltage -> Raw value form the ADC, which represents the voltage
                 mq_channel -> Analog channel where the MQ sensor is connected
        Output:  Current resistance of the sensor
        """
        resistance = 0.0
        if(mq_channel == MQ7_CHANNEL):
            resistance = float(MQ7_RL*(1023.0-voltage)/float(voltage))
        elif(mq_channel == MQ2_CHANNEL):
            resistance = float(MQ2_RL*(1023.0-voltage)/float(voltage))

        return resistance


    def getGasPPM(self, rs_ro_ratio, mq_channel):
        """
        Calculate the ppm of the target gases.

        Input:   rs_ro_ratio -> Value obtained of the division Rs/Ro
                 mq_channel -> Analog channel where the MQ sensor is connected
        Output:  Current gas percentage in the environment
        """
        percentage = 0
        if(mq_channel == MQ7_CHANNEL):
            percentage =  self.getMQPPM(rs_ro_ratio, CO_Curve)
        elif(mq_channel == MQ2_CHANNEL):
            percentage =  self.getMQPPM(rs_ro_ratio, LGP_Curve)

        return percentage


    def getMQPPM(self, rs_ro_ratio, mq_curve):
        """
        Calculate the ppm of the target gas using the slope and a point
        form the line obtained aproximating the sensitivity characteristic curve.

        Input:   rs_ro_ratio -> Value obtained of the division Rs/Ro
                 mq_curve -> Line obtained using two points form the sensitivity
                    characteristic curve
        Output:  Current gas percentage in the environment
        """
        return (math.pow(10,(((math.log(rs_ro_ratio)-mq_curve[1])/ mq_curve[2]) + mq_curve[0])))
