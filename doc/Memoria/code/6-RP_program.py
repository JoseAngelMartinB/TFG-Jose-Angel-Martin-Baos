#!/usr/bin/python3

from config import *
from CountVehicles import CountVehicles
from MotionAnalysis import MotionAnalysis
from Sensors import Sensors
import threading
import signal
""" ... """

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
        """ Camera Module code ... """
        print('* Camera module has stopped')


class SensorsModule(threading.Thread):
    """Obtain data from the Sensors installed in the device."""
    def __init__(self, lock):
        threading.Thread.__init__(self)
        self.shutdown_flag = threading.Event()
        self.lock = lock
        """ Sensors initialization code ... """

    def run(self):
        global sensor_data
        """ Sensors Module code ... """


class CommunicationModule():
    """Obtain data from the CameraModule and the SensorsModule and send it to
    the Cloud."""
    def __init__(self, lock, id_device, time_interval):
        self.lock = lock
        self.id_device = id_device
        self.time_interval = time_interval

    def run(self):
        global list_vehicles, sensor_data
        """ Communication Module code ... """


# Main program
def serviceShutdown(signum, frame):
    """ Raise ProgramExit exception in order to exit from the program."""
    print('\nCaught signal %d - Attempting peaceful exit: Stopping all the modules.' % signum)
    raise ProgramExit


# MAIN PROGRAM
if __name__ == "__main__":
    # Initialize variables
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
        comm = CommunicationModule(lock, id_device, time_interval)
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

        # Wait for the threads termination...
        cam_module.join()
        sen_module.join()
        print('* The main program has finished')
