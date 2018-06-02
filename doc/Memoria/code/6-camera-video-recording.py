#!/usr/bin/python3
# -*- coding: utf-8; mode: python -*-

import picamera

with picamera.PiCamera() as camera:
	camera.resolution = (VIDEO_WIDTH, VIDEO_HEIGHT)
	camera.framerate = FRAMERATE
	camera.hflip = HFLIP
	camera.vflip = VFLIP
	time.sleep(2)
	camera.start_recording('my_video.h264')
	camera.wait_recording(RECORDING_TIME)
	camera.stop_recording()
