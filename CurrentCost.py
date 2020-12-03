import serial
import xml.etree.ElementTree as ET
import time
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
	keepLooping = True
	inputBuffer = ""
	receiving = True
	while receiving == True and keepLooping == True:
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
			keepLooping = False


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


def getAverage(data):
	total = 0
	for watts in data:
		total += watts
	if len(data) != 0:
		return int(total/len(data))

def create_json(data):
    #influx data json structure
    json_body = [
        {
            "measurement": "CurrentCost",
            '''
			"tags": {
                "areaName": data["data"][0]["areaName"],
                "areaCode": data['data'][0]['areaCode']
            },
			'''
            "time": data["lastUpdate"],
            "fields": {
                "newCases": data['data'][0]['newCasesByPublishDate'],
                "cumulativeCases": data['data'][0]['cumCasesByPublishDate'],
                "newDeaths": data['data'][0]['newDeathsByDeathDate'],
                "cumulativeDeaths": data['data'][0]['cumDeathsByDeathDate']
            }
        }
    ]
    return json_body


def main():
	client.loop_start()
	looping = True
	averageDuration1 = 60 # time in seconds
	averageDuration2 = 60 * 5 # 5 minutes
	averageDuration3 = 60 * 60 # 1 hour
	data1 = []
	data2 = []
	data3 = []
	averageWatts = [0,0,0]
	calculateAverage1 = time.perf_counter() + averageDuration1
	calculateAverage2 = time.perf_counter() + averageDuration2
	calculateAverage3 = time.perf_counter() + averageDuration3
	while(looping):
		try:
			temp, watts = getStream()
			data1.append(watts)
			data2.append(watts)
			data3.append(watts)
			#print(data1)
			#print(data2)
			#print(data3)

			# record data for 60 second average
			if time.perf_counter() > calculateAverage1:
				averageWatts[0] = getAverage(data1)
				print("Last 60 seconds average = ",averageWatts[0])
				data1 = []
				calculateAverage1 = time.perf_counter() + averageDuration1

			# record data for 5 munbute average
			if time.perf_counter() > calculateAverage2:
				averageWatts[1] =  getAverage(data2)
				print("Last 5 minute average = ", averageWatts[1])
				data2 = []
				calculateAverage2 = time.perf_counter() + averageDuration2

			# record data for 60 munbute average
			if time.perf_counter() > calculateAverage3:
				averageWatts[2] = getAverage(data3)
				print("Last 60 minute average = ",averageWatts[2])
				data3 = []
				calculateAverage3 = time.perf_counter() + averageDuration3

			print("Temperature = ", temp)
			print("Power = ", watts)
			publishToMQTT(temp, watts, averageWatts)
			averageWatts = [0,0,0]
			time.sleep(3)


		except KeyboardInterrupt:
				print ("Closing down")
				looping = False



if __name__ == "__main__":
	main()
	ser.close()
