import ibmiotf.device

# Initialize the device client.
try:
	deviceFile = "device.conf"
	deviceOptions = ibmiotf.device.ParseConfigFile(deviceFile)
	deviceClient = ibmiotf.device.Client(deviceOptions)
	deviceClient.connect()
except Exception as e:
	print(str(e))
	raise ProgramExit

# Send data variable (dictionary with all the sensor data) to Watson IoT Platform
success = deviceClient.publishEvent("sensor_update", "json", data, qos=0)
if not success:
    print("- Error: Not connected to IBM IoT Platform.")
else:
    print("* Event sent to cloud")

# Disconnect the device from the cloud
deviceClient.disconnect()
