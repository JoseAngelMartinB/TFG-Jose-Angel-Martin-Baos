#!/usr/bin/python3
# -*- coding: utf-8; mode: python -*-

import time, os, picamera
import picamera.array
import numpy as np
import datetime as dt
from config import *
from ImageAnalizer import ImageAnalizer # Extends PiMotionAnalysis class

class Recorder():
	def main(self, distance, angle):
		with picamera.PiCamera() as camera:
			with ImageAnalizer(camera) as output:
				camera.resolution = (VIDEO_WIDTH, VIDEO_HEIGHT)
				camera.framerate = FRAMERATE
				camera.hflip = HFLIP
				camera.vflip = VFLIP
				time.sleep(2)

				print("Starting the recording during %i seconds..." % RECORDING_TIME)
				file_name = dt.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H:%M')
				file_name = str(VIDEO_WIDTH) + angle + distance + file_name
				motion_file_name = 'motion_data/' + file_name + '.data'
				camera.start_recording(OUTPUT_DIRECTORY +  file_name + '.h264', format='h264', motion_output=motion_file_name)
				camera.wait_recording(RECORDING_TIME)
				print("Stoping the recording...")
				camera.stop_recording()
				print("Converting video to .mp4...")
				os.system("MP4Box -fps %i -add %s/%s.h264 %s/%s.mp4" % (FRAMERATE, OUTPUT_DIRECTORY, file_name, OUTPUT_DIRECTORY, file_name))


