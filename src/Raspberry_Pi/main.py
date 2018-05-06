#!/usr/bin/python3
# -*- coding: utf-8; mode: python -*-

# BSC Thesis
#
# Author
#  - José Ángel Martín Baos

from config import *
from CountVehicles import CountVehicles
from MotionAnalysis import MotionAnalysis
from Sensors import Sensors
import picamera
import RPi.GPIO as GPIO
import ibmiotf.device
import os
import threading
import signal
import time
from datetime import datetime


class ProgramExit(Exception):
    """Exception used to trigger the termination of the main program and all the
    running threads."""
    pass


class CameraModule(threading.Thread):
    """Obtain the car flow using the camera installed in the device."""
    def __init__(self, lock):
        threading.Thread.__init__(self)

        self.shutdown_flag = threading.Event()
        self.lock = lock

    def run(self):
        global list_vehicles

        with picamera.PiCamera() as camera:
            count_vehicles = CountVehicles()
            with MotionAnalysis(camera, count_vehicles) as motion_analysis:
                camera.resolution = (VIDEO_WIDTH, VIDEO_HEIGHT)
                camera.framerate = FRAMERATE
                camera.hflip = HFLIP
                camera.vflip = VFLIP
                time.sleep(2)

                print('* Camera module has started')

                camera.start_recording('/dev/null', format='h264',
                    motion_output=motion_analysis)

                while not self.shutdown_flag.is_set():
                    camera.wait_recording(RECORDING_TIME)
                    vehicles = count_vehicles.getVehicles()

                    self.lock.acquire()
                    list_vehicles.append(vehicles)
                    self.lock.release()

                camera.stop_recording()

        print('* Camera module has stopped')


class SensorsModule(threading.Thread):
    """Obtain data from the Sensors installed in the device."""
    def __init__(self, lock):
        threading.Thread.__init__(self)

        self.shutdown_flag = threading.Event()
        self.lock = lock

        #Set GPIO interface
        GPIO.setwarnings(False)
        GPIO.cleanup()              # Clean up previous configuration
        GPIO.setmode(GPIO.BCM)		# Specify the pin numbering system

        # Set PWM cycle to generate 1.4 volts for MQ-7 sensors
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(16, GPIO.OUT)
        self.pwm = GPIO.PWM(16, 100)
        self.pwm.start(14)   # Generate a duty cycle capable of providing 1.4 volts

        self.sensors = Sensors(MQ7_Ro, MQ2_Ro)

    def run(self):
        global sensor_data

        print('* Sensors module has started')
        sensor_data_aux = {}

        # First measurement
        self.lock.acquire()
        sensor_data = self.sensors.getSensorData().copy()
        self.lock.release()

        while not self.shutdown_flag.is_set():
            # Obtain data from sensors
            self.pwm.start(14)   # Generate a duty cycle capable of providing 1.4 volts to MQ-7
            time.sleep(60)  # Wait 60 seconds to obtain results
            sensor_data_aux = self.sensors.getSensorData().copy()

            # Apply smoothed average and copy the data into the global variable
            self.lock.acquire()
            for k, v in sensor_data_aux.items():
                sensor_data[k] = ALPHA*v + (1-ALPHA)*sensor_data[k]
            self.lock.release()

            self.pwm.start(100)   # Generate a duty cycle capable of providing 1.4 volts to MQ-7
            time.sleep(90)

        print('* Sensors module has stopped')


class CommunicatorModule():
    """Obtain data from the CameraModule and the SensorsModule and send it to
    the Cloud."""
    def __init__(self, lock, id_device, time_interval):
        self.lock = lock
        self.id_device = id_device
        self.time_interval = time_interval

    def run(self):
        global list_vehicles, sensor_data

        time.sleep(5) # Wait for teh rest of modules to start
        print('* Communicator module has started')

        # Initialize the device client.
        try:
            deviceFile = "device.conf"
            deviceOptions = ibmiotf.device.ParseConfigFile(deviceFile)
            deviceClient = ibmiotf.device.Client(deviceOptions)
            deviceClient.connect()
        except Exception as e:
        	print(str(e))
        	raise ProgramExit

        while True:
            time.sleep(self.time_interval)
            date_time = datetime.now()
            date_time = date_time.strftime('%Y-%m-%d %H:%M:%S')

            self.lock.acquire()
            vehicles_per_hour = int((sum(list_vehicles)/len(list_vehicles))*60)
            list_vehicles = []
            data = { 'idDevice' : self.id_device,
                     'time_interval' : self.time_interval,
                     'vehicles_per_hour' : vehicles_per_hour,
                     'temperature' : sensor_data["Temperature"],
                     'humidity' : sensor_data["Humidity"],
                     'pressure' : sensor_data["Pressure"],
                     'CO' : sensor_data["CO"],
                     'LPG_gas' : sensor_data["LPG"],
                     'date_time' : date_time}
            self.lock.release()

            success = deviceClient.publishEvent("sensor_update", "json", data, qos=0)
            if not success:
        	    print("- Error: Not connected to IBM IoT Platform.")
            else:
                print("* Event sent to cloud")

        # Disconnect the device from the cloud
        deviceClient.disconnect()
        print('* Communicator module has stopped')


# Main program
def serviceShutdown(signum, frame):
    """
    Raise ProgramExit exception in order to exit the program.
    """
    print('\nCaught signal %d - Attempting peaceful exit: Stopping all the modules.' % signum)
    raise ProgramExit

def removeLogFiles():
    """
    Remove log files generated by IBM IoT platform.
    """
    directory = "./"
    list_files = os.listdir( directory )

    for item in list_files:
        if item.endswith(".log"):
            os.remove(os.path.join(directory, item ))


# MAIN PROGRAM
if __name__ == "__main__":
    removeLogFiles()

    # Initlialize variables
    id_device = DEVICEID
    list_vehicles = []
    sensor_data = {
		"Temperature" : 0,
		"Humidity" : 0,
		"Pressure" : 0,
		"CO" : 0,
		"LPG" : 0
	}
    time_interval = TIME_INTERVAL

    # Register the signal handlers
    signal.signal(signal.SIGTERM, serviceShutdown)
    signal.signal(signal.SIGINT, serviceShutdown)

    print('* Starting main program...')

    try:
        lock = threading.Lock()

        # Create modules
        comm = CommunicatorModule(lock, id_device, time_interval)
        cam_module = CameraModule(lock)
        sen_module = SensorsModule(lock)
        cam_module.start()
        sen_module.start()
        comm.run()

    except ProgramExit:
        # Terminate the running threads
        # Set shutdown flag on each thread
        cam_module.shutdown_flag.set()
        sen_module.shutdown_flag.set()

        # Release the lock
        if lock.locked():
            lock.release()

        # Wait for the threads termination...
        cam_module.join()
        sen_module.join()

        print('* The main program has finished')
