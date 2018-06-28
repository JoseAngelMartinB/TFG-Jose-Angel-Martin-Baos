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
