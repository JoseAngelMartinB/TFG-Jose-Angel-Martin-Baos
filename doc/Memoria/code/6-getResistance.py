def getResistance(self, adc_value, mq_channel):
    """
    Calculate the current resistance of the sensor given its current voltage.

    Input:   adc_value -> Raw value form the ADC. Voltage = adc*Vref/1024
             mq_channel -> Analog channel where the MQ sensor is connected
    Output:  Current resistance of the sensor
    """
    resistance = 0.0
    if adc_value == 0: # Avoid division by 0
        adc_value = 1
    if(mq_channel == MQ7_CHANNEL):
        resistance = float(MQ7_RL*(1024.0-adc_value)/float(adc_value))
    elif(mq_channel == MQ2_CHANNEL):
        resistance = float(MQ2_RL*(1024.0-adc_value)/float(adc_value))

    return resistance
