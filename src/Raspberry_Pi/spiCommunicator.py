#!/usr/bin/python3
# -*- coding: utf-8; mode: python -*-

# BSC Thesis
#
# Author
#  - José Ángel Martín Baos

import RPi.GPIO as GPIO

class spiCommunicator():
    """Comuicate using SPI protocol over GPIO pins."""

    def __init__(self, clock_pin, mosi_pin, miso_pin, cs_pin):
        self.clock_pin = clock_pin
        self.mosi_pin = mosi_pin
        self.miso_pin = miso_pin
        self.cs_pin = cs_pin

        # Set up the SPI interface pins
        GPIO.setup(self.clock_pin, GPIO.OUT)
        GPIO.setup(self.miso_pin, GPIO.IN)
        GPIO.setup(self.mosi_pin, GPIO.OUT)
        GPIO.setup(self.cs_pin, GPIO.OUT)


    def read(self, channel):
        """
        Read SPI data from MCP3008 chip.

        Input:   channel -> Analogue channel where the target MQ sensor is connected
        Output:  Digital value obtained from the MCP3008 chip
        """
        if((channel > 7) or (channel < 0)):
            return -1

        # SPI initialization
        GPIO.output(self.cs_pin, True)
        GPIO.output(self.clock_pin, False)
        GPIO.output(self.cs_pin, False)

        # command_out -> Start bit | single-ended bit | channel (3 bits)
        command_out = channel
        command_out |= 0x18  # start bit + single-ended bit
        command_out <<= 3    # Only 5 bits are needed to be sended
        for i in range(5):
            if(command_out & 0x80):
                GPIO.output(self.mosi_pin, True)
            else:
                GPIO.output(self.mosi_pin, False)
            command_out <<= 1
            GPIO.output(self.clock_pin, True)
            GPIO.output(self.clock_pin, False)

        # Read the data (one empty bit, one null bit and 10 data bits)
        adc_out = 0
        for i in range(12):
            GPIO.output(self.clock_pin, True)
            GPIO.output(self.clock_pin, False)
            adc_out <<= 1
            if(GPIO.input(self.miso_pin)):
                adc_out |= 0x1

        # Finishing SPI comunication
        GPIO.output(self.cs_pin, True)

        adc_out >>= 1   # Drop first bit (null one)
        return adc_out
