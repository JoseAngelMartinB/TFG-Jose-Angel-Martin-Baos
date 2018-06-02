#!/usr/bin/python3
# -*- coding: utf-8; mode: python -*-

import picamera
import picamera.array
import numpy as np
import time, os
import datetime as dt
from config import *
from ImageAnalizer import ImageAnalizer

class Recorder():
	def main(self, distance, angle):
		with picamera.PiCamera() as camera:
			with ImageAnalizer(camera) as output:
				camera.resolution = (VIDEO\_WIDTH, VIDEO\_HEIGHT)
				camera.framerate = FRAMERATE
				camera.hflip = HFLIP
				camera.vflip = VFLIP
				time.sleep(2)

				print("Starting the recording during %i seconds..." % RECORDING\_TIME)
				file\_name = dt.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d\_%H:%M')
				file\_name = str(VIDEO\_WIDTH) + angle + distance + file\_name
				motion\_file\_name = 'motion\_data/' + file\_name + '.data'
				camera.start\_recording(OUTPUT\_DIRECTORY +  file\_name + '.h264', format='h264', motion\_output=motion\_file\_name)
				camera.wait\_recording(RECORDING\_TIME)
				print("Stoping the recording...")
				camera.stop\_recording()
				print("Converting video to .mp4...")
				os.system("MP4Box -fps %i -add %s/%s.h264 %s/%s.mp4" % (FRAMERATE, OUTPUT\_DIRECTORY, file\_name, OUTPUT\_DIRECTORY, file\_name))


