#!/usr/bin/python3
# -*- coding: utf-8; mode: python -*-

# BSC Thesis
#
# Author
#  - José Ángel Martín Baos

# CONFIGURATION FILE

## Camera module configuration:
# TODO


## Sensors module configuration:
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
CALIBRATION_SAMPLE_TIMES     = 50   # Number of samples taken in the calibration phase
CALIBRATION_SAMPLE_INTERVAL  = 500  # Time interal(in milisecond) between each samples in the cablibration phase
MQ7_Ro                       = 10.722
MQ2_Ro                       = 9.313

# MQ read settings
READ_SAMPLE_TIMES            = 5     # Number of samples taken in reading phase
READ_SAMPLE_INTERVAL         = 500   # Time interval(in milisecond) between each sample in reading phase
ALPHA                        = 0.57  # Factor that indicates how much niew values affect the final value of the measurements

# MQ Sensor Load Resistances
MQ7_RL = 10     # MQ-7 Sensor Load Resistance in kilo ohms
MQ2_RL = 5      # MQ-2 Sensor Load Resistance in kilo ohms

# Gas Curves. Data format: {slope (m), y-intercept (n)}
CO_Curve = [-0.68, 1.416]
LPG_Curve = [-0.47, 1.291]

# Temperature calibration
CPU_TEMP_FACTOR = 2.5


## IBM IoT platform configuration:
DEVICEID = 1            # ID of the device
TIME_INTERVAL = 300     # Seconds between updates
