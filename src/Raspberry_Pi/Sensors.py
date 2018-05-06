#!/usr/bin/python3
# -*- coding: utf-8; mode: python -*-

# BSC Thesis
#
# Author
#  - José Ángel Martín Baos

import time
import math
import os
from config import *
from spiCommunicator import spiCommunicator
from sense_hat import SenseHat


class Sensors():
    """Obtain data from the Atmospheric sensors."""

    def __init__(self, MQ7_Ro, MQ2_Ro):

        # Gas sensor ajustments
        self.MQ7_Ro = MQ7_Ro   # Sensor resistance at 100 ppm of CO
        self.MQ2_Ro = MQ2_Ro   # Sensor resistance at 1000 ppm of H2

        # Initializing
        self.spi_comm = spiCommunicator(SPICLK, SPIMOSI, SPIMISO, SPICS)
        self.sense = SenseHat()

        print("* Initializing sensors. Please wait 20 seconds...")
        self.sense.set_rotation(ROTATION)
        self.sense.show_message("INITIALIZING...", text_colour=TEXT_COLOUR,
            scroll_speed=TEXT_SPEED)
        self.sense.show_letter("-", [255, 0, 0])
        time.sleep(20)
        # Execute a first measurement in order to avoid error data from sensors
        self.getSensorData()


    def calibration(self, mq_channel):
        """
        Assuming that the sensor is in clean air, this function calculates the
        sensor resistance in clean air, and divide it by RO_CLEAN_AIR_FACTOR.

        Input:   mq_channel -> Analog channel where the MQ sensor is connected
        Output:  Ro of the sensor
        """
        ro = 0.0
        for i in range(CALIBRATION_SAMPLE_TIMES):
            ro += self.getResistance(self.spi_comm.read(mq_channel), mq_channel)
            time.sleep(CALIBRATION_SAMPLE_INTERVAL/1000.0)

        ro = ro/CALIBRATION_SAMPLE_TIMES

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
        data["LPG"] = self.getGasPPM(float(mq2_Rs)/self.MQ2_Ro, MQ7_CHANNEL)

        # Calculate the real temperature compensating the CPU heating
        temp1 = self.sense.get_temperature_from_humidity()
        temp2 = self.sense.get_temperature_from_pressure()
        temp_cpu = self.getCPUTemperature()
        temp = (temp1+temp2)/2
        real_temp = temp - ((temp_cpu-temp)/CPU_TEMP_FACTOR)

        # Environment sensors
        data["Temperature"] = real_temp
        data["Humidity"] = self.sense.get_humidity()
        data["Pressure"] = self.sense.get_pressure()

        # Set screen colors:
        self.setScreen(data["CO"], data["LPG"])

        return data


    def setScreen(self, CO, LPG):
        """
        Set SenseHat screen depending on the CO and LPG levels.

        Input:   CO -> CO gas level.
                 LPG -> LPG level.
        """
        O = [0, 0, 0]
        X = COLOURS_LEVELS[4]
        Y = COLOURS_LEVELS[4]
        for i in reversed(range(0,4)):
            if CO < LIMITS['CO'][i]: X = COLOURS_LEVELS[i]
            if LPG < LIMITS['LPG'][i]: Y = COLOURS_LEVELS[i]

        screen = [
            O, O, X, X, X, O, O, O,
            O, O, X, X, X, O, O, O,
            O, O, X, X, X, O, O, O,
            O, O, O, O, O, O, O, O,
            O, O, O, O, O, O, O, O,
            O, O, Y, Y, Y, O, O, O,
            O, O, Y, Y, Y, O, O, O,
            O, O, Y, Y, Y, O, O, O
        ]
        self.sense.set_pixels(screen)


    def getCPUTemperature(self):
        """
        Calculate CPU temperature.

        Output:  Current CPU temperature
        """
        command_res = os.popen("vcgencmd measure_temp").readline()
        t = float(command_res.replace("temp=","").replace("'C\n",""))
        return(t)


    def read(self, mq_channel):
        """
        Calculate the current sensor resistance which depens on the different
        concentration of the target gas.

        Input:   mq_channel -> Analog channel where the MQ sensor is connected
        Output:  Rs of the sensor
        """
        Rs = 0.0
        for i in range(READ_SAMPLE_TIMES):
            adc_value = self.spi_comm.read(mq_channel)
            Rs += self.getResistance(adc_value, mq_channel)
            time.sleep(READ_SAMPLE_INTERVAL/1000.0)

        Rs = Rs/READ_SAMPLE_TIMES

        return Rs


    def getResistance(self, adc_value, mq_channel):
        """
        Calculate the current resistance of the sensor given its current voltage.

        Input:   adc_value -> Raw value form the ADC. Voltage = adc*Vref/1024
                 mq_channel -> Analog channel where the MQ sensor is connected
        Output:  Current resistance of the sensor
        """
        resistance = 0.0
        if adc_value == 0: # Avoid division by 0
            adc_value = 1
        if(mq_channel == MQ7_CHANNEL):
            resistance = float(MQ7_RL*(1024.0-adc_value)/float(adc_value))
        elif(mq_channel == MQ2_CHANNEL):
            resistance = float(MQ2_RL*(1024.0-adc_value)/float(adc_value))

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
            percentage =  self.getMQPPM(rs_ro_ratio, LPG_Curve)

        return percentage


    def getMQPPM(self, rs_ro_ratio, mq_curve):
        """
        Calculate the ppm of the target gas using the slope and a point
        form the line obtained aproximating the sensitivity characteristic curve.
        x = (y-n)/m

        Input:   rs_ro_ratio -> Value obtained of the division Rs/Ro
                 mq_curve -> Line obtained using two points form the sensitivity
                    characteristic curve
        Output:  Current gas percentage in the environment
        """
        return (math.pow(10, (math.log10(rs_ro_ratio)-mq_curve[1]) / mq_curve[0]))
