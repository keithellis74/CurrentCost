import serial
import xml.etree.ElementTree as ET
import time
import datetime
import paho.mqtt.client as mqtt 
from influxdb import InfluxDBClient
import json

# Setup MQTT
mqttBroker ="192.168.54.30" 
client = mqtt.Client(client_id="CurrentCost")
client.connect(mqttBroker) 

# Setup Influx
influxclient = InfluxDBClient(host='192.168.54.30', port=8086)
influxclient.switch_database('CurrentCost')

# Setup serial connection
ser = serial.Serial(port='/dev/ttyAMA0',
                    baudrate=2400,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=120)

ser.close()
ser.open()


def getStream():
	inputBuffer = ""
	receiving = True
	while receiving == True:
		try:
			if ser.in_waiting > 0:
				x = ser.read(ser.in_waiting)
				inputBuffer = inputBuffer + str(x, 'utf-8')

				if inputBuffer.find("</msg>") > 0:
					tempbuf = inputBuffer.split("</msg>", 1)
					inputBuffer = tempbuf[1]
					tempbuf[0] = tempbuf[0]+"</msg>"

					root = ET.fromstring(tempbuf[0])

					temp = 0
					watts = 0

					for child in root:
						if child.tag == "tmpr" :
							temp = float(child.text)
						if child.tag == "ch1" :
							watts = int(child.find('watts').text)

					if watts > 0 :
						receiving = False
						return temp, watts
						#print("Temperature: ", temp)
						#print("Power: ", watts)


		except serial.SerialTimeoutException:
			print ("TimeOut Error")
		except serial.SerialException:
			print ("serial Error")
		except KeyboardInterrupt:
			print ("Closing down")
			receiving = False


def publishToMQTT(temp, watts, averageWatts):
	client.publish("homeassistant/currentcost/temperature", temp)
	client.publish("homeassistant/currentcost/power", watts)
	location = ["homeassistant/currentcost/average_power60s",
			"homeassistant/currentcost/average_power5m",
			"homeassistant/currentcost/average_power60m"]
	print("averageWatts = ", averageWatts)
	for i in range(len(averageWatts)):
		if averageWatts[i] > 0:
			client.publish(location[i], averageWatts[i])
			print("Publishing ", location[i], averageWatts[i])


def getAverage(data, count):
	if len(data) >= count:
		total = sum(data[-1:count*-1-1:-1])
		print("******** Average ********")
		print("Data = ", data)
		print("Count = ", count)
		print("Total = ", total)
		print("Average = ", int(total/count))
		print("Average data = ", data[-1:count*-1-1:-1])
		return int(total/count)
	else:
		return None


# Get date formatted for Influx
def getDate():
	date = datetime.datetime.now()
	return date.strftime("%Y-%m-%dT%H:%M:%S%Z")


# Data structure as required by InfluxDB
def createJson(temp, watts, averageWatts):
    #influx data json structure
	for i in range(len(averageWatts)):
		if averageWatts[i] == 0:
			averageWatts[i] = None

	json_body = [
        {
		"measurement": "powerUsage",

		"tags": {
			"resource": "electricity",
			"location": "20 Cedarcroft Road"
			},

		"time": getDate(),
		"fields": {
			"temperature": temp,
			"power": watts,
			"power_60s_avg": averageWatts[0],
			"power_5min_avg": averageWatts[1],
			"poer_60min_avg": averageWatts[2]
			}
		}
	]
	return json_body

def publishToInflux(temp, watts, averageWatts):
	data = createJson(temp, watts, averageWatts)
	influxclient.write_points(data)


def main():
	client.loop_start() # Start the MQTT loop
	looping = True
	averageDuration1 = 60 # time in seconds
	averageDuration2 = 60 * 5 # 5 minutes
	averageDuration3 = 60 * 60 # 1 hour
	counter = [0, 0, 0] # Store number of readings for each average, 60s, 5min and 60min
	data = []
	averageWatts = [0,0,0]  # store the latest average readings here
	now = time.perf_counter()
	calculateAverage1 = now + averageDuration1
	calculateAverage2 = now + averageDuration2
	calculateAverage3 = now + averageDuration3
	while(looping):
		try:
			temp, watts = getStream()  # Get the latest temperature and power readings from CurrentCost
			data.append(watts)
			for i in range(3):
				counter[i] += 1
			while len(data) > max(counter):
				data.pop(0)
			print("length of data = ", len(data))
			print("max counter = ", max(counter))

			# record data for 60 second average
			if time.perf_counter() > calculateAverage1:
				averageWatts[0] = getAverage(data, counter[0])
				print("Last 60 seconds average = ",averageWatts[0])
				data1 = []
				calculateAverage1 = time.perf_counter() + averageDuration1
				counter[0] = 0

			# record data for 5 munbute average
			if time.perf_counter() > calculateAverage2:
				averageWatts[1] =  getAverage(data, counter[1])
				print("Last 5 minute average = ", averageWatts[1])
				data2 = []
				calculateAverage2 = time.perf_counter() + averageDuration2
				counter[1] = 0

			# record data for 60 munbute average
			if time.perf_counter() > calculateAverage3:
				averageWatts[2] = getAverage(data, counter[2])
				print("Last 60 minute average = ",averageWatts[2])
				data3 = []
				calculateAverage3 = time.perf_counter() + averageDuration3
				counter[2] = 0

			print("Temperature = ", temp)
			print("Power = ", watts)
			publishToMQTT(temp, watts, averageWatts)
			publishToInflux(temp, watts, averageWatts)
#			print(createJson(temp, watts, averageWatts))
			averageWatts = [0,0,0]
			time.sleep(3)


		except KeyboardInterrupt:
				print ("Closing down")
				looping = False



if __name__ == "__main__":
	main()
	ser.close()
