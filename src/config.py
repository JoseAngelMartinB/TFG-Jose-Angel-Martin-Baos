#!/usr/bin/python3
# -*- coding: utf-8; mode: python -*-

# BSC Thesis
#
# Author
#  - José Ángel Martín Baos

# GPIO pins used
SPICLK  = 21    # SPI CLK signal
SPIMISO = 19    # SPI MISO signal
SPIMOSI = 20    # SPI MOSI signal
SPICS   = 18    # SPI CS signal

# MQ channels
MQ7_CHANNEL = 0  # Analog channel of MQ-7 Sensor
MQ2_CHANNEL = 1  # Analog channel of MQ-2 Sensor

# MQ calibration settings
MQ7_RO_CLEAN_AIR_FACTOR      = 28   # (Sensor resistance in clean air)/RO
MQ2_RO_CLEAN_AIR_FACTOR      = 9.83 # (Sensor resistance in clean air)/RO
CALIBARAION_SAMPLE_TIMES     = 50   # Number of samples taken in the calibration phase
CALIBRATION_SAMPLE_INTERVAL  = 500  # Time interal(in milisecond) between each samples in the cablibration phase
MQ7_Ro                       = 10.722
MQ2_Ro                       = 9.313

# MQ read settings
READ_SAMPLE_TIMES            = 5    # Number of samples taken in reading phase
READ_SAMPLE_INTERVAL         = 500   # Time interval(in milisecond) between each sample in reading phase

# MQ Sensor Load Resistances
MQ7_RL = 10     # MQ-7 Sensor Load Resistance in kilo ohms
MQ2_RL = 5      # MQ-2 Sensor Load Resistance in kilo ohms

# Gas Curves. Data format: {x, y, slope}
# TODO: Source https://tutorials-raspberrypi.com/configure-and-read-out-the-raspberry-pi-gas-sensor-mq-x/
CO_Curve = [1.7,0.26,-0.68]
LPG_Curve = [2.3,0.21,-0.47]
