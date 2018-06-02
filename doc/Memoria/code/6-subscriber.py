from Persistence.DBBroker import DBBroker
import ibmiotf.application
import sys

# Auxiliar functions:
def sensorUpdate(event):
    """
    This method is executed everytime an event arrives with new data from the
    Raspberry Pi devices. The data is processed and stored into the database.

    Input:   event -> Event recived from IBM IoT.
    """
    data = event.data
    date_time = event.timestamp

    db = DBBroker()
    sql = "INSERT INTO data(idDevice, DateAndTime, Temperature, Humidity, Pressure, CO, LPG, VehiclesPerHour) \
            VALUES ('%s', '%s', '%f', '%f', '%f', '%f', '%f', '%f')" % \
            (data['idDevice'], data['date_time'], data['temperature'], data['humidity'], data['pressure'], data['CO'], data['LPG_gas'], data['vehicles_per_hour'])
    db.update(sql)

    print("Stored into the DB live data from %s (%s) sent at %s" % (event.deviceId, event.deviceType, date_time))

# Main Function
if __name__ == "__main__":
    # Initialize the application client for IBM IoT
    try:
        applicationFile = "application.conf"
        options = ibmiotf.application.ParseConfigFile(applicationFile)
        client = ibmiotf.application.Client(options)
    except Exception as e:
    	print("Caught exception connecting: %s" % str(e))
    	sys.exit()

    client.connect()
    client.subscribeToDeviceEvents(deviceType="Raspberry_Pi", event="sensor_update")
    client.deviceEventCallback = sensorUpdate
