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
